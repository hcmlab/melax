import speech_recognition as sr
from queue import Queue
import threading
import time


class MeLaXASR:
    """
    A custom ASR class for the MeLaX system that transcribes audio in real-time
    using the Google Speech Recognition API.
    """

    def __init__(self, api_key: str, language: str = "en-US"):
        """
        Initialize the MeLaXASR system.

        :param api_key: Google Cloud Speech Recognition API key.
        :param language: Language code for transcription (default is "en-US").
        """
        self.api_key = api_key
        self.language = language
        self.recognizer = sr.Recognizer()
        self.audio_queue = Queue()
        self.transcription_thread = None
        self.running = False
        self.callbacks = []

    def _transcribe_audio(self):
        """Internal method to transcribe audio from the queue in real-time."""
        while self.running:
            try:
                audio_data = self.audio_queue.get(timeout=1)  # Wait for audio input
                if audio_data is None:  # Stop signal
                    break

                # Transcribe using Google API
                try:
                    transcription = self.recognizer.recognize_google(
                        audio_data, key=self.api_key, language=self.language
                    )
                    self._notify_callbacks(transcription)
                except sr.UnknownValueError:
                    print("Google ASR could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Google ASR request failed: {e}")
            except Exception as e:
                print(f"Error during transcription: {e}")

    def _notify_callbacks(self, transcription: str):
        """
        Notify all registered callbacks with the transcription result.

        :param transcription: Transcribed text.
        """
        for callback in self.callbacks:
            callback(transcription)

    def add_callback(self, callback):
        """
        Add a callback function to handle transcribed results.

        :param callback: A callable that takes a transcription string as input.
        """
        self.callbacks.append(callback)

    def start_listening(self, device_index=None):
        """
        Start listening to the microphone and enqueue audio for transcription.

        :param device_index: Microphone device index to use (default is None for the default microphone).
        """
        self.running = True
        self.transcription_thread = threading.Thread(target=self._transcribe_audio)
        self.transcription_thread.start()

        def listen_to_microphone():
            with sr.Microphone(device_index=device_index) as source:
                self.recognizer.adjust_for_ambient_noise(source)
                print("Listening for audio... Speak now!")
                while self.running:
                    try:
                        audio = self.recognizer.listen(source, timeout=10)
                        self.audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        print("Listening timed out. Waiting for speech...")

        threading.Thread(target=listen_to_microphone, daemon=True).start()

    def stop_listening(self):
        """
        Stop listening and terminate transcription threads.
        """
        self.running = False
        self.audio_queue.put(None)  # Send stop signal
        if self.transcription_thread:
            self.transcription_thread.join()

    def is_running(self) -> bool:
        """
        Check if the ASR system is currently running.

        :return: True if running, False otherwise.
        """
        return self.running


# Example Usage
if __name__ == "__main__":
    API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"

    def handle_transcription(transcription):
        print(f"Transcription: {transcription}")

    melax_asr = MeLaXASR(api_key=API_KEY)

    melax_asr.add_callback(handle_transcription)
    melax_asr.start_listening()

    try:
        while melax_asr.is_running():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping ASR...")
        melax_asr.stop_listening()
