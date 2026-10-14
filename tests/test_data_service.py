import csv
import json
import tempfile
import unittest
from pathlib import Path

from services.data_service import DataService


class DataServiceTests(unittest.TestCase):
    def _sample(
        self, timestamp: str, station_id: int = 1, product_sn: str = "GBX-SN-001"
    ) -> dict:
        return {
            "sample_no": 1,
            "timestamp_local": timestamp,
            "elapsed_seconds": 1,
            "station_id": station_id,
            "product_sn": product_sn,
            "speed_rpm": 1500.1,
            "current_ma": 2250.0,
            "pressure": 120.0,
            "torque_nm": 4.5,
            "temperature_1_c": 42.1,
            "temperature_2_c": 40.2,
            "temperature_3_c": 38.3,
            "target_speed_rpm": 1500,
            "target_torque_nm": 4.5,
            "pressure_compensation": 0.1,
            "temperature_high_c": 85.0,
            "temperature_low_c": 5.0,
            "running": 1,
            "warning": 0,
            "data_quality": "GOOD",
        }

    def test_writes_station_csv_with_product_sn(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            service = DataService(Path(temporary_dir), minimum_free_space_gb=0)
            session_dir = service.start_session({"session_id": "test_session"})
            service.write_sample(self._sample("2026-10-12T08:30:00.000+08:00"))
            service.write_event("01 号工位", "开始测试")
            service.stop_session("completed")

            csv_path = session_dir / "station_01" / "GBX-SN-001.csv"
            with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["product_sn"], "GBX-SN-001")
            self.assertEqual(rows[0]["current_ma"], "2250.0")
            metadata = json.loads(
                (session_dir / "test_info.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["status"], "completed")
            self.assertEqual(metadata["sample_count"], 1)

    def test_keeps_same_product_sn_in_one_csv_across_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            service = DataService(Path(temporary_dir), minimum_free_space_gb=0)
            session_dir = service.start_session({"session_id": "rotation"})
            service.write_sample(self._sample("2026-10-12T23:59:59.000+08:00"))
            service.write_sample(self._sample("2026-10-13T00:00:00.000+08:00"))
            service.stop_session("completed")
            csv_path = session_dir / "station_01" / "GBX-SN-001.csv"
            with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(len(rows), 2)
            self.assertEqual(
                [row["timestamp_local"][:10] for row in rows],
                ["2026-10-12", "2026-10-13"],
            )
            self.assertEqual(list((session_dir / "station_01").glob("*.csv")), [csv_path])

    def test_separates_different_product_sns_on_same_station_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            service = DataService(Path(temporary_dir), minimum_free_space_gb=0)
            session_dir = service.start_session({"session_id": "separate_sn"})
            service.write_sample(
                self._sample(
                    "2026-10-12T08:30:00.000+08:00", product_sn="GBX-SN-001"
                )
            )
            service.write_sample(
                self._sample(
                    "2026-10-12T09:30:00.000+08:00", product_sn="GBX-SN-002"
                )
            )
            service.stop_session("completed")

            first_path = session_dir / "station_01" / "GBX-SN-001.csv"
            second_path = session_dir / "station_01" / "GBX-SN-002.csv"
            with first_path.open(encoding="utf-8-sig", newline="") as csv_file:
                first_rows = list(csv.DictReader(csv_file))
            with second_path.open(encoding="utf-8-sig", newline="") as csv_file:
                second_rows = list(csv.DictReader(csv_file))
            self.assertEqual([row["product_sn"] for row in first_rows], ["GBX-SN-001"])
            self.assertEqual([row["product_sn"] for row in second_rows], ["GBX-SN-002"])

    def test_sanitizes_product_sn_used_as_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            service = DataService(Path(temporary_dir), minimum_free_space_gb=0)
            session_dir = service.start_session({"session_id": "safe_sn"})
            service.write_sample(
                self._sample(
                    "2026-10-12T08:30:00.000+08:00", product_sn="GBX/001"
                )
            )
            service.stop_session("completed")

            csv_files = list((session_dir / "station_01").glob("*.csv"))
            self.assertEqual(len(csv_files), 1)
            self.assertNotIn("/", csv_files[0].name)
            csv_path = csv_files[0]
            with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows[0]["product_sn"], "GBX/001")


if __name__ == "__main__":
    unittest.main()
