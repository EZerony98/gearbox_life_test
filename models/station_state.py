"""六工位寿命测试的界面状态模型。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List


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
    """单工位实时采样值。"""

    speed_rpm: float = 0.0
    current_a: float = 0.0
    pressure: float = 0.0
    torque_nm: float = 0.0
    temperature_1: float = 24.0
    temperature_2: float = 24.0
    temperature_3: float = 24.0


@dataclass
class StationState:
    """用于首版界面演示的轻量状态与全程历史。"""

    MAX_HISTORY_POINTS = 20_000

    station_id: int
    serial_number: str
    parameters: StationParameters = field(default_factory=StationParameters)
    realtime: StationRealtime = field(default_factory=StationRealtime)
    enabled: bool = True
    running: bool = False
    warning: bool = False
    demo_warning: bool = False
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
    _random: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._random = random.Random(1000 + self.station_id)

    @property
    def status_text(self) -> str:
        if self.warning:
            return "温度告警"
        if self.running:
            return "测试运行中"
        if self.enabled:
            return "待机"
        return "已停用"

    @property
    def status_key(self) -> str:
        if self.warning:
            return "warning"
        if self.running:
            return "running"
        if self.enabled:
            return "standby"
        return "disabled"

    def simulate_tick(self, record: bool = True) -> None:
        """生成确定性的界面演示数据；后续由 PLC worker 替换。"""

        if self.running:
            self.elapsed_seconds += 1
            phase = self.elapsed_seconds / 12.0 + self.station_id * 0.7
            noise = self._random.uniform(-1.0, 1.0)
            target_speed = float(self.parameters.speed_rpm)
            target_torque = self.parameters.torque_target
            self.realtime.speed_rpm = max(0.0, target_speed + math.sin(phase) * 18 + noise * 4)
            self.realtime.torque_nm = max(0.0, target_torque + math.sin(phase * 0.55) * 0.12 + noise * 0.03)
            self.realtime.current_a = max(0.0, 0.75 + target_torque * 0.31 + math.sin(phase * 0.8) * 0.08)
            self.realtime.pressure = 112.0 + self.station_id * 3.2 + math.sin(phase * 0.42) * 2.4
            heat_bias = 34.0 if self.demo_warning else 0.0
            warm_up = min(14.0, self.elapsed_seconds / 38.0)
            self.realtime.temperature_1 = 37.0 + self.station_id * 1.6 + warm_up + heat_bias + math.sin(phase * 0.22)
            self.realtime.temperature_2 = 34.0 + self.station_id * 1.3 + warm_up * 0.82 + heat_bias * 0.82 + math.sin(phase * 0.19)
            self.realtime.temperature_3 = 32.0 + self.station_id * 1.1 + warm_up * 0.68 + heat_bias * 0.70 + math.sin(phase * 0.17)
            self.sample_count += 1
        else:
            phase = self.sample_count / 20.0 + self.station_id
            ambient = 24.0 + math.sin(phase) * 0.25
            self.realtime = StationRealtime(
                temperature_1=ambient,
                temperature_2=ambient - 0.3,
                temperature_3=ambient - 0.5,
            )

        highest_temperature = max(
            self.realtime.temperature_1,
            self.realtime.temperature_2,
            self.realtime.temperature_3,
        )
        self.warning = self.running and highest_temperature > self.parameters.temperature_high

        if record and self.running:
            self._append_history()

    def _append_history(self) -> None:
        self.history["minutes"].append(self.sample_count / 60.0)
        speed_base = max(float(self.parameters.speed_rpm), 1.0)
        torque_base = max(self.parameters.torque_target, 0.1)
        temperature_base = max(self.parameters.temperature_high, 1.0)
        self.history["speed"].append(self.realtime.speed_rpm / speed_base * 100.0)
        self.history["current"].append(self.realtime.current_a / 3.5 * 100.0)
        self.history["torque"].append(self.realtime.torque_nm / torque_base * 100.0)
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
        """对界面趋势做分层抽样，原始秒级数据仍完整保存在 CSV。"""

        for key, values in self.history.items():
            self.history[key] = values[::2]

    def elapsed_text(self) -> str:
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
