import queue
import threading
import numpy as np
import sounddevice as sd
import whisperx
import time

class RealTimeSpeakingTranscriberWhisperX:
    def __init__(self, model_name="base", language="en", device="cuda"):
        """
        Initialize the real-time transcriber with WhisperX.
        """
        self.language = language
        self.device = device
        self.transcription_model = whisperx.load_model(model_name, device=device)

        self.sample_rate = 16000  # WhisperX requires 16kHz audio
        self.audio_queue = queue.Queue()
        self.running = False
        self.transcription_thread = None
        self.stream = None
        self.audio_buffer = np.empty((0,), dtype=np.float32)

    def _audio_callback(self, indata, frames, time, status):
        """
        Callback function to handle incoming audio data.
        """
        if status:
            print(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def _process_audio(self):
        """
        Process audio chunks and transcribe them in real-time.
        """
        while self.running:
            try:
                # Check if the queue has audio data
                audio_chunk = self.audio_queue.get(timeout=1)
                self.audio_buffer = np.append(self.audio_buffer, audio_chunk.flatten())

                # Process audio in chunks of 0.5 seconds
                if len(self.audio_buffer) >= self.sample_rate // 2:
                    audio_data = self.audio_buffer[: self.sample_rate // 2]
                    self.audio_buffer = self.audio_buffer[self.sample_rate // 2:]
                    self._transcribe(audio_data)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error during audio processing: {e}")

    def _transcribe(self, audio_data):
        """
        Transcribe audio using WhisperX.
        """
        try:
            # Normalize audio to WhisperX's expected input format
            audio_data = audio_data / np.max(np.abs(audio_data))

            # Transcribe using WhisperX
            transcription = self.transcription_model.transcribe(audio_data, language=self.language)

            # Output the transcription
            print(f"Transcription: {transcription['text']}")
        except Exception as e:
            print(f"Error during transcription: {e}")

    def start(self):
        """
        Start the audio stream and processing.
        """
        self.running = True
        self.transcription_thread = threading.Thread(target=self._process_audio, daemon=True)
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
        """
        Stop the audio stream and processing.
        """
        self.running = False
        if self.transcription_thread:
            self.transcription_thread.join()
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("Stopped.")


if __name__ == "__main__":
    try:
        # Initialize WhisperX-based transcriber
        transcriber = RealTimeSpeakingTranscriberWhisperX(
            model_name="base", language="en", device="cuda"
        )
        transcriber.start()

        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        transcriber.stop()
