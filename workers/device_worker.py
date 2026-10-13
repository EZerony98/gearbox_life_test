"""PLC 连接、轮询和写入后台任务。"""

from __future__ import annotations

import time
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from drivers.base_device import BaseDevice


class DeviceWorker(QObject):
    """在独立线程中轮询 PLC，断线后按间隔自动重连。"""

    data_ready = Signal(dict)
    connection_changed = Signal(bool, str)
    operation_finished = Signal(str, int, bool, str)
    finished = Signal()

    def __init__(
        self,
        device: BaseDevice,
        poll_interval_ms: int = 1000,
        reconnect_interval_ms: int = 3000,
    ) -> None:
        super().__init__()
        self.device = device
        self.poll_interval_ms = max(100, int(poll_interval_ms))
        self.reconnect_interval_ms = max(500, int(reconnect_interval_ms))
        self._timer: Optional[QTimer] = None
        self._stopping = False
        self._next_connect_at = 0.0
        self._reported_connected: Optional[bool] = None

    @Slot()
    def start(self) -> None:
        if self._timer is not None:
            return
        self._stopping = False
        self._timer = QTimer(self)
        self._timer.setInterval(self.poll_interval_ms)
        self._timer.timeout.connect(self.poll_once)
        self._timer.start()
        self.poll_once()

    @Slot()
    def poll_once(self) -> None:
        if self._stopping:
            return
        if not self.device.is_connected and time.monotonic() < self._next_connect_at:
            return
        try:
            if not self.device.is_connected:
                self.device.connect()
            snapshot = self.device.read()
        except Exception as error:
            self.device.disconnect()
            self._next_connect_at = time.monotonic() + self.reconnect_interval_ms / 1000.0
            self._set_connection(False, str(error))
            return
        self._next_connect_at = 0.0
        self._set_connection(True, "PLC 已连接")
        self.data_ready.emit(snapshot)

    @Slot(int, dict)
    def write_parameters(self, station_id: int, values: dict) -> None:
        self._run_operation(
            "parameters",
            station_id,
            lambda: self.device.write_station_parameters(station_id, values),
            "参数已写入 PLC",
        )

    @Slot(int, bool)
    def set_running(self, station_id: int, running: bool) -> None:
        self._run_operation(
            "start" if running else "stop",
            station_id,
            lambda: self.device.set_station_running(station_id, running),
            "启动指令已写入 PLC" if running else "停止指令已写入 PLC",
        )

    @Slot(int, bool)
    def set_paused(self, station_id: int, paused: bool) -> None:
        """暂停与继续复用 PLC 的 start_stop 位。"""

        self._run_operation(
            "pause" if paused else "resume",
            station_id,
            lambda: self.device.set_station_running(station_id, not paused),
            "暂停指令已写入 PLC" if paused else "继续指令已写入 PLC",
        )

    @Slot(int, bool)
    def set_enabled(self, station_id: int, enabled: bool) -> None:
        self._run_operation(
            "enable" if enabled else "disable",
            station_id,
            lambda: self.device.set_station_enabled(station_id, enabled),
            "工位使能指令已写入 PLC"
            if enabled
            else "工位停用指令已写入 PLC",
        )

    @Slot()
    def stop(self) -> None:
        self._stopping = True
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None
        self.device.disconnect()
        self.finished.emit()

    def _run_operation(
        self,
        operation: str,
        station_id: int,
        action: Callable[[], None],
        success_message: str,
    ) -> None:
        if not self.device.is_connected:
            self.operation_finished.emit(operation, station_id, False, "PLC 未连接")
            return
        try:
            action()
        except Exception as error:
            self.device.disconnect()
            self._next_connect_at = time.monotonic() + self.reconnect_interval_ms / 1000.0
            self._set_connection(False, str(error))
            self.operation_finished.emit(operation, station_id, False, str(error))
            return
        self.operation_finished.emit(operation, station_id, True, success_message)

    def _set_connection(self, connected: bool, message: str) -> None:
        if self._reported_connected == connected:
            return
        self._reported_connected = connected
        self.connection_changed.emit(connected, message)
