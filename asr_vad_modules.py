from PySide6.QtCore import QThread, Signal
import whisper
import speech_recognition as sr
import torch
import numpy as np

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
