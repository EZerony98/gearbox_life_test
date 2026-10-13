"""齿轮箱寿命测试主窗口。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Mapping, Optional

import pyqtgraph as pg
from PySide6.QtCore import QMetaObject, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QColor, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QListWidgetItem, QMainWindow

from drivers.plc_fins import FinsPlcDriver
from models.station_state import StationState
from services.config_service import ConfigService
from services.data_service import DataService
from ui.station_card import StationCard
from ui.theme import APP_STYLE
from ui.ui_main import Ui_MainWindow
from workers.data_writer_worker import DataWriterWorker
from workers.device_worker import DeviceWorker


PROJECT_DIR = Path(__file__).resolve().parent.parent


class MainWindow(QMainWindow):
    """六工位寿命测试监控界面，数据只来自真实 PLC。"""

    HISTORY_COLORS = {
        "speed": "#d8132f",
        "current": "#4267b2",
        "torque": "#16875c",
        "temperature": "#e18428",
    }

    sample_for_storage = Signal(dict)
    event_for_storage = Signal(str, str, str)
    storage_start_requested = Signal(dict)
    plc_parameters_requested = Signal(int, dict)
    plc_run_requested = Signal(int, bool)

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        enable_storage: bool = True,
        enable_plc: bool = True,
    ) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setStyleSheet(APP_STYLE)

        self.config_service = ConfigService(PROJECT_DIR / "config")
        self.address_config = self.config_service.load("plc_addresses")
        self.device_config = self.config_service.load("devices")
        self.station_cards: Dict[int, StationCard] = {}
        self.stations: Dict[int, StationState] = {}
        self.history_curves: Dict[str, pg.PlotDataItem] = {}

        self._plc_connected = False
        self._plc_shutdown = False
        self._received_plc_data = False
        self._plc_thread: Optional[QThread] = None
        self._plc_worker: Optional[DeviceWorker] = None
        self._storage_ready = False
        self._storage_shutdown = False
        self._csv_sample_count = 0
        self._data_thread: Optional[QThread] = None
        self._data_worker: Optional[DataWriterWorker] = None
        self._session_path = ""

        self._setup_branding()
        self._build_stations()
        self._build_history_plot()
        self._connect_signals()
        self._initialize_disconnected_view()
        if enable_storage:
            self._setup_data_storage(data_dir or PROJECT_DIR / "data")
        if enable_plc:
            self._setup_plc()

        self.ui.mainSplitter.setSizes([610, 245])
        plc_config = self.device_config.get("plc", {})
        self.ui.statusbar.showMessage(
            f"真实设备模式｜FINS/UDP {plc_config.get('host', '--')}:{plc_config.get('port', '--')}｜未连接时不生成测试数据"
        )
        self._update_clock()
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start()

    def _setup_branding(self) -> None:
        image = QImage(str(PROJECT_DIR / "resources" / "logo.png"))
        if image.isNull():
            self.ui.brandLogo.setText("LOGO")
            return

        # 用户提供的图片带有较大透明/白色留边，显示时只截取实际图形区域。
        left, top, right, bottom = image.width(), image.height(), -1, -1
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                is_visible = color.alpha() > 8 and not (
                    color.red() > 248 and color.green() > 248 and color.blue() > 248
                )
                if is_visible:
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x)
                    bottom = max(bottom, y)
        if right >= left and bottom >= top:
            image = image.copy(left, top, right - left + 1, bottom - top + 1)
        pixmap = QPixmap.fromImage(image).scaled(
            200,
            56,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.ui.brandLogo.setPixmap(pixmap)

    def _build_stations(self) -> None:
        address_by_station = {
            int(item["station"]): item
            for item in self.address_config.get("stations", [])
        }
        for station_id in range(1, 7):
            state = StationState(station_id=station_id)
            self.stations[station_id] = state
            addresses = address_by_station.get(station_id, {})
            int_addresses = addresses.get("int", {})
            real_addresses = addresses.get("real", {})
            address_hint = (
                f"转速 {int_addresses.get('speed', '--')}  ·  "
                f"电流 {real_addresses.get('current', '--')}"
            )
            card = StationCard(
                station_id,
                address_hint,
                self.ui.stationScrollContents,
            )
            card.set_state(state, sync_parameters=True)
            self.station_cards[station_id] = card
            self.ui.stationGridLayout.addWidget(
                card, (station_id - 1) // 3, (station_id - 1) % 3
            )
            self.ui.stationGridLayout.setColumnStretch((station_id - 1) % 3, 1)
            self.ui.stationGridLayout.setRowStretch((station_id - 1) // 3, 1)
            self.ui.historyStationCombo.addItem(f"{station_id:02d} 号工位", station_id)

    def _build_history_plot(self) -> None:
        pg.setConfigOptions(antialias=True, foreground="#687586")
        self.history_plot = pg.PlotWidget(self.ui.historyPlotHost)
        plot_layout = QHBoxLayout(self.ui.historyPlotHost)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.history_plot)
        self.history_plot.setBackground("#fafbfc")
        self.history_plot.showGrid(x=True, y=True, alpha=0.18)
        self.history_plot.setLabel("left", "相对设定值", units="%")
        self.history_plot.setLabel("bottom", "测试时间", units="min")
        self.history_plot.setYRange(0, 125, padding=0.02)
        self.history_plot.addLegend(offset=(10, 5), brush="#ffffffdd", pen="#d7dde4")
        self.history_plot.getPlotItem().getAxis("left").setWidth(52)
        definitions = (
            ("speed", "转速 / 目标", 2.1),
            ("current", "电流 / 量程", 1.7),
            ("torque", "扭矩 / 目标", 1.7),
            ("temperature", "最高温 / 上限", 1.9),
        )
        for key, name, width in definitions:
            self.history_curves[key] = self.history_plot.plot(
                [], [], name=name, pen=pg.mkPen(self.HISTORY_COLORS[key], width=width)
            )

    def _connect_signals(self) -> None:
        for card in self.station_cards.values():
            card.start_requested.connect(self._start_station)
            card.stop_requested.connect(self._stop_station)
            card.parameters_requested.connect(self._apply_parameters)
            card.product_sn_changed.connect(self._set_product_sn)
            card.selected.connect(self._select_station)
        self.ui.startAllButton.clicked.connect(self._start_all)
        self.ui.stopAllButton.clicked.connect(self._stop_all)
        self.ui.settingsButton.clicked.connect(self._show_connection_settings)
        self.ui.historyStationCombo.currentIndexChanged.connect(
            self._refresh_history_plot
        )
        self.ui.resetViewButton.clicked.connect(self._fit_history)

    def _initialize_disconnected_view(self) -> None:
        self._set_plc_ui_state(False, "PLC 未连接")
        self._select_station(1)
        self._update_summary()
        self._refresh_history_plot()
        self._add_event(
            "系统", "界面初始化完成，等待 PLC 真实数据", persist=False
        )

    def _setup_plc(self) -> None:
        plc_config = self.device_config.get("plc", {})
        if not plc_config.get("enabled", False):
            self._set_plc_ui_state(False, "PLC 未启用")
            self._add_event(
                "PLC", "config/devices.json 中 PLC 未启用", level="WARNING", persist=False
            )
            return
        try:
            driver = FinsPlcDriver(plc_config, self.address_config)
        except Exception as error:
            self._set_plc_ui_state(False, "PLC 配置错误")
            self._add_event("PLC", str(error), level="ERROR", persist=False)
            return

        self._plc_thread = QThread(self)
        self._plc_thread.setObjectName("finsPlcWorkerThread")
        self._plc_worker = DeviceWorker(
            driver,
            poll_interval_ms=int(plc_config.get("poll_interval_ms", 1000)),
            reconnect_interval_ms=int(
                plc_config.get("reconnect_interval_ms", 3000)
            ),
        )
        self._plc_worker.moveToThread(self._plc_thread)
        self._plc_thread.started.connect(self._plc_worker.start)
        self._plc_worker.data_ready.connect(self._on_plc_data)
        self._plc_worker.connection_changed.connect(
            self._on_plc_connection_changed
        )
        self._plc_worker.operation_finished.connect(self._on_plc_operation_finished)
        self.plc_parameters_requested.connect(
            self._plc_worker.write_parameters, Qt.ConnectionType.QueuedConnection
        )
        self.plc_run_requested.connect(
            self._plc_worker.set_running, Qt.ConnectionType.QueuedConnection
        )
        self._plc_thread.start()
        application = QApplication.instance()
        if application is not None:
            application.aboutToQuit.connect(self._shutdown_plc)

    def _on_plc_connection_changed(self, connected: bool, message: str) -> None:
        was_connected = self._plc_connected
        self._set_plc_ui_state(connected, "PLC 已连接" if connected else "PLC 未连接")
        self.ui.plcStatusLabel.setToolTip(message)
        if connected and not was_connected:
            self._add_event("PLC", "FINS/UDP 通讯已建立")
        elif not connected:
            for station_id, state in self.stations.items():
                state.mark_disconnected()
                self.station_cards[station_id].set_state(state)
            self._update_summary()
            if was_connected or not self._received_plc_data:
                self._add_event("PLC", f"未连接：{message}", level="WARNING")

    def _set_plc_ui_state(self, connected: bool, text: str) -> None:
        self._plc_connected = connected
        self.ui.plcStatusLabel.setText(f"● {text}")
        self.ui.plcStatusLabel.setProperty("connected", connected)
        self.ui.plcStatusLabel.style().unpolish(self.ui.plcStatusLabel)
        self.ui.plcStatusLabel.style().polish(self.ui.plcStatusLabel)
        self.ui.startAllButton.setEnabled(connected)
        self.ui.stopAllButton.setEnabled(connected)

    def _on_plc_data(self, payload: Dict[str, object]) -> None:
        timestamp = datetime.now().astimezone()
        first_snapshot = not self._received_plc_data
        stations = payload.get("stations", [])
        if not isinstance(stations, list):
            return
        for snapshot in stations:
            if not isinstance(snapshot, Mapping):
                continue
            station_id = int(snapshot.get("station_id", 0))
            if station_id not in self.stations:
                continue
            state = self.stations[station_id]
            state.apply_plc_snapshot(snapshot, record=True)
            self.station_cards[station_id].set_state(
                state, sync_parameters=first_snapshot
            )
            if state.running and self._storage_ready:
                self.sample_for_storage.emit(self._sample_record(state, timestamp))
                self._csv_sample_count += 1
        self._received_plc_data = True
        self._update_summary()
        self._refresh_history_plot()

    def _on_plc_operation_finished(
        self, operation: str, station_id: int, succeeded: bool, message: str
    ) -> None:
        names = {"start": "启动", "stop": "停止", "parameters": "参数写入"}
        action = names.get(operation, operation)
        level = "INFO" if succeeded else "ERROR"
        self._add_event(
            f"{station_id:02d} 号工位",
            f"{action}{'成功' if succeeded else '失败'}：{message}",
            level=level,
        )

    def _show_connection_settings(self) -> None:
        plc_config = self.device_config.get("plc", {})
        self._add_event(
            "系统",
            f"PLC 通讯：FINS/UDP {plc_config.get('host')}:{plc_config.get('port')}",
        )

    def _update_clock(self) -> None:
        self.ui.clockLabel.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _start_station(self, station_id: int) -> None:
        state = self.stations[station_id]
        if not self._plc_connected:
            self._add_event(
                f"{station_id:02d} 号工位", "PLC 未连接，不能启动", level="WARNING"
            )
            return
        if not state.enabled:
            self._add_event(
                f"{station_id:02d} 号工位", "PLC 反馈工位未使能", level="WARNING"
            )
            return
        product_sn = self.station_cards[station_id].serial_edit.text().strip()
        if not product_sn:
            self._add_event(
                f"{station_id:02d} 号工位",
                "未输入产品 SN，不能启动测试",
                level="WARNING",
            )
            self.station_cards[station_id].serial_edit.setFocus()
            return
        state.serial_number = product_sn
        self.plc_run_requested.emit(station_id, True)

    def _stop_station(self, station_id: int) -> None:
        if not self._plc_connected:
            self._add_event(
                f"{station_id:02d} 号工位", "PLC 未连接，不能下发停止指令", level="WARNING"
            )
            return
        self.plc_run_requested.emit(station_id, False)

    def _start_all(self) -> None:
        for station_id in self.stations:
            self._start_station(station_id)

    def _stop_all(self) -> None:
        if not self._plc_connected:
            self._add_event("全部工位", "PLC 未连接，不能下发停止指令", level="WARNING")
            return
        for station_id in self.stations:
            self.plc_run_requested.emit(station_id, False)

    def _apply_parameters(self, station_id: int, values: Dict[str, object]) -> None:
        if not self._plc_connected:
            self._add_event(
                f"{station_id:02d} 号工位", "PLC 未连接，参数未写入", level="WARNING"
            )
            return
        if float(values["temperature_low"]) >= float(values["temperature_high"]):
            self._add_event(
                f"{station_id:02d} 号工位",
                "温度下限必须小于温度上限",
                level="WARNING",
            )
            return
        serial_number = str(values["serial_number"])
        self._set_product_sn(station_id, serial_number)
        self.plc_parameters_requested.emit(station_id, values)

    def _set_product_sn(self, station_id: int, product_sn: str) -> None:
        state = self.stations[station_id]
        product_sn = product_sn.strip()
        if state.running and product_sn != state.serial_number:
            self.station_cards[station_id].serial_edit.setText(state.serial_number)
            self._add_event(
                f"{station_id:02d} 号工位",
                "测试运行中不能更换产品 SN，请先停止测试",
                level="WARNING",
            )
            return
        if product_sn != state.serial_number:
            old_sn = state.serial_number
            state.serial_number = product_sn
            self._add_event(
                f"{station_id:02d} 号工位",
                f"产品 SN 已由 {old_sn or '空'} 更新为 {product_sn or '空'}",
            )

    def _select_station(self, station_id: int) -> None:
        for current_id, card in self.station_cards.items():
            card.set_selected(current_id == station_id)
        combo_index = self.ui.historyStationCombo.findData(station_id)
        if combo_index >= 0 and combo_index != self.ui.historyStationCombo.currentIndex():
            self.ui.historyStationCombo.setCurrentIndex(combo_index)
        self._refresh_history_plot()

    def _refresh_history_plot(self, _index: int = -1) -> None:
        station_id = self.ui.historyStationCombo.currentData()
        if station_id is None:
            return
        state = self.stations[int(station_id)]
        x_values = state.history["minutes"]
        for key, curve in self.history_curves.items():
            curve.setData(x_values, state.history[key])

    def _fit_history(self) -> None:
        self.history_plot.enableAutoRange(x=True, y=False)
        self.history_plot.setYRange(0, 125, padding=0.02)

    def _update_summary(self) -> None:
        running = sum(1 for state in self.stations.values() if state.running)
        warnings = sum(1 for state in self.stations.values() if state.warning)
        self.ui.runningCountLabel.setText(f"运行  {running}")
        self.ui.warningCountLabel.setText(f"告警  {warnings}")
        if self._storage_ready:
            self.ui.recordStateLabel.setText(f"● CSV 已提交 {self._csv_sample_count:,} 条")

    def _add_event(
        self, source: str, message: str, level: str = "INFO", persist: bool = True
    ) -> None:
        item = QListWidgetItem(f"{datetime.now():%H:%M:%S}   {source}  {message}")
        if level in {"WARNING", "ERROR"} or "告警" in message or "超过" in message:
            item.setForeground(QColor("#b65d11" if level == "WARNING" else "#b42334"))
        elif "成功" in message or "完成" in message or "已建立" in message:
            item.setForeground(QColor("#15734f"))
        self.ui.eventList.insertItem(0, item)
        while self.ui.eventList.count() > 30:
            self.ui.eventList.takeItem(self.ui.eventList.count() - 1)
        if persist and self._storage_ready:
            self.event_for_storage.emit(source, message, level)

    def _setup_data_storage(self, data_dir: Path) -> None:
        process_config = self.config_service.load("process")
        storage_config = process_config.get("storage", {})
        service = DataService(
            data_dir,
            flush_interval_seconds=int(
                storage_config.get("flush_interval_seconds", 5)
            ),
            fsync_interval_seconds=int(
                storage_config.get("fsync_interval_seconds", 60)
            ),
            minimum_free_space_gb=float(
                storage_config.get("minimum_free_space_gb", 5)
            ),
        )
        self._data_thread = QThread(self)
        self._data_thread.setObjectName("csvDataWriterThread")
        self._data_worker = DataWriterWorker(service)
        self._data_worker.moveToThread(self._data_thread)
        self.storage_start_requested.connect(
            self._data_worker.start_session, Qt.ConnectionType.QueuedConnection
        )
        self.sample_for_storage.connect(
            self._data_worker.write_sample, Qt.ConnectionType.QueuedConnection
        )
        self.event_for_storage.connect(
            self._data_worker.write_event, Qt.ConnectionType.QueuedConnection
        )
        self._data_worker.session_started.connect(self._on_storage_started)
        self._data_worker.error.connect(self._on_storage_error)
        self._data_thread.start()
        application = QApplication.instance()
        if application is not None:
            application.aboutToQuit.connect(self._shutdown_storage)
        self.ui.recordStateLabel.setText("● 正在建立 CSV 记录")
        self.storage_start_requested.emit(
            {
                "test_name": "齿轮箱寿命测试",
                "station_count": 6,
                "sample_interval_seconds": int(
                    process_config.get("sample_interval_seconds", 1)
                ),
                "mode": "real_plc",
                "plc_protocol": "FINS/UDP",
                "product_sn_by_station": {
                    str(station_id): state.serial_number
                    for station_id, state in self.stations.items()
                },
            }
        )

    def _on_storage_started(self, session_path: str) -> None:
        self._storage_ready = True
        self._session_path = session_path
        self.ui.recordStateLabel.setText("● CSV 记录就绪")
        self.ui.recordStateLabel.setToolTip(session_path)
        self._add_event("数据存储", f"CSV 会话已建立：{Path(session_path).name}")

    def _on_storage_error(self, message: str) -> None:
        self._storage_ready = False
        self.ui.recordStateLabel.setText("● CSV 存储异常")
        self.ui.recordStateLabel.setStyleSheet("color: #b42334;")
        self._add_event("数据存储", message, level="ERROR", persist=False)

    @staticmethod
    def _sample_record(state: StationState, timestamp: datetime) -> Dict[str, object]:
        realtime = state.realtime
        parameters = state.parameters
        return {
            "sample_no": state.sample_count,
            "timestamp_local": timestamp.isoformat(timespec="milliseconds"),
            "elapsed_seconds": state.elapsed_seconds,
            "station_id": state.station_id,
            "product_sn": state.serial_number,
            "speed_rpm": round(realtime.speed_rpm, 3),
            "current_a": round(realtime.current_a, 4),
            "pressure": round(realtime.pressure, 4),
            "torque_nm": round(realtime.torque_nm, 4),
            "temperature_1_c": round(realtime.temperature_1, 3),
            "temperature_2_c": round(realtime.temperature_2, 3),
            "temperature_3_c": round(realtime.temperature_3, 3),
            "target_speed_rpm": parameters.speed_rpm,
            "target_torque_nm": parameters.torque_target,
            "pressure_compensation": parameters.pressure_compensation,
            "temperature_high_c": parameters.temperature_high,
            "temperature_low_c": parameters.temperature_low,
            "running": int(state.running),
            "warning": int(state.warning),
            "data_quality": "PLC",
        }

    def _shutdown_plc(self) -> None:
        if self._plc_shutdown:
            return
        self._plc_shutdown = True
        if (
            self._plc_thread is not None
            and self._plc_worker is not None
            and self._plc_thread.isRunning()
        ):
            QMetaObject.invokeMethod(
                self._plc_worker,
                "stop",
                Qt.ConnectionType.BlockingQueuedConnection,
            )
            self._plc_thread.quit()
            self._plc_thread.wait(5000)

    def _shutdown_storage(self) -> None:
        if self._storage_shutdown:
            return
        self._storage_shutdown = True
        if hasattr(self, "_clock_timer"):
            self._clock_timer.stop()
        if (
            self._data_thread is not None
            and self._data_worker is not None
            and self._data_thread.isRunning()
        ):
            QMetaObject.invokeMethod(
                self._data_worker,
                "stop_session",
                Qt.ConnectionType.BlockingQueuedConnection,
            )
            self._data_thread.quit()
            self._data_thread.wait(5000)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._shutdown_plc()
        self._shutdown_storage()
        super().closeEvent(event)
