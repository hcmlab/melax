import sys
import os
import speech_recognition as sr
import openai
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QPushButton, QLineEdit, QFileDialog
from PySide6.QtCore import QThread, Signal, Slot
from ui_form import Ui_MainWindow
from local_logger import ThreadSafeLogger
from pathlib import Path
import requests
import json
from llm_modules import OpenAIWorker, OllamaWorker
from tts_modules import TTSWorker, GoogleTTSEngine, CoquiTTSEngine
from asr_vad_modules import WhisperTranscriptionThread, GoogleASRTranscriptionThread
#from behaviour_module import Audio2FaceHeadlessThread


class MainWindow(QMainWindow):
    """
    A more modular MainWindow that defines:
      - start_llm() / stop_llm()
      - start_asr() / stop_asr()
      - start_tts() / stop_tts()
      - allStart() / allStop() / allClear() to control them together.
    """

    # Custom signals
    transcription_signal = Signal(str)                 # ASR -> GUI
    openai_request_signal = Signal(str, object, int, float)  # LLM request
    tts_request_signal =  Signal(str)         # TTS request (text)
    ollama_request_signal = Signal(str, int, float)      # Ollama LLM request (messages)

    API_MESSAGE_DEFAULT = "Enter here or set as OPENAI_API_KEY variable"
    API_MESSAGE_FOUND_ENV = "Found it in env variables"
    API_MESSAGE_MISSING = "Please enter your key here or set OPENAI_API_KEY as an environment variable."

    def __init__(self):
        super().__init__()
        # ----------------------------------------------------
        # UI Setup
        # ----------------------------------------------------

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("MeLaX-Engine")

        # Logger
        self.logger = ThreadSafeLogger("interactive_gui.log")
        self.logger.log_emitted.connect(self.append_log)
        self.context = []

        # Directory for stylesheets
        self.stylesheets_folder = Path(__file__).parent / "stylesheets"

        # ----------------------------------------------------
        # We'll hold references to the workers/threads
        # so we can stop them individually
        # ----------------------------------------------------
        #self.openai_worker = None
        #self.openai_worker_thread = None
        self.llm_worker = None
        self.llm_worker_thread = None
        self.transcription_thread = None
        self.tts_worker = None
        self.MAX_CONTEXT_LENGTH = 50

        # ----------------------------------------------------
        # Setup UI
        # ----------------------------------------------------
        self.setup_ui()
        self.populate_microphones()
        self.populate_languages()

        # Initialize system prompt if empty
        # system_prompt_text = self.ui.systemPromptEdit.toPlainText().strip()
        # if not system_prompt_text:
        #     system_prompt_text = "You are a helpful assistant."
        #     self.ui.systemPromptEdit.setText(system_prompt_text)
        # self.context = [{"role": "system", "content": system_prompt_text}]


        #self.load_selected_usd()

        #self.ui.loadUSDButton.clicked.connect(self.load_usd_to_server)
        #self.ui.checkServerButton.clicked.connect(self.check_server_status)

        # ----------------------------------------------------
        # Connect LLM choice dropdown to dynamically update worker
        # ----------------------------------------------------
        self.ui.LLMChocie.currentTextChanged.connect(self.switch_llm_worker)

        # Initialize LLM choice and worker
        self.current_llm = self.ui.LLMChocie.currentText()
        self.logger.log_info(f"Selected LLM: {self.current_llm}")

        # ----------------------------------------------------
        # Connect ASR transcription signal to handle_transcription
        # (create the actual ASR thread in start_asr().)
        # ----------------------------------------------------
        self.transcription_signal.connect(self.handle_transcription)

        # ----------------------------------------------------
        # Apply default theme (dark)
        # ----------------------------------------------------
        self.setup_theme_selection()
        self.apply_default_theme()

    # ----------------------------------------------------
    # UI Setup & Theme
    # ----------------------------------------------------
    def setup_ui(self):
        """
        Connect your buttons, combos, and menu actions here.
        """
        # Populate combos for ASR
        self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large"])
        self.ui.whisperDevice.addItems(["CPU", "GPU"])
        self.ui.recognizerMBOX.addItems(["Google", "Whisper"])

        # Populate combos for LLM
        self.ui.LLMChocie.addItems(["OpenAI", "LLAMA"])
        self.models = ["gpt-4o-mini", "gpt-3.5-turbo"]
        self.ui.llmMBOX.addItems(self.models)

        self.ui.llmMBOX_Llama.addItems(["llama3.2"])

        # Set default visibility
        self.toggle_llm_group_visibility(self.ui.LLMChocie.currentText())

        # Rename Start/Stop/Clear buttons in the .ui to something like startAll, stopAll, clearAll
        self.ui.startAll.setText("allStart")
        self.ui.stopAll.setText("allStop")
        self.ui.clearAll.setText("allClear")

        self.ui.startAll.clicked.connect(self.allStart)
        self.ui.stopAll.clicked.connect(self.allStop)
        self.ui.clearAll.clicked.connect(self.allClear)

        # Connect OpenAI key update
        # Read the key from UI
        self.ui.openaiAPIKey.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.ui.openaiAPIKey.setText(self.api_key if self.api_key else "")
        self.ui.openaiAPIKey.textChanged.connect(self.update_api_key)

        # Connect system prompt update
        self.update_system_prompt()
        self.ui.systemPromptEdit.textChanged.connect(self.update_system_prompt)

        # Connect Llama temperature slider to label update
        self.ui.temperatureLlama.setRange(0, 100)
        #self.ui.temperatureLlama.valueChanged.connect(self.update_temperature_label)
        self.ui.temperatureLlama.setValue(70)
        self.ui.temperatureLlama.valueChanged.connect(self.update_temperature_label_llama)

        # Connect OpenAI temperature slider to label update
        self.ui.temperatureOpenAI.setRange(0, 100)
        #self.ui.temperatureOpenAI.valueChanged.connect(self.update_temperature_label)
        self.ui.temperatureOpenAI.setValue(70)
        self.ui.temperatureOpenAI.valueChanged.connect(self.update_temperature_label_openai)

        # If temperature/max tokens aren't set, set defaults

        #self.update_temperature_label(self.ui.temperatureOpenAI.value())

        self.ui.maxTokenOpenAI.setValue(1024)

        self.ui.recognizerMBOX.currentTextChanged.connect(self.toggle_asr_options)
        self.toggle_asr_options("Google")

        # TTS combos
        self.ui.ttsEngineCombo.addItems(["Google", "Coqui", "VoiceX"])
        self.ui.ttslanguage.addItems(["en", "en-US", "en-GB", "es", "fr"])
        self.ui.a2fUrl.setText("localhost:50051")
        self.ui.a2fInstanceName.setText("/World/audio2face/PlayerStreaming")

        self.ui.ttsSentenceSplit.addItems(["Regex", "NLP"])
        self.ui.ttsPlayback.addItems(["SinglePush", "Stream"])
        self.ui.blockUntilFinish.setChecked(True)

        # Connect chunk slider and dial signals to local slots
        self.ui.ttsChunkDuration.valueChanged.connect(self.update_chunk_label)
        self.ui.ttsDelayBetweenChunks.valueChanged.connect(self.update_delay_label)

        # Chunk Duration slider
        self.ui.ttsChunkDuration.setRange(1, 99)
        self.ui.ttsChunkDuration.setValue(10)

        # Delay dial
        self.ui.ttsDelayBetweenChunks.setRange(0, 50)
        self.ui.ttsDelayBetweenChunks.setValue(4)

        self.update_chunk_label(self.ui.ttsChunkDuration.value())
        self.update_delay_label(self.ui.ttsDelayBetweenChunks.value())

        # Google config
        self.ui.googleAPI.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.ui.googleAPI.setText("AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw")
        self.ui.googleEndPoint.setText("http://www.google.com/speech-api/v2/recognize")

        # Connect menu actions for dark/light
        self.ui.actiondark.triggered.connect(self.apply_dark_theme)
        self.ui.actionlight.triggered.connect(self.apply_light_theme)

        # name tabs
        self.ui.chatOutpuTab.setTabText(0,"Conversation")  # Rename first tab
        self.ui.chatOutpuTab.setTabText(1,"Log Terminal")  # Rename second tab
        self.ui.chatOutpuTab.setTabText(3,"Behaviour Log")


        # Initialize the headless server URL from QLineEdit
        # load usd
        self.usd_folder_path = os.path.join(os.getcwd(), "usd")
        self.populate_usd_list()
        self.ui.a2fUrl_headless.setText("http://localhost:8011")
        self.headless_server_url = self.ui.a2fUrl_headless.text().strip()

        self.ui.emotionsQCombo.addItems([
            "neutral", "amazement", "anger", "cheekiness", "disgust", "fear",
            "grief", "joy", "outofbreath", "pain", "sadness"
        ])

        self.ui.emotionsQCombo.currentTextChanged.connect(self.on_emotion_selected)

        #self.check_server_status()
        self.ui.connectHeadlessPushbutton.clicked.connect(self.on_connect_button_clicked)
        self.ui.loadUsdPushbutton.clicked.connect(self.on_load_usd_button_clicked)


    def setup_theme_selection(self):
        """
        Placeholder: gather .qss files if needed
        """
        pass

    def apply_default_theme(self):
        """
        Apply the first 'dark' .qss file if found
        """
        if not self.stylesheets_folder.exists():
            return
        for f in self.stylesheets_folder.glob("*.qss"):
            if f.stem.lower().startswith("dark"):
                with open(f, "r", encoding="utf-8") as file:
                    self.setStyleSheet(file.read())
                return

    def apply_dark_theme(self):
        """
        Triggered by actiondark
        """
        if not self.stylesheets_folder.exists():
            return
        for f in self.stylesheets_folder.glob("*.qss"):
            if f.stem.lower().startswith("dark"):
                with open(f, "r", encoding="utf-8") as file:
                    self.setStyleSheet(file.read())
                return

    def apply_light_theme(self):
        """
        Triggered by actionlight
        """
        if not self.stylesheets_folder.exists():
            return
        for f in self.stylesheets_folder.glob("*.qss"):
            if f.stem.lower().startswith("light"):
                with open(f, "r", encoding="utf-8") as file:
                    self.setStyleSheet(file.read())
                return

    # ----------------------------------------------------
    # Microphone & Language
    # ----------------------------------------------------
    def populate_microphones(self):
        try:
            mic_list = sr.Microphone.list_microphone_names()
            self.ui.microphoneMBox.clear()
            if mic_list:
                self.ui.microphoneMBox.addItems(mic_list)
            else:
                self.ui.microphoneMBox.addItem("No microphones detected")
        except Exception as e:
            self.ui.microphoneMBox.addItem(f"Error: {e}")

    def populate_languages(self):
        from whisper.tokenizer import LANGUAGES
        self.ui.whisperLanguage.clear()
        for lang_name, lang_key in LANGUAGES.items():
            self.ui.whisperLanguage.addItem(lang_name, lang_key)

        self.ui.googleLanguage.clear()
        google_languages = ["en-US", "es-ES", "fr-FR", "de-DE"]
        self.ui.googleLanguage.addItems(google_languages)

    def toggle_asr_options(self, recognizer_type):
        if recognizer_type == "Google":
            self.ui.googleGroupBox.setVisible(True)
            self.ui.whisperGroupBox.setVisible(False)
        else:
            self.ui.googleGroupBox.setVisible(False)
            self.ui.whisperGroupBox.setVisible(True)

    # ----------------------------------------------------
    # allStart / allStop / allClear
    # ----------------------------------------------------
    def allStart(self):
        """
        Start all modules (LLM, ASR, TTS) in a clean manner.
        """
        self.logger.log_info("allStart clicked.")
        # Stop everything first
        self.allStop()

        # Dynamically start LLM based on selection
        self.switch_llm_worker(self.ui.LLMChocie.currentText())
        # Start ASR
        self.start_asr()
        # Start TTS
        self.start_tts()
        # audio2face


        self.logger.log_info("allStart - all modules started.")

    def allStop(self):
        """
        Stop LLM, ASR, TTS threads.
        """
        self.logger.log_info("allStop clicked.")
        self.stop_asr()
        self.stop_tts()
        self.stop_llm()
        #self.stop_audio2face_headless()
        self.logger.log_info("allStop - all modules stopped.")

    def allClear(self):
        """
        Clear everything & reset combos to default after stopping.
        """
        self.logger.log_info("allClear clicked.")
        self.allStop()

        # Clear the context browser
        self.ui.contextBrowserOpenAI.clear()

        # Reset system prompt
        self.ui.systemPromptEdit.setText("You are a helpful assistant.")
        self.context = [{"role": "system", "content": "You are a helpful assistant."}]

        # Reset TTS combos
        self.ui.ttsEngineCombo.setCurrentIndex(0)
        self.ui.ttslanguage.setCurrentIndex(0)
        self.ui.a2fUrl.setText("localhost:50051")
        self.ui.a2fInstanceName.setText("/World/audio2face/PlayerStreaming")
        self.ui.ttsSentenceSplit.setCurrentIndex(0)  # Regex
        self.ui.ttsPlayback.setCurrentIndex(0)       # Stream
        self.ui.blockUntilFinish.setChecked(True)
        self.ui.ttsChunkDuration.setValue(10)
        self.ui.ttsDelayBetweenChunks.setValue(4)

        # Reset ASR combos
        self.ui.recognizerMBOX.setCurrentIndex(0)
        self.ui.whisperModel.setCurrentIndex(0)
        self.ui.whisperDevice.setCurrentIndex(0)
        self.ui.googleLanguage.setCurrentIndex(0)
        self.ui.microphoneMBox.setCurrentIndex(0)

        # Reset LLM combos
        self.ui.LLMChocie.setCurrentIndex(0)
        self.ui.llmMBOX.setCurrentIndex(0)
        self.ui.temperatureOpenAI.setValue(70)
        self.ui.maxTokenOpenAI.setValue(1024)

        self.logger.log_info("allClear - all settings & context reset to defaults.")

    # ----------------------------------------------------
    # Dynamic LLM Worker Selection
    # ----------------------------------------------------

    def switch_llm_worker(self, llm_choice: str):
        """
        Switches the LLM worker based on the selected LLM choice.
        """
        self.logger.log_info(f"Switching LLM to: {llm_choice}")
        self.stop_llm()  # Stop the current worker, if any

        if llm_choice == "OpenAI":
            self.logger.log_info("Selected OpenAI Worker.")
            self.ui.openai_group.setVisible(True)
            self.ui.llama_group.setVisible(False)
            self.start_llm_openai()
        elif llm_choice == "LLAMA":
            self.ui.openai_group.setVisible(False)
            self.ui.llama_group.setVisible(True)
            self.logger.log_info("Selected Ollama Worker.")
            self.start_llm_ollama()
        else:
            self.logger.log_error(f"Unsupported LLM choice: {llm_choice}")

    def toggle_llm_group_visibility(self, llm_choice: str):
        """
        Toggles the visibility of OpenAI and Llama groups based on the LLM choice.
        """
        if llm_choice == "OpenAI":
            self.ui.openai_group.setVisible(True)
            self.ui.llama_group.setVisible(False)
        elif llm_choice == "LLAMA":
            self.ui.openai_group.setVisible(False)
            self.ui.llama_group.setVisible(True)
        else:
            self.ui.openai_group.setVisible(False)
            self.ui.llama_group.setVisible(False)

    def get_temperature(self):
        """
        Fetch temperature value from the active widget.
        """
        if self.ui.openai_group.isVisible():
            return self.ui.temperatureOpenAI.value() / 100.0  # Scale 0-100 slider to 0.0-1.0
        elif self.ui.llama_group.isVisible():
            return self.ui.temperatureLlama.value() / 100.0
        return 0.7  # Default temperature

    def get_max_tokens(self):
        """
        Fetch max tokens value from the active widget.
        """
        if self.ui.openai_group.isVisible():
            return self.ui.maxTokenOpenAI.value()
        elif self.ui.llama_group.isVisible():
            return self.ui.maxTokenLlama.value()
        return 1024  # Default max tokens

    def update_temperature_label_llama(self, value: int):
        """
        Update the Llama temperature label when the slider value changes.
        """
        temperature = value / 100.0
        self.ui.TemperatureLablellama.setText(f"{temperature:.2f}")

    def update_temperature_label_openai(self, value: int):
        """
        Update the OpenAI temperature label when the slider value changes.
        """
        temperature = value / 100.0
        self.ui.llmTemperatureLable.setText(f"{temperature:.2f}")


    # ----------------------------------------------------
    # OpenAI Worker
    # ----------------------------------------------------
    def start_llm_openai(self):
        """
        Create & start OpenAI worker with the current API key.
        """
        self.logger.log_info("Starting OpenAI Worker.")

        # Read the key from UI
        self.api_key = self.ui.openaiAPIKey.text().strip()
        if not self.api_key:
            self.api_key = os.getenv('OPENAI_API_KEY')
            self.ui.openaiAPIKey.setText(self.api_key if self.api_key else "")
        openai.api_key = self.api_key

        # Create the worker
        self.llm_worker = OpenAIWorker(api_key=self.api_key)
        self.llm_worker_thread = QThread()
        self.llm_worker.moveToThread(self.llm_worker_thread)
        self.llm_worker.responseReady.connect(self.display_llm_response)
        self.llm_worker.errorOccurred.connect(self.display_llm_error)

        # Connect OpenAI request signal to worker
        self.openai_request_signal.connect(self.llm_worker.add_request)

        self.llm_worker_thread.start()
        self.logger.log_info("OpenAI Worker started.")

        # ----------------------------------------------------
        # Ollama Worker
        # ----------------------------------------------------

    def start_llm_ollama(self):
        """
        Create & start Ollama worker.
        """
        self.logger.log_info("Starting Ollama Worker.")

        # Create the worker
        self.llm_worker = OllamaWorker(model_name="llama3.2")
        self.llm_worker_thread = QThread()
        self.llm_worker.moveToThread(self.llm_worker_thread)
        self.llm_worker.responseReady.connect(self.display_llm_response)
        self.llm_worker.errorOccurred.connect(self.display_llm_error)

        # Connect Ollama request signal to worker
        self.ollama_request_signal.connect(self.llm_worker.add_request)

        self.llm_worker_thread.start()
        self.logger.log_info("Ollama Worker started.")

    def send_to_llm(self, user_input: str):
        """
        Sends a request to the selected LLM worker.
        """
        self.logger.log_info(f"Sending input to LLM: {user_input}")
        self.ui.contextBrowserOpenAI.append(f"<b>User:</b> {user_input}")

        # Prepare the context and parameters
        temperature = self.get_temperature()
        max_tokens = self.get_max_tokens()

        if self.ui.openai_group.isVisible():
            selected_model = self.ui.llmMBOX.currentText()
            context = [{"role": "user", "content": user_input}]
            self.llm_worker.add_request(selected_model, context, max_tokens, temperature)
        elif self.ui.llama_group.isVisible():
            #selected_model = self.ui.llmMBOX_Llama.currentText()
            messages = [{"role": "user", "content": user_input}]
            self.llm_worker.add_request(messages, max_tokens, temperature)



    def stop_llm(self):
        """
        Stop the current LLM worker, if running.
        """
        self.logger.log_info("Stopping LLM Worker.")
        if self.llm_worker:
            self.llm_worker.stop()
            self.llm_worker = None
        if self.llm_worker_thread:
            self.llm_worker_thread.quit()
            self.llm_worker_thread.wait()
            self.llm_worker_thread = None

        # ----------------------------------------------------
        # LLM Request Handling
        # ----------------------------------------------------
    # def send_to_llm(self, user_input: str):
    #     """
    #     Sends user input to the active LLM worker.
    #     """
    #     self.logger.log_info(f"Sending input to LLM: {user_input}")
    #     self.ui.contextBrowserOpenAI.append(f"<b>User:</b> {user_input}")
    #
    #     # Append user input to context
    #     self.context.append({"role": "user", "content": user_input})
    #
    #     # Truncate context if it exceeds the maximum length
    #     if len(self.context) > self.MAX_CONTEXT_LENGTH:
    #         self.context = self.context[-self.MAX_CONTEXT_LENGTH:]
    #
    #     # Prepare parameters
    #     max_tokens = self.ui.maxTokenOpenAI.value()
    #     temperature = self.ui.temperatureOpenAI.value() / 100
    #     messages = self.context
    #
    #     # Emit the appropriate signal based on the selected worker
    #     if self.current_llm == "OpenAI":
    #         self.openai_request_signal.emit(self.ui.llmMBOX.currentText(), messages, max_tokens, temperature)
    #     elif self.current_llm == "LLAMA":
    #         self.ollama_request_signal.emit(messages, max_tokens, temperature)
    # ----------------------------------------------------
    # LLM Response Handling
    # ----------------------------------------------------

    @Slot(str)
    def display_llm_response(self, response):
        """
        Handles the response from the LLM (OpenAI or Ollama) and appends it to the context.
        """
        self.context.append({"role": "assistant", "content": response})
        self.ui.contextBrowserOpenAI.append(f"<b>Assistant:</b> {response}")

        # Automatically trigger TTS for the assistant response
        self.tts_request_signal.emit(response)

    @Slot(str)
    def display_llm_error(self, error_message):
        """
        Displays an error message for the LLM worker.
        """
        QMessageBox.critical(self, "LLM Error", error_message)
        self.logger.log_error(f"LLM Error: {error_message}")

    # def send_to_openai(self, user_input):
    #     """
    #     Sends user input to OpenAI API after appending it to the context.
    #     Truncates the context if it exceeds the maximum allowed length.
    #     """
    #     self.ui.contextBrowserOpenAI.append(f"<b>User:</b> {user_input}")
    #
    #     # Append the user message to the context
    #     self.context.append({
    #         "role": "user",
    #         "content": [{"type": "text", "text": user_input}]
    #     })
    #
    #
    #     # Truncate the context if it exceeds MAX_CONTEXT_LENGTH
    #     if len(self.context) > self.MAX_CONTEXT_LENGTH + 1:  # +1 for the developer role
    #         self.context = self.context[:1] + self.context[-self.MAX_CONTEXT_LENGTH:]
    #
    #     # Prepare parameters for OpenAI request
    #     context_copy = self.context.copy()
    #     max_tokens = self.ui.maxTokenOpenAI.value()
    #     temperature = self.ui.temperatureOpenAI.value() / 100
    #     selected_model = self.ui.llmMBOX.currentText()
    #
    #     # Emit the OpenAI request signal
    #     self.openai_request_signal.emit(selected_model, context_copy, max_tokens, temperature)

    # @Slot(int)
    # def update_temperature_label(self, slider_value: int):
    #     """
    #     Convert slider_value (0..200) to a float in 0..2 range
    #     and update llmTemperatureLable text accordingly.
    #     """
    #     # Scale the integer to a float between 0..2:
    #     temperature = slider_value / 100.0
    #     # Update the label:
    #     self.ui.llmTemperatureLable.setText(f"value: {temperature:.2f}")
    # ----------------------------------------------------
    # ASR (Whisper or Google)
    # ----------------------------------------------------

    def start_asr(self):
        self.logger.log_info("start_asr() called.")
        self.stop_asr()  # ensure we don't have a leftover thread

        asr_choice = self.ui.recognizerMBOX.currentText()
        if asr_choice == "Whisper":
            selected_model = self.ui.whisperModel.currentText()
            device_txt = self.ui.whisperDevice.currentText()
            lang_key = self.ui.whisperLanguage.currentData()

            device_map = {"CPU": "cpu", "GPU": "cuda"}
            device = device_map.get(device_txt, "cpu")

            self.transcription_thread = WhisperTranscriptionThread(
                model=selected_model,
                device=device,
                language=lang_key,
                logger=self.logger
            )
            self.transcription_thread.transcription_signal.connect(self.transcription_signal.emit)
            self.transcription_thread.start()
            self.logger.log_info(f"Whisper ASR started with model={selected_model}, device={device}")
        elif asr_choice == "Google":
            # Create & start GoogleASRTranscriptionThread
            api_key = self.ui.googleAPI.text().strip() or "YOUR_DEFAULT_API_KEY"
            endpoint = self.ui.googleEndPoint.text().strip() or "http://www.google.com/speech-api/v2/recognize"
            lang = self.ui.googleLanguage.currentText()  # e.g. "en-US"

            self.transcription_thread = GoogleASRTranscriptionThread(
                api_key=api_key,
                endpoint=endpoint,
                language=lang,
                energy_threshold=1000,
                record_timeout=2.0,
                logger=self.logger
            )
            self.transcription_thread.transcription_signal.connect(self.transcription_signal.emit)
            self.transcription_thread.start()

            self.logger.log_info(f"Google ASR started with lang={lang}, endpoint={endpoint}")
        else:
            self.logger.log_info("Unsupported ASR choice. No thread started.")

    def stop_asr(self):
        self.logger.log_info("stop_asr() called.")
        if self.transcription_thread:
            self.transcription_thread.stop()
            self.transcription_thread = None

    # ----------------------------------------------------
    # TTS (Google or Coqui)
    # ----------------------------------------------------
    def start_tts(self):
        """
        Create TTSWorker using user-chosen engine, language, A2F settings, etc.
        """
        self.logger.log_info("start_tts() called.")

        self.stop_tts()

        # TTS engine choice
        engine_choice = self.ui.ttsEngineCombo.currentText()  # "Google" / "Coqui"
        lang_choice = self.ui.ttslanguage.currentText()       # e.g. "en-US", "en"

        if engine_choice == "Google":
            tts_engine = GoogleTTSEngine()
        else:
            tts_engine = CoquiTTSEngine()

        # A2F config
        a2f_url = self.ui.a2fUrl.text().strip() or "localhost:50051"
        a2f_inst = self.ui.a2fInstanceName.text().strip() or "/World/audio2face/PlayerStreaming"

        # Sentence splitting
        split_choice = self.ui.ttsSentenceSplit.currentText()  # "Regex" / "NLP"
        use_nlp = (split_choice == "NLP")

        # Playback method
        playback = self.ui.ttsPlayback.currentText()  # "Stream" / "SinglePush"
        use_streaming = (playback == "Stream")

        # Block until finish
        block_until = self.ui.blockUntilFinish.isChecked()

        # Chunk + delay
        chunk_dur = self.ui.ttsChunkDuration.value()
        delay_chunks = self.ui.ttsDelayBetweenChunks.value()

        # Now instantiate TTSWorker
        self.tts_worker = TTSWorker(
            tts_engine=tts_engine,
            language=lang_choice,
            url=a2f_url,
            instance_name=a2f_inst,
            use_nlp_split=use_nlp,
            use_audio_streaming=use_streaming,
            block_until_playback_is_finished=block_until,
            chunk_duration=chunk_dur,
            delay_between_chunks=delay_chunks
        )
        self.tts_worker.ttsFinished.connect(self.handle_tts_finished)
        self.tts_worker.ttsError.connect(self.handle_tts_error)

        # Connect the TTS request signal (text -> TTS)
        self.tts_request_signal.connect(self.tts_worker.add_request)

        self.tts_worker.start()
        self.logger.log_info("TTS worker started.")

    def stop_tts(self):
        self.logger.log_info("stop_tts() called.")
        if self.tts_worker:
            self.tts_worker.stop()
            self.tts_worker.quit()
            self.tts_worker.wait()
            self.tts_worker = None

    @Slot(int)
    def update_chunk_label(self, value: int):
        """
        Update the chunckSizeLable with the current slider value.
        """
        self.ui.chunckSizeLable.setText(f"value: {value}")

    @Slot(int)
    def update_delay_label(self, value: int):
        """
        Update the delayLable with the current dial value.
        """
        self.ui.delayLable.setText(f"value: {value}")

    # ----------------------------------------------------
    # Behaviour streaming
    # ----------------------------------------------------
    def on_connect_button_clicked(self):
        # Use the text from a2fUrl_headless
        self.headless_server_url = self.ui.a2fUrl_headless.text().strip() or "http://localhost:8011"
        # Attempt to connect:
        connected = self.check_server_status()  # returns True/False
        self.update_server_status(connected)
        if connected:
            self.logger.log_info("Headless server connected.")
        else:
            self.logger.log_error("Unable to connect to headless server.")

    def populate_usd_list(self):
        """
        Populates the USD ComboBox with the names of .usd files in the specified folder.
        """
        if not os.path.exists(self.usd_folder_path):
            self.ui.usdCombo.addItem("No USD folder found")
            self.ui.usdCombo.setEnabled(False)
            return

        usd_files = [f for f in os.listdir(self.usd_folder_path) if f.endswith((".usd", ".usda", ".usdc"))]
        if usd_files:
            self.ui.usdCombo.addItems(usd_files)
            self.ui.usdCombo.setEnabled(True)
        else:
            self.ui.usdCombo.addItem("No USD files available")
            self.ui.usdCombo.setEnabled(False)

    def check_server_status(self) -> bool:
        try:
            url = f"{self.headless_server_url}/status"
            self.logger.log_info(f"Checking status: {url}")
            response = requests.get(url, timeout=2, headers={"accept": "application/json"})
            self.logger.log_info(f"Status check response text: {response.text, response.status_code}")

            if response.status_code == 200:
                # Since body is "OK" in JSON form, response.json() will yield the string "OK"
                data = response.json()  # this should be the literal string "OK"
                if data == "OK":
                    return True
        except requests.exceptions.RequestException as e:
            self.logger.log_error(f"Error checking server status: {e}")

        return False

    def update_server_status(self, connected: bool):
        """
        Updates the connectHeadlessPushbutton color/icon
        to indicate connected or disconnected.
        """
        if connected:
            self.ui.connectHeadlessPushbutton.setStyleSheet("QToolButton { background-color: green; }")
            # or set an icon with self.ui.connectHeadlessPushbutton.setIcon(QIcon("green.png"))
        else:
            self.ui.connectHeadlessPushbutton.setStyleSheet("QToolButton { background-color: red; }")
            # or self.ui.connectHeadlessPushbutton.setIcon(QIcon("red.png"))

    def on_load_usd_button_clicked(self):
        """
        Load the selected USD (only if connected).
        """
        # Optionally check if the button is green or if the server is connected
        connected = self.check_server_status()
        if not connected:
            self.logger.log_error("Server not connected, cannot load USD.")
            return

        success = self.load_selected_usd()
        # Optionally color the button based on success/failure
        if success:
            self.ui.loadUsdPushbutton.setStyleSheet("QToolButton { background-color: green; }")
        else:
            self.ui.loadUsdPushbutton.setStyleSheet("QToolButton { background-color: red; }")

    def load_selected_usd(self) -> bool:
        selected_usd = self.ui.usdCombo.currentText()
        if not selected_usd or selected_usd.startswith("No USD"):
            self.logger.log_error("Invalid USD selection.")
            return False

        usd_path = os.path.join(self.usd_folder_path, selected_usd)
        try:
            payload = {"file_name": usd_path}
            response = requests.post(
                f"{self.headless_server_url}/A2F/USD/Load",
                headers={"accept": "application/json", "Content-Type": "application/json"},
                json=payload
            )
            if response.status_code == 200 and response.json().get("status") == "OK":
                self.logger.log_info(f"USD loaded successfully: {usd_path}")
                return True
            else:
                self.logger.log_error("Failed to load USD.")
        except requests.exceptions.RequestException as e:
            self.logger.log_error(f"Error loading USD: {e}")
        return False

    def on_emotion_selected(self, emotion: str):
        """
        Sends a request to set the selected emotion to 1 and all others to 0.
        """
        emotions = [
            "amazement", "anger", "cheekiness", "disgust", "fear",
            "grief", "joy", "outofbreath", "pain", "sadness"
        ]

        # Create the payload with all values set to 0
        payload = {
            "a2f_instance": "/World/audio2face/CoreFullface",
            "emotions": {e: 0 for e in emotions}
        }

        # If the selected emotion is not "Neutral", set it to 1
        if emotion != "neutral":
            payload["emotions"][emotion] = 1

        try:
            self.logger.log_info(
                f"Emotion payload: {payload}")
            response = requests.post(
                f"{self.headless_server_url}/A2F/A2E/SetEmotionByName",
                headers={"accept": "application/json", "Content-Type": "application/json"},
                json=payload
            )

            if response.status_code == 422:
                self.logger.log_error(f"Validation error: {response.text}")
                return

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("status") == "OK":
                    self.logger.log_info(
                        f"Emotion set successfully: {emotion}, Message: {response_data.get('message')}")
                else:
                    self.logger.log_error(f"Unexpected response: {response.text}")
            else:
                self.logger.log_error(f"Failed to set emotion: {emotion}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            self.logger.log_error(f"Error setting emotion: {e}")



    # ----------------------------------------------------
    # Updating OpenAI / System Prompt
    # ----------------------------------------------------
    def update_api_key(self, text):
        self.api_key = text.strip()
        openai.api_key = self.api_key

    def update_system_prompt(self):
        """
        Updates the system prompt as a developer role and resets the context.
        """
        new_prompt = self.ui.systemPromptEdit.toPlainText().strip()

        if new_prompt:
            # Log the prompt update
            self.logger.log_info(f"System prompt updated: {new_prompt}")

            # Reset the context with the new developer message
            self.context = [
                {
                    "role": "developer",
                    "content": [{"type": "text", "text": new_prompt}]
                }
            ]

            # Clear UI to reflect the reset
            self.ui.contextBrowserOpenAI.clear()
            self.ui.contextBrowserOpenAI.append(f"<b>Developer:</b> {new_prompt}")
        else:
            # Default prompt in case the field is empty
            default_prompt = "You are a helpful and knowledgeable assistant that answers questions short and clear."
            self.ui.systemPromptEdit.setText(default_prompt)
            self.logger.log_info("System prompt was empty. Resetting to default.")

            self.context = [
                {
                    "role": "developer",
                    "content": [{"type": "text", "text": default_prompt}]
                }
            ]

            # Update UI
            self.ui.contextBrowserOpenAI.clear()
            self.ui.contextBrowserOpenAI.append(f"<b>Developer:</b> {default_prompt}")


    # ----------------------------------------------------
    # ASR -> LLM -> TTS Pipeline
    # ----------------------------------------------------
    @Slot(str)
    def handle_transcription(self, user_input):
        self.logger.log_info(f"ASR recognized: {user_input}")
        # Optionally show in some text browser: self.ui.asrTextBrowser.append(user_input)
        self.send_to_llm(user_input)


    @Slot(str)
    def display_openai_response(self, response):
        """
        Handles the response from OpenAI and appends it to the context.
        """
        # Append the assistant's response to the context
        self.context.append({
            "role": "assistant",
            "content": [{"type": "text", "text": response}]
        })

        # Display the response in the UI
        self.ui.contextBrowserOpenAI.append(f"<b>Assistant:</b> {response}")

        # Automatically trigger TTS for the assistant response
        self.tts_request_signal.emit(response)

    @Slot(str)
    def display_openai_error(self, error_message):
        QMessageBox.critical(self, "OpenAI Error", error_message)

    # ----------------------------------------------------
    # TTS Feedback
    # ----------------------------------------------------
    @Slot(str)
    def handle_tts_finished(self, msg):
        self.logger.log_info(f"TTS finished: {msg}")

    @Slot(str)
    def handle_tts_error(self, error_message):
        QMessageBox.critical(self, "TTS Error", error_message)
        self.logger.log_info(f"TTS error: {error_message}")

    # ----------------------------------------------------
    # Logger
    # ----------------------------------------------------

    @Slot(str)
    def append_log(self, message: str):
        """
        Slot to receive log messages from ThreadSafeLogger and append them
        to the logOutput QTextBrowser (or any other widget).
        """
        self.ui.logOutput.append(message)

    # ----------------------------------------------------
    # Close Event
    # ----------------------------------------------------
    def closeEvent(self, event):
        self.logger.log_info("Application closing; stopping threads.")
        self.allStop()
        event.accept()


# class MainWindow(QMainWindow):
#     API_MESSAGE_DEFAULT = "Enter here or set as OPENAI_API_KEY variable"
#     API_MESSAGE_FOUND_ENV = "Found it in env variables"
#     API_MESSAGE_MISSING = "Please enter your key here or set OPENAI_API_KEY as an environment variable."
#     transcription_signal = Signal(str)
#     openai_request_signal = Signal(str, object, int, float)
#     tts_request_signal = Signal(str, str)
#
#     def __init__(self):
#         super().__init__()
#         self.ui = Ui_MainWindow()
#         self.ui.setupUi(self)
#
#         # Logger
#         self.logger = ThreadSafeLogger("interactive_gui.log")
#         self.context = []
#
#         # ASR Thread
#         self.transcription_thread = None
#         # populate languages
#         self.populate_languages()
#
#         # OpenAI Worker
#         self.api_key = os.getenv('OPENAI_API_KEY')
#         self.ui.openaiAPIKey.setText(self.api_key if self.api_key else "")
#         self.openai_worker = OpenAIWorker(api_key=self.api_key)
#         self.openai_worker_thread = QThread()
#
#         self.openai_worker.moveToThread(self.openai_worker_thread)
#         self.openai_worker.responseReady.connect(self.display_openai_response)
#         self.openai_worker.errorOccurred.connect(self.display_openai_error)
#         self.openai_worker_thread.start()
#
#         # Connect the signal to the worker's slot
#         self.openai_request_signal.connect(self.openai_worker.add_request)
#
#         # Example using GoogleTTSEngine
#         tts_engine = GoogleTTSEngine()
#
#         # Setup TTS Worker
#         self.tts_worker = TTSWorker(
#             tts_engine=tts_engine,
#             url="localhost:50051",
#             instance_name="/World/audio2face/PlayerStreaming",
#             use_nlp_split=False,  # if True => advanced splitter, else regex
#             use_audio_streaming=True,  # if True => chunk-based streaming, else single push
#             block_until_playback_is_finished=True
#         )
#         self.tts_worker.ttsFinished.connect(self.handle_tts_finished)
#         self.tts_worker.ttsError.connect(self.handle_tts_error)
#         self.tts_worker.start()
#
#         # Connect the signal to the TTS worker's slot
#         self.tts_request_signal.connect(self.tts_worker.add_request)
#
#         # google
#         self.ui.googleAPI.setText("AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw")
#         self.ui.googleEndPoint.setText("http://www.google.com/speech-api/v2/recognize")
#         # UI Setup
#         self.setup_ui()
#         self.populate_microphones()
#         self.populate_languages()
#
#         # Signal-Slot Connections
#         self.transcription_signal.connect(self.handle_transcription)
#
#         # OpenAI context initialization
#         system_prompt_text = self.ui.systemPromptEdit.toPlainText().strip()
#         if not system_prompt_text:
#             system_prompt_text = "You are a helpful assistant."
#             self.ui.systemPromptEdit.setText(system_prompt_text)
#         self.context = [{"role": "system", "content": system_prompt_text}]
#
#         # Setup Audio Player for TTS
#         self.audio_player = QMediaPlayer(self)
#         self.audio_output = QAudioOutput(self)
#         self.audio_player.setAudioOutput(self.audio_output)
#
#     def setup_ui(self):
#         self.stylesheets_folder = Path(__file__).parent / "stylesheets"
#         self.setup_theme_selection()
#
#         # Populate ASR models
#         self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large"])
#         self.ui.whisperDevice.addItems(["CPU", "GPU"])
#         self.ui.recognizerMBOX.addItems(["Google", "Whisper"])
#
#         # Populate LLM models
#         self.ui.LLMChocie.addItems(["OpenAI", "LLAMA"])
#         self.models = ["gpt-4o-mini", "gpt-3.5-turbo"]
#         self.ui.llmMBOX.addItems(self.models)
#
#         # Connect UI actions
#         self.ui.startASR.clicked.connect(self.start_transcription)
#         self.ui.stopASR.clicked.connect(self.stop_transcription)
#         self.ui.clearASR.clicked.connect(self.clear_transcription)
#
#         # Connect OpenAI API key update
#         self.ui.openaiAPIKey.textChanged.connect(self.update_api_key)
#
#         # Connect system prompt update
#         self.ui.systemPromptEdit.textChanged.connect(self.update_system_prompt)
#
#         # Set default values for temperature and max tokens if not already set
#         if not self.ui.temperatureOpenAI.value():
#             self.ui.temperatureOpenAI.setValue(70)
#         if not self.ui.maxTokenOpenAI.value():
#             self.ui.maxTokenOpenAI.setValue(1024)
#
#         self.ui.recognizerMBOX.currentTextChanged.connect(self.toggle_asr_options)
#         self.toggle_asr_options("Google")
#
#     def populate_microphones(self):
#         try:
#             mic_list = sr.Microphone.list_microphone_names()
#             self.ui.microphoneMBox.addItems(mic_list if mic_list else ["No microphones detected"])
#         except Exception as e:
#             self.ui.microphoneMBox.addItem(f"Error: {e}")
#
#     def populate_languages(self):
#         """Populate both Whisper and Google language options."""
#         from whisper.tokenizer import LANGUAGES
#         # Clear existing items to avoid duplicates
#         self.ui.whisperLanguage.clear()
#         for lang_name, lang_key in LANGUAGES.items():
#             self.ui.whisperLanguage.addItem(lang_name, lang_key)
#
#         # Clear and populate google languages
#         self.ui.googleLanguage.clear()
#         google_languages = ["en-US", "es-ES", "fr-FR", "de-DE"]
#         self.ui.googleLanguage.addItems(google_languages)
#
#     def toggle_asr_options(self, recognizer_type):
#         """
#         Show or hide specific ASR options based on the selected recognizer type.
#         """
#         if recognizer_type == "Google":
#             self.ui.googleGroupBox.setVisible(True)
#             self.ui.whisperGroupBox.setVisible(False)
#         elif recognizer_type == "Whisper":
#             self.ui.googleGroupBox.setVisible(False)
#             self.ui.whisperGroupBox.setVisible(True)
#
#     def setup_theme_selection(self):
#         self.ui.themeComboBox.clear()
#         themes = self.get_available_themes()
#         self.ui.themeComboBox.addItems(themes)
#         self.ui.themeComboBox.currentIndexChanged.connect(self.apply_selected_theme)
#
#
#     def get_available_themes(self):
#         if self.stylesheets_folder.exists():
#             return [f.name for f in self.stylesheets_folder.glob("*.qss")]
#         return []
#
#     def apply_selected_theme(self):
#         selected_theme = self.ui.themeComboBox.currentText()
#         stylesheet_path = self.stylesheets_folder / selected_theme
#         if stylesheet_path.exists():
#             with stylesheet_path.open("r", encoding="utf-8") as file:
#                 self.setStyleSheet(file.read())
#
#     def start_transcription(self):
#         if self.transcription_thread and self.transcription_thread.isRunning():
#             self.stop_transcription()
#
#         self.start_whisper()
#
#     def start_whisper(self):
#         selected_model = self.ui.whisperModel.currentText()
#         selected_device = self.ui.whisperDevice.currentText()
#         selected_language_key = self.ui.whisperLanguage.currentData()
#
#         device_map = {"CPU": "cpu", "GPU": "cuda"}
#         device = device_map.get(selected_device, "cpu")
#
#         self.transcription_thread = WhisperTranscriptionThread(
#             model=selected_model,
#             device=device,
#             language=selected_language_key,
#             logger=self.logger,
#         )
#         self.transcription_thread.transcription_signal.connect(self.transcription_signal.emit)
#         self.transcription_thread.start()
#
#     def stop_transcription(self):
#         if self.transcription_thread:
#             self.transcription_thread.stop()
#             self.transcription_thread = None
#
#     def clear_transcription(self):
#         self.ui.contextBrowserOpenAI.clear()
#         self.context.append({"role": "system", "content": self.ui.systemPromptEdit.toPlainText().strip()})
#
#     def update_api_key(self, text):
#         self.api_key = text.strip()
#         openai.api_key = self.api_key
#
#     def update_system_prompt(self):
#         system_prompt_text = self.ui.systemPromptEdit.toPlainText().strip()
#         if system_prompt_text:
#             # Update the system prompt in the context
#             self.context.append({"role": "system", "content": system_prompt_text})
#         else:
#             # Reset to default if empty
#             self.context.append({"role": "system", "content": "You are a helpful assistant."})
#
#     @Slot(str)
#     def handle_transcription(self, user_input):
#         # Display the ASR transcription
#         #self.ui.asrTextBrowser.append(user_input)
#
#         # Proceed to send to OpenAI
#         self.send_to_openai(user_input)
#
#     def send_to_openai(self, user_input):
#         # Append user's message to context
#         self.context.append({"role": "user", "content": user_input})
#
#         # Display user's message in contextBrowserOpenAI
#         self.ui.contextBrowserOpenAI.append(f"<b>User:</b> {user_input}")
#
#         # Make a copy of the context to avoid threading issues
#         context_copy = self.context.copy()
#
#         # Read parameters from GUI
#         max_tokens = self.ui.maxTokenOpenAI.value()
#         temperature = self.ui.temperatureOpenAI.value() / 100
#
#         # Read the selected model from GUI
#         selected_model = self.ui.llmMBOX.currentText()
#
#         # Emit signal to OpenAIWorker
#         self.openai_request_signal.emit(
#             selected_model,
#             context_copy,
#             max_tokens,
#             temperature
#         )
#
#     @Slot(str)
#     def display_openai_response(self, response):
#         # Append assistant's message to context
#         self.context.append({"role": "assistant", "content": response})
#
#         # Display assistant's message in contextBrowserOpenAI
#         self.ui.contextBrowserOpenAI.append(f"<b>Assistant:</b> {response}")
#
#         # Automatically trigger TTS for the assistant response
#         audio_filename = "assistant_response.mp3"
#         self.tts_request_signal.emit(response, audio_filename)
#
#     @Slot(str)
#     def display_openai_error(self, error_message):
#         QMessageBox.critical(self, "OpenAI Error", error_message)
#
#     @Slot(str)
#     def handle_tts_finished(self, message: str):
#         self.logger.log_info(f"TTS completed:{message}")
#
#     @Slot(str)
#     def handle_tts_error(self, error_message):
#         QMessageBox.critical(self, "TTS Error", error_message)
#         self.logger.log_info(f"TTS error:{error_message}")
#
#     def play_audio(self, filename):
#         if os.path.exists(filename):
#             self.audio_player.setSource(filename)
#             self.audio_player.play()
#         else:
#             QMessageBox.warning(self, "Audio Error", f"File {filename} not found.")
#
#     def closeEvent(self, event):
#         self.logger.log_info("Application closing, stopping threads.")
#         self.stop_transcription()
#
#         self.tts_worker.stop()
#         self.tts_worker = None
#
#         self.openai_worker.stop()
#         self.openai_worker_thread.quit()
#         self.openai_worker_thread.wait()
#
#         event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
