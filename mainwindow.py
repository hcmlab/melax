import sys
import queue
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton,
    QTextBrowser, QWidget
)
from PySide6.QtCore import Signal, QObject
from ui_form import Ui_MainWindow  # Generated UI module from .ui file
from test_cases.google_with_mp_vda import RealTimeSpeakingTranscriberGoogleAPI
from test_cases.whisper_with_mp_vda import RealTimeSpeakingTranscriber
from utils import list_microphones


class WorkerSignals(QObject):
    update_text = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Queues for audio and recognized text
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.signals = WorkerSignals()

        # ASR module placeholder
        self.current_asr = None

        # Thread placeholders
        self.listening_thread = None
        self.recognition_thread = None

        # Event for stopping threads
        self.stop_event = threading.Event()

        # Connect signals
        self.signals.update_text.connect(self.update_transcribed_text)

        # Configure UI and dynamic behavior
        self.setup_ui()

    def setup_ui(self):
        """
        Configure UI elements and connect buttons to their respective slots.
        """
        # Populate microphone list
        self.populate_microphone_list()

        # Populate recognizer dropdown
        self.ui.recognizerMBOX.addItems(["Google", "Whisper"])

        # Configure Google ASR options
        self.ui.googleAPI.setText("AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw")
        self.ui.googleEndPoint.setText("http://www.google.com/speech-api/v2/recognize")
        self.ui.googleLanguage.addItems(["en-US", "es-ES", "fr-FR", "de-DE", "zh-CN"])  # Language options

        # Configure Whisper ASR options
        self.ui.whisperDevice.addItems(["cpu", "cuda"])
        self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large", "turbo"])
        self.ui.whisperLanguage.addItems(["Auto-detect", "en", "es", "fr", "de", "zh"])  # Language options

        # Connect recognizer selection to toggle ASR options
        self.ui.recognizerMBOX.currentTextChanged.connect(self.toggle_asr_options)

        # Connect buttons to their slots
        self.ui.StartListening.clicked.connect(self.start_listening)
        self.ui.StopandClearListening.clicked.connect(self.stop_and_clear)

        # Show Google ASR options by default
        self.toggle_asr_options("Google")

    def populate_microphone_list(self):
        """
        Populates a QComboBox with available microphone devices.
        """
        self.ui.microphoneMBox.clear()
        microphones = list_microphones()
        for idx, name in microphones:
            self.ui.microphoneMBox.addItem(name, userData=idx)

    def toggle_asr_options(self, recognizer_type):
        """
        Show or hide specific ASR options based on the selected recognizer type.
        """
        if recognizer_type == "Google":
            self.ui.googleGroupBox.setVisible(True)
            self.ui.whisperGroupBox.setVisible(False)
        elif recognizer_type == "Whisper":
            self.ui.googleGroupBox.setVisible(False)
            self.ui.whisperGroupBox.setVisible(True)

    def start_listening(self):
        """
        Start the ASR listening and recognition threads.
        """
        if self.listening_thread and self.listening_thread.is_alive():
            self.ui.statusbar.showMessage("Already listening...")
            return

        recognizer_type = self.ui.recognizerMBOX.currentText()

        if recognizer_type == "Google":
            api_key = self.ui.googleAPI.text()
            endpoint = self.ui.googleEndPoint.text()
            language = self.ui.googleLanguage.currentText()
            self.current_asr = RealTimeSpeakingTranscriberGoogleAPI(api_key=api_key, endpoint=endpoint, language=language)
        elif recognizer_type == "Whisper":
            model_name = self.ui.whisperModel.currentText()
            device = self.ui.whisperDevice.currentText()
            language = self.ui.whisperLanguage.currentText()
            self.current_asr = RealTimeSpeakingTranscriber(model_name=model_name, device=device, language=language)
        else:
            self.ui.statusbar.showMessage("Please select a valid ASR recognizer.")
            return

        self.stop_event.clear()

        # Start the listening thread
        self.listening_thread = threading.Thread(
            target=self.current_asr.start,
            daemon=True
        )
        self.listening_thread.start()

        # Start the recognition thread
        self.recognition_thread = threading.Thread(
            target=self.process_responses,
            daemon=True
        )
        self.recognition_thread.start()

    def process_responses(self):
        """
        Continuously monitors the response queue and updates the GUI with recognized text.
        """
        while not self.stop_event.is_set():
            if not self.response_queue.empty():
                text = self.response_queue.get()  # Retrieve the recognized text
                self.signals.update_text.emit(text)  # Emit a signal to update the text in the GUI

    def stop_and_clear(self):
        """
        Stop ASR processing and clear the transcription box.
        """
        self.stop_event.set()  # Signal the thread to stop

        if self.listening_thread:
            self.current_asr.stop()
            self.listening_thread = None

        if self.recognition_thread:
            self.recognition_thread = None

        # Clear the transcribed text
        self.ui.asrTextBrowser.clear()
        self.ui.statusbar.showMessage("Stopped and cleared.")

    def update_transcribed_text(self, text):
        """
        Update the transcribed text in the GUI.
        """
        self.ui.asrTextBrowser.append(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
