"""主界面样式。"""

APP_STYLE = r"""
QMainWindow, QWidget {
    background: #eef3f7;
    color: #213247;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
    font-size: 12px;
}
QFrame#headerFrame { background: #0b1f35; border: none; }
QLabel#brandMark {
    min-width: 42px; max-width: 42px; min-height: 42px; max-height: 42px;
    margin-right: 4px; border-radius: 10px; background: #2e82ff;
    color: white; font-size: 22px; font-weight: 800;
}
QLabel#titleLabel { background: transparent; color: #ffffff; font-size: 21px; font-weight: 700; }
QLabel#subtitleLabel { background: transparent; color: #8ca1b8; font-size: 10px; letter-spacing: 1px; }
QLabel#clockLabel { background: #102a45; color: #d9e7f5; border: 1px solid #21405e; border-radius: 6px; padding: 0 8px; }
QLabel#plcStatusLabel { background: transparent; color: #f5a94f; font-weight: 600; padding: 0 8px; }
QLabel#demoBadge { background: #173a5d; color: #7fc1ff; border: 1px solid #2a567d; border-radius: 12px; padding: 5px 10px; font-size: 11px; }
QFrame#headerFrame QPushButton { min-height: 34px; padding: 0 14px; border-radius: 6px; font-weight: 600; }
QPushButton#settingsButton { color: #dbe8f5; background: #102a45; border: 1px solid #36516c; }
QPushButton#startAllButton { color: #ffffff; background: #168757; border: 1px solid #168757; }
QPushButton#stopAllButton { color: #ffffff; background: #b83a45; border: 1px solid #b83a45; }
QPushButton:hover { opacity: 0.92; }
QFrame#summaryFrame, QFrame#overviewFrame {
    background: #ffffff; border: 1px solid #d8e1ea; border-radius: 8px;
}
QLabel#pageTitle { background: transparent; color: #142b43; font-size: 17px; font-weight: 700; }
QLabel#pageHint, QLabel#historyHint { background: transparent; color: #78889a; padding-left: 8px; }
QLabel#stationTotalLabel, QLabel#runningCountLabel, QLabel#warningCountLabel, QLabel#recordStateLabel {
    background: #f6f8fb; color: #40546a; border: 1px solid #e0e6ed; border-radius: 13px; padding: 5px 11px; font-weight: 600;
}
QLabel#runningCountLabel { color: #15774d; }
QLabel#warningCountLabel { color: #b96a18; }
QLabel#recordStateLabel { color: #2374cf; }
QScrollArea, QWidget#stationScrollContents { background: transparent; }
QFrame#stationCard {
    background: #ffffff; border: 1px solid #d6dfe8; border-left: 4px solid #91a2b2; border-radius: 8px;
}
QFrame#stationCard[state="running"] { border-left-color: #1a9d65; }
QFrame#stationCard[state="warning"] { border-left-color: #e38327; }
QFrame#stationCard[selected="true"] { border: 2px solid #2e82ff; border-left: 5px solid #2e82ff; }
QLabel#stationNumber { background: transparent; color: #142b43; font-size: 16px; font-weight: 750; }
QLabel#elapsedLabel { background: transparent; color: #6b7d8f; font-family: Menlo, monospace; }
QLabel#stationStatus { border-radius: 11px; padding: 4px 9px; font-size: 11px; font-weight: 650; }
QLabel#stationStatus[state="running"] { background: #e4f7ee; color: #14744c; }
QLabel#stationStatus[state="warning"] { background: #fff0df; color: #b75e0d; }
QLabel#stationStatus[state="standby"] { background: #edf1f5; color: #647688; }
QLabel#stationStatus[state="disabled"] { background: #f3f3f3; color: #999999; }
QLabel#fieldCaption, QLabel#paramCaption { background: transparent; color: #8391a0; font-size: 10px; }
QLineEdit#serialEdit { min-height: 25px; background: #f7f9fb; border: 1px solid #d9e1e8; border-radius: 4px; padding: 0 7px; font-weight: 600; }
QFrame#metricTile { background: #f6f9fc; border: 1px solid #e4eaf0; border-radius: 5px; }
QLabel#metricName { background: transparent; color: #7a8998; font-size: 10px; }
QLabel#metricValue { background: transparent; color: #18314c; font-size: 16px; font-weight: 750; }
QLabel#metricUnit { background: transparent; color: #8191a1; font-size: 9px; }
QFrame#parameterPanel { background: #fbfcfd; border-top: 1px solid #e5ebf0; border-bottom: 1px solid #e5ebf0; }
QSpinBox, QDoubleSpinBox, QComboBox {
    min-height: 25px; background: #ffffff; color: #24384c; border: 1px solid #ccd7e1; border-radius: 4px; padding: 0 4px;
}
QPushButton#applyButton { min-height: 27px; color: #246ab3; background: #edf5fd; border: 1px solid #bfdaef; border-radius: 4px; padding: 0 9px; font-weight: 600; }
QPushButton#stationStartButton, QPushButton#stationStopButton { min-height: 29px; border-radius: 5px; padding: 0 14px; font-weight: 650; }
QPushButton#stationStartButton { color: white; background: #168757; border: 1px solid #168757; }
QPushButton#stationStopButton { color: #b43a45; background: #fff5f5; border: 1px solid #e8bdc1; }
QLabel#addressHint { background: transparent; color: #8b9bab; font-family: Menlo, monospace; font-size: 9px; }
QLabel#historyTitle, QLabel#eventTitle { background: transparent; color: #18314c; font-size: 14px; font-weight: 700; }
QFrame#eventPanel { border-left: 1px solid #e2e8ef; }
QListWidget { background: #f8fafc; border: 1px solid #e1e7ed; border-radius: 5px; outline: none; padding: 2px; }
QListWidget::item { min-height: 29px; color: #526579; border-bottom: 1px solid #edf1f5; padding-left: 5px; }
QPushButton#resetViewButton { min-height: 27px; color: #315d87; background: #f3f7fb; border: 1px solid #cfdae5; border-radius: 4px; padding: 0 9px; }
QStatusBar { background: #e6edf3; color: #627487; font-size: 10px; }
QSplitter::handle { background: transparent; height: 8px; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical { background: #bdc8d3; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

