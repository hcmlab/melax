import queue
import threading
import numpy as np
import sounddevice as sd
from mediapipe.tasks import python
from mediapipe.tasks.python.components import containers
from mediapipe.tasks.python import audio
import whisper
import urllib.request
import os
import time

def download_model_if_not_exists(url, file_name):
    """
    Downloads a model file from the given URL if it doesn't already exist.

    :param url: The URL to download the model from.
    :param file_name: The name to save the model file as.
    """
    if not os.path.exists(file_name):
        print(f"{file_name} not found. Downloading...")
        urllib.request.urlretrieve(url, file_name)
        print(f"Downloaded {file_name}.")
    else:
        print(f"{file_name} already exists. Skipping download.")

# Real-Time Audio Classification and Transcription
class RealTimeSpeakingTranscriber:
    def __init__(self, model_name="base",language="en", audio_model_path="classifier.tflite", device="cuda"):
        self.language = language
        self.device = device
        self.transcription_model = whisper.load_model(model_name, device=device)

        # Load MediaPipe Audio Classifier
        base_options = python.BaseOptions(model_asset_path=audio_model_path)
        self.audio_classifier_options = audio.AudioClassifierOptions(
            base_options=base_options, max_results=4
        )
        self.sample_rate = 16000  # MediaPipe and Whisper require 16kHz
        self.audio_queue = queue.Queue()
        self.running = False
        self.transcription_thread = None
        self.stream = None
        self.audio_buffer = np.empty((0,), dtype=np.float32)

    def _audio_callback(self, indata, frames, time, status):
        """Callback function to handle incoming audio data."""
        if status:
            print(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def _process_audio(self):
        """Process audio chunks and classify/transcribe them in real-time."""
        with audio.AudioClassifier.create_from_options(self.audio_classifier_options) as classifier:
            speaking_buffer = np.empty((0,), dtype=np.float32)
            is_speaking = False

            while self.running:
                try:
                    audio_chunk = self.audio_queue.get(timeout=1)
                    self.audio_buffer = np.append(self.audio_buffer, audio_chunk.flatten())

                    # Process chunks of 1 second
                    if len(self.audio_buffer) >= self.sample_rate:
                        wav_data = self.audio_buffer[: self.sample_rate]
                        self.audio_buffer = self.audio_buffer[self.sample_rate:]
                        audio_clip = containers.AudioData.create_from_array(
                            wav_data.astype(float), self.sample_rate
                        )
                        result = classifier.classify(audio_clip)

                        # Detect if speaking is occurring
                        top_category = result[0].classifications[0].categories[0]
                        if top_category.category_name == "Speech" and top_category.score > 0.5:
                            print(f"Detected speech: {top_category.score:.2f}")
                            is_speaking = True
                            speaking_buffer = np.append(speaking_buffer, wav_data)
                        else:
                            if is_speaking:
                                # End of speaking turn, transcribe the buffer
                                print("Speaking turn ended. Transcribing...")
                                self._transcribe(speaking_buffer)
                                speaking_buffer = np.empty((0,), dtype=np.float32)
                            is_speaking = False

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Error during processing: {e}")

    def _transcribe(self, audio_data):
        """Transcribe audio using Whisper."""
        print("Transcribing audio buffer...")
        result = self.transcription_model.transcribe(audio_data, language=self.language)
        print(f"Transcription: {result['text']}")

    def start(self):
        """Start audio stream and processing."""
        self.running = True
        self.transcription_thread = threading.Thread(target=self._process_audio)
        self.transcription_thread.start()

        print("Starting audio stream...")
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop(self):
        """Stop audio stream and processing."""
        self.running = False
        if self.transcription_thread:
            self.transcription_thread.join()
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("Stopped.")

if __name__ == "__main__":
    model_url = "https://storage.googleapis.com/mediapipe-models/audio_classifier/yamnet/float32/1/yamnet.tflite"
    model_file_name = "classifier.tflite"

    download_model_if_not_exists(model_url, model_file_name)
    try:
        # Initialize the system
        transcriber = RealTimeSpeakingTranscriber(
            model_name="base", audio_model_path="classifier.tflite", device="cuda"
        )
        transcriber.start()

        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        transcriber.stop()
