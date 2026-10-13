# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QSplitter, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1720, 1000)
        MainWindow.setMinimumSize(QSize(1180, 720))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.rootLayout = QVBoxLayout(self.centralwidget)
        self.rootLayout.setSpacing(0)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(0, 0, 0, 0)
        self.headerFrame = QFrame(self.centralwidget)
        self.headerFrame.setObjectName(u"headerFrame")
        self.headerFrame.setMinimumSize(QSize(0, 78))
        self.headerFrame.setMaximumSize(QSize(16777215, 78))
        self.headerLayout = QHBoxLayout(self.headerFrame)
        self.headerLayout.setObjectName(u"headerLayout")
        self.headerLayout.setContentsMargins(22, -1, 22, -1)
        self.brandMark = QLabel(self.headerFrame)
        self.brandMark.setObjectName(u"brandMark")
        self.brandMark.setAlignment(Qt.AlignCenter)

        self.headerLayout.addWidget(self.brandMark)

        self.titleLayout = QVBoxLayout()
        self.titleLayout.setSpacing(1)
        self.titleLayout.setObjectName(u"titleLayout")
        self.titleLabel = QLabel(self.headerFrame)
        self.titleLabel.setObjectName(u"titleLabel")

        self.titleLayout.addWidget(self.titleLabel)

        self.subtitleLabel = QLabel(self.headerFrame)
        self.subtitleLabel.setObjectName(u"subtitleLabel")

        self.titleLayout.addWidget(self.subtitleLabel)


        self.headerLayout.addLayout(self.titleLayout)

        self.headerSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.headerLayout.addItem(self.headerSpacer)

        self.demoBadge = QLabel(self.headerFrame)
        self.demoBadge.setObjectName(u"demoBadge")
        self.demoBadge.setAlignment(Qt.AlignCenter)

        self.headerLayout.addWidget(self.demoBadge)

        self.clockLabel = QLabel(self.headerFrame)
        self.clockLabel.setObjectName(u"clockLabel")
        self.clockLabel.setMinimumSize(QSize(142, 34))
        self.clockLabel.setAlignment(Qt.AlignCenter)

        self.headerLayout.addWidget(self.clockLabel)

        self.plcStatusLabel = QLabel(self.headerFrame)
        self.plcStatusLabel.setObjectName(u"plcStatusLabel")

        self.headerLayout.addWidget(self.plcStatusLabel)

        self.settingsButton = QPushButton(self.headerFrame)
        self.settingsButton.setObjectName(u"settingsButton")

        self.headerLayout.addWidget(self.settingsButton)

        self.startAllButton = QPushButton(self.headerFrame)
        self.startAllButton.setObjectName(u"startAllButton")

        self.headerLayout.addWidget(self.startAllButton)

        self.stopAllButton = QPushButton(self.headerFrame)
        self.stopAllButton.setObjectName(u"stopAllButton")

        self.headerLayout.addWidget(self.stopAllButton)


        self.rootLayout.addWidget(self.headerFrame)

        self.contentWidget = QWidget(self.centralwidget)
        self.contentWidget.setObjectName(u"contentWidget")
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setSpacing(12)
        self.contentLayout.setObjectName(u"contentLayout")
        self.contentLayout.setContentsMargins(16, 14, 16, 12)
        self.summaryFrame = QFrame(self.contentWidget)
        self.summaryFrame.setObjectName(u"summaryFrame")
        self.summaryFrame.setMinimumSize(QSize(0, 58))
        self.summaryFrame.setMaximumSize(QSize(16777215, 58))
        self.summaryLayout = QHBoxLayout(self.summaryFrame)
        self.summaryLayout.setObjectName(u"summaryLayout")
        self.summaryLayout.setContentsMargins(14, -1, 14, -1)
        self.pageTitle = QLabel(self.summaryFrame)
        self.pageTitle.setObjectName(u"pageTitle")

        self.summaryLayout.addWidget(self.pageTitle)

        self.pageHint = QLabel(self.summaryFrame)
        self.pageHint.setObjectName(u"pageHint")

        self.summaryLayout.addWidget(self.pageHint)

        self.summarySpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.summaryLayout.addItem(self.summarySpacer)

        self.stationTotalLabel = QLabel(self.summaryFrame)
        self.stationTotalLabel.setObjectName(u"stationTotalLabel")

        self.summaryLayout.addWidget(self.stationTotalLabel)

        self.runningCountLabel = QLabel(self.summaryFrame)
        self.runningCountLabel.setObjectName(u"runningCountLabel")

        self.summaryLayout.addWidget(self.runningCountLabel)

        self.warningCountLabel = QLabel(self.summaryFrame)
        self.warningCountLabel.setObjectName(u"warningCountLabel")

        self.summaryLayout.addWidget(self.warningCountLabel)

        self.recordStateLabel = QLabel(self.summaryFrame)
        self.recordStateLabel.setObjectName(u"recordStateLabel")

        self.summaryLayout.addWidget(self.recordStateLabel)


        self.contentLayout.addWidget(self.summaryFrame)

        self.mainSplitter = QSplitter(self.contentWidget)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Vertical)
        self.stationScrollArea = QScrollArea(self.mainSplitter)
        self.stationScrollArea.setObjectName(u"stationScrollArea")
        self.stationScrollArea.setWidgetResizable(True)
        self.stationScrollArea.setFrameShape(QFrame.NoFrame)
        self.stationScrollContents = QWidget()
        self.stationScrollContents.setObjectName(u"stationScrollContents")
        self.stationScrollContents.setGeometry(QRect(0, 0, 1664, 560))
        self.stationGridLayout = QGridLayout(self.stationScrollContents)
        self.stationGridLayout.setObjectName(u"stationGridLayout")
        self.stationGridLayout.setHorizontalSpacing(10)
        self.stationGridLayout.setVerticalSpacing(10)
        self.stationGridLayout.setContentsMargins(0, 0, 0, 0)
        self.stationScrollArea.setWidget(self.stationScrollContents)
        self.mainSplitter.addWidget(self.stationScrollArea)
        self.overviewFrame = QFrame(self.mainSplitter)
        self.overviewFrame.setObjectName(u"overviewFrame")
        self.overviewFrame.setMinimumSize(QSize(0, 220))
        self.overviewLayout = QHBoxLayout(self.overviewFrame)
        self.overviewLayout.setSpacing(12)
        self.overviewLayout.setObjectName(u"overviewLayout")
        self.overviewLayout.setContentsMargins(14, 12, 14, 12)
        self.historyPanel = QFrame(self.overviewFrame)
        self.historyPanel.setObjectName(u"historyPanel")
        self.historyLayout = QVBoxLayout(self.historyPanel)
        self.historyLayout.setSpacing(6)
        self.historyLayout.setObjectName(u"historyLayout")
        self.historyLayout.setContentsMargins(0, 0, 0, 0)
        self.historyHeaderLayout = QHBoxLayout()
        self.historyHeaderLayout.setObjectName(u"historyHeaderLayout")
        self.historyTitle = QLabel(self.historyPanel)
        self.historyTitle.setObjectName(u"historyTitle")

        self.historyHeaderLayout.addWidget(self.historyTitle)

        self.historyHint = QLabel(self.historyPanel)
        self.historyHint.setObjectName(u"historyHint")

        self.historyHeaderLayout.addWidget(self.historyHint)

        self.historySpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.historyHeaderLayout.addItem(self.historySpacer)

        self.historyStationCombo = QComboBox(self.historyPanel)
        self.historyStationCombo.setObjectName(u"historyStationCombo")

        self.historyHeaderLayout.addWidget(self.historyStationCombo)

        self.resetViewButton = QPushButton(self.historyPanel)
        self.resetViewButton.setObjectName(u"resetViewButton")

        self.historyHeaderLayout.addWidget(self.resetViewButton)


        self.historyLayout.addLayout(self.historyHeaderLayout)

        self.historyPlotHost = QWidget(self.historyPanel)
        self.historyPlotHost.setObjectName(u"historyPlotHost")

        self.historyLayout.addWidget(self.historyPlotHost)


        self.overviewLayout.addWidget(self.historyPanel)

        self.eventPanel = QFrame(self.overviewFrame)
        self.eventPanel.setObjectName(u"eventPanel")
        self.eventPanel.setMinimumSize(QSize(360, 0))
        self.eventPanel.setMaximumSize(QSize(410, 16777215))
        self.eventLayout = QVBoxLayout(self.eventPanel)
        self.eventLayout.setSpacing(6)
        self.eventLayout.setObjectName(u"eventLayout")
        self.eventLayout.setContentsMargins(12, 0, 0, 0)
        self.eventTitle = QLabel(self.eventPanel)
        self.eventTitle.setObjectName(u"eventTitle")

        self.eventLayout.addWidget(self.eventTitle)

        self.eventList = QListWidget(self.eventPanel)
        self.eventList.setObjectName(u"eventList")

        self.eventLayout.addWidget(self.eventList)


        self.overviewLayout.addWidget(self.eventPanel)

        self.mainSplitter.addWidget(self.overviewFrame)

        self.contentLayout.addWidget(self.mainSplitter)


        self.rootLayout.addWidget(self.contentWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u9f7f\u8f6e\u7bb1\u5bff\u547d\u6d4b\u8bd5\u53f0", None))
        self.brandMark.setText(QCoreApplication.translate("MainWindow", u"G", None))
        self.titleLabel.setText(QCoreApplication.translate("MainWindow", u"\u9f7f\u8f6e\u7bb1\u5bff\u547d\u6d4b\u8bd5\u53f0", None))
        self.subtitleLabel.setText(QCoreApplication.translate("MainWindow", u"GEARBOX ENDURANCE TEST PLATFORM \u00b7 6 STATIONS", None))
        self.demoBadge.setText(QCoreApplication.translate("MainWindow", u"\u754c\u9762\u6f14\u793a \u00b7 \u6a21\u62df\u6570\u636e", None))
        self.clockLabel.setText(QCoreApplication.translate("MainWindow", u"2026-10-10 14:30:00", None))
        self.plcStatusLabel.setText(QCoreApplication.translate("MainWindow", u"\u25cf PLC \u672a\u8fde\u63a5", None))
        self.settingsButton.setText(QCoreApplication.translate("MainWindow", u"\u7cfb\u7edf\u8bbe\u7f6e", None))
        self.startAllButton.setText(QCoreApplication.translate("MainWindow", u"\u5168\u90e8\u542f\u52a8", None))
        self.stopAllButton.setText(QCoreApplication.translate("MainWindow", u"\u5168\u90e8\u505c\u6b62", None))
        self.pageTitle.setText(QCoreApplication.translate("MainWindow", u"\u5de5\u4f4d\u5b9e\u65f6\u76d1\u63a7", None))
        self.pageHint.setText(QCoreApplication.translate("MainWindow", u"\u4ea7\u54c1 SN \u4e0e\u53c2\u6570\u72ec\u7acb\u8bbe\u5b9a \u00b7 \u79d2\u7ea7\u6570\u636e\u6309\u5de5\u4f4d\u5199\u5165 CSV", None))
        self.stationTotalLabel.setText(QCoreApplication.translate("MainWindow", u"\u5de5\u4f4d  6", None))
        self.runningCountLabel.setText(QCoreApplication.translate("MainWindow", u"\u8fd0\u884c  0", None))
        self.warningCountLabel.setText(QCoreApplication.translate("MainWindow", u"\u544a\u8b66  0", None))
        self.recordStateLabel.setText(QCoreApplication.translate("MainWindow", u"\u25cf \u6570\u636e\u8bb0\u5f55\u5c31\u7eea", None))
        self.historyTitle.setText(QCoreApplication.translate("MainWindow", u"\u5168\u7a0b\u6570\u636e\u7f29\u7565\u56fe", None))
        self.historyHint.setText(QCoreApplication.translate("MainWindow", u"\u5f52\u4e00\u5316\u8d8b\u52bf \u00b7 \u81ea\u52a8\u4fdd\u7559\u672c\u6b21\u6d4b\u8bd5\u5168\u7a0b", None))
        self.resetViewButton.setText(QCoreApplication.translate("MainWindow", u"\u9002\u914d\u5168\u7a0b", None))
        self.eventTitle.setText(QCoreApplication.translate("MainWindow", u"\u8fd0\u884c\u4e8b\u4ef6", None))
    # retranslateUi

