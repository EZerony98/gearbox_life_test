import struct
import unittest
from unittest.mock import Mock

from drivers.plc_fins import FinsPlcDriver


class FinsPlcDriverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = FinsPlcDriver(
            {
                "host": "192.168.250.1",
                "port": 9600,
                "real_word_order": "low_high",
            },
            {"stations": []},
        )

    def test_parses_dm_word_and_bit_addresses(self) -> None:
        self.assertEqual(self.driver._parse_address("%D3500.11"), (3500, 11))
        self.assertEqual(self.driver._parse_address("D3702"), (3702, None))

    def test_real_round_trip_uses_configured_word_order(self) -> None:
        words = self.driver._encode_real(42.25)
        self.assertAlmostEqual(self.driver._decode_real(list(words)), 42.25)
        high, low = struct.unpack(">HH", struct.pack(">f", 42.25))
        self.assertEqual(words, (low, high))

    def test_station_enable_writes_configured_fins_bit(self) -> None:
        driver = FinsPlcDriver(
            {"host": "192.168.250.1", "port": 9600},
            {
                "stations": [
                    {"station": 2, "bool": {"enable": "%D3500.12"}}
                ]
            },
        )
        driver._connected = True
        driver._socket = Mock()
        driver._write_bool = Mock()
        driver.set_station_enabled(2, True)
        driver._write_bool.assert_called_once_with("%D3500.12", True)

    def test_station_snapshot_uses_real_speed_channel(self) -> None:
        addresses = {
            "station": 1,
            "bool": {
                "enabled_feedback": "%D3501.05",
                "running": "%D3502.09",
            },
            "int": {"speed": "%D3509", "speed_setpoint": "%D3519"},
            "real": {
                "current": "%D3702",
                "pressure": "%D3720",
                "torque": "%D3722",
                "speed": "%D3724",
                "temperature_1": "%D3726",
                "temperature_2": "%D3728",
                "temperature_3": "%D3730",
                "pressure_compensation": "%D3732",
                "torque_target": "%D3734",
                "temperature_high": "%D3736",
                "temperature_low": "%D3738",
                "elapsed": "%D3842",
            },
        }
        control_words = [0] * 25
        control_words[3509 - 3500] = 12000
        control_words[3519 - 3500] = 12000
        real_words = [0] * 252
        speed_offset = 3724 - 3702
        real_words[speed_offset : speed_offset + 2] = self.driver._encode_real(11940.0)

        snapshot = self.driver._station_snapshot(
            1, addresses, control_words, 3500, real_words, 3702
        )

        self.assertEqual(snapshot["speed_rpm"], 11940.0)


if __name__ == "__main__":
    unittest.main()
