import json
import unittest
from pathlib import Path


class PlcAddressConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "plc_addresses.json"
        self.config = json.loads(config_path.read_text(encoding="utf-8"))

    def test_has_six_station_mappings(self) -> None:
        stations = self.config["stations"]
        self.assertEqual([item["station"] for item in stations], list(range(1, 7)))

    def test_representative_addresses_match_source_workbook(self) -> None:
        first, last = self.config["stations"][0], self.config["stations"][-1]
        self.assertEqual(first["bool"]["start_stop"], "%D3500.01")
        self.assertEqual(first["real"]["current"], "%D3702")
        self.assertEqual(last["bool"]["speed_write"], "%D3506.00")
        self.assertEqual(last["real"]["elapsed"], "%D3852")


if __name__ == "__main__":
    unittest.main()
