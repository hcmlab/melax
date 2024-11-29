import queue
import threading
import numpy as np
import sounddevice as sd
from mediapipe.tasks import python
from mediapipe.tasks.python.components import containers
from mediapipe.tasks.python import audio
import requests
import json
import os
import time
from scipy.io.wavfile import write
import urllib.request

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
# OutputParser class
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


# Real-Time Audio Classification and Transcription
class RealTimeSpeakingTranscriberGoogleAPI:
    def __init__(self, api_key, endpoint, language="en-US", audio_model_path="classifier.tflite"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.language = language
        self.sample_rate = 16000  # MediaPipe and Google ASR require 16kHz
        self.audio_queue = queue.Queue()
        self.running = False
        self.transcription_thread = None
        self.stream = None
        self.audio_buffer = np.empty((0,), dtype=np.float32)

        # Load MediaPipe Audio Classifier
        base_options = python.BaseOptions(model_asset_path=audio_model_path)
        self.audio_classifier_options = audio.AudioClassifierOptions(
            base_options=base_options, max_results=4
        )

        # Initialize OutputParser
        self.parser = OutputParser(show_all=True, with_confidence=True)

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
        """Transcribe audio using Google Speech-to-Text API."""
        print("Transcribing audio buffer...")
        try:
            # Convert the audio buffer to WAV
            temp_filename = "temp_audio.wav"
            write(temp_filename, self.sample_rate, (audio_data * 32767).astype(np.int16))

            # Send HTTP request to Google Speech API
            with open(temp_filename, "rb") as audio_file:
                headers = {"Content-Type": "audio/l16; rate=16000"}
                params = {
                    "key": self.api_key,
                    "output": "json",
                    "lang": self.language,
                }
                response = requests.post(
                    self.endpoint, params=params, headers=headers, data=audio_file
                )

            os.remove(temp_filename)

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
    google_api_key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
    google_asr_endpoint = "http://www.google.com/speech-api/v2/recognize"

    #download_model_if_not_exists(model_url, model_file_name)
    try:
        # Initialize the system
        transcriber = RealTimeSpeakingTranscriberGoogleAPI(
            api_key=google_api_key, endpoint=google_asr_endpoint, audio_model_path=model_file_name
        )
        transcriber.start()

        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        transcriber.stop()
