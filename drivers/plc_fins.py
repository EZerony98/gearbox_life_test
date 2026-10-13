"""欧姆龙 FINS PLC 驱动占位。"""

from typing import Any, Dict

from .base_device import BaseDevice, DeviceConnectionError


class FinsPlcDriver(BaseDevice):
    def connect(self) -> None:
        raise DeviceConnectionError("PLC 通讯协议尚未配置")

    def disconnect(self) -> None:
        self._connected = False

    def read(self) -> Dict[str, Any]:
        if not self.is_connected:
            raise DeviceConnectionError("PLC 未连接")
        return {}

