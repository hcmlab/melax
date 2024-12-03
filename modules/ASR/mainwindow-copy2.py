import sys
import os
import requests
import numpy as np
import speech_recognition as sr
import whisper
import torch
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QThread, Signal
from ui_form import Ui_MainWindow  # Import your UI file
from local_logger import ThreadSafeLogger
import json
class WhisperTranscriptionThread(QThread):
    transcription_signal = Signal(str)

    def __init__(self, model="medium", device="cpu", language="en", energy_threshold=1000, record_timeout=2.0, parent=None, logger=None):
        super().__init__(parent)
        self.model_name = model
        self.device = device
        self.language = language
        self.energy_threshold = energy_threshold
        self.record_timeout = record_timeout
        self.running = True
        self.logger = logger

    def run(self):
        try:
            self.logger.log_info("Starting Whisper Transcription Thread")
            recorder = sr.Recognizer()
            recorder.energy_threshold = self.energy_threshold
            recorder.dynamic_energy_threshold = False

            source = sr.Microphone(sample_rate=16000)
            audio_model = whisper.load_model(self.model_name, device=self.device)

            transcription_buffer = ""

            def record_callback(_, audio: sr.AudioData):
                if not self.running:
                    return

                data = audio.get_raw_data()
                audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                result = audio_model.transcribe(audio_np, language=self.language, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                nonlocal transcription_buffer
                transcription_buffer += text + " "
                self.transcription_signal.emit(transcription_buffer)

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
        self.logger.log_debug("Stopping Whisper Transcription Thread")
        self.running = False
        self.quit()
        self.wait()


class GoogleASRTranscriptionThread(QThread):
    transcription_signal = Signal(str)

    def __init__(self, api_key, endpoint, language, energy_threshold=1000, record_timeout=2.0, parent=None, logger=None):
        super().__init__(parent)
        self.api_key = api_key
        self.endpoint = endpoint
        self.language = language
        self.energy_threshold = energy_threshold
        self.record_timeout = record_timeout
        self.running = True
        self.logger = logger

    def run(self):
        try:
            self.logger.log_info("Starting Google ASR Transcription Thread")
            recorder = sr.Recognizer()
            recorder.energy_threshold = self.energy_threshold
            recorder.dynamic_energy_threshold = False

            source = sr.Microphone(sample_rate=16000)

            transcription_buffer = ""

            def record_callback(_, audio: sr.AudioData):
                if not self.running:
                    return

                audio_data = audio.get_wav_data()
                headers = {
                    "Content-Type": "audio/l16; rate=16000",
                }
                params = {
                    "key": self.api_key,
                    "lang": self.language,
                }

                try:
                    # Send the audio data to the Google ASR endpoint
                    response = requests.post(
                        self.endpoint, params=params, headers=headers, data=audio_data
                    )

                    # Check for a valid response
                    if response.status_code == 200:
                        try:
                            # Split the response text into separate JSON objects
                            for line in response.text.splitlines():
                                if line.strip():  # Ignore empty lines
                                    try:
                                        response_json = json.loads(line)
                                        # Process each JSON object
                                        # {"result":[{"alternative":[{"transcript":"hello","confidence":0.95212841}],"final":true}],"result_index":0}
                                        if "result" in response_json and len(response_json["result"]) > 0:
                                            text = response_json["result"][0]["alternative"][0]["transcript"]
                                            nonlocal transcription_buffer
                                            transcription_buffer += text + " "
                                            self.transcription_signal.emit(transcription_buffer)
                                    except json.JSONDecodeError as e:
                                        self.logger.log_error(f"JSONDecodeError: {e} | Line: {line}")
                        except Exception as e:
                            self.logger.log_error(f"Error processing JSON stream: {e}")
                    else:
                        self.logger.log_error(
                            f"Google ASR API returned status code {response.status_code}: {response.text}")
                except Exception as e:
                    # Handle any unexpected errors
                    self.logger.log_error(f"Error during Google ASR request: {e}")

            with source:
                recorder.adjust_for_ambient_noise(source)
            stop_listening = recorder.listen_in_background(source, record_callback)

            while self.running:
                self.msleep(100)

            stop_listening()
            self.logger.log_info("Google ASR Transcription Thread Stopped")

        except Exception as e:
            self.logger.log_error(f"Error in Google ASR Transcription Thread: {e}")
            self.transcription_signal.emit(f"Error: {e}")

    def stop(self):
        self.logger.log_debug("Stopping Google ASR Transcription Thread")
        self.running = False
        self.quit()
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.logger = ThreadSafeLogger("asr_application.log")  # Initialize logger
        self.transcription_thread = None

        # Populate options
        self.populate_microphones()
        self.populate_languages()
        self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large"])
        self.ui.whisperDevice.addItems(["CPU", "GPU"])
        self.ui.recognizerMBOX.addItems(["Google", "Whisper"])

        # Connect buttons
        self.ui.startASR.clicked.connect(self.start_transcription)
        self.ui.stopASR.clicked.connect(self.stop_transcription)
        self.ui.clearASR.clicked.connect(self.clear_transcription)

        self.transcription_thread = None  # Active transcription thread
        #
        self.ui.googleAPI.setText("AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw")
        self.ui.googleEndPoint.setText("http://www.google.com/speech-api/v2/recognize")

        # Connect recognizer selection to toggle ASR options
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
        for lang_name, lang_key in LANGUAGES.items():
            self.ui.whisperLanguage.addItem(lang_name, lang_key)

        google_languages = ["en-US", "es-ES", "fr-FR", "de-DE"]  # Common Google ASR languages
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

    def start_transcription(self):
        if self.transcription_thread and self.transcription_thread.isRunning():
            self.stop_transcription()

        selected_recognizer = self.ui.recognizerMBOX.currentText()
        if selected_recognizer == "Whisper":
            self.start_whisper()
        elif selected_recognizer == "Google":
            self.start_google_asr()

    def start_whisper(self):
        self.logger.log_info("Starting Whisper Transcription")
        selected_model = self.ui.whisperModel.currentText()
        selected_device = self.ui.whisperDevice.currentText()
        selected_language_key = self.ui.whisperLanguage.currentData()

        device_map = {"CPU": "cpu", "GPU": "cuda"}
        device = device_map.get(selected_device, "cpu")

        self.transcription_thread = WhisperTranscriptionThread(
            model=selected_model,
            device=device,
            language=selected_language_key,
            energy_threshold=1000,
            record_timeout=2.0,
            logger=self.logger
        )
        self.transcription_thread.transcription_signal.connect(self.update_transcription)
        self.transcription_thread.finished.connect(self.thread_finished)
        self.transcription_thread.start()

    def start_google_asr(self):
        self.logger.log_info("Starting Google ASR Transcription")
        api_key = self.ui.googleAPI.text()
        endpoint = self.ui.googleEndPoint.text()
        language = self.ui.googleLanguage.currentText()

        self.transcription_thread = GoogleASRTranscriptionThread(
            api_key=api_key,
            endpoint=endpoint,
            language=language,
            energy_threshold=1000,
            record_timeout=2.0,
            logger=self.logger
        )
        self.transcription_thread.transcription_signal.connect(self.update_transcription)
        self.transcription_thread.finished.connect(self.thread_finished)
        self.transcription_thread.start()

    def stop_transcription(self):
        if self.transcription_thread and self.transcription_thread.isRunning():
            self.transcription_thread.stop()
            self.transcription_thread = None

    def clear_transcription(self):
        self.ui.asrTextBrowser.clear()

    def update_transcription(self, text):
        self.ui.asrTextBrowser.setText(text)

    def thread_finished(self):
        self.transcription_thread = None

    def closeEvent(self, event):
        self.logger.log_info("Application closing, stopping transcription thread.")
        self.stop_transcription()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
