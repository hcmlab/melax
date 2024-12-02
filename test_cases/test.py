import queue
import threading
import numpy as np
import sounddevice as sd
from mediapipe.tasks.python import audio
from mediapipe.tasks.python.audio import AudioClassifier, AudioClassifierOptions
from mediapipe.tasks.python.components.containers import AudioData
from mediapipe.tasks.python.core.base_options import BaseOptions
import mediapipe
RunningMode = mediapipe.tasks.audio.RunningMode
import requests
import os
import time
from scipy.io.wavfile import write
import io
import json

class OutputParser:
    def __init__(self, *, show_all: bool, with_confidence: bool) -> None:
        self.show_all = show_all
        self.with_confidence = with_confidence

    def parse(self, response_text: str):
        print(response_text)
        actual_result = self.convert_to_result(response_text)
        if self.show_all:
            return actual_result

        best_hypothesis = self.find_best_hypothesis(actual_result["alternative"])
        confidence = best_hypothesis.get("confidence", 0.5)
        if self.with_confidence:
            return best_hypothesis["transcript"], confidence
        return best_hypothesis["transcript"]

    @staticmethod
    def convert_to_result(response_text: str):
        for line in response_text.split("\n"):
            if not line:
                continue
            result = json.loads(line)["result"]
            if len(result) != 0:
                if len(result[0].get("alternative", [])) == 0:
                    raise ValueError("No alternatives available in response.")
                return result[0]
        raise ValueError("No valid results found in response.")

    @staticmethod
    def find_best_hypothesis(alternatives: list):
        if "confidence" in alternatives:
            best_hypothesis = max(
                alternatives,
                key=lambda alternative: alternative["confidence"],
            )
        else:
            best_hypothesis = alternatives[0]
        if "transcript" not in best_hypothesis:
            raise ValueError("No transcript found in best hypothesis.")
        return best_hypothesis


class RealTimeSpeakingTranscriberGoogleAPI:
    def __init__(self, api_key, endpoint, audio_model_path="classifier.tflite"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.sample_rate = 16000  # MediaPipe and Google ASR require 16kHz
        self.audio_queue = queue.Queue()
        self.running = False
        self.classifier = None
        self.stream = None
        self.audio_buffer = np.empty((0,), dtype=np.float32)
        self.speaking_buffer = np.empty((0,), dtype=np.float32)
        self.is_speaking = False
        self.start_time = time.time()
        self.total_samples = 0
        self.parser = OutputParser(show_all=False, with_confidence=True)

        # Configure MediaPipe AudioClassifier in streaming mode
        base_options = BaseOptions(model_asset_path=audio_model_path)
        self.audio_classifier_options = AudioClassifierOptions(
            base_options=base_options,
            running_mode=RunningMode.AUDIO_STREAM,
            max_results=1,
            result_callback=self._classification_callback,
        )

    def _classification_callback(self, result, timestamp_ms):
        """Handles classification results asynchronously."""
        for classification in result.classifications:
            top_category = classification.categories[0]
            if top_category.category_name == "Speech" and top_category.score > 0.5:
                print(f"[{timestamp_ms} ms] Detected Speech: Confidence {top_category.score:.2f}")
                self.is_speaking = True
            else:
                if self.is_speaking:
                    print("End of speech detected. Transcribing...")
                    self._transcribe(self.speaking_buffer)
                    self.speaking_buffer = np.empty((0,), dtype=np.float32)
                self.is_speaking = False

    import io  # For in-memory binary streams

    def _transcribe(self, audio_data):
        """Transcribe audio using Google Speech-to-Text API without file writing."""
        print("Transcribing audio buffer...")
        try:
            # Convert the audio buffer to WAV format in memory
            wav_buffer = io.BytesIO()
            write(wav_buffer, self.sample_rate, (audio_data * 32767).astype(np.int16))
            wav_buffer.seek(0)  # Rewind the buffer to the beginning

            # Send HTTP request to Google Speech API
            headers = {"Content-Type": "audio/l16; rate=16000"}
            params = {
                "key": self.api_key,
                "output": "json",
                "lang": "en-US",  # Specify the language
            }
            response = requests.post(
                self.endpoint, params=params, headers=headers, data=wav_buffer.read()
            )

            # Parse response using OutputParser
            if response.status_code == 200:
                parsed_result = self.parser.parse(response.text)
                if isinstance(parsed_result, tuple):  # With confidence
                    transcript, confidence = parsed_result
                    print(f"Transcription: {transcript} (Confidence: {confidence:.2f})")
                else:  # Without confidence
                    print(f"Transcription: {parsed_result}")
            else:
                print(f"Google ASR API error: {response.status_code}, {response.text}")

        except Exception as e:
            print(f"Error during transcription: {e}")

    def _audio_callback(self, indata, frames, time_info, status):
        """Audio callback function for processing live audio."""
        if status:
            print(f"Audio stream status: {status}")

        # Normalize audio data
        buffer = indata.flatten()
        normalized_buffer = buffer.astype(float) / np.iinfo(np.int16).max

        # Create AudioData
        audio_data = AudioData.create_from_array(normalized_buffer, self.sample_rate)

        # Calculate timestamp based on the number of samples processed
        timestamp_ms = int(self.start_time * 1000 + (self.total_samples / self.sample_rate) * 1000)
        self.total_samples += frames  # Update total samples processed

        # Classify asynchronously
        self.classifier.classify_async(audio_data, timestamp_ms)

    def start(self):
        """Start audio stream and processing."""
        print("Starting real-time audio classification and transcription...")
        self.running = True

        # Initialize the AudioClassifier
        self.classifier = AudioClassifier.create_from_options(self.audio_classifier_options)

        # Start the audio stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop(self):
        """Stop audio stream and processing."""
        print("Stopping...")
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.classifier:
            self.classifier.close()
        print("Stopped.")


if __name__ == "__main__":
    model_url = "https://storage.googleapis.com/mediapipe-models/audio_classifier/yamnet/float32/1/yamnet.tflite"
    model_file_name = "classifier.tflite"
    google_api_key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
    google_asr_endpoint = "http://www.google.com/speech-api/v2/recognize"

    # Download the model if it doesn't exist
    if not os.path.exists(model_file_name):
        import urllib
        print(f"Downloading model {model_file_name}...")
        urllib.request.urlretrieve(model_url, model_file_name)

    # Initialize and start the transcriber
    try:
        transcriber = RealTimeSpeakingTranscriberGoogleAPI(
            api_key=google_api_key, endpoint=google_asr_endpoint, audio_model_path=model_file_name
        )
        transcriber.start()

        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        transcriber.stop()
