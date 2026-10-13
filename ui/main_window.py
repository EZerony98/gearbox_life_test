"""齿轮箱寿命测试主窗口与首版交互演示。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pyqtgraph as pg
from PySide6.QtCore import QMetaObject, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QColor
from PySide6.QtWidgets import QApplication, QHBoxLayout, QListWidgetItem, QMainWindow

from models.station_state import StationParameters, StationState
from services.config_service import ConfigService
from services.data_service import DataService
from ui.station_card import StationCard
from ui.theme import APP_STYLE
from ui.ui_main import Ui_MainWindow
from workers.data_writer_worker import DataWriterWorker


PROJECT_DIR = Path(__file__).resolve().parent.parent


class MainWindow(QMainWindow):
    """六工位寿命测试监控界面。

    当前版本使用确定性模拟数据展示交互效果；PLC 配置只读加载，不执行写入。
    """

    HISTORY_COLORS = {
        "speed": "#2e82ff",
        "current": "#9b59d0",
        "torque": "#16a085",
        "temperature": "#e07a2d",
    }

    sample_for_storage = Signal(dict)
    event_for_storage = Signal(str, str, str)
    storage_start_requested = Signal(dict)

    def __init__(
        self, data_dir: Optional[Path] = None, enable_storage: bool = True
    ) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setStyleSheet(APP_STYLE)
        self.station_cards: Dict[int, StationCard] = {}
        self.stations: Dict[int, StationState] = {}
        self.history_curves: Dict[str, pg.PlotDataItem] = {}
        self._storage_ready = False
        self._storage_shutdown = False
        self._csv_sample_count = 0
        self._data_thread: Optional[QThread] = None
        self._data_worker: Optional[DataWriterWorker] = None
        self._session_path = ""
        self._build_stations()
        self._build_history_plot()
        self._connect_signals()
        self._seed_demo_data()
        if enable_storage:
            self._setup_data_storage(data_dir or PROJECT_DIR / "data")
        self.ui.mainSplitter.setSizes([610, 245])
        self.ui.statusbar.showMessage(
            "演示模式｜PLC 地址已从 地址内容.xlsx 整理到 config/plc_addresses.json｜当前不会写入设备"
        )
        self._update_clock()
        self._sample_timer = QTimer(self)
        self._sample_timer.setInterval(1000)
        self._sample_timer.timeout.connect(self._on_sample_tick)
        self._sample_timer.start()

    def _build_stations(self) -> None:
        for station_id in range(1, 7):
            parameters = StationParameters(
                speed_rpm=1350 + station_id * 120,
                torque_target=3.4 + station_id * 0.25,
                pressure_compensation=round((station_id - 3) * 0.15, 2),
                temperature_high=75.0 if station_id == 5 else 85.0,
                temperature_low=5.0,
            )
            state = StationState(
                station_id=station_id,
                serial_number=f"GBX-2610-{station_id:02d}",
                parameters=parameters,
                running=station_id in {1, 3, 5, 6},
                demo_warning=station_id == 5,
            )
            self.stations[station_id] = state
            speed_address = 3508 + station_id
            current_address = 3700 + station_id * 2
            card = StationCard(
                station_id,
                f"转速 %D{speed_address}  ·  电流 %D{current_address}",
                self.ui.stationScrollContents,
            )
            self.station_cards[station_id] = card
            self.ui.stationGridLayout.addWidget(card, (station_id - 1) // 3, (station_id - 1) % 3)
            self.ui.stationGridLayout.setColumnStretch((station_id - 1) % 3, 1)
            self.ui.stationGridLayout.setRowStretch((station_id - 1) // 3, 1)
            self.ui.historyStationCombo.addItem(f"{station_id:02d} 号工位", station_id)

    def _build_history_plot(self) -> None:
        pg.setConfigOptions(antialias=True, foreground="#68798b")
        self.history_plot = pg.PlotWidget(self.ui.historyPlotHost)
        plot_layout = QHBoxLayout(self.ui.historyPlotHost)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.history_plot)
        self.history_plot.setBackground("#f8fafc")
        self.history_plot.showGrid(x=True, y=True, alpha=0.18)
        self.history_plot.setLabel("left", "相对设定值", units="%")
        self.history_plot.setLabel("bottom", "测试时间", units="min")
        self.history_plot.setYRange(0, 125, padding=0.02)
        self.history_plot.addLegend(offset=(10, 5), brush="#ffffffdd", pen="#d7e0e8")
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
        self.ui.settingsButton.clicked.connect(
            lambda: self._add_event("系统", "设置入口已预留，待确认 PLC 通讯参数")
        )
        self.ui.historyStationCombo.currentIndexChanged.connect(self._refresh_history_plot)
        self.ui.resetViewButton.clicked.connect(self._fit_history)

    def _seed_demo_data(self) -> None:
        for _ in range(95):
            for state in self.stations.values():
                state.simulate_tick(record=True)
        for station_id, card in self.station_cards.items():
            card.set_state(self.stations[station_id], sync_parameters=True)
        self._select_station(1)
        self._update_summary()
        self._refresh_history_plot()
        self._add_event("系统", "界面初始化完成，当前为模拟数据")
        self._add_event("05 号工位", "温度 1 超过设定上限，请检查负载")
        self._add_event("03 号工位", "开始测试并建立数据记录")
        self._add_event("PLC", "通讯未启用，设备写入已锁定")

    def _on_sample_tick(self) -> None:
        self._update_clock()
        timestamp = datetime.now().astimezone()
        for station_id, state in self.stations.items():
            state.simulate_tick(record=True)
            self.station_cards[station_id].set_state(state)
            if state.running and self._storage_ready:
                self.sample_for_storage.emit(self._sample_record(state, timestamp))
                self._csv_sample_count += 1
        self._update_summary()
        self._refresh_history_plot()

    def _update_clock(self) -> None:
        self.ui.clockLabel.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _start_station(self, station_id: int) -> None:
        state = self.stations[station_id]
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
        state.running = True
        self._add_event(f"{station_id:02d} 号工位", "测试已启动，开始记录实时数据")
        self.station_cards[station_id].set_state(state)

    def _stop_station(self, station_id: int) -> None:
        state = self.stations[station_id]
        state.running = False
        state.demo_warning = False
        state.warning = False
        self._add_event(f"{station_id:02d} 号工位", "测试已停止，记录保持可追溯")
        self.station_cards[station_id].set_state(state)

    def _start_all(self) -> None:
        for station_id in self.stations:
            self._start_station(station_id)
        self._add_event("全部工位", "已执行演示启动，缺少产品 SN 的工位已跳过")

    def _stop_all(self) -> None:
        for state in self.stations.values():
            state.running = False
            state.demo_warning = False
            state.warning = False
        self._add_event("全部工位", "已执行演示停止")

    def _apply_parameters(self, station_id: int, values: Dict[str, object]) -> None:
        state = self.stations[station_id]
        state.parameters.speed_rpm = int(values["speed_rpm"])
        state.parameters.torque_target = float(values["torque_target"])
        state.parameters.pressure_compensation = float(values["pressure_compensation"])
        state.parameters.temperature_high = float(values["temperature_high"])
        state.parameters.temperature_low = float(values["temperature_low"])
        serial_number = str(values["serial_number"])
        self._set_product_sn(station_id, serial_number)
        self._add_event(f"{station_id:02d} 号工位", "参数已保存到界面缓存，未写入 PLC")
        self.station_cards[station_id].set_state(state, sync_parameters=True)

    def _set_product_sn(self, station_id: int, product_sn: str) -> None:
        state = self.stations[station_id]
        product_sn = product_sn.strip()
        if not product_sn:
            return
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
                f"产品 SN 已由 {old_sn or '空'} 更新为 {product_sn}",
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
        if "告警" in message or "超过" in message:
            item.setForeground(QColor("#b85e0c"))
        elif "启动" in message or "完成" in message:
            item.setForeground(QColor("#15754d"))
        self.ui.eventList.insertItem(0, item)
        while self.ui.eventList.count() > 30:
            self.ui.eventList.takeItem(self.ui.eventList.count() - 1)
        if persist and self._storage_ready:
            self.event_for_storage.emit(source, message, level)

    def _setup_data_storage(self, data_dir: Path) -> None:
        process_config = ConfigService(PROJECT_DIR / "config").load("process")
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
                "mode": "demo",
                "product_sn_by_station": {
                    str(station_id): state.serial_number
                    for station_id, state in self.stations.items()
                },
            }
        )

    def _on_storage_started(self, session_path: str) -> None:
        self._storage_ready = True
        self._session_path = session_path
        self.ui.recordStateLabel.setText("● CSV 记录中")
        self.ui.recordStateLabel.setToolTip(session_path)
        self._add_event("数据存储", f"CSV 会话已建立：{Path(session_path).name}")

    def _on_storage_error(self, message: str) -> None:
        self._storage_ready = False
        self.ui.recordStateLabel.setText("● CSV 存储异常")
        self.ui.recordStateLabel.setStyleSheet("color: #b4232f;")
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
            "data_quality": "SIMULATED",
        }

    def _shutdown_storage(self) -> None:
        if self._storage_shutdown:
            return
        self._storage_shutdown = True
        if hasattr(self, "_sample_timer"):
            self._sample_timer.stop()
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
        self._shutdown_storage()
        super().closeEvent(event)
