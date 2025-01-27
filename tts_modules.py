from abc import ABC, abstractmethod
import io
import time
import grpc
import soundfile
from pydub import AudioSegment
from gtts import gTTS
from queue import Queue
import re
from TTS.api import TTS
import numpy as np
from nltk.tokenize import sent_tokenize

from PySide6.QtCore import QThread, Signal, Slot
from streaming_server.proto.old import audio2face_pb2_grpc, audio2face_pb2

LANGUAGE_TLD_MAP = {
    "en": "com",        # English (US) default
    "en-GB": "co.uk",   # British English
    "en-AU": "com.au",  # Australian English
    "en-IN": "co.in",   # Indian English
    "fr": "fr",         # French
    "es": "es",         # Spanish
    "de": "de",         # German
    "ru": "ru",         # Russian
    "it": "it",         # Italian
    # ...
}
class BaseTTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, language:str) -> (np.ndarray, int):
        """
        Synthesize `text` into audio data (float32 array) and return (audio_data, sample_rate).
        """
        pass

class GoogleTTSEngine(BaseTTSEngine):
    def synthesize(self, text: str,language:str ) -> (np.ndarray, int):
        # 1) Generate MP3 in memory
        mp3_buffer = io.BytesIO()
        tts = gTTS(text=text, lang=language, tld=self.get_tld_for_language(language))
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)

        # 2) Decode MP3 to PCM (wav) in memory with pydub
        audio_seg = AudioSegment.from_file(mp3_buffer, format="mp3")
        wav_buffer = io.BytesIO()
        audio_seg.export(wav_buffer, format='wav')
        wav_buffer.seek(0)

        # 3) Read PCM data with soundfile => np.float32
        audio_data, sample_rate = soundfile.read(wav_buffer, dtype='float32')
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)  # stereo -> mono
        return audio_data, sample_rate

    def get_tld_for_language(self, lang: str) -> str:
        """
        Given a language code like 'en', 'en-GB', 'fr', 'es', etc.,
        return the corresponding TLD for gTTS usage.
        If the language code isn't in the map, fallback to 'com'.
        """
        return LANGUAGE_TLD_MAP.get(lang, "com")

class CoquiTTSEngine(BaseTTSEngine):
    def __init__(self, model_name="tts_models/en/ljspeech/tacotron2-DDC"):
        # Initialize the Coqui TTS model once
        self._tts = TTS(model_name)

    def synthesize(self, text: str, language: str) -> (np.ndarray, int):
        """
        Generate audio in memory using Coqui TTS.
        Coqui TTS may return a Python list, so we convert that to a NumPy array.
        """
        # 1) Coqui call returns a Python list of floats
        audio_list = self._tts.tts(text)

        # 2) Convert list => float32 np.array
        audio_data = np.array(audio_list, dtype=np.float32)

        # 3) Mono check
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)  # stereo -> mono

        # 4) Sample rate from the model
        sample_rate = self._tts.synthesizer.output_sample_rate

        return audio_data, sample_rate

def nlp_sentence_split(text: str):
    """
    Placeholder for an advanced NLP-based sentence splitter.
    In real usage, you might use spaCy or NLTK to parse text properly.
    """
    return sent_tokenize(text)


def regex_sentence_split(text: str):
    """
    A simple regex-based sentence splitter: splits on '.', '?', '!'
    but retains punctuation at the end of each chunk.
    Cleans the text to remove any '#' and '*' characters before splitting.

    Args:
        text (str): The input text to be processed.

    Returns:
        list: A list of sentences with punctuation retained.
    """
    # Remove '#' and '*' from the text
    cleaned_text = re.sub(r'[\#\*]', '', text)

    # Split the cleaned text into sentences
    parts = re.split(r'([.!?])', cleaned_text)
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        sentence = parts[i].strip()
        punctuation = parts[i + 1].strip()
        if sentence:
            sentences.append(f"{sentence}{punctuation}")

    return sentences

def push_audio_track(url, audio_data, samplerate, instance_name, block_until_playback_is_finished=True):
    """
    Pushes the whole audio track at once using PushAudioRequest().
    """
    with grpc.insecure_channel(url) as channel:
        stub = audio2face_pb2_grpc.Audio2FaceStub(channel)
        request = audio2face_pb2.PushAudioRequest()
        # Convert to float32 + tobytes()
        request.audio_data = audio_data.astype(np.float32).tobytes()
        request.samplerate = samplerate
        request.instance_name = instance_name
        request.block_until_playback_is_finished = block_until_playback_is_finished
        print("Sending entire audio track...")
        response = stub.PushAudio(request)
        if response.success:
            print("SUCCESS")
        else:
            print(f"ERROR: {response.message}")
    print("Closed channel for single push")

def push_audio_track_stream(url, audio_data, samplerate, instance_name, chunk_duration, delay_between_chunks,block_until_playback_is_finished=True):
    """
    Pushes audio in chunks sequentially via PushAudioStreamRequest().
    """
    chunk_size = samplerate // chunk_duration  # ~100ms chunk if chunk_size = samplerate/10
    sleep_between_chunks = delay_between_chunks/100  # Emulate streaming delay

    with grpc.insecure_channel(url) as channel:
        print("Channel created for streaming")
        stub = audio2face_pb2_grpc.Audio2FaceStub(channel)

        def make_generator():
            # First message with start_marker
            start_marker = audio2face_pb2.PushAudioRequestStart(
                samplerate=samplerate,
                instance_name=instance_name,
                block_until_playback_is_finished=block_until_playback_is_finished,
            )
            yield audio2face_pb2.PushAudioStreamRequest(start_marker=start_marker)

            # Then send chunks
            total_len = len(audio_data)
            idx = 0
            while idx < total_len:
                time.sleep(sleep_between_chunks)
                chunk = audio_data[idx : idx + chunk_size]
                idx += chunk_size
                yield audio2face_pb2.PushAudioStreamRequest(
                    audio_data=chunk.astype(np.float32).tobytes()
                )

        request_generator = make_generator()
        print("Streaming audio data...")
        response = stub.PushAudioStream(request_generator)
        if response.success:
            print("SUCCESS")
        else:
            print(f"ERROR: {response.message}")
    print("Channel closed for streaming")


class TTSWorker(QThread):
    """
    A QThread-based worker that:
      1) Takes text from a queue,
      2) Splits the text (either with regex or 'NLP'),
      3) Uses a provided TTS engine to synthesize each sentence,
      4) Pushes the resulting audio to Audio2Face (either all-at-once or streaming).
    """

    ttsFinished = Signal(str)  # Emitted on successful completion
    ttsError = Signal(str)     # Emitted on error

    def __init__(
        self,
        tts_engine,
        language="en",
        url="localhost:50051",
        instance_name="/World/audio2face/PlayerStreaming",
        use_nlp_split=False,        # If True => NLP-based splitting, else regex
        use_audio_streaming=False,         # If True => push audio in a stream, else in one chunk
        block_until_playback_is_finished=True,
        chunk_duration=10,
        delay_between_chunks=0.04 ,
        parent=None
    ):
        """
        :param tts_engine: An object implementing BaseTTSEngine
        :param url: The gRPC server URL for Audio2Face, e.g. 'localhost:50051'
        :param instance_name: The prim path of the Audio2Face Streaming Audio Player
        :param use_nlp_split: Whether to use an NLP-based splitting vs. simple regex
        :param use_audio_streaming: Whether to stream audio or send in one shot
        :param block_until_playback_is_finished: pass to Audio2Face to block
        """
        super().__init__(parent)

        self.tts_engine = tts_engine
        self.language = language
        self.url = url
        self.instance_name = instance_name
        self.use_nlp_split = use_nlp_split
        self.use_streaming = use_audio_streaming
        self.block_until_playback_is_finished = block_until_playback_is_finished
        self.chunk_duration= chunk_duration
        self.delay_between_chunks = delay_between_chunks

        self.request_queue = Queue()
        self.should_exit = False
        self.is_processing = False

    def run(self):
        """
        Main loop: Wait for text in queue, process it by splitting TTS -> Audio2Face.
        """
        while not self.should_exit:
            if self.is_processing:
                self.msleep(100)
                continue

            if self.request_queue.empty():
                self.msleep(100)
                continue

            # Get text from the queue
            text = self.request_queue.get()
            self.is_processing = True
            try:
                self._process_text_to_a2f(text)
            except Exception as e:
                print(e)
                self.ttsError.emit(str(e))
            finally:
                self.is_processing = False

    @Slot(str)
    def add_request(self, text: str):
        """
        Enqueue a new TTS request.
        """
        if self.should_exit:
            return
        self.request_queue.put(text)

    def stop(self):
        """
        Signal the thread to stop and clear pending requests.
        """
        self.should_exit = True
        with self.request_queue.mutex:
            self.request_queue.queue.clear()

    def _process_text_to_a2f(self, text: str):
        """
        1) Split text into sentences,
        2) For each sentence => TTS => send to Audio2Face
           (either streaming or single shot).
        """
        if self.use_nlp_split:
            sentences = nlp_sentence_split(text)
        else:
            sentences = regex_sentence_split(text)

        # If you want to combine all sentences into one big TTS call,
        # you could do: combined_text = "# ".join(sentences)
        # audio_data, samplerate = self.tts_engine.synthesize(combined_text)
        # and then call push once. But let's do them sentence-by-sentence:
        for idx, sentence in enumerate(sentences, start=1):
            # 1) Synthesize
            audio_data, samplerate = self.tts_engine.synthesize(sentence, language=self.language)

            # 2) Push to A2F
            if self.use_streaming:
                push_audio_track_stream(
                    self.url,
                    audio_data,
                    samplerate,
                    self.instance_name,
                    self.chunk_duration,
                    self.delay_between_chunks,
                    block_until_playback_is_finished=self.block_until_playback_is_finished,
                )
            else:
                push_audio_track(
                    self.url,
                    audio_data,
                    samplerate,
                    self.instance_name,
                    block_until_playback_is_finished=self.block_until_playback_is_finished
                )

        self.ttsFinished.emit(f"TTS done for text: {text}")

# class TTSWorker(QThread):
#     """
#     A QThread-based worker that:
#       1) Takes text from a queue,
#       2) Generates TTS audio (with gTTS),
#       3) Streams the audio in chunks to an Audio2Face instance via gRPC.
#     """
#
#     # Signals to notify the outside world about results or errors
#     ttsFinished = Signal(str)   # Emitted when streaming to A2F completes successfully
#     ttsError = Signal(str)      # Emitted if any error occurs
#
#     def __init__(
#         self,
#         url="localhost:50051",
#         instance_name="/World/audio2face/PlayerStreaming",
#         chunk_duration=0.05,
#         block_until_playback_is_finished=True,
#         parent=None
#     ):
#         """
#         :param url: The gRPC server URL for Audio2Face, e.g. 'localhost:50051'
#         :param instance_name: The prim path of the Audio2Face Streaming Audio Player
#         :param chunk_duration: Approx duration (in seconds) of each audio chunk
#         :param block_until_playback_is_finished: Whether we block until playback finishes
#         """
#         super().__init__(parent)
#
#         self.url = url
#         self.instance_name = instance_name
#         self.chunk_duration = chunk_duration
#         self.block_until_playback_is_finished = block_until_playback_is_finished
#
#         self.request_queue = Queue()
#         self.should_exit = False
#         self.is_processing = False
#
#     def run(self):
#         """
#         Main thread loop:
#         Continuously checks for new text requests in the queue and processes them.
#         """
#         while not self.should_exit:
#             if self.is_processing:
#                 # Busy: let it finish
#                 self.msleep(100)
#                 continue
#
#             if self.request_queue.empty():
#                 # No new requests
#                 self.msleep(100)
#                 continue
#
#             # Get text from the queue
#             text = self.request_queue.get()
#             self.is_processing = True
#             try:
#                 self._process_text_to_a2f(text)
#             except Exception as e:
#                 self.ttsError.emit(str(e))
#             finally:
#                 self.is_processing = False
#
#     @Slot(str)
#     def add_request(self, text: str):
#         """
#         Add a new TTS request to the queue.
#         :param text: The text to synthesize and stream to Audio2Face.
#         """
#         if self.should_exit:
#             return
#         self.request_queue.put(text)
#
#     def stop(self):
#         """
#         Signal the thread to exit and clear any pending requests.
#         """
#         self.should_exit = True
#         with self.request_queue.mutex:
#             self.request_queue.queue.clear()
#
#     def _process_text_to_a2f(self, text: str):
#         """
#         1) Generate TTS in-memory (MP3)
#         2) Convert MP3 -> PCM (WAV) in memory
#         3) Stream PCM data to Audio2Face via gRPC
#         """
#
#         # --- 1) Generate TTS audio as MP3 in memory
#         mp3_buffer = io.BytesIO()
#         tts = gTTS(text=text, lang='en')
#         tts.write_to_fp(mp3_buffer)
#         mp3_buffer.seek(0)
#
#         # --- 2) Convert MP3 to raw float32 PCM data
#         audio_seg = AudioSegment.from_file(mp3_buffer, format="mp3")
#         wav_buffer = io.BytesIO()
#         audio_seg.export(wav_buffer, format='wav')
#         wav_buffer.seek(0)
#
#         # Read raw samples (float32) using soundfile
#         data, samplerate = soundfile.read(wav_buffer, dtype='float32')
#         # If stereo, average to mono (Audio2Face only accepts mono)
#         if len(data.shape) > 1:
#             data = np.mean(data, axis=1)
#
#         # --- 3) Stream audio data to Audio2Face
#         self._push_audio_track_stream(data, samplerate)
#
#     def _push_audio_track_stream(self, audio_data: np.ndarray, samplerate: int):
#         """
#         Emulate your push_audio_track_stream() function:
#          - Create a generator of PushAudioStreamRequest
#          - Connect and call stub.PushAudioStream(...)
#         """
#         # Determine how many samples per chunk
#         chunk_size = int(samplerate * self.chunk_duration)
#
#         with grpc.insecure_channel(self.url) as channel:
#             stub = audio2face_pb2_grpc.Audio2FaceStub(channel)
#
#             def make_generator():
#                 # 1) Start marker message (no audio data yet)
#                 start_marker = audio2face_pb2.PushAudioRequestStart(
#                     samplerate=samplerate,
#                     instance_name=self.instance_name,
#                     block_until_playback_is_finished=self.block_until_playback_is_finished,
#                 )
#                 yield audio2face_pb2.PushAudioStreamRequest(start_marker=start_marker)
#
#                 # 2) Stream out the PCM data in chunks
#                 idx = 0
#                 while idx < len(audio_data):
#                     chunk = audio_data[idx : idx + chunk_size]
#                     idx += chunk_size
#
#                     # Convert chunk to bytes (float32)
#                     chunk_bytes = chunk.astype(np.float32).tobytes()
#                     yield audio2face_pb2.PushAudioStreamRequest(audio_data=chunk_bytes)
#
#                     # This sleep emulates a "realtime" feed. Tweak or remove as needed.
#                     time.sleep(0.01)
#
#             # Actually do the streaming
#             request_generator = make_generator()
#             response = stub.PushAudioStream(request_generator)
#
#         if response.success:
#             self.ttsFinished.emit(f"Successfully pushed TTS audio to {self.instance_name}")
#         else:
#             raise RuntimeError(f"Audio2Face streaming error: {response.message}")
