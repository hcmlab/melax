import sys
import speech_recognition as sr
import whisper
import openai
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QThread, Signal, Slot
from ui_form import Ui_MainWindow
from local_logger import ThreadSafeLogger
import numpy as np
from pathlib import Path
from PySide6.QtCore import QObject
from openai import OpenAI, OpenAIError
import os


class WhisperTranscriptionThread(QThread):
    transcription_signal = Signal(str)

    def __init__(self, model="medium", device="cpu", language="en", logger=None, parent=None):
        super().__init__(parent)
        self.model_name = model
        self.device = device
        self.language = language
        self.running = True
        self.logger = logger

    def run(self):
        try:
            self.logger.log_info("Starting Whisper Transcription Thread")
            recorder = sr.Recognizer()
            source = sr.Microphone(sample_rate=16000)
            audio_model = whisper.load_model(self.model_name, device=self.device)

            def record_callback(_, audio: sr.AudioData):
                if not self.running:
                    return

                data = audio.get_raw_data()
                audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                result = audio_model.transcribe(audio_np, language=self.language)
                text = result['text'].strip()
                self.transcription_signal.emit(text)

            with source:
                recorder.adjust_for_ambient_noise(source)
            stop_listening = recorder.listen_in_background(source, record_callback)

            while self.running:
                self.msleep(100)

            stop_listening()
            self.logger.log_info("Whisper Transcription Thread Stopped")
        except Exception as e:
            self.logger.log_error(f"Error in Whisper Transcription Thread: {e}")
            self.transcription_signal.emit(f"Error: {e}")

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class OpenAIWorker(QObject):
    responseReady = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, api_key, parent=None):
        super(OpenAIWorker, self).__init__(parent)
        self.api_key = api_key
        self.openai_client = OpenAI(api_key=self.api_key)

    @Slot(str)
    def process_request(self, model, context, max_tokens, temperature):
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=context,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            assistant_message = response.choices[0]["message"]["content"].strip()
            self.responseReady.emit(assistant_message)
        except Exception as e:
            self.errorOccurred.emit(str(e))


class MainWindow(QMainWindow):
    API_MESSAGE_DEFAULT = "Enter here or set as OPENAI_API_KEY variable"
    API_MESSAGE_FOUND_ENV = "Found it in env variables"
    API_MESSAGE_MISSING = "Please enter your key here or set OPENAI_API_KEY as an environment variable."
    transcription_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Logger
        self.logger = ThreadSafeLogger("../interactive_gui.log")

        # ASR Thread
        self.transcription_thread = None

        # OpenAI Worker
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.ui.openaiAPIKey
        self.openai_worker = OpenAIWorker(api_key="your-openai-api-key")
        self.openai_worker_thread = QThread()
        self.openai_worker.moveToThread(self.openai_worker_thread)
        self.openai_worker.responseReady.connect(self.display_openai_response)
        self.openai_worker.errorOccurred.connect(self.display_openai_error)
        self.openai_worker_thread.start()

        # UI Setup
        self.setup_ui()
        self.populate_microphones()
        self.populate_languages()

        # Signal-Slot Connections
        self.transcription_signal.connect(self.send_to_openai)

    def setup_ui(self):
        self.stylesheets_folder = Path(__file__).parent / "stylesheets"
        self.setup_theme_selection()

        # Populate ASR models
        self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large"])
        self.ui.whisperDevice.addItems(["CPU", "GPU"])
        self.ui.recognizerMBOX.addItems(["Whisper"])

        # Connect UI actions
        self.ui.startASR.clicked.connect(self.start_transcription)
        self.ui.stopASR.clicked.connect(self.stop_transcription)
        self.ui.clearASR.clicked.connect(self.clear_transcription)

    def populate_microphones(self):
        try:
            mic_list = sr.Microphone.list_microphone_names()
            self.ui.microphoneMBox.addItems(mic_list if mic_list else ["No microphones detected"])
        except Exception as e:
            self.ui.microphoneMBox.addItem(f"Error: {e}")

    def populate_languages(self):
        from whisper.tokenizer import LANGUAGES
        for lang_name, lang_key in LANGUAGES.items():
            self.ui.whisperLanguage.addItem(lang_name, lang_key)

    def setup_theme_selection(self):
        self.ui.themeComboBox.clear()
        themes = self.get_available_themes()
        self.ui.themeComboBox.addItems(themes)
        self.ui.themeComboBox.currentIndexChanged.connect(self.apply_selected_theme)


    def get_available_themes(self):
        if self.stylesheets_folder.exists():
            return [f.name for f in self.stylesheets_folder.glob("*.qss")]
        return []

    def apply_selected_theme(self):
        selected_theme = self.ui.themeComboBox.currentText()
        stylesheet_path = self.stylesheets_folder / selected_theme
        if stylesheet_path.exists():
            with stylesheet_path.open("r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())

    def start_transcription(self):
        if self.transcription_thread and self.transcription_thread.isRunning():
            self.stop_transcription()

        self.start_whisper()

    def start_whisper(self):
        selected_model = self.ui.whisperModel.currentText()
        selected_device = self.ui.whisperDevice.currentText()
        selected_language_key = self.ui.whisperLanguage.currentData()

        device_map = {"CPU": "cpu", "GPU": "cuda"}
        device = device_map.get(selected_device, "cpu")

        self.transcription_thread = WhisperTranscriptionThread(
            model=selected_model,
            device=device,
            language=selected_language_key,
            logger=self.logger,
        )
        self.transcription_thread.transcription_signal.connect(self.transcription_signal.emit)
        self.transcription_thread.start()

    def stop_transcription(self):
        if self.transcription_thread:
            self.transcription_thread.stop()
            self.transcription_thread = None

    def clear_transcription(self):
        self.ui.asrTextBrowser.clear()


    @Slot(str)
    def send_to_openai(self, user_input):
        context = [{"role": "system", "content": "You are a helpful assistant."},
                   {"role": "user", "content": user_input}]
        self.ui.asrTextBrowser.append(f"User: {user_input}")
        self.openai_worker.process_request("gpt-3.5-turbo", context, max_tokens=150, temperature=0.7)

    @Slot(str)
    def display_openai_response(self, response):
        self.ui.asrTextBrowser.append(f"Assistant: {response}")

    @Slot(str)
    def display_openai_error(self, error_message):
        QMessageBox.critical(self, "OpenAI Error", error_message)

    def closeEvent(self, event):
        self.logger.log_info("Application closing, stopping threads.")
        self.stop_transcription()
        self.openai_worker_thread.quit()
        self.openai_worker_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
