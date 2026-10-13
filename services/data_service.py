"""长时间寿命测试的分段 CSV 数据保存服务。"""

from __future__ import annotations

import csv
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, IO, Optional, Tuple


class DataService:
    """在后台线程中持续写入按工位、按日期分段的 CSV 文件。"""

    SAMPLE_FIELDS = (
        "sample_no",
        "timestamp_local",
        "elapsed_seconds",
        "station_id",
        "product_sn",
        "speed_rpm",
        "current_ma",
        "pressure",
        "torque_nm",
        "temperature_1_c",
        "temperature_2_c",
        "temperature_3_c",
        "target_speed_rpm",
        "target_torque_nm",
        "pressure_compensation",
        "temperature_high_c",
        "temperature_low_c",
        "running",
        "warning",
        "data_quality",
    )
    EVENT_FIELDS = ("timestamp_local", "level", "source", "message")

    def __init__(
        self,
        data_dir: Path,
        flush_interval_seconds: int = 5,
        fsync_interval_seconds: int = 60,
        minimum_free_space_gb: float = 5.0,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.flush_interval_seconds = max(1, int(flush_interval_seconds))
        self.fsync_interval_seconds = max(
            self.flush_interval_seconds, int(fsync_interval_seconds)
        )
        self.minimum_free_bytes = int(max(0.0, minimum_free_space_gb) * 1024**3)
        self.session_dir: Optional[Path] = None
        self.session_id = ""
        self._metadata: Dict[str, Any] = {}
        self._files: Dict[int, IO[str]] = {}
        self._writers: Dict[int, csv.DictWriter] = {}
        self._file_dates: Dict[int, str] = {}
        self._event_file: Optional[IO[str]] = None
        self._event_writer: Optional[csv.DictWriter] = None
        self._last_flush = time.monotonic()
        self._last_fsync = time.monotonic()
        self._last_space_check = 0.0
        self._sample_count = 0

    def start_session(self, metadata: Dict[str, Any]) -> Path:
        if self.session_dir is not None:
            raise RuntimeError("数据记录会话已经启动")
        self._check_free_space(force=True)
        started_at = datetime.now().astimezone()
        base_id = str(metadata.get("session_id") or started_at.strftime("%Y%m%d_%H%M%S"))
        self.session_id = self._unique_session_id(base_id)
        self.session_dir = self.data_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=False)
        self._metadata = dict(metadata)
        self._metadata.update(
            {
                "session_id": self.session_id,
                "started_at": started_at.isoformat(timespec="seconds"),
                "status": "running",
                "storage_format": "CSV",
                "rotation": "station_and_local_date",
                "sample_fields": list(self.SAMPLE_FIELDS),
            }
        )
        self._write_metadata()
        event_path = self.session_dir / "events.csv"
        self._event_file, self._event_writer = self._open_csv(
            event_path, self.EVENT_FIELDS
        )
        return self.session_dir

    def write_sample(self, sample: Dict[str, Any]) -> None:
        self._require_session()
        self._check_free_space()
        station_id = int(sample["station_id"])
        timestamp = str(sample.get("timestamp_local") or "")
        local_date = timestamp[:10] if len(timestamp) >= 10 else datetime.now().date().isoformat()
        writer = self._station_writer(station_id, local_date)
        writer.writerow({field: sample.get(field, "") for field in self.SAMPLE_FIELDS})
        self._sample_count += 1
        self._flush_if_due()

    def write_event(self, source: str, message: str, level: str = "INFO") -> None:
        self._require_session()
        if self._event_writer is None or self._event_file is None:
            raise RuntimeError("事件记录文件尚未打开")
        self._event_writer.writerow(
            {
                "timestamp_local": datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ),
                "level": level,
                "source": source,
                "message": message,
            }
        )
        self._event_file.flush()

    def stop_session(self, result: str = "stopped") -> None:
        if self.session_dir is None:
            return
        self._flush_all(force_sync=True)
        for file_handle in self._files.values():
            file_handle.close()
        self._files.clear()
        self._writers.clear()
        self._file_dates.clear()
        if self._event_file is not None:
            self._event_file.close()
            self._event_file = None
            self._event_writer = None
        self._metadata.update(
            {
                "finished_at": datetime.now()
                .astimezone()
                .isoformat(timespec="seconds"),
                "status": result,
                "sample_count": self._sample_count,
            }
        )
        self._write_metadata()

    def _station_writer(self, station_id: int, local_date: str) -> csv.DictWriter:
        if self.session_dir is None:
            raise RuntimeError("数据记录会话尚未启动")
        if self._file_dates.get(station_id) == local_date:
            return self._writers[station_id]
        old_file = self._files.pop(station_id, None)
        if old_file is not None:
            old_file.flush()
            os.fsync(old_file.fileno())
            old_file.close()
        self._writers.pop(station_id, None)
        station_dir = self.session_dir / f"station_{station_id:02d}"
        station_dir.mkdir(parents=True, exist_ok=True)
        path = station_dir / f"{local_date}.csv"
        file_handle, writer = self._open_csv(path, self.SAMPLE_FIELDS)
        self._files[station_id] = file_handle
        self._writers[station_id] = writer
        self._file_dates[station_id] = local_date
        return writer

    @staticmethod
    def _open_csv(
        path: Path, fieldnames: Tuple[str, ...]
    ) -> Tuple[IO[str], csv.DictWriter]:
        is_new_file = not path.exists() or path.stat().st_size == 0
        encoding = "utf-8-sig" if is_new_file else "utf-8"
        file_handle = path.open("a", encoding=encoding, newline="", buffering=262144)
        writer = csv.DictWriter(
            file_handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        if is_new_file:
            writer.writeheader()
            file_handle.flush()
        return file_handle, writer

    def _flush_if_due(self) -> None:
        now = time.monotonic()
        if now - self._last_flush < self.flush_interval_seconds:
            return
        force_sync = now - self._last_fsync >= self.fsync_interval_seconds
        self._flush_all(force_sync=force_sync)
        self._last_flush = now
        if force_sync:
            self._last_fsync = now

    def _flush_all(self, force_sync: bool = False) -> None:
        handles = list(self._files.values())
        if self._event_file is not None:
            handles.append(self._event_file)
        for file_handle in handles:
            file_handle.flush()
            if force_sync:
                os.fsync(file_handle.fileno())

    def _check_free_space(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_space_check < 60:
            return
        free_bytes = shutil.disk_usage(self.data_dir).free
        self._last_space_check = now
        if free_bytes < self.minimum_free_bytes:
            free_gb = free_bytes / 1024**3
            minimum_gb = self.minimum_free_bytes / 1024**3
            raise OSError(
                f"数据盘剩余空间不足：{free_gb:.1f} GB，要求至少 {minimum_gb:.1f} GB"
            )

    def _write_metadata(self) -> None:
        if self.session_dir is None:
            return
        path = self.session_dir / "test_info.json"
        temporary_path = path.with_suffix(".json.tmp")
        temporary_path.write_text(
            json.dumps(self._metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)

    def _unique_session_id(self, base_id: str) -> str:
        candidate = base_id
        suffix = 1
        while (self.data_dir / candidate).exists():
            candidate = f"{base_id}_{suffix:02d}"
            suffix += 1
        return candidate

    def _require_session(self) -> None:
        if self.session_dir is None:
            raise RuntimeError("数据记录会话尚未启动")
