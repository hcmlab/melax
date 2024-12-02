# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QStatusBar, QTextBrowser, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1984, 1036)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(110, 120, 441, 531))
        self.microphoneMBox = QComboBox(self.groupBox)
        self.microphoneMBox.setObjectName(u"microphoneMBox")
        self.microphoneMBox.setGeometry(QRect(120, 70, 241, 24))
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 70, 81, 16))
        self.groupBox_2 = QGroupBox(self.groupBox)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 290, 351, 61))
        self.startASR = QPushButton(self.groupBox_2)
        self.startASR.setObjectName(u"startASR")
        self.startASR.setGeometry(QRect(10, 30, 101, 24))
        self.clearASR = QPushButton(self.groupBox_2)
        self.clearASR.setObjectName(u"clearASR")
        self.clearASR.setGeometry(QRect(120, 30, 101, 24))
        self.stopASR = QPushButton(self.groupBox_2)
        self.stopASR.setObjectName(u"stopASR")
        self.stopASR.setGeometry(QRect(230, 30, 101, 24))
        self.asrTextBrowser = QTextBrowser(self.groupBox)
        self.asrTextBrowser.setObjectName(u"asrTextBrowser")
        self.asrTextBrowser.setGeometry(QRect(10, 370, 351, 131))
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(10, 40, 81, 16))
        self.recognizerMBOX = QComboBox(self.groupBox)
        self.recognizerMBOX.setObjectName(u"recognizerMBOX")
        self.recognizerMBOX.setGeometry(QRect(120, 40, 241, 24))
        self.googleGroupBox = QGroupBox(self.groupBox)
        self.googleGroupBox.setObjectName(u"googleGroupBox")
        self.googleGroupBox.setGeometry(QRect(10, 100, 421, 171))
        self.label_2 = QLabel(self.googleGroupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(10, 40, 61, 16))
        self.googleLanguage = QComboBox(self.googleGroupBox)
        self.googleLanguage.setObjectName(u"googleLanguage")
        self.googleLanguage.setGeometry(QRect(120, 40, 91, 24))
        self.label_3 = QLabel(self.googleGroupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 70, 81, 16))
        self.label_4 = QLabel(self.googleGroupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(10, 100, 91, 16))
        self.googleAPI = QLineEdit(self.googleGroupBox)
        self.googleAPI.setObjectName(u"googleAPI")
        self.googleAPI.setGeometry(QRect(120, 70, 291, 24))
        self.googleEndPoint = QLineEdit(self.googleGroupBox)
        self.googleEndPoint.setObjectName(u"googleEndPoint")
        self.googleEndPoint.setGeometry(QRect(120, 100, 291, 24))
        self.whisperGroupBox = QGroupBox(self.groupBox)
        self.whisperGroupBox.setObjectName(u"whisperGroupBox")
        self.whisperGroupBox.setGeometry(QRect(10, 100, 211, 181))
        self.whisperModel = QComboBox(self.whisperGroupBox)
        self.whisperModel.setObjectName(u"whisperModel")
        self.whisperModel.setGeometry(QRect(80, 40, 72, 24))
        self.label_12 = QLabel(self.whisperGroupBox)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(10, 40, 61, 16))
        self.label_13 = QLabel(self.whisperGroupBox)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setGeometry(QRect(10, 70, 61, 16))
        self.whisperDevice = QComboBox(self.whisperGroupBox)
        self.whisperDevice.setObjectName(u"whisperDevice")
        self.whisperDevice.setGeometry(QRect(80, 70, 72, 24))
        self.whisperLanguage = QComboBox(self.whisperGroupBox)
        self.whisperLanguage.setObjectName(u"whisperLanguage")
        self.whisperLanguage.setGeometry(QRect(80, 100, 72, 24))
        self.label_14 = QLabel(self.whisperGroupBox)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setGeometry(QRect(10, 100, 61, 16))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1984, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Automatic Speech Recognition", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Microphone", None))
        self.groupBox_2.setTitle("")
        self.startASR.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.clearASR.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.stopASR.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"ASR", None))
        self.googleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Google Options", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Language", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"API", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Endpoint", None))
        self.whisperGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Whisper Options", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Model", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Device", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Language", None))
    # retranslateUi

