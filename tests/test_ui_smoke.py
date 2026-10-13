import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_builds_six_station_cards(self) -> None:
        window = MainWindow(enable_storage=False, enable_plc=False)
        self.assertEqual(len(window.station_cards), 6)
        self.assertEqual(window.ui.stationGridLayout.count(), 6)
        self.assertEqual(window.station_cards[1].serial_edit.placeholderText(), "请输入或扫描齿轮箱产品 SN")
        self.assertEqual(window.ui.modeBadge.text(), "实时设备 · FINS/UDP")
        self.assertEqual(window.ui.plcStatusLabel.text(), "● PLC 未连接")
        self.assertFalse(window.station_cards[1].start_button.isEnabled())
        self.assertEqual(window.station_cards[1].speed_spin.minimum(), 0)
        self.assertEqual(window.station_cards[1].speed_spin.maximum(), 12000)
        self.assertIn("转速 %D3724", window.station_cards[1].address_label.text())
        self.assertEqual(window.station_cards[1].pause_button.text(), "暂停")
        self.assertFalse(window.station_cards[1].pause_button.isEnabled())
        self.assertFalse(window.station_cards[1].apply_button.isEnabled())
        self.assertEqual(window.station_cards[1].enable_button.text(), "启用工位")
        self.assertFalse(window.station_cards[1].enable_button.isEnabled())
        self.assertFalse(window.ui.brandLogo.pixmap().isNull())

        state = window.stations[1]
        state.connected = True
        state.enabled = True
        state.paused = True
        state.serial_number = "GBX-PAUSE-001"
        state.realtime.current_ma = 250.0
        state.realtime.pressure = 0.475
        state.realtime.torque_nm = 0.0333
        card = window.station_cards[1]
        card.serial_edit.setText(state.serial_number)
        card.set_state(state)
        self.assertEqual(card.pause_button.text(), "继续")
        self.assertTrue(card.pause_button.isEnabled())
        self.assertTrue(card.stop_button.isEnabled())
        self.assertFalse(card.start_button.isEnabled())
        self.assertFalse(card.serial_edit.isEnabled())
        self.assertEqual(card._metrics["speed"].name_label.text(), "实时转速")
        self.assertEqual(card._metrics["temperature_1"].name_label.text(), "电机温度")
        self.assertEqual(card._metrics["temperature_2"].name_label.text(), "齿轮箱温度")
        self.assertEqual(card._metrics["temperature_3"].name_label.text(), "制动器温度")
        self.assertEqual(card._metrics["current"].value_label.text(), "250")
        self.assertEqual(card._metrics["pressure"].value_label.text(), "0.4750")
        self.assertEqual(card._metrics["torque"].value_label.text(), "0.0333")

        window._on_plc_operation_finished("stop", 1, True, "停止指令已写入 PLC")
        self.assertEqual(state.serial_number, "")
        self.assertEqual(card.serial_edit.text(), "")
        window.close()

    def test_fast_plc_refresh_keeps_csv_at_one_sample_per_second(self) -> None:
        window = MainWindow(enable_storage=False, enable_plc=False)
        window._storage_ready = True
        samples = []
        window.sample_for_storage.connect(samples.append)
        snapshot = {
            "station_id": 1,
            "enabled": True,
            "running": True,
            "elapsed_seconds": 1,
            "speed_rpm": 11940.0,
            "current_ma": 250.0,
            "pressure": 0.475,
            "torque_nm": 0.0333,
            "temperature_1": 31.2,
            "temperature_2": 29.6,
            "temperature_3": 27.0,
        }
        with patch(
            "ui.main_window.time.monotonic",
            side_effect=[0.0, 0.25, 0.5, 0.75, 1.0],
        ):
            for _ in range(5):
                window._on_plc_data({"stations": [snapshot]})

        self.assertEqual(len(samples), 2)
        self.assertEqual(window.stations[1].sample_count, 2)
        window.close()


if __name__ == "__main__":
    unittest.main()
