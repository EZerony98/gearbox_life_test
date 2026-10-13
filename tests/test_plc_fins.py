import struct
import unittest

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


if __name__ == "__main__":
    unittest.main()
