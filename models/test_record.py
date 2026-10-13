"""齿轮箱寿命测试会话摘要模型。"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class TestRecord:
    record_id: str
    product_model: str
    serial_number: str
    station_id: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    finished_at: str = ""
    result: str = "running"
    sample_count: int = 0
    csv_directory: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
