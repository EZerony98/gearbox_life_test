import os
import unittest

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
        self.assertFalse(window.station_cards[1].apply_button.isEnabled())
        self.assertFalse(window.ui.brandLogo.pixmap().isNull())
        window.close()


if __name__ == "__main__":
    unittest.main()
