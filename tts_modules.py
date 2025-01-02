import io
import time
import grpc
import numpy as np
import soundfile
from pydub import AudioSegment
from gtts import gTTS
from queue import Queue

from PySide6.QtCore import QThread, Signal, Slot
from streaming_server import audio2face_pb2, audio2face_pb2_grpc



class TTSWorker(QThread):
    """
    A QThread-based worker that:
      1) Takes text from a queue,
      2) Generates TTS audio (with gTTS),
      3) Streams the audio in chunks to an Audio2Face instance via gRPC.
    """

    # Signals to notify the outside world about results or errors
    ttsFinished = Signal(str)   # Emitted when streaming to A2F completes successfully
    ttsError = Signal(str)      # Emitted if any error occurs

    def __init__(
        self,
        url="localhost:50051",
        instance_name="/World/audio2face/PlayerStreaming",
        chunk_duration=0.05,
        block_until_playback_is_finished=True,
        parent=None
    ):
        """
        :param url: The gRPC server URL for Audio2Face, e.g. 'localhost:50051'
        :param instance_name: The prim path of the Audio2Face Streaming Audio Player
        :param chunk_duration: Approx duration (in seconds) of each audio chunk
        :param block_until_playback_is_finished: Whether we block until playback finishes
        """
        super().__init__(parent)

        self.url = url
        self.instance_name = instance_name
        self.chunk_duration = chunk_duration
        self.block_until_playback_is_finished = block_until_playback_is_finished

        self.request_queue = Queue()
        self.should_exit = False
        self.is_processing = False

    def run(self):
        """
        Main thread loop:
        Continuously checks for new text requests in the queue and processes them.
        """
        while not self.should_exit:
            if self.is_processing:
                # Busy: let it finish
                self.msleep(100)
                continue

            if self.request_queue.empty():
                # No new requests
                self.msleep(100)
                continue

            # Get text from the queue
            text = self.request_queue.get()
            self.is_processing = True
            try:
                self._process_text_to_a2f(text)
            except Exception as e:
                self.ttsError.emit(str(e))
            finally:
                self.is_processing = False

    @Slot(str)
    def add_request(self, text: str):
        """
        Add a new TTS request to the queue.
        :param text: The text to synthesize and stream to Audio2Face.
        """
        if self.should_exit:
            return
        self.request_queue.put(text)

    def stop(self):
        """
        Signal the thread to exit and clear any pending requests.
        """
        self.should_exit = True
        with self.request_queue.mutex:
            self.request_queue.queue.clear()

    def _process_text_to_a2f(self, text: str):
        """
        1) Generate TTS in-memory (MP3)
        2) Convert MP3 -> PCM (WAV) in memory
        3) Stream PCM data to Audio2Face via gRPC
        """

        # --- 1) Generate TTS audio as MP3 in memory
        mp3_buffer = io.BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)

        # --- 2) Convert MP3 to raw float32 PCM data
        audio_seg = AudioSegment.from_file(mp3_buffer, format="mp3")
        wav_buffer = io.BytesIO()
        audio_seg.export(wav_buffer, format='wav')
        wav_buffer.seek(0)

        # Read raw samples (float32) using soundfile
        data, samplerate = soundfile.read(wav_buffer, dtype='float32')
        # If stereo, average to mono (Audio2Face only accepts mono)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # --- 3) Stream audio data to Audio2Face
        self._push_audio_track_stream(data, samplerate)

    def _push_audio_track_stream(self, audio_data: np.ndarray, samplerate: int):
        """
        Emulate your push_audio_track_stream() function:
         - Create a generator of PushAudioStreamRequest
         - Connect and call stub.PushAudioStream(...)
        """
        # Determine how many samples per chunk
        chunk_size = int(samplerate * self.chunk_duration)

        with grpc.insecure_channel(self.url) as channel:
            stub = audio2face_pb2_grpc.Audio2FaceStub(channel)

            def make_generator():
                # 1) Start marker message (no audio data yet)
                start_marker = audio2face_pb2.PushAudioRequestStart(
                    samplerate=samplerate,
                    instance_name=self.instance_name,
                    block_until_playback_is_finished=self.block_until_playback_is_finished,
                )
                yield audio2face_pb2.PushAudioStreamRequest(start_marker=start_marker)

                # 2) Stream out the PCM data in chunks
                idx = 0
                while idx < len(audio_data):
                    chunk = audio_data[idx : idx + chunk_size]
                    idx += chunk_size

                    # Convert chunk to bytes (float32)
                    chunk_bytes = chunk.astype(np.float32).tobytes()
                    yield audio2face_pb2.PushAudioStreamRequest(audio_data=chunk_bytes)

                    # This sleep emulates a "realtime" feed. Tweak or remove as needed.
                    time.sleep(0.01)

            # Actually do the streaming
            request_generator = make_generator()
            response = stub.PushAudioStream(request_generator)

        if response.success:
            self.ttsFinished.emit(f"Successfully pushed TTS audio to {self.instance_name}")
        else:
            raise RuntimeError(f"Audio2Face streaming error: {response.message}")
