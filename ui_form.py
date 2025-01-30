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
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDial,
    QFormLayout, QGroupBox, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QSlider, QSpinBox, QStatusBar,
    QTabWidget, QTextBrowser, QTextEdit, QToolButton,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1374, 985)
        self.actiondark = QAction(MainWindow)
        self.actiondark.setObjectName(u"actiondark")
        self.actionlight = QAction(MainWindow)
        self.actionlight.setObjectName(u"actionlight")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 491, 491))
        font = QFont()
        font.setPointSize(12)
        self.groupBox.setFont(font)
        self.googleGroupBox = QGroupBox(self.groupBox)
        self.googleGroupBox.setObjectName(u"googleGroupBox")
        self.googleGroupBox.setGeometry(QRect(10, 130, 461, 171))
        self.googleGroupBox.setFont(font)
        self.formLayoutWidget = QWidget(self.googleGroupBox)
        self.formLayoutWidget.setObjectName(u"formLayoutWidget")
        self.formLayoutWidget.setGeometry(QRect(10, 40, 160, 31))
        self.formLayout = QFormLayout(self.formLayoutWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.formLayoutWidget)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setPointSize(9)
        self.label_2.setFont(font1)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.googleLanguage = QComboBox(self.formLayoutWidget)
        self.googleLanguage.setObjectName(u"googleLanguage")
        self.googleLanguage.setFont(font1)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.googleLanguage)

        self.formLayoutWidget_2 = QWidget(self.googleGroupBox)
        self.formLayoutWidget_2.setObjectName(u"formLayoutWidget_2")
        self.formLayoutWidget_2.setGeometry(QRect(10, 80, 441, 80))
        self.formLayout_2 = QFormLayout(self.formLayoutWidget_2)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.formLayoutWidget_2)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font1)
        self.label_3.setTextFormat(Qt.TextFormat.AutoText)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.googleAPI = QLineEdit(self.formLayoutWidget_2)
        self.googleAPI.setObjectName(u"googleAPI")
        self.googleAPI.setFont(font1)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.googleAPI)

        self.label_4 = QLabel(self.formLayoutWidget_2)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font1)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.googleEndPoint = QLineEdit(self.formLayoutWidget_2)
        self.googleEndPoint.setObjectName(u"googleEndPoint")
        self.googleEndPoint.setFont(font1)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.googleEndPoint)

        self.whisperGroupBox = QGroupBox(self.groupBox)
        self.whisperGroupBox.setObjectName(u"whisperGroupBox")
        self.whisperGroupBox.setGeometry(QRect(10, 110, 211, 171))
        self.whisperGroupBox.setFont(font)
        self.formLayoutWidget_3 = QWidget(self.whisperGroupBox)
        self.formLayoutWidget_3.setObjectName(u"formLayoutWidget_3")
        self.formLayoutWidget_3.setGeometry(QRect(0, 50, 201, 111))
        self.formLayout_3 = QFormLayout(self.formLayoutWidget_3)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_12 = QLabel(self.formLayoutWidget_3)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font1)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_12)

        self.whisperModel = QComboBox(self.formLayoutWidget_3)
        self.whisperModel.setObjectName(u"whisperModel")
        self.whisperModel.setFont(font1)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.whisperModel)

        self.label_13 = QLabel(self.formLayoutWidget_3)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font1)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_13)

        self.whisperDevice = QComboBox(self.formLayoutWidget_3)
        self.whisperDevice.setObjectName(u"whisperDevice")
        self.whisperDevice.setFont(font1)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.whisperDevice)

        self.label_14 = QLabel(self.formLayoutWidget_3)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font1)

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_14)

        self.whisperLanguage = QComboBox(self.formLayoutWidget_3)
        self.whisperLanguage.setObjectName(u"whisperLanguage")
        self.whisperLanguage.setFont(font1)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.whisperLanguage)

        self.formLayoutWidget_11 = QWidget(self.groupBox)
        self.formLayoutWidget_11.setObjectName(u"formLayoutWidget_11")
        self.formLayoutWidget_11.setGeometry(QRect(10, 40, 281, 61))
        self.formLayout_11 = QFormLayout(self.formLayoutWidget_11)
        self.formLayout_11.setObjectName(u"formLayout_11")
        self.formLayout_11.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.formLayoutWidget_11)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font1)

        self.formLayout_11.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.recognizerMBOX = QComboBox(self.formLayoutWidget_11)
        self.recognizerMBOX.setObjectName(u"recognizerMBOX")
        self.recognizerMBOX.setFont(font1)

        self.formLayout_11.setWidget(0, QFormLayout.FieldRole, self.recognizerMBOX)

        self.label_27 = QLabel(self.formLayoutWidget_11)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setFont(font1)

        self.formLayout_11.setWidget(1, QFormLayout.LabelRole, self.label_27)

        self.microphoneMBox = QComboBox(self.formLayoutWidget_11)
        self.microphoneMBox.setObjectName(u"microphoneMBox")
        self.microphoneMBox.setFont(font1)

        self.formLayout_11.setWidget(1, QFormLayout.FieldRole, self.microphoneMBox)

        self.groupBox_6 = QGroupBox(self.centralwidget)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setGeometry(QRect(520, 10, 431, 491))
        self.groupBox_6.setFont(font)
        self.formLayoutWidget_4 = QWidget(self.groupBox_6)
        self.formLayoutWidget_4.setObjectName(u"formLayoutWidget_4")
        self.formLayoutWidget_4.setGeometry(QRect(10, 40, 160, 41))
        self.formLayout_4 = QFormLayout(self.formLayoutWidget_4)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_24 = QLabel(self.formLayoutWidget_4)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setFont(font1)

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_24)

        self.LLMChocie = QComboBox(self.formLayoutWidget_4)
        self.LLMChocie.setObjectName(u"LLMChocie")
        self.LLMChocie.setFont(font1)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.LLMChocie)

        self.formLayoutWidget_7 = QWidget(self.groupBox_6)
        self.formLayoutWidget_7.setObjectName(u"formLayoutWidget_7")
        self.formLayoutWidget_7.setGeometry(QRect(10, 310, 411, 151))
        self.formLayout_7 = QFormLayout(self.formLayoutWidget_7)
        self.formLayout_7.setObjectName(u"formLayout_7")
        self.formLayout_7.setContentsMargins(0, 0, 0, 0)
        self.systemPromptEdit = QTextEdit(self.formLayoutWidget_7)
        self.systemPromptEdit.setObjectName(u"systemPromptEdit")
        self.systemPromptEdit.setFont(font1)

        self.formLayout_7.setWidget(0, QFormLayout.FieldRole, self.systemPromptEdit)

        self.label_18 = QLabel(self.formLayoutWidget_7)
        self.label_18.setObjectName(u"label_18")
        font2 = QFont()
        font2.setFamilies([u"Segoe UI"])
        font2.setPointSize(9)
        self.label_18.setFont(font2)

        self.formLayout_7.setWidget(0, QFormLayout.LabelRole, self.label_18)

        self.openai_group = QGroupBox(self.groupBox_6)
        self.openai_group.setObjectName(u"openai_group")
        self.openai_group.setGeometry(QRect(10, 90, 411, 211))
        self.openai_group.setFont(font)
        self.formLayoutWidget_5 = QWidget(self.openai_group)
        self.formLayoutWidget_5.setObjectName(u"formLayoutWidget_5")
        self.formLayoutWidget_5.setGeometry(QRect(10, 40, 381, 77))
        self.formLayout_5 = QFormLayout(self.formLayoutWidget_5)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.formLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_19 = QLabel(self.formLayoutWidget_5)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setFont(font2)

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_19)

        self.openaiAPIKey = QLineEdit(self.formLayoutWidget_5)
        self.openaiAPIKey.setObjectName(u"openaiAPIKey")
        self.openaiAPIKey.setFont(font1)

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.openaiAPIKey)

        self.formLayoutWidget_6 = QWidget(self.openai_group)
        self.formLayoutWidget_6.setObjectName(u"formLayoutWidget_6")
        self.formLayoutWidget_6.setGeometry(QRect(10, 120, 201, 79))
        self.formLayout_6 = QFormLayout(self.formLayoutWidget_6)
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.formLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_21 = QLabel(self.formLayoutWidget_6)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setFont(font2)

        self.formLayout_6.setWidget(2, QFormLayout.LabelRole, self.label_21)

        self.maxTokenOpenAI = QSpinBox(self.formLayoutWidget_6)
        self.maxTokenOpenAI.setObjectName(u"maxTokenOpenAI")
        self.maxTokenOpenAI.setFont(font1)
        self.maxTokenOpenAI.setMinimum(1)
        self.maxTokenOpenAI.setMaximum(4096)
        self.maxTokenOpenAI.setValue(1024)

        self.formLayout_6.setWidget(2, QFormLayout.FieldRole, self.maxTokenOpenAI)

        self.label_22 = QLabel(self.formLayoutWidget_6)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setFont(font2)

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.label_22)

        self.temperatureOpenAI = QSlider(self.formLayoutWidget_6)
        self.temperatureOpenAI.setObjectName(u"temperatureOpenAI")
        font3 = QFont()
        font3.setPointSize(14)
        self.temperatureOpenAI.setFont(font3)
        self.temperatureOpenAI.setMaximum(100)
        self.temperatureOpenAI.setSingleStep(1)
        self.temperatureOpenAI.setValue(70)
        self.temperatureOpenAI.setOrientation(Qt.Orientation.Horizontal)

        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.temperatureOpenAI)

        self.label_23 = QLabel(self.formLayoutWidget_6)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setFont(font2)

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_23)

        self.llmMBOX = QComboBox(self.formLayoutWidget_6)
        self.llmMBOX.setObjectName(u"llmMBOX")
        self.llmMBOX.setFont(font1)

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.llmMBOX)

        self.llmTemperatureLable = QLabel(self.openai_group)
        self.llmTemperatureLable.setObjectName(u"llmTemperatureLable")
        self.llmTemperatureLable.setGeometry(QRect(230, 130, 89, 37))
        self.llmTemperatureLable.setFont(font1)
        self.llama_group = QGroupBox(self.groupBox_6)
        self.llama_group.setObjectName(u"llama_group")
        self.llama_group.setGeometry(QRect(20, 90, 251, 121))
        self.llama_group.setFont(font)
        self.formLayoutWidget_13 = QWidget(self.llama_group)
        self.formLayoutWidget_13.setObjectName(u"formLayoutWidget_13")
        self.formLayoutWidget_13.setGeometry(QRect(0, 30, 201, 79))
        self.formLayout_13 = QFormLayout(self.formLayoutWidget_13)
        self.formLayout_13.setObjectName(u"formLayout_13")
        self.formLayout_13.setContentsMargins(0, 0, 0, 0)
        self.label_29 = QLabel(self.formLayoutWidget_13)
        self.label_29.setObjectName(u"label_29")
        self.label_29.setFont(font2)

        self.formLayout_13.setWidget(2, QFormLayout.LabelRole, self.label_29)

        self.maxTokenLlama = QSpinBox(self.formLayoutWidget_13)
        self.maxTokenLlama.setObjectName(u"maxTokenLlama")
        self.maxTokenLlama.setFont(font1)
        self.maxTokenLlama.setMinimum(1)
        self.maxTokenLlama.setMaximum(4096)
        self.maxTokenLlama.setValue(1024)

        self.formLayout_13.setWidget(2, QFormLayout.FieldRole, self.maxTokenLlama)

        self.label_30 = QLabel(self.formLayoutWidget_13)
        self.label_30.setObjectName(u"label_30")
        self.label_30.setFont(font2)

        self.formLayout_13.setWidget(1, QFormLayout.LabelRole, self.label_30)

        self.temperatureLlama = QSlider(self.formLayoutWidget_13)
        self.temperatureLlama.setObjectName(u"temperatureLlama")
        self.temperatureLlama.setFont(font3)
        self.temperatureLlama.setMaximum(100)
        self.temperatureLlama.setSingleStep(1)
        self.temperatureLlama.setValue(70)
        self.temperatureLlama.setOrientation(Qt.Orientation.Horizontal)

        self.formLayout_13.setWidget(1, QFormLayout.FieldRole, self.temperatureLlama)

        self.label_31 = QLabel(self.formLayoutWidget_13)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setFont(font2)

        self.formLayout_13.setWidget(0, QFormLayout.LabelRole, self.label_31)

        self.llmMBOX_Llama = QComboBox(self.formLayoutWidget_13)
        self.llmMBOX_Llama.setObjectName(u"llmMBOX_Llama")
        self.llmMBOX_Llama.setFont(font1)

        self.formLayout_13.setWidget(0, QFormLayout.FieldRole, self.llmMBOX_Llama)

        self.TemperatureLablellama = QLabel(self.llama_group)
        self.TemperatureLablellama.setObjectName(u"TemperatureLablellama")
        self.TemperatureLablellama.setGeometry(QRect(210, 50, 89, 37))
        self.TemperatureLablellama.setFont(font1)
        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(970, 10, 391, 141))
        self.groupBox_3.setFont(font)
        self.formLayoutWidget_9 = QWidget(self.groupBox_3)
        self.formLayoutWidget_9.setObjectName(u"formLayoutWidget_9")
        self.formLayoutWidget_9.setGeometry(QRect(10, 30, 160, 80))
        self.formLayout_9 = QFormLayout(self.formLayoutWidget_9)
        self.formLayout_9.setObjectName(u"formLayout_9")
        self.formLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.formLayoutWidget_9)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font1)

        self.formLayout_9.setWidget(0, QFormLayout.LabelRole, self.label_5)

        self.ttsEngineCombo = QComboBox(self.formLayoutWidget_9)
        self.ttsEngineCombo.setObjectName(u"ttsEngineCombo")
        self.ttsEngineCombo.setFont(font1)

        self.formLayout_9.setWidget(0, QFormLayout.FieldRole, self.ttsEngineCombo)

        self.label_7 = QLabel(self.formLayoutWidget_9)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font1)

        self.formLayout_9.setWidget(1, QFormLayout.LabelRole, self.label_7)

        self.ttslanguage = QComboBox(self.formLayoutWidget_9)
        self.ttslanguage.setObjectName(u"ttslanguage")
        self.ttslanguage.setFont(font1)

        self.formLayout_9.setWidget(1, QFormLayout.FieldRole, self.ttslanguage)

        self.chatOutpuTab = QTabWidget(self.centralwidget)
        self.chatOutpuTab.setObjectName(u"chatOutpuTab")
        self.chatOutpuTab.setGeometry(QRect(10, 580, 1361, 331))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.contextBrowserOpenAI = QTextBrowser(self.tab)
        self.contextBrowserOpenAI.setObjectName(u"contextBrowserOpenAI")
        self.contextBrowserOpenAI.setGeometry(QRect(0, 10, 1351, 291))
        self.contextBrowserOpenAI.setFont(font3)
        self.chatOutpuTab.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.logOutput = QTextBrowser(self.tab_2)
        self.logOutput.setObjectName(u"logOutput")
        self.logOutput.setGeometry(QRect(0, 0, 1351, 301))
        self.chatOutpuTab.addTab(self.tab_2, "")
        self.groupBox_4 = QGroupBox(self.centralwidget)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(970, 160, 391, 341))
        self.groupBox_4.setFont(font)
        self.formLayoutWidget_8 = QWidget(self.groupBox_4)
        self.formLayoutWidget_8.setObjectName(u"formLayoutWidget_8")
        self.formLayoutWidget_8.setGeometry(QRect(10, 160, 241, 171))
        self.formLayout_8 = QFormLayout(self.formLayoutWidget_8)
        self.formLayout_8.setObjectName(u"formLayout_8")
        self.formLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_26 = QLabel(self.formLayoutWidget_8)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setFont(font1)

        self.formLayout_8.setWidget(0, QFormLayout.LabelRole, self.label_26)

        self.emotionsQCombo = QComboBox(self.formLayoutWidget_8)
        self.emotionsQCombo.setObjectName(u"emotionsQCombo")
        self.emotionsQCombo.setFont(font1)

        self.formLayout_8.setWidget(0, QFormLayout.FieldRole, self.emotionsQCombo)

        self.label_8 = QLabel(self.formLayoutWidget_8)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font1)

        self.formLayout_8.setWidget(1, QFormLayout.LabelRole, self.label_8)

        self.ttsSentenceSplit = QComboBox(self.formLayoutWidget_8)
        self.ttsSentenceSplit.setObjectName(u"ttsSentenceSplit")
        self.ttsSentenceSplit.setFont(font1)

        self.formLayout_8.setWidget(1, QFormLayout.FieldRole, self.ttsSentenceSplit)

        self.label_9 = QLabel(self.formLayoutWidget_8)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font1)

        self.formLayout_8.setWidget(2, QFormLayout.LabelRole, self.label_9)

        self.ttsPlayback = QComboBox(self.formLayoutWidget_8)
        self.ttsPlayback.setObjectName(u"ttsPlayback")
        self.ttsPlayback.setFont(font1)

        self.formLayout_8.setWidget(2, QFormLayout.FieldRole, self.ttsPlayback)

        self.label_10 = QLabel(self.formLayoutWidget_8)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font1)

        self.formLayout_8.setWidget(3, QFormLayout.LabelRole, self.label_10)

        self.blockUntilFinish = QCheckBox(self.formLayoutWidget_8)
        self.blockUntilFinish.setObjectName(u"blockUntilFinish")

        self.formLayout_8.setWidget(3, QFormLayout.FieldRole, self.blockUntilFinish)

        self.label_15 = QLabel(self.formLayoutWidget_8)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setFont(font1)

        self.formLayout_8.setWidget(5, QFormLayout.LabelRole, self.label_15)

        self.ttsDelayBetweenChunks = QDial(self.formLayoutWidget_8)
        self.ttsDelayBetweenChunks.setObjectName(u"ttsDelayBetweenChunks")

        self.formLayout_8.setWidget(5, QFormLayout.FieldRole, self.ttsDelayBetweenChunks)

        self.label_11 = QLabel(self.formLayoutWidget_8)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font1)

        self.formLayout_8.setWidget(4, QFormLayout.LabelRole, self.label_11)

        self.ttsChunkDuration = QSlider(self.formLayoutWidget_8)
        self.ttsChunkDuration.setObjectName(u"ttsChunkDuration")
        self.ttsChunkDuration.setMinimum(1)
        self.ttsChunkDuration.setOrientation(Qt.Orientation.Horizontal)

        self.formLayout_8.setWidget(4, QFormLayout.FieldRole, self.ttsChunkDuration)

        self.formLayoutWidget_10 = QWidget(self.groupBox_4)
        self.formLayoutWidget_10.setObjectName(u"formLayoutWidget_10")
        self.formLayoutWidget_10.setGeometry(QRect(10, 90, 351, 61))
        self.formLayout_10 = QFormLayout(self.formLayoutWidget_10)
        self.formLayout_10.setObjectName(u"formLayout_10")
        self.formLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_16 = QLabel(self.formLayoutWidget_10)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setFont(font1)

        self.formLayout_10.setWidget(0, QFormLayout.LabelRole, self.label_16)

        self.a2fUrl = QLineEdit(self.formLayoutWidget_10)
        self.a2fUrl.setObjectName(u"a2fUrl")
        self.a2fUrl.setFont(font1)

        self.formLayout_10.setWidget(0, QFormLayout.FieldRole, self.a2fUrl)

        self.label_17 = QLabel(self.formLayoutWidget_10)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setFont(font1)

        self.formLayout_10.setWidget(1, QFormLayout.LabelRole, self.label_17)

        self.a2fInstanceName = QLineEdit(self.formLayoutWidget_10)
        self.a2fInstanceName.setObjectName(u"a2fInstanceName")
        self.a2fInstanceName.setFont(font1)

        self.formLayout_10.setWidget(1, QFormLayout.FieldRole, self.a2fInstanceName)

        self.verticalLayoutWidget = QWidget(self.groupBox_4)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(260, 210, 91, 80))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.chunckSizeLable = QLabel(self.verticalLayoutWidget)
        self.chunckSizeLable.setObjectName(u"chunckSizeLable")
        self.chunckSizeLable.setFont(font1)

        self.verticalLayout.addWidget(self.chunckSizeLable)

        self.delayLable = QLabel(self.verticalLayoutWidget)
        self.delayLable.setObjectName(u"delayLable")
        self.delayLable.setFont(font1)

        self.verticalLayout.addWidget(self.delayLable)

        self.a2fUrl_headless = QLineEdit(self.groupBox_4)
        self.a2fUrl_headless.setObjectName(u"a2fUrl_headless")
        self.a2fUrl_headless.setGeometry(QRect(110, 30, 141, 21))
        font4 = QFont()
        font4.setPointSize(8)
        self.a2fUrl_headless.setFont(font4)
        self.label_25 = QLabel(self.groupBox_4)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setGeometry(QRect(10, 30, 81, 21))
        self.label_25.setFont(font1)
        self.label_20 = QLabel(self.groupBox_4)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setGeometry(QRect(10, 60, 81, 21))
        self.label_20.setFont(font1)
        self.usdCombo = QComboBox(self.groupBox_4)
        self.usdCombo.setObjectName(u"usdCombo")
        self.usdCombo.setGeometry(QRect(110, 60, 131, 22))
        self.usdCombo.setFont(font1)
        self.connectHeadlessPushbutton = QToolButton(self.groupBox_4)
        self.connectHeadlessPushbutton.setObjectName(u"connectHeadlessPushbutton")
        self.connectHeadlessPushbutton.setGeometry(QRect(272, 30, 20, 20))
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.SyncSynchronizing))
        self.connectHeadlessPushbutton.setIcon(icon)
        self.loadUsdPushbutton = QToolButton(self.groupBox_4)
        self.loadUsdPushbutton.setObjectName(u"loadUsdPushbutton")
        self.loadUsdPushbutton.setGeometry(QRect(271, 60, 21, 21))
        icon1 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ListAdd))
        self.loadUsdPushbutton.setIcon(icon1)
        self.startAll = QPushButton(self.centralwidget)
        self.startAll.setObjectName(u"startAll")
        self.startAll.setGeometry(QRect(540, 540, 101, 41))
        self.startAll.setFont(font3)
        icon2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.MediaPlaybackStart))
        self.startAll.setIcon(icon2)
        self.stopAll = QPushButton(self.centralwidget)
        self.stopAll.setObjectName(u"stopAll")
        self.stopAll.setGeometry(QRect(680, 540, 111, 41))
        self.stopAll.setFont(font3)
        icon3 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.MediaPlaybackStop))
        self.stopAll.setIcon(icon3)
        self.clearAll = QPushButton(self.centralwidget)
        self.clearAll.setObjectName(u"clearAll")
        self.clearAll.setGeometry(QRect(830, 540, 101, 41))
        self.clearAll.setFont(font3)
        icon4 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRestore))
        self.clearAll.setIcon(icon4)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1374, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuGUI_Theme = QMenu(self.menuView)
        self.menuGUI_Theme.setObjectName(u"menuGUI_Theme")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menuView.addAction(self.menuGUI_Theme.menuAction())
        self.menuGUI_Theme.addAction(self.actiondark)
        self.menuGUI_Theme.addAction(self.actionlight)

        self.retranslateUi(MainWindow)

        self.chatOutpuTab.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actiondark.setText(QCoreApplication.translate("MainWindow", u"dark", None))
        self.actionlight.setText(QCoreApplication.translate("MainWindow", u"light", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Audio Classification and Speech to Text", None))
        self.googleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Google Options", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Language", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"API Key", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Endpoint", None))
        self.whisperGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Whisper Options", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Model", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Device", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Language", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"ASR", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Microphone", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Conversation Orchestrator", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"LLM", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Assistant Persona", None))
        self.openai_group.setTitle(QCoreApplication.translate("MainWindow", u"OpenAI Options", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"API Key", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Max-tokens", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"Temperature", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Model", None))
        self.llmTemperatureLable.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.llama_group.setTitle(QCoreApplication.translate("MainWindow", u"Llama Options", None))
        self.label_29.setText(QCoreApplication.translate("MainWindow", u"Max-tokens", None))
        self.label_30.setText(QCoreApplication.translate("MainWindow", u"Temperature", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", u"Model", None))
        self.TemperatureLablellama.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Voice Synthesis", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"TTS Engine", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Language", None))
        self.chatOutpuTab.setTabText(self.chatOutpuTab.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Conversation", None))
        self.chatOutpuTab.setTabText(self.chatOutpuTab.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Log", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Behavior Generator", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"Emotion", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Sentence Split", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Playback Method", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Block Until Finish", None))
        self.blockUntilFinish.setText("")
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"Delay Between Chunks", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Chunk Duration", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Audio2Face Url:", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Instance Name", None))
        self.chunckSizeLable.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.delayLable.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.a2fUrl_headless.setText("")
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Server Address", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"Load USD", None))
        self.connectHeadlessPushbutton.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.loadUsdPushbutton.setText("")
        self.startAll.setText("")
        self.stopAll.setText("")
        self.clearAll.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menuGUI_Theme.setTitle(QCoreApplication.translate("MainWindow", u"GUI Theme", None))
    # retranslateUi

