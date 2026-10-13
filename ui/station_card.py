"""可复用的单工位监控卡片。"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from models.station_state import StationState


class MetricTile(QFrame):
    def __init__(self, name: str, unit: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricTile")
        self.setMinimumHeight(44)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 4, 7, 4)
        layout.setSpacing(0)
        self.name_label = QLabel(name, self)
        self.name_label.setObjectName("metricName")
        value_row = QHBoxLayout()
        value_row.setSpacing(3)
        self.value_label = QLabel("--", self)
        self.value_label.setObjectName("metricValue")
        unit_label = QLabel(unit, self)
        unit_label.setObjectName("metricUnit")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        value_row.addWidget(self.value_label)
        value_row.addWidget(unit_label)
        value_row.addStretch()
        layout.addWidget(self.name_label)
        layout.addLayout(value_row)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class StationCard(QFrame):
    enable_requested = Signal(int, bool)
    start_requested = Signal(int)
    pause_requested = Signal(int, bool)
    stop_requested = Signal(int)
    parameters_requested = Signal(int, dict)
    product_sn_changed = Signal(int, str)
    selected = Signal(int)

    def __init__(self, station_id: int, address_hint: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.station_id = station_id
        self.setObjectName("stationCard")
        self.setProperty("state", "standby")
        self.setProperty("selected", False)
        self.setMinimumSize(360, 278)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._metrics: Dict[str, MetricTile] = {}
        self._station_enabled = False
        self._station_paused = False
        self._build_ui(address_hint)

    def _build_ui(self, address_hint: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(11, 8, 11, 8)
        root.setSpacing(5)

        header = QHBoxLayout()
        header.setSpacing(7)
        title = QLabel(f"{self.station_id:02d} 号工位", self)
        title.setObjectName("stationNumber")
        self.status_label = QLabel("待机", self)
        self.status_label.setObjectName("stationStatus")
        self.status_label.setProperty("state", "standby")
        self.elapsed_label = QLabel("00:00:00", self)
        self.elapsed_label.setObjectName("elapsedLabel")
        header.addWidget(title)
        header.addWidget(self.status_label)
        header.addStretch()
        header.addWidget(QLabel("运行时间", self))
        header.addWidget(self.elapsed_label)
        root.addLayout(header)

        serial_row = QHBoxLayout()
        serial_row.setSpacing(6)
        caption = QLabel("产品 SN", self)
        caption.setObjectName("fieldCaption")
        self.serial_edit = QLineEdit(self)
        self.serial_edit.setObjectName("serialEdit")
        self.serial_edit.setPlaceholderText("请输入或扫描齿轮箱产品 SN")
        self.serial_edit.setClearButtonEnabled(True)
        serial_row.addWidget(caption)
        serial_row.addWidget(self.serial_edit)
        root.addLayout(serial_row)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(5)
        metrics.setVerticalSpacing(5)
        definitions = (
            ("speed", "实时转速", "rpm"),
            ("current", "实时电流", "mA"),
            ("torque", "实时扭矩", "N·m"),
            ("pressure", "实时压力", ""),
            ("temperature_1", "电机温度", "℃"),
            ("temperature_2", "齿轮箱温度", "℃"),
            ("temperature_3", "制动器温度", "℃"),
            ("records", "记录点", "条"),
        )
        for index, (key, name, unit) in enumerate(definitions):
            tile = MetricTile(name, unit, self)
            self._metrics[key] = tile
            metrics.addWidget(tile, index // 4, index % 4)
        root.addLayout(metrics)

        parameter_panel = QFrame(self)
        parameter_panel.setObjectName("parameterPanel")
        parameter_layout = QVBoxLayout(parameter_panel)
        parameter_layout.setContentsMargins(0, 4, 0, 4)
        parameter_layout.setSpacing(3)
        parameter_header = QHBoxLayout()
        parameter_title = QLabel("工位参数", parameter_panel)
        parameter_title.setObjectName("paramCaption")
        self.apply_button = QPushButton("写入参数", parameter_panel)
        self.apply_button.setObjectName("applyButton")
        parameter_header.addWidget(parameter_title)
        parameter_header.addStretch()
        parameter_header.addWidget(self.apply_button)
        parameter_layout.addLayout(parameter_header)

        parameter_grid = QGridLayout()
        parameter_grid.setHorizontalSpacing(5)
        parameter_grid.setVerticalSpacing(2)
        self.speed_spin = QSpinBox(parameter_panel)
        self.speed_spin.setRange(0, 12000)
        self.speed_spin.setSingleStep(50)
        self.speed_spin.setSuffix(" rpm")
        self.torque_spin = QDoubleSpinBox(parameter_panel)
        self.torque_spin.setRange(0.0, 50.0)
        self.torque_spin.setDecimals(2)
        self.torque_spin.setSuffix(" N·m")
        self.pressure_spin = QDoubleSpinBox(parameter_panel)
        self.pressure_spin.setRange(-100.0, 100.0)
        self.pressure_spin.setDecimals(2)
        self.temp_high_spin = QDoubleSpinBox(parameter_panel)
        self.temp_high_spin.setRange(0.0, 200.0)
        self.temp_high_spin.setSuffix(" ℃")
        self.temp_low_spin = QDoubleSpinBox(parameter_panel)
        self.temp_low_spin.setRange(-50.0, 100.0)
        self.temp_low_spin.setSuffix(" ℃")
        fields: Tuple[Tuple[str, QWidget], ...] = (
            ("目标转速", self.speed_spin),
            ("目标扭矩", self.torque_spin),
            ("压力补偿", self.pressure_spin),
            ("温度上限", self.temp_high_spin),
            ("温度下限", self.temp_low_spin),
        )
        for column, (label_text, editor) in enumerate(fields):
            label = QLabel(label_text, parameter_panel)
            label.setObjectName("paramCaption")
            parameter_grid.addWidget(label, 0, column)
            parameter_grid.addWidget(editor, 1, column)
        parameter_layout.addLayout(parameter_grid)
        root.addWidget(parameter_panel)

        footer = QHBoxLayout()
        footer.setSpacing(6)
        self.address_label = QLabel(address_hint, self)
        self.address_label.setObjectName("addressHint")
        self.enable_button = QPushButton("启用工位", self)
        self.enable_button.setObjectName("stationEnableButton")
        self.enable_button.setProperty("stationEnabled", False)
        self.start_button = QPushButton("启动测试", self)
        self.start_button.setObjectName("stationStartButton")
        self.pause_button = QPushButton("暂停", self)
        self.pause_button.setObjectName("stationPauseButton")
        self.pause_button.setProperty("paused", False)
        self.stop_button = QPushButton("停止", self)
        self.stop_button.setObjectName("stationStopButton")
        footer.addWidget(self.address_label)
        footer.addStretch()
        footer.addWidget(self.enable_button)
        footer.addWidget(self.start_button)
        footer.addWidget(self.pause_button)
        footer.addWidget(self.stop_button)
        root.addLayout(footer)

        self.enable_button.clicked.connect(self._emit_enable_request)
        self.start_button.clicked.connect(lambda: self.start_requested.emit(self.station_id))
        self.pause_button.clicked.connect(self._emit_pause_request)
        self.stop_button.clicked.connect(lambda: self.stop_requested.emit(self.station_id))
        self.apply_button.clicked.connect(self._emit_parameters)
        self.serial_edit.editingFinished.connect(self._emit_product_sn)

    def _emit_enable_request(self) -> None:
        self.enable_requested.emit(self.station_id, not self._station_enabled)

    def _emit_pause_request(self) -> None:
        self.pause_requested.emit(self.station_id, not self._station_paused)

    def _emit_product_sn(self) -> None:
        self.product_sn_changed.emit(self.station_id, self.serial_edit.text().strip())

    def _emit_parameters(self) -> None:
        self.parameters_requested.emit(
            self.station_id,
            {
                "speed_rpm": self.speed_spin.value(),
                "torque_target": self.torque_spin.value(),
                "pressure_compensation": self.pressure_spin.value(),
                "temperature_high": self.temp_high_spin.value(),
                "temperature_low": self.temp_low_spin.value(),
                "serial_number": self.serial_edit.text().strip(),
            },
        )

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_state(self, state: StationState, sync_parameters: bool = False) -> None:
        self.setProperty("state", state.status_key)
        self.status_label.setProperty("state", state.status_key)
        self.status_label.setText(state.status_text)
        self.elapsed_label.setText(state.elapsed_text() if state.connected else "--:--:--")
        if sync_parameters:
            self.serial_edit.setText(state.serial_number)
            self.speed_spin.setValue(state.parameters.speed_rpm)
            self.torque_spin.setValue(state.parameters.torque_target)
            self.pressure_spin.setValue(state.parameters.pressure_compensation)
            self.temp_high_spin.setValue(state.parameters.temperature_high)
            self.temp_low_spin.setValue(state.parameters.temperature_low)
        if state.connected:
            self._metrics["speed"].set_value(f"{state.realtime.speed_rpm:,.0f}")
            self._metrics["current"].set_value(f"{state.realtime.current_ma:,.0f}")
            self._metrics["torque"].set_value(f"{state.realtime.torque_nm:.4f}")
            self._metrics["pressure"].set_value(f"{state.realtime.pressure:.4f}")
            self._metrics["temperature_1"].set_value(
                f"{state.realtime.temperature_1:.1f}"
            )
            self._metrics["temperature_2"].set_value(
                f"{state.realtime.temperature_2:.1f}"
            )
            self._metrics["temperature_3"].set_value(
                f"{state.realtime.temperature_3:.1f}"
            )
            self._metrics["records"].set_value(f"{state.sample_count:,}")
        else:
            for metric in self._metrics.values():
                metric.set_value("--")

        can_operate = state.connected and state.enabled
        test_active = state.running or state.paused
        self._station_enabled = state.enabled
        self._station_paused = state.paused
        self.enable_button.setText("停用工位" if state.enabled else "启用工位")
        self.enable_button.setProperty("stationEnabled", state.enabled)
        self.enable_button.setEnabled(state.connected)
        self.start_button.setEnabled(can_operate and not test_active)
        self.pause_button.setText("继续" if state.paused else "暂停")
        self.pause_button.setProperty("paused", state.paused)
        self.pause_button.setEnabled(can_operate and test_active)
        self.stop_button.setEnabled(can_operate and test_active)
        self.apply_button.setEnabled(can_operate and not test_active)
        self.serial_edit.setEnabled(not test_active)
        unavailable_hint = "" if state.connected else "PLC 未连接，设备操作已锁定"
        self.start_button.setToolTip(unavailable_hint)
        self.pause_button.setToolTip(unavailable_hint)
        self.stop_button.setToolTip(unavailable_hint)
        self.apply_button.setToolTip(unavailable_hint)
        self.enable_button.setToolTip(unavailable_hint)
        self.style().unpolish(self)
        self.style().polish(self)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.enable_button.style().unpolish(self.enable_button)
        self.enable_button.style().polish(self.enable_button)
        self.pause_button.style().unpolish(self.pause_button)
        self.pause_button.style().polish(self.pause_button)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.selected.emit(self.station_id)
        super().mousePressEvent(event)
