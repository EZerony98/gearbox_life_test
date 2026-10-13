"""欧姆龙 FINS/UDP PLC 实时读写驱动。"""

from __future__ import annotations

import math
import re
import socket
import struct
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .base_device import BaseDevice, DeviceConnectionError


class FinsProtocolError(DeviceConnectionError):
    """PLC 返回了无效 FINS 帧或非零结束码。"""


class FinsPlcDriver(BaseDevice):
    """使用 FINS/UDP 访问地址表中的 DM 区数据。

    FINS 的 DM 字与位存储区代码分别为 ``0x82`` 和 ``0x02``。PLC
    中的 REAL 跨两个字，字序由 ``real_word_order`` 配置，默认采用欧姆龙
    DM 区常用的低字在前（``low_high``）。
    """

    DM_WORD_AREA = 0x82
    DM_BIT_AREA = 0x02
    MEMORY_AREA_READ = b"\x01\x01"
    MEMORY_AREA_WRITE = b"\x01\x02"
    _ADDRESS_PATTERN = re.compile(r"^%?D(?P<word>\d+)(?:\.(?P<bit>\d{1,2}))?$")

    def __init__(
        self, config: Dict[str, Any], address_config: Mapping[str, Any]
    ) -> None:
        super().__init__(config)
        if str(config.get("transport", "udp")).lower() != "udp":
            raise ValueError("当前 FINS 驱动仅支持 UDP 传输")
        self.address_config = address_config
        self._stations = {
            int(item["station"]): item
            for item in address_config.get("stations", [])
        }
        self._socket: Optional[socket.socket] = None
        self._sid = 0
        self._source_node = 0
        self._destination_node = int(
            config.get("destination_node") or str(config["host"]).split(".")[-1]
        )
        self._real_word_order = str(
            config.get("real_word_order", "low_high")
        ).lower()
        if self._real_word_order not in {"low_high", "high_low"}:
            raise ValueError("real_word_order 必须是 low_high 或 high_low")

    def connect(self) -> None:
        self.disconnect()
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(float(self.config.get("timeout_seconds", 1.0)))
        local_host = str(self.config.get("local_host", "")).strip()
        local_port = int(self.config.get("local_port", 0))
        try:
            if local_host or local_port:
                udp_socket.bind((local_host or "0.0.0.0", local_port))
            udp_socket.connect((str(self.config["host"]), int(self.config["port"])))
            local_ip = udp_socket.getsockname()[0]
        except OSError as error:
            udp_socket.close()
            raise DeviceConnectionError(f"PLC 网络初始化失败：{error}") from error
        configured_source = int(self.config.get("source_node", 0))
        self._source_node = configured_source or int(local_ip.split(".")[-1])
        self._socket = udp_socket
        # UDP connect 只设置目标地址，首次读到有效响应后才算真正连接。
        self._connected = False

    def disconnect(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        self._connected = False

    def read(self) -> Dict[str, Any]:
        if self._socket is None:
            self.connect()
        try:
            control_words = self._read_words(3500, 25)
            real_words = self._read_words(3702, 252)
            stations = [
                self._station_snapshot(
                    station_id, addresses, control_words, 3500, real_words, 3702
                )
                for station_id, addresses in sorted(self._stations.items())
            ]
        except (OSError, socket.timeout, FinsProtocolError) as error:
            self.disconnect()
            if isinstance(error, socket.timeout):
                raise DeviceConnectionError("PLC 响应超时") from error
            if isinstance(error, DeviceConnectionError):
                raise
            raise DeviceConnectionError(f"PLC 通讯失败：{error}") from error
        self._connected = True
        return {"stations": stations, "protocol": "FINS/UDP"}

    def set_station_running(self, station_id: int, running: bool) -> None:
        self._require_connected()
        address = self._station_addresses(station_id)["bool"]["start_stop"]
        self._write_bool(address, running)

    def set_station_enabled(self, station_id: int, enabled: bool) -> None:
        """写入工位使能位；界面状态仍以 enabled_feedback 为准。"""

        self._require_connected()
        address = self._station_addresses(station_id)["bool"]["enable"]
        self._write_bool(address, enabled)

    def write_station_parameters(
        self, station_id: int, values: Mapping[str, object]
    ) -> None:
        self._require_connected()
        addresses = self._station_addresses(station_id)
        bool_addresses = addresses["bool"]
        int_addresses = addresses["int"]
        real_addresses = addresses["real"]

        speed_address, _ = self._parse_address(int_addresses["speed_setpoint"])
        self._write_words(speed_address, [int(values["speed_rpm"]) & 0xFFFF])
        real_values = (
            (
                real_addresses["pressure_comp_write_value"],
                float(values["pressure_compensation"]),
            ),
            (
                real_addresses["torque_target_write_value"],
                float(values["torque_target"]),
            ),
            (
                real_addresses["temperature_high_write_value"],
                float(values["temperature_high"]),
            ),
            (
                real_addresses["temperature_low_write_value"],
                float(values["temperature_low"]),
            ),
        )
        for address, value in real_values:
            word, _ = self._parse_address(address)
            self._write_words(word, self._encode_real(value))

        triggers = (
            bool_addresses["speed_write"],
            bool_addresses["pressure_comp_write"],
            bool_addresses["torque_target_write"],
            bool_addresses["temperature_high_write"],
            bool_addresses["temperature_low_write"],
        )
        for address in triggers:
            self._write_bool(address, True)
        time.sleep(float(self.config.get("write_pulse_seconds", 0.1)))
        for address in triggers:
            self._write_bool(address, False)

    def _station_snapshot(
        self,
        station_id: int,
        addresses: Mapping[str, Any],
        control_words: List[int],
        control_start: int,
        real_words: List[int],
        real_start: int,
    ) -> Dict[str, Any]:
        bool_addresses = addresses["bool"]
        int_addresses = addresses["int"]
        float_addresses = addresses["real"]

        def boolean(name: str) -> bool:
            word, bit = self._parse_address(bool_addresses[name])
            if bit is None:
                raise FinsProtocolError(f"布尔地址缺少位号：{bool_addresses[name]}")
            return bool((control_words[word - control_start] >> bit) & 1)

        def integer(name: str) -> int:
            word, _ = self._parse_address(int_addresses[name])
            raw = control_words[word - control_start]
            return raw - 0x10000 if raw & 0x8000 else raw

        def real(name: str) -> float:
            word, _ = self._parse_address(float_addresses[name])
            offset = word - real_start
            return self._decode_real(real_words[offset : offset + 2])

        return {
            "station_id": station_id,
            "enabled": boolean("enabled_feedback"),
            "running": boolean("running"),
            # 实时显示使用 REAL 转速地址（如 1 号工位 D3724）；整数地址会保持设定值。
            "speed_rpm": real("speed"),
            # 地址表未定义缩放倍率；现场原界面按三位数显示，原始 REAL 按 mA 使用。
            "current_ma": real("current"),
            "pressure": real("pressure"),
            "torque_nm": real("torque"),
            "temperature_1": real("temperature_1"),
            "temperature_2": real("temperature_2"),
            "temperature_3": real("temperature_3"),
            "elapsed_seconds": max(0.0, real("elapsed")),
            "parameters": {
                "speed_rpm": integer("speed_setpoint"),
                "pressure_compensation": real("pressure_compensation"),
                "torque_target": real("torque_target"),
                "temperature_high": real("temperature_high"),
                "temperature_low": real("temperature_low"),
            },
        }

    def _read_words(self, start_word: int, count: int) -> List[int]:
        payload = (
            bytes((self.DM_WORD_AREA,))
            + struct.pack(">H", start_word)
            + b"\x00"
            + struct.pack(">H", count)
        )
        data = self._exchange(self.MEMORY_AREA_READ, payload)
        expected = count * 2
        if len(data) != expected:
            raise FinsProtocolError(
                f"PLC 返回数据长度错误：期望 {expected} 字节，实际 {len(data)} 字节"
            )
        return list(struct.unpack(f">{count}H", data))

    def _write_words(self, start_word: int, values: Iterable[int]) -> None:
        words = [int(value) & 0xFFFF for value in values]
        payload = (
            bytes((self.DM_WORD_AREA,))
            + struct.pack(">H", start_word)
            + b"\x00"
            + struct.pack(">H", len(words))
            + struct.pack(f">{len(words)}H", *words)
        )
        self._exchange(self.MEMORY_AREA_WRITE, payload)

    def _write_bool(self, address: str, value: bool) -> None:
        word, bit = self._parse_address(address)
        if bit is None:
            raise ValueError(f"布尔地址缺少位号：{address}")
        payload = (
            bytes((self.DM_BIT_AREA,))
            + struct.pack(">H", word)
            + bytes((bit,))
            + b"\x00\x01"
            + bytes((1 if value else 0,))
        )
        self._exchange(self.MEMORY_AREA_WRITE, payload)

    def _exchange(self, command: bytes, payload: bytes) -> bytes:
        if self._socket is None:
            raise DeviceConnectionError("PLC UDP 套接字未建立")
        self._sid = (self._sid + 1) & 0xFF
        header = bytes(
            (
                0x80,
                0x00,
                0x02,
                0x00,
                self._destination_node,
                int(self.config.get("destination_unit", 0)),
                0x00,
                self._source_node,
                int(self.config.get("source_unit", 0)),
                self._sid,
            )
        )
        self._socket.send(header + command + payload)
        response = self._socket.recv(4096)
        if len(response) < 14:
            raise FinsProtocolError("PLC 返回的 FINS 帧过短")
        if response[9] != self._sid or response[10:12] != command:
            raise FinsProtocolError("PLC 返回的 FINS 帧与请求不匹配")
        end_code = struct.unpack(">H", response[12:14])[0]
        if end_code != 0:
            raise FinsProtocolError(f"PLC FINS 结束码：0x{end_code:04X}")
        return response[14:]

    def _decode_real(self, words: List[int]) -> float:
        if len(words) != 2:
            raise FinsProtocolError("REAL 数据需要两个 DM 字")
        ordered = words[::-1] if self._real_word_order == "low_high" else words
        value = struct.unpack(">f", struct.pack(">HH", *ordered))[0]
        if not math.isfinite(value):
            raise FinsProtocolError("PLC 返回了无效 REAL 数据")
        return float(value)

    def _encode_real(self, value: float) -> Tuple[int, int]:
        if not math.isfinite(value):
            raise ValueError("不能向 PLC 写入非有限 REAL 数值")
        high, low = struct.unpack(">HH", struct.pack(">f", float(value)))
        return (low, high) if self._real_word_order == "low_high" else (high, low)

    @classmethod
    def _parse_address(cls, address: str) -> Tuple[int, Optional[int]]:
        match = cls._ADDRESS_PATTERN.match(str(address).strip())
        if not match:
            raise ValueError(f"不支持的 PLC 地址：{address}")
        bit_text = match.group("bit")
        bit = int(bit_text) if bit_text is not None else None
        if bit is not None and not 0 <= bit <= 15:
            raise ValueError(f"PLC 位地址超出范围：{address}")
        return int(match.group("word")), bit

    def _station_addresses(self, station_id: int) -> Mapping[str, Any]:
        try:
            return self._stations[int(station_id)]
        except KeyError as error:
            raise ValueError(f"不存在的工位：{station_id}") from error

    def _require_connected(self) -> None:
        if not self.is_connected or self._socket is None:
            raise DeviceConnectionError("PLC 未连接")
