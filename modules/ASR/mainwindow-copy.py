import sys
import os
import numpy as np
import speech_recognition as sr
import whisper
import torch
from queue import Queue
from time import sleep
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QThread, Signal
from ui_form import Ui_MainWindow

class TranscriptionThread(QThread):
    transcription_signal = Signal(str)

    def __init__(self, model="medium", device="cpu", language="en", energy_threshold=1000, record_timeout=2.0, parent=None):
        super().__init__(parent)
        self.model_name = model
        self.device = device
        self.language = language
        self.energy_threshold = energy_threshold
        self.record_timeout = record_timeout
        self.running = True

    def run(self):
        """Run the transcription process."""
        try:
            recorder = sr.Recognizer()
            recorder.energy_threshold = self.energy_threshold
            recorder.dynamic_energy_threshold = False

            source = sr.Microphone(sample_rate=16000)
            audio_model = whisper.load_model(self.model_name, device=self.device)

            transcription_buffer = ""

            def record_callback(_, audio: sr.AudioData):
                """Callback for processing audio data."""
                if not self.running:  # Stop processing if stopped
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
                sleep(0.1)

            stop_listening()  # Stop the background listener

        except Exception as e:
            self.transcription_signal.emit(f"Error: {e}")

    def stop(self):
        """Stop the transcription thread."""
        self.running = False
        self.quit()  # Signal the thread to terminate


# class MainWindow(QMainWindow):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.ui = Ui_MainWindow()
#         self.ui.setupUi(self)
#         self.populate_microphones()
#         self.populate_languages()
#
#         self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large"])
#         self.ui.whisperDevice.addItems(["CPU", "GPU"])
#         self.ui.recognizerMBOX.addItems(["Google", "Whisper"])
#
#         self.ui.StartListening.clicked.connect(self.start_transcription)
#         self.ui.StopandClearListening.clicked.connect(self.stop_transcription)
#
#         self.transcription_thread = None
#
#     def populate_microphones(self):
#         try:
#             mic_list = sr.Microphone.list_microphone_names()
#             if not mic_list:
#                 mic_list = ["No microphones detected"]
#             self.ui.microphoneMBox.addItems(mic_list)
#         except Exception as e:
#             self.ui.microphoneMBox.addItem(f"Error detecting microphones: {e}")
#
#     def populate_languages(self):
#         """Populate the whisperLanguage ComboBox with supported languages."""
#         from whisper.tokenizer import LANGUAGES
#         for lang_name, lang_key in LANGUAGES.items():
#             self.ui.whisperLanguage.addItem(lang_name, lang_key)
#
#     def start_transcription(self):
#         selected_model = self.ui.whisperModel.currentText()
#         selected_device = self.ui.whisperDevice.currentText()
#         selected_language_key = self.ui.whisperLanguage.currentData()  # Fetch key tag for the language
#
#         device_map = {"CPU": "cpu", "GPU": "cuda"}
#         device = device_map.get(selected_device, "cpu")
#
#         if self.transcription_thread and self.transcription_thread.isRunning():
#             self.stop_transcription()
#
#         self.transcription_thread = TranscriptionThread(
#             model=selected_model,
#             device=device,
#             language=selected_language_key,
#             energy_threshold=1000,
#             record_timeout=2.0,
#         )
#         self.transcription_thread.transcription_signal.connect(self.update_transcription)
#         self.transcription_thread.start()
#
#     def stop_transcription(self):
#         if self.transcription_thread and self.transcription_thread.isRunning():
#             self.transcription_thread.stop()
#             self.transcription_thread = None
#
#     def update_transcription(self, text):
#         self.ui.asrTextBrowser.setText(text)
#
#     def closeEvent(self, event):
#         self.stop_transcription()
#         event.accept()
#
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Populate combo boxes
        self.populate_microphones()
        self.populate_languages()
        self.ui.whisperModel.addItems(["tiny", "base", "small", "medium", "large"])
        self.ui.whisperDevice.addItems(["CPU", "GPU"])
        self.ui.recognizerMBOX.addItems(["Google", "Whisper"])

        # Connect buttons
        self.ui.startASR.clicked.connect(self.start_transcription)
        self.ui.stopASR.clicked.connect(self.stop_transcription)
        self.ui.clearASR.clicked.connect(self.clear_transcription)

        self.transcription_thread = None  # Thread to handle ASR

    def populate_microphones(self):
        """Populate the microphoneMBox with available microphones."""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            self.ui.microphoneMBox.addItems(mic_list if mic_list else ["No microphones detected"])
        except Exception as e:
            self.ui.microphoneMBox.addItem(f"Error: {e}")

    def populate_languages(self):
        """Populate the whisperLanguage ComboBox with supported languages."""
        from whisper.tokenizer import LANGUAGES
        for lang_name, lang_key in LANGUAGES.items():
            self.ui.whisperLanguage.addItem(lang_name, lang_key)

    def start_transcription(self):
        """Start the transcription process."""
        # Ensure no other thread is running
        if self.transcription_thread and self.transcription_thread.isRunning():
            self.stop_transcription()

        # Get user-selected options
        selected_model = self.ui.whisperModel.currentText()
        selected_device = self.ui.whisperDevice.currentText()
        selected_language_key = self.ui.whisperLanguage.currentData()

        device_map = {"CPU": "cpu", "GPU": "cuda"}
        device = device_map.get(selected_device, "cpu")

        # Initialize the transcription thread
        self.transcription_thread = TranscriptionThread(
            model=selected_model,
            device=device,
            language=selected_language_key,
            energy_threshold=1000,
            record_timeout=2.0,
        )
        self.transcription_thread.transcription_signal.connect(self.update_transcription)
        self.transcription_thread.finished.connect(self.thread_finished)  # Graceful exit handler
        self.transcription_thread.start()

    def stop_transcription(self):
        """Stop the transcription thread gracefully."""
        if self.transcription_thread and self.transcription_thread.isRunning():
            self.transcription_thread.stop()  # Signal the thread to stop
            self.transcription_thread.wait()  # Wait for thread to finish
            self.transcription_thread = None  # Clear the reference

    def clear_transcription(self):
        """Clear the transcription display."""
        self.ui.asrTextBrowser.clear()

    def update_transcription(self, text):
        """Update the text browser with the transcribed text."""
        self.ui.asrTextBrowser.setText(text)

    def thread_finished(self):
        """Handle cleanup when the transcription thread finishes."""
        self.transcription_thread = None  # Clear the reference to the thread
        self.ui.asrTextBrowser.setText("closed all threads")

    def closeEvent(self, event):
        """Ensure all resources are released when the window is closed."""
        self.stop_transcription()
        event.accept()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
