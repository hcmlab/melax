import queue
import threading
import sounddevice as sd
import numpy as np
import whisper
import torch
import time

class RealTimeWhisperASR:
    def __init__(self, model_name="base", device="cuda", chunk_duration=5, language="en"):
        """
        Real-Time ASR using OpenAI's Whisper model.
        :param model_name: Whisper model size (e.g., "base", "small", "medium", "large").
        :param device: Device for inference ("cuda" or "cpu").
        :param chunk_duration: Duration of audio chunks in seconds.
        :param language: Language code for transcription.
        """
        self.model = whisper.load_model(model_name, device=device)
        self.device = device
        self.chunk_duration = chunk_duration
        self.language = language
        self.sample_rate = 16000  # Whisper requires 16 kHz
        self.audio_queue = queue.Queue()
        self.running = False
        self.transcription_thread = None
        self.stream = None

    def _audio_callback(self, indata, frames, time, status):
        """Callback function to handle incoming audio data."""
        if status:
            print(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def _process_audio(self):
        """Process audio chunks and transcribe them."""
        audio_buffer = np.empty((0,), dtype=np.float32)

        while self.running:
            try:
                # Get audio chunk from the queue
                audio_chunk = self.audio_queue.get(timeout=1)
                audio_buffer = np.append(audio_buffer, audio_chunk.flatten())

                # Process chunks of the specified duration
                if len(audio_buffer) >= self.chunk_duration * self.sample_rate:
                    print("Processing audio chunk...")
                    audio = whisper.pad_or_trim(audio_buffer)
                    print(f"Audio buffer shape: {audio.shape}")

                    # Perform transcription
                    result = self.model.transcribe(
                        audio,
                        language=self.language,
                        fp16=torch.cuda.is_available(),
                    )
                    print(f"Transcription: {result['text']}")

                    # Clear processed buffer
                    audio_buffer = np.empty((0,), dtype=np.float32)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error during transcription: {e}")

    def start(self):
        """Start the audio stream and transcription."""
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
        """Stop the audio stream and transcription."""
        self.running = False
        if self.transcription_thread:
            self.transcription_thread.join()
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("Stopped.")

if __name__ == "__main__":
    try:
        asr = RealTimeWhisperASR(model_name="base", device="cuda", chunk_duration=5, language="en")
        asr.start()

        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping ASR...")
        asr.stop()
