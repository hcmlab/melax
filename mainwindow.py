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
from llm_modules import OpenAIWorker
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
    tts_request_signal = Signal(str)              # TTS request (text)

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
        self.openai_worker = None
        self.openai_worker_thread = None
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

        # ----------------------------------------------------
        # Audio2Face
        # ----------------------------------------------------
        # load usd
        self.usd_folder_path = os.path.join(os.getcwd(), "usd")
        self.populate_usd_list()
        self.load_selected_usd()
        self.headless_server_url = None

        #self.ui.loadUSDButton.clicked.connect(self.load_usd_to_server)
        #self.ui.checkServerButton.clicked.connect(self.check_server_status)

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
        self.ui.LLMChocie.addItems(["OpenAI", "LLAMA", "Gemini"])
        self.models = ["gpt-4o-mini", "gpt-3.5-turbo"]
        self.ui.llmMBOX.addItems(self.models)

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

        # If temperature/max tokens aren't set, set defaults
        self.ui.temperatureOpenAI.setRange(0, 100)
        self.ui.temperatureOpenAI.valueChanged.connect(self.update_temperature_label)
        self.ui.temperatureOpenAI.setValue(70)
        self.update_temperature_label(self.ui.temperatureOpenAI.value())

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
        self.ui.a2fUrl_headless.setText("http://localhost:8011/")
        self.headless_server_url = self.ui.a2fUrl_headless.text().strip()
        self.check_server_status()


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

        # Start LLM
        self.start_llm()
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
    # LLM (OpenAI)
    # ----------------------------------------------------
    def start_llm(self):
        """
        Create & start OpenAI worker with the current API key.
        """
        self.logger.log_info("start_llm() called.")

        # Stop existing if any
        self.stop_llm()

        # Read the key from UI
        self.api_key = self.ui.openaiAPIKey.text().strip()
        if not self.api_key:
            self.api_key = os.getenv('OPENAI_API_KEY')
            self.ui.openaiAPIKey.setText(self.api_key if self.api_key else "")
        openai.api_key = self.api_key

        # Create the worker
        self.openai_worker = OpenAIWorker(api_key=self.api_key)
        self.openai_worker_thread = QThread()
        self.openai_worker.moveToThread(self.openai_worker_thread)
        self.openai_worker.responseReady.connect(self.display_openai_response)
        self.openai_worker.errorOccurred.connect(self.display_openai_error)

        # Connect LLM request signal to worker
        self.openai_request_signal.connect(self.openai_worker.add_request)

        self.openai_worker_thread.start()
        self.logger.log_info("OpenAI worker started.")

    def stop_llm(self):
        """
        Stop the OpenAI worker if running.
        """
        self.logger.log_info("stop_llm() called.")
        if self.openai_worker:
            self.openai_worker.stop()
            self.openai_worker = None
        if self.openai_worker_thread:
            self.openai_worker_thread.quit()
            self.openai_worker_thread.wait()
            self.openai_worker_thread = None

    @Slot(int)
    def update_temperature_label(self, slider_value: int):
        """
        Convert slider_value (0..200) to a float in 0..2 range
        and update llmTemperatureLable text accordingly.
        """
        # Scale the integer to a float between 0..2:
        temperature = slider_value / 100.0
        # Update the label:
        self.ui.llmTemperatureLable.setText(f"value: {temperature:.2f}")
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

    def check_server_status(self):
        """
        Sends a GET request to check the status of the headless server.
        If the server responds with "OK", updates the server status label to green "connected".
        """
        try:
            response = requests.get(f"{self.headless_server_url}/status", headers={"accept": "application/json"})
            if response.status_code == 200:
                try:
                    response_json = json.loads(response.text)
                    if response_json == "OK":
                        self.update_server_status(True)
                    else:
                        self.update_server_status(False)
                except ValueError as e:
                    print(f"Error parsing JSON response: {e}")
                    self.update_server_status(False)
            else:
                self.update_server_status(False)
        except requests.exceptions.RequestException as e:
            print(f"Error checking server status: {e}")
            self.update_server_status(False)

    def load_selected_usd(self):
        """
        Loads the selected USD from the combo box to the server.
        """
        selected_usd = self.ui.usdCombo.currentText()
        if not selected_usd or selected_usd in ["No USD files available", "No USD folder found"]:
            self.ui.usdPathLable.setStyleSheet("color: red;")
            self.ui.usdPathLable.setText("Invalid USD selection.")
            return

        usd_path = os.path.join(self.usd_folder_path, selected_usd)
        try:
            payload = {"file_name": usd_path}
            response = requests.post(
                f"{self.headless_server_url}/A2F/USD/Load",
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if response.status_code == 200 and response.json().get("status") == "OK":
                self.ui.usdPathLable.setStyleSheet("color: green;")
                self.ui.usdPathLable.setText("USD Loaded Successfully!")
            else:
                self.ui.usdPathLable.setStyleSheet("color: red;")
                self.ui.usdPathLable.setText("Failed to Load USD.")
        except requests.exceptions.RequestException as e:
            print(f"Error loading USD: {e}")
            self.ui.usdPathLable.setStyleSheet("color: red;")
            self.ui.usdPathLable.setText("Error Loading USD.")

    def update_server_status(self, connected: bool):
        """
        Updates the server status label based on the connection status.
        """
        if connected:
            self.ui.headlessServerStatus.setStyleSheet("color: green;")
            self.ui.headlessServerStatus.setText("Connected")
        else:
            self.ui.headlessServerStatus.setStyleSheet("color: red;")
            self.ui.headlessServerStatus.setText("Disconnected")

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
            default_prompt = "You are a helpful assistant."
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
        self.send_to_openai(user_input)

    def send_to_openai(self, user_input):
        """
        Sends user input to OpenAI API after appending it to the context.
        Truncates the context if it exceeds the maximum allowed length.
        """
        self.ui.contextBrowserOpenAI.append(f"<b>User:</b> {user_input}")

        # Append the user message to the context
        self.context.append({
            "role": "user",
            "content": [{"type": "text", "text": user_input}]
        })


        # Truncate the context if it exceeds MAX_CONTEXT_LENGTH
        if len(self.context) > self.MAX_CONTEXT_LENGTH + 1:  # +1 for the developer role
            self.context = self.context[:1] + self.context[-self.MAX_CONTEXT_LENGTH:]

        # Prepare parameters for OpenAI request
        context_copy = self.context.copy()
        max_tokens = self.ui.maxTokenOpenAI.value()
        temperature = self.ui.temperatureOpenAI.value() / 100
        selected_model = self.ui.llmMBOX.currentText()

        # Emit the OpenAI request signal
        self.openai_request_signal.emit(selected_model, context_copy, max_tokens, temperature)

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
