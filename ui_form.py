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
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QTextBrowser, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1984, 1036)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(30, 30, 371, 491))
        self.microphoneMBox = QComboBox(self.groupBox)
        self.microphoneMBox.setObjectName(u"microphoneMBox")
        self.microphoneMBox.setGeometry(QRect(120, 70, 241, 24))
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 70, 81, 16))
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(10, 100, 61, 16))
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 130, 81, 16))
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(10, 160, 91, 16))
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(10, 190, 91, 16))
        self.groupBox_2 = QGroupBox(self.groupBox)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 270, 271, 61))
        self.StartListening = QPushButton(self.groupBox_2)
        self.StartListening.setObjectName(u"StartListening")
        self.StartListening.setGeometry(QRect(10, 30, 101, 24))
        self.StopandClearListening = QPushButton(self.groupBox_2)
        self.StopandClearListening.setObjectName(u"StopandClearListening")
        self.StopandClearListening.setGeometry(QRect(140, 30, 101, 24))
        self.languageMBOX = QComboBox(self.groupBox)
        self.languageMBOX.setObjectName(u"languageMBOX")
        self.languageMBOX.setGeometry(QRect(120, 100, 91, 24))
        self.samplerateMBOX = QComboBox(self.groupBox)
        self.samplerateMBOX.setObjectName(u"samplerateMBOX")
        self.samplerateMBOX.setGeometry(QRect(120, 130, 91, 24))
        self.noisereductionMBOX = QComboBox(self.groupBox)
        self.noisereductionMBOX.setObjectName(u"noisereductionMBOX")
        self.noisereductionMBOX.setGeometry(QRect(120, 160, 91, 24))
        self.sensitivityMBOX = QComboBox(self.groupBox)
        self.sensitivityMBOX.setObjectName(u"sensitivityMBOX")
        self.sensitivityMBOX.setGeometry(QRect(120, 190, 91, 24))
        self.asrTextBrowser = QTextBrowser(self.groupBox)
        self.asrTextBrowser.setObjectName(u"asrTextBrowser")
        self.asrTextBrowser.setGeometry(QRect(10, 340, 351, 131))
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(10, 40, 81, 16))
        self.recognizerMBOX = QComboBox(self.groupBox)
        self.recognizerMBOX.setObjectName(u"recognizerMBOX")
        self.recognizerMBOX.setGeometry(QRect(120, 40, 241, 24))
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
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Language", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Sample rate", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Noise Reduction", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Sensitivity", None))
        self.groupBox_2.setTitle("")
        self.StartListening.setText(QCoreApplication.translate("MainWindow", u"Start Listening", None))
        self.StopandClearListening.setText(QCoreApplication.translate("MainWindow", u"Stop and Clear", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"ASR", None))
    # retranslateUi

