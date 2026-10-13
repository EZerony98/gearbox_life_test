"""六工位齿轮箱寿命测试的实时状态模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping


@dataclass
class StationParameters:
    """单工位可下发参数。"""

    speed_rpm: int = 1500
    torque_target: float = 4.0
    pressure_compensation: float = 0.0
    temperature_high: float = 85.0
    temperature_low: float = 5.0


@dataclass
class StationRealtime:
    """单工位从 PLC 读取的实时采样值。"""

    speed_rpm: float = 0.0
    current_ma: float = 0.0
    pressure: float = 0.0
    torque_nm: float = 0.0
    temperature_1: float = 0.0
    temperature_2: float = 0.0
    temperature_3: float = 0.0


@dataclass
class StationState:
    """单工位状态与用于界面缩略图的抽样历史。"""

    MAX_HISTORY_POINTS = 20_000
    CURRENT_CHART_RANGE_MA = 3500.0

    station_id: int
    serial_number: str = ""
    parameters: StationParameters = field(default_factory=StationParameters)
    realtime: StationRealtime = field(default_factory=StationRealtime)
    connected: bool = False
    enabled: bool = False
    running: bool = False
    paused: bool = False
    warning: bool = False
    elapsed_seconds: int = 0
    sample_count: int = 0
    history: Dict[str, List[float]] = field(
        default_factory=lambda: {
            "minutes": [],
            "speed": [],
            "current": [],
            "torque": [],
            "temperature": [],
        }
    )
    _stop_latched: bool = field(default=False, init=False, repr=False)

    @property
    def status_text(self) -> str:
        if not self.connected:
            return "PLC 未连接"
        if self.warning:
            return "温度告警"
        if self.running:
            return "测试运行中"
        if self.paused:
            return "测试已暂停"
        if self.enabled:
            return "待机"
        return "工位未使能"

    @property
    def status_key(self) -> str:
        if not self.connected:
            return "disconnected"
        if self.warning:
            return "warning"
        if self.running:
            return "running"
        if self.paused:
            return "paused"
        if self.enabled:
            return "standby"
        return "disabled"

    def mark_disconnected(self) -> None:
        """通信中断后立即清除可能造成误判的运行状态。"""

        self.connected = False
        self.enabled = False
        self.running = False
        self.paused = False
        self.warning = False
        self._stop_latched = False

    def mark_start_requested(self) -> None:
        """PLC 已接受启动指令，等待真实运行反馈。"""

        self.paused = False
        self._stop_latched = False

    def mark_paused(self) -> None:
        """暂停后立即停止界面计数和 CSV 记录。"""

        self.paused = True
        self.running = False
        self.warning = False
        self._stop_latched = False

    def mark_resumed(self) -> None:
        """PLC 已接受继续指令，等待真实运行反馈后恢复记录。"""

        self.paused = False
        self.running = False
        self.warning = False
        self._stop_latched = False

    def mark_stopped(self) -> None:
        """停止测试并锁住运行态，直到 PLC 确认运行位已经复位。"""

        self.serial_number = ""
        self.paused = False
        self.running = False
        self.warning = False
        self._stop_latched = True

    def apply_plc_snapshot(self, snapshot: Mapping[str, object], record: bool = True) -> None:
        """应用一次真实 PLC 快照，不生成或补造任何测量值。"""

        self.connected = True
        self.enabled = bool(snapshot.get("enabled", False))
        plc_running = bool(snapshot.get("running", False))
        if self._stop_latched:
            if not plc_running:
                self._stop_latched = False
            self.running = False
        else:
            self.running = plc_running and not self.paused
        self.elapsed_seconds = max(0, int(float(snapshot.get("elapsed_seconds", 0))))
        self.realtime = StationRealtime(
            speed_rpm=float(snapshot.get("speed_rpm", 0.0)),
            current_ma=float(snapshot.get("current_ma", 0.0)),
            pressure=float(snapshot.get("pressure", 0.0)),
            torque_nm=float(snapshot.get("torque_nm", 0.0)),
            temperature_1=float(snapshot.get("temperature_1", 0.0)),
            temperature_2=float(snapshot.get("temperature_2", 0.0)),
            temperature_3=float(snapshot.get("temperature_3", 0.0)),
        )

        plc_parameters = snapshot.get("parameters")
        if isinstance(plc_parameters, Mapping):
            self.parameters = StationParameters(
                speed_rpm=int(float(plc_parameters.get("speed_rpm", self.parameters.speed_rpm))),
                torque_target=float(plc_parameters.get("torque_target", self.parameters.torque_target)),
                pressure_compensation=float(
                    plc_parameters.get(
                        "pressure_compensation", self.parameters.pressure_compensation
                    )
                ),
                temperature_high=float(
                    plc_parameters.get("temperature_high", self.parameters.temperature_high)
                ),
                temperature_low=float(
                    plc_parameters.get("temperature_low", self.parameters.temperature_low)
                ),
            )

        temperatures = (
            self.realtime.temperature_1,
            self.realtime.temperature_2,
            self.realtime.temperature_3,
        )
        self.warning = self.running and (
            max(temperatures) > self.parameters.temperature_high
            or min(temperatures) < self.parameters.temperature_low
        )

        if record and self.running:
            self.record_sample()

    def record_sample(self) -> None:
        """按 CSV 记录节拍累计一次样本并更新缩略趋势。"""

        if not self.running:
            return
        self.sample_count += 1
        self._append_history()

    def _append_history(self) -> None:
        self.history["minutes"].append(self.elapsed_seconds / 60.0)
        speed_base = max(float(self.parameters.speed_rpm), 1.0)
        torque_base = max(self.parameters.torque_target, 0.1)
        temperature_base = max(self.parameters.temperature_high, 1.0)
        self.history["speed"].append(self.realtime.speed_rpm / speed_base * 100.0)
        self.history["current"].append(
            self.realtime.current_ma / self.CURRENT_CHART_RANGE_MA * 100.0
        )
        self.history["torque"].append(
            self.realtime.torque_nm / torque_base * 100.0
        )
        self.history["temperature"].append(
            max(
                self.realtime.temperature_1,
                self.realtime.temperature_2,
                self.realtime.temperature_3,
            )
            / temperature_base
            * 100.0
        )
        if len(self.history["minutes"]) > self.MAX_HISTORY_POINTS:
            self._compact_history()

    def _compact_history(self) -> None:
        """界面趋势分层抽样；原始秒级数据仍完整保存在 CSV。"""

        for key, values in self.history.items():
            self.history[key] = values[::2]

    def elapsed_text(self) -> str:
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
