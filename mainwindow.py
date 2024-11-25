import sys
import threading
import queue
from PySide6.QtWidgets import QApplication, QMainWindow, QInputDialog, QMessageBox
from PySide6.QtCore import Signal, QObject
from ui_form import Ui_MainWindow
import asr_utils  # Utility module containing ASR functions


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

        # Thread placeholders
        self.listening_thread = None
        self.recognition_thread = None

        # Event for stopping threads
        self.stop_event = threading.Event()

        # Store API keys
        self.api_keys = {}

        # Connect signals
        self.signals.update_text.connect(self.update_transcribed_text)

        # Configure UI
        self.setup_ui()

    def setup_ui(self):
        """
        Configure UI elements and connect buttons to their respective slots.
        """
        # Populate dropdowns
        asr_utils.populate_microphone_list(self.ui.microphoneMBox)
        self.ui.languageMBOX.addItems(["en-US", "es-ES", "de-DE"])  # Language options
        self.ui.samplerateMBOX.addItems(["16000", "22050", "44100"])  # Sample rate options
        self.ui.noisereductionMBOX.addItems(["Enabled", "Disabled"])  # Noise reduction options
        self.ui.sensitivityMBOX.addItems(["Low", "Medium", "High"])  # Sensitivity options
        self.ui.recognizerMBOX.addItems([
                    "Google Web Speech API",
                    "Google Cloud Speech API",
                    "Whisper",
                    "Whisper API"
                ])

        # Connect buttons and dropdowns
        self.ui.StartListening.clicked.connect(self.start_listening)
        self.ui.StopandClearListening.clicked.connect(self.stop_and_clear)
        self.ui.recognizerMBOX.currentTextChanged.connect(self.handle_recognizer_selection)

    def process_responses(self):
           """
           Continuously monitors the response queue and updates the GUI with recognized text.
           """
           while True:
               if not self.response_queue.empty():
                   text = self.response_queue.get()  # Retrieve the recognized text
                   self.signals.update_text.emit(text)  # Emit a signal to update the text in the GUI


    def handle_recognizer_selection(self, recognizer_type):
       if recognizer_type in ["Google Cloud Speech API", "Whisper API"]:
           api_key_description = "Google Cloud JSON Credentials" if recognizer_type == "Google Cloud Speech API" else "OpenAI API Key"
           api_key, ok = QInputDialog.getText(
               self, f"API Key Required for {recognizer_type}", f"Enter your {api_key_description}:"
           )
           if ok and api_key:
               key_name = "google_cloud" if recognizer_type == "Google Cloud Speech API" else "openai"
               self.api_keys[key_name] = api_key

    def prompt_for_api_key(self, recognizer_type, api_key_description):
        if recognizer_type in ["Wit.ai", "Bing Speech API", "Azure Speech API"]:
            api_key, ok = QInputDialog.getText(
                self,
                f"API Key Required for {recognizer_type}",
                f"Enter your {api_key_description}:",
            )
            if ok and api_key:
                self.api_keys[recognizer_type] = api_key

    def start_listening(self):
        if self.listening_thread and self.listening_thread.is_alive():
            self.ui.statusbar.showMessage("Already listening...")
            return

        language = self.ui.languageMBOX.currentText()
        sample_rate = int(self.ui.samplerateMBOX.currentText())
        noise_reduction = self.ui.noisereductionMBOX.currentText()
        sensitivity = self.ui.sensitivityMBOX.currentText()
        recognizer_type = self.ui.recognizerMBOX.currentText()

        self.stop_event.clear()

        self.listening_thread = threading.Thread(
            target=asr_utils.listen_in_background,
            args=(self.audio_queue, self.stop_event, language, sample_rate, noise_reduction, sensitivity),
            daemon=True,
        )
        self.listening_thread.start()

        if not self.recognition_thread or not self.recognition_thread.is_alive():
            self.recognition_thread = threading.Thread(
                target=asr_utils.recognize_speech,
                args=(self.audio_queue, self.response_queue, self.stop_event, recognizer_type, self.api_keys),
                daemon=True,
            )
            self.recognition_thread.start()

    def stop_and_clear(self):
        """
        Stops listening and clears the transcribed text.
        """
        self.stop_event.set()  # Signal the thread to stop

        # Send termination signal to audio queue
        self.audio_queue.put(None)

        # Wait for the listening thread to finish
        if self.listening_thread:
            self.listening_thread.join()
            self.listening_thread = None

        # Wait for the recognition thread to finish
        if self.recognition_thread:
            self.recognition_thread.join()
            self.recognition_thread = None

        # Clear the transcribed text
        self.ui.asrTextBrowser.clear()
        self.ui.statusbar.showMessage("Stopped and cleared.")

    def update_transcribed_text(self, text):
        self.ui.asrTextBrowser.append(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()

    response_thread = threading.Thread(
        target=widget.process_responses,
        daemon=True,
    )
    response_thread.start()

    sys.exit(app.exec())
