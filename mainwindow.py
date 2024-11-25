# This Python file uses the following encoding: utf-8
import sys
import threading
import queue
import logging
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Signal, QObject
from ui_form import Ui_MainWindow  # Ensure the ui_form.py file is generated and available
import speech_recognition as sr
import time

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define global variables for recognizer and microphone
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Signal class for communication between threads and GUI
class WorkerSignals(QObject):
    update_text = Signal(str)

# Global flag for listening state
is_listening = False

def populate_microphone_list(combo_box):
    """
    Populates the given QComboBox with the available microphone options.

    Parameters:
        combo_box (QComboBox): The dropdown to populate with microphone names.
    """
    try:
        # Get the list of available microphone names
        microphone_list = sr.Microphone.list_microphone_names()

        # Clear the combo box in case it's already populated
        combo_box.clear()

        # Add each microphone to the combo box
        for index, mic_name in enumerate(microphone_list):
            combo_box.addItem(f"{index}: {mic_name}")

        if not microphone_list:
            combo_box.addItem("No microphones found")
    except Exception as e:
        combo_box.addItem("Error detecting microphones")
        print(f"Error: {e}")

# Listening in the background
def listen_in_background(audio_queue):
    global is_listening
    logger.info("Listening thread started")
    while True:
        with microphone as source:
            if is_listening:
                logger.info("Microphone listening...")
                audio = recognizer.listen(source)
                audio_queue.put(audio)
            else:
                time.sleep(0.1)

# Recognize speech from the audio queue
def recognize_speech(audio_queue, response_queue):
    global is_listening
    logger.info("Recognition thread started")
    while True:
        audio = audio_queue.get()
        if is_listening:
            try:
                logger.info("Recognizing speech...")
                text = recognizer.recognize_google(audio)
                logger.info(f"Recognized speech: {text}")
                response_queue.put(text)
            except sr.UnknownValueError:
                logger.warning("Failed to understand audio")
            except sr.RequestError as e:
                logger.error(f"Recognition service error: {e}")

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Queues for audio and recognized text
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.signals = WorkerSignals()

        # Connect signals
        self.signals.update_text.connect(self.update_transcribed_text)


        # Configure UI
        self.setup_ui()

        # Start recognition thread
        self.recognition_thread = threading.Thread(
            target=recognize_speech,
            args=(self.audio_queue, self.response_queue),
            daemon=True,
        )
        self.recognition_thread.start()

    def populate_microphone_list(self, combo_box):
           """
           Populates the microphone dropdown with available microphones.
           """
           populate_microphone_list(combo_box)

    def setup_ui(self):
        """
        Configure UI elements and connect buttons to their respective slots.
        """
        # Populate dropdowns
        self.populate_microphone_list(self.ui.microphoneMBox)
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
        global is_listening
        is_listening = True
        self.ui.statusbar.showMessage("Listening...")

        # Start background listening thread
        self.listening_thread = threading.Thread(
            target=listen_in_background,
            args=(self.audio_queue,),
            daemon=True,
        )
        self.listening_thread.start()

    def stop_and_clear(self):
        """
        Stops listening and clears the transcribed text.
        """
        global is_listening
        is_listening = False
        self.ui.statusbar.showMessage("Stopped.")
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
