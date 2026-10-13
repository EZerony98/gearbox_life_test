"""齿轮箱寿命测试台主界面样式。"""

APP_STYLE = r"""
QMainWindow, QWidget {
    background: #f2f4f7;
    color: #243142;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
    font-size: 12px;
}
QFrame#headerFrame { background: #ffffff; border: none; border-bottom: 2px solid #d8132f; }
QLabel#brandLogo {
    background: #ffffff; border: none; border-radius: 8px; padding: 2px 6px;
}
QLabel#titleLabel { background: transparent; color: #202b3a; font-size: 26px; font-weight: 750; }
QLabel#subtitleLabel { background: transparent; color: #7c8795; font-size: 11px; letter-spacing: 1px; }
QLabel#clockLabel { background: #f5f7f9; color: #334155; border: 1px solid #dce1e7; border-radius: 7px; padding: 0 9px; }
QLabel#plcStatusLabel { background: transparent; color: #f2a43a; font-weight: 650; padding: 0 8px; }
QLabel#plcStatusLabel[connected="true"] { color: #14865b; }
QLabel#modeBadge { background: #fff4f5; color: #9f1830; border: 1px solid #f1d4d9; border-radius: 12px; padding: 5px 11px; font-size: 11px; }
QFrame#headerFrame QPushButton { min-height: 34px; padding: 0 14px; border-radius: 6px; font-weight: 600; }
QPushButton#settingsButton { color: #334155; background: #f5f7f9; border: 1px solid #d4dae1; }
QPushButton#startAllButton { color: #ffffff; background: #14865b; border: 1px solid #14865b; }
QPushButton#stopAllButton { color: #ffffff; background: #d8132f; border: 1px solid #d8132f; }
QPushButton:hover { border-color: #ffffff; }
QPushButton:disabled { color: #98a2ad; background: #e6e9ed; border-color: #d5d9de; }
QFrame#summaryFrame, QFrame#overviewFrame {
    background: #ffffff; border: 1px solid #dce1e7; border-radius: 9px;
}
QLabel#pageTitle { background: transparent; color: #202b3a; font-size: 17px; font-weight: 700; }
QLabel#pageHint, QLabel#historyHint { background: transparent; color: #7b8796; padding-left: 8px; }
QLabel#stationTotalLabel, QLabel#runningCountLabel, QLabel#warningCountLabel, QLabel#recordStateLabel {
    background: #f6f7f9; color: #445267; border: 1px solid #e0e4e9; border-radius: 13px; padding: 5px 11px; font-weight: 600;
}
QLabel#runningCountLabel { color: #11734c; }
QLabel#warningCountLabel { color: #b76512; }
QLabel#recordStateLabel { color: #365f91; }
QScrollArea, QWidget#stationScrollContents { background: transparent; }
QFrame#stationCard {
    background: #ffffff; border: 1px solid #d9dee5; border-left: 4px solid #a5afb9; border-radius: 8px;
}
QFrame#stationCard[state="running"] { border-left-color: #16875c; }
QFrame#stationCard[state="warning"] { border-left-color: #ed8a24; }
QFrame#stationCard[state="disconnected"] { border-left-color: #9ba4ae; background: #fbfbfc; }
QFrame#stationCard[selected="true"] { border: 2px solid #d8132f; border-left: 5px solid #d8132f; }
QLabel#stationNumber { background: transparent; color: #202b3a; font-size: 16px; font-weight: 750; }
QLabel#elapsedLabel { background: transparent; color: #667588; font-family: Menlo, monospace; }
QLabel#stationStatus { border-radius: 11px; padding: 4px 9px; font-size: 11px; font-weight: 650; }
QLabel#stationStatus[state="running"] { background: #def5eb; color: #106d49; }
QLabel#stationStatus[state="warning"] { background: #fff0df; color: #b75e0d; }
QLabel#stationStatus[state="standby"] { background: #edf1f5; color: #5e6e7f; }
QLabel#stationStatus[state="disabled"] { background: #f1f2f4; color: #818b95; }
QLabel#stationStatus[state="disconnected"] { background: #f4e7e9; color: #a23a4a; }
QLabel#fieldCaption, QLabel#paramCaption { background: transparent; color: #7e8a98; font-size: 10px; }
QLineEdit#serialEdit { min-height: 25px; background: #fafbfc; border: 1px solid #d7dde4; border-radius: 4px; padding: 0 7px; font-weight: 600; }
QLineEdit#serialEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #d8132f; }
QFrame#metricTile { background: #f6f8fa; border: 1px solid #e4e8ed; border-radius: 5px; }
QLabel#metricName { background: transparent; color: #778596; font-size: 10px; }
QLabel#metricValue { background: transparent; color: #223348; font-size: 16px; font-weight: 750; }
QLabel#metricUnit { background: transparent; color: #8190a0; font-size: 9px; }
QFrame#parameterPanel { background: #fcfcfd; border-top: 1px solid #e6e9ed; border-bottom: 1px solid #e6e9ed; }
QSpinBox, QDoubleSpinBox, QComboBox {
    min-height: 25px; background: #ffffff; color: #26364a; border: 1px solid #ccd3dc; border-radius: 4px; padding: 0 4px;
}
QPushButton#applyButton { min-height: 27px; color: #a70d26; background: #fff1f3; border: 1px solid #edbec6; border-radius: 4px; padding: 0 9px; font-weight: 600; }
QPushButton#stationStartButton, QPushButton#stationStopButton { min-height: 29px; border-radius: 5px; padding: 0 14px; font-weight: 650; }
QPushButton#stationStartButton { color: white; background: #14865b; border: 1px solid #14865b; }
QPushButton#stationStopButton { color: #b1122a; background: #fff3f5; border: 1px solid #e8b9c1; }
QPushButton#applyButton:disabled,
QPushButton#stationStartButton:disabled,
QPushButton#stationStopButton:disabled,
QPushButton#startAllButton:disabled,
QPushButton#stopAllButton:disabled {
    color: #9aa3ad; background: #e9ecef; border: 1px solid #d8dde2;
}
QLabel#addressHint { background: transparent; color: #8794a2; font-family: Menlo, monospace; font-size: 9px; }
QLabel#historyTitle, QLabel#eventTitle { background: transparent; color: #202f42; font-size: 14px; font-weight: 700; }
QFrame#eventPanel { border-left: 1px solid #e1e5ea; }
QListWidget { background: #fafbfc; border: 1px solid #e0e4e9; border-radius: 5px; outline: none; padding: 2px; }
QListWidget::item { min-height: 29px; color: #526174; border-bottom: 1px solid #edf0f3; padding-left: 5px; }
QPushButton#resetViewButton { min-height: 27px; color: #3b546f; background: #f4f6f8; border: 1px solid #cfd6de; border-radius: 4px; padding: 0 9px; }
QStatusBar { background: #e9edf1; color: #5f6d7d; font-size: 10px; }
QSplitter::handle { background: transparent; height: 8px; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical { background: #b8c0c9; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
