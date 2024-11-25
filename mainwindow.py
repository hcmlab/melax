import sys
import threading
import queue
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Signal, QObject
from ui_form import Ui_MainWindow
import asr_utils  # Utility module containing ASR functions


# Signal class for communication between threads and GUI
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

        # Connect buttons
        self.ui.StartListening.clicked.connect(self.start_listening)
        self.ui.StopandClearListening.clicked.connect(self.stop_and_clear)

    def start_listening(self):
        """
        Starts listening for audio input.
        """
        if self.listening_thread and self.listening_thread.is_alive():
            self.ui.statusbar.showMessage("Already listening...")
            return

        # Gather options from UI
        language = self.ui.languageMBOX.currentText()
        sample_rate = int(self.ui.samplerateMBOX.currentText())
        noise_reduction = self.ui.noisereductionMBOX.currentText()
        sensitivity = self.ui.sensitivityMBOX.currentText()

        # Clear stop event
        self.stop_event.clear()

        self.ui.statusbar.showMessage("Listening...")

        # Start background listening thread
        self.listening_thread = threading.Thread(
            target=asr_utils.listen_in_background,
            args=(self.audio_queue, self.stop_event, language, sample_rate, noise_reduction, sensitivity),
            daemon=True,
        )
        self.listening_thread.start()

        # Start recognition thread if not already running
        if not self.recognition_thread or not self.recognition_thread.is_alive():
            self.recognition_thread = threading.Thread(
                target=asr_utils.recognize_speech,
                args=(self.audio_queue, self.response_queue, self.stop_event),
                daemon=True,
            )
            self.recognition_thread.start()

    def stop_and_clear(self):
        """
        Stops listening and clears the transcribed text.
        """
        self.stop_event.set()  # Signal threads to stop
        self.ui.statusbar.showMessage("Stopped.")

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

    def update_transcribed_text(self, text):
        """
        Updates the transcribed text in the QTextBrowser.
        """
        self.ui.asrTextBrowser.append(text)

    def process_responses(self):
        """
        Process responses from the ASR response queue and update the GUI.
        """
        while True:
            if not self.response_queue.empty():
                text = self.response_queue.get()
                self.signals.update_text.emit(text)  # Emit signal to update GUI


# Main application entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()

    # Start response processing thread
    response_thread = threading.Thread(
        target=widget.process_responses,
        daemon=True,
    )
    response_thread.start()

    sys.exit(app.exec())
