import sys
import os
import speech_recognition as sr
import openai
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QPushButton
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QThread, Signal, Slot
from ui_form import Ui_MainWindow
from local_logger import ThreadSafeLogger
from pathlib import Path

from llm_modules import OpenAIWorker
from tts_modules import TTSWorker
from asr_vad_modules import WhisperTranscriptionThread



class MainWindow(QMainWindow):
    API_MESSAGE_DEFAULT = "Enter here or set as OPENAI_API_KEY variable"
    API_MESSAGE_FOUND_ENV = "Found it in env variables"
    API_MESSAGE_MISSING = "Please enter your key here or set OPENAI_API_KEY as an environment variable."
    transcription_signal = Signal(str)
    openai_request_signal = Signal(str, object, int, float)
    tts_request_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Logger
        self.logger = ThreadSafeLogger("interactive_gui.log")
        self.context = []

        # ASR Thread
        self.transcription_thread = None
        # populate languages
        self.populate_languages()

        # OpenAI Worker
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.ui.openaiAPIKey.setText(self.api_key if self.api_key else "")
        self.openai_worker = OpenAIWorker(api_key=self.api_key)
        self.openai_worker_thread = QThread()

        self.openai_worker.moveToThread(self.openai_worker_thread)
        self.openai_worker.responseReady.connect(self.display_openai_response)
        self.openai_worker.errorOccurred.connect(self.display_openai_error)
        self.openai_worker_thread.start()

        # Connect the signal to the worker's slot
        self.openai_request_signal.connect(self.openai_worker.add_request)

        # Setup TTS Worker
        self.tts_worker = TTSWorker(
            url="localhost:50051",
            instance_name="/World/audio2face/PlayerStreaming"
        )
        self.tts_worker.ttsFinished.connect(self.handle_tts_finished)
        self.tts_worker.ttsError.connect(self.handle_tts_error)
        self.tts_worker.start()

        # Connect the signal to the TTS worker's slot
        self.tts_request_signal.connect(self.tts_worker.add_request)

        # google
        self.ui.googleAPI.setText("AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw")
        self.ui.googleEndPoint.setText("http://www.google.com/speech-api/v2/recognize")
        # UI Setup
        self.setup_ui()
        self.populate_microphones()
        self.populate_languages()

        # Signal-Slot Connections
        self.transcription_signal.connect(self.handle_transcription)

        # OpenAI context initialization
        system_prompt_text = self.ui.systemPromptEdit.toPlainText().strip()
        if not system_prompt_text:
            system_prompt_text = "You are a helpful assistant."
            self.ui.systemPromptEdit.setText(system_prompt_text)
        self.context = [{"role": "system", "content": system_prompt_text}]

        # Setup Audio Player for TTS
        self.audio_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_player.setAudioOutput(self.audio_output)

    def setup_ui(self):
        self.stylesheets_folder = Path(__file__).parent / "stylesheets"
        self.setup_theme_selection()

        # Populate ASR models
        self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large"])
        self.ui.whisperDevice.addItems(["CPU", "GPU"])
        self.ui.recognizerMBOX.addItems(["Google", "Whisper"])

        # Populate LLM models
        self.ui.LLMChocie.addItems(["OpenAI", "LLAMA"])
        self.models = ["gpt-4o-mini", "gpt-3.5-turbo"]
        self.ui.llmMBOX.addItems(self.models)

        # Connect UI actions
        self.ui.startASR.clicked.connect(self.start_transcription)
        self.ui.stopASR.clicked.connect(self.stop_transcription)
        self.ui.clearASR.clicked.connect(self.clear_transcription)

        # Connect OpenAI API key update
        self.ui.openaiAPIKey.textChanged.connect(self.update_api_key)

        # Connect system prompt update
        self.ui.systemPromptEdit.textChanged.connect(self.update_system_prompt)

        # Set default values for temperature and max tokens if not already set
        if not self.ui.temperatureOpenAI.value():
            self.ui.temperatureOpenAI.setValue(70)
        if not self.ui.maxTokenOpenAI.value():
            self.ui.maxTokenOpenAI.setValue(1024)

        self.ui.recognizerMBOX.currentTextChanged.connect(self.toggle_asr_options)
        self.toggle_asr_options("Google")

    def populate_microphones(self):
        try:
            mic_list = sr.Microphone.list_microphone_names()
            self.ui.microphoneMBox.addItems(mic_list if mic_list else ["No microphones detected"])
        except Exception as e:
            self.ui.microphoneMBox.addItem(f"Error: {e}")

    def populate_languages(self):
        """Populate both Whisper and Google language options."""
        from whisper.tokenizer import LANGUAGES
        # Clear existing items to avoid duplicates
        self.ui.whisperLanguage.clear()
        for lang_name, lang_key in LANGUAGES.items():
            self.ui.whisperLanguage.addItem(lang_name, lang_key)

        # Clear and populate google languages
        self.ui.googleLanguage.clear()
        google_languages = ["en-US", "es-ES", "fr-FR", "de-DE"]
        self.ui.googleLanguage.addItems(google_languages)

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
        self.ui.contextBrowserOpenAI.clear()
        self.context.append({"role": "system", "content": self.ui.systemPromptEdit.toPlainText().strip()})

    def update_api_key(self, text):
        self.api_key = text.strip()
        openai.api_key = self.api_key

    def update_system_prompt(self):
        system_prompt_text = self.ui.systemPromptEdit.toPlainText().strip()
        if system_prompt_text:
            # Update the system prompt in the context
            self.context.append({"role": "system", "content": system_prompt_text})
        else:
            # Reset to default if empty
            self.context.append({"role": "system", "content": "You are a helpful assistant."})

    @Slot(str)
    def handle_transcription(self, user_input):
        # Display the ASR transcription
        #self.ui.asrTextBrowser.append(user_input)

        # Proceed to send to OpenAI
        self.send_to_openai(user_input)

    def send_to_openai(self, user_input):
        # Append user's message to context
        self.context.append({"role": "user", "content": user_input})

        # Display user's message in contextBrowserOpenAI
        self.ui.contextBrowserOpenAI.append(f"<b>User:</b> {user_input}")

        # Make a copy of the context to avoid threading issues
        context_copy = self.context.copy()

        # Read parameters from GUI
        max_tokens = self.ui.maxTokenOpenAI.value()
        temperature = self.ui.temperatureOpenAI.value() / 100

        # Read the selected model from GUI
        selected_model = self.ui.llmMBOX.currentText()

        # Emit signal to OpenAIWorker
        self.openai_request_signal.emit(
            selected_model,
            context_copy,
            max_tokens,
            temperature
        )

    @Slot(str)
    def display_openai_response(self, response):
        # Append assistant's message to context
        self.context.append({"role": "assistant", "content": response})

        # Display assistant's message in contextBrowserOpenAI
        self.ui.contextBrowserOpenAI.append(f"<b>Assistant:</b> {response}")

        # Automatically trigger TTS for the assistant response
        audio_filename = "assistant_response.mp3"
        self.tts_request_signal.emit(response, audio_filename)

    @Slot(str)
    def display_openai_error(self, error_message):
        QMessageBox.critical(self, "OpenAI Error", error_message)

    @Slot(str)
    def handle_tts_finished(self, message: str):
        self.logger.log_info(f"TTS completed:{message}")

    @Slot(str)
    def handle_tts_error(self, error_message):
        QMessageBox.critical(self, "TTS Error", error_message)

    def play_audio(self, filename):
        if os.path.exists(filename):
            self.audio_player.setSource(filename)
            self.audio_player.play()
        else:
            QMessageBox.warning(self, "Audio Error", f"File {filename} not found.")

    def closeEvent(self, event):
        self.logger.log_info("Application closing, stopping threads.")
        self.stop_transcription()

        self.tts_worker.stop()
        self.tts_worker = None

        self.openai_worker.stop()
        self.openai_worker_thread.quit()
        self.openai_worker_thread.wait()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
