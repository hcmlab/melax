from PySide6.QtCore import QThread, Signal
import whisper
import speech_recognition as sr
import torch
import numpy as np
import requests
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
                if text:
                    self.transcription_signal.emit(text)

            with source:
                recorder.adjust_for_ambient_noise(source)
            stop_listening = recorder.listen_in_background(source, record_callback, phrase_time_limit=self.record_timeout)

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
        import pydevd;pydevd.settrace(suspend=False)
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
                                            #nonlocal transcription_buffer
                                            #transcription_buffer += text + " "
                                            if text:
                                                self.transcription_signal.emit(text)
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
            self.logger.log_error(f"Error in Google ASR Transcription Thread: {e}. This error occurs e.g. when the wrong microphone input is selected.")
            # Stop the ASR if an error occurs as it would be called over and over again
            self.stop() 

    def stop(self):
        self.logger.log_debug("Stopping Google ASR Transcription Thread")
        self.running = False
        self.quit()
        self.wait()