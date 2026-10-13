"""PySide6 齿轮箱寿命测试台入口。"""

import sys
from typing import Optional, Sequence

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def create_application(argv: Optional[Sequence[str]] = None) -> QApplication:
    app = QApplication(list(argv) if argv is not None else sys.argv)
    app.setApplicationName("gearbox_life_test")
    app.setApplicationDisplayName("齿轮箱寿命测试台")
    app.setOrganizationName("Gearbox Test")
    return app


def main(argv: Optional[Sequence[str]] = None) -> int:
    app = create_application(argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
