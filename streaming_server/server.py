import os
import sys
import logging
from concurrent import futures

import grpc
import numpy as np
from grpc import _common, _server

# --------------------------------------------------------------------------------
# Custom logger setup (basic example)
# --------------------------------------------------------------------------------
logger = logging.getLogger("audio2face_server")
logger.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Format for log messages
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

# Attach handler to logger
logger.addHandler(ch)

# --------------------------------------------------------------------------------
# If needed during development for hot-reloading gRPC/protobuf, uncomment below:
# --------------------------------------------------------------------------------

# Use this only during development, this helps to hot-reload grpc/protobuf properly
# os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
# from google.protobuf.internal import api_implementation
# logger.warning(
#      "DEV MODE (turn it off in production): api_implementation.Type() == {}".format(api_implementation.Type())
#  )


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
from streaming_server.proto.old import audio2face_pb2_grpc, audio2face_pb2


class Audio2FaceServicer(audio2face_pb2_grpc.Audio2FaceServicer):
    def __init__(self, audio_start_callback, push_chunk_callback, audio_end_callback):
        self._audio_start_callback = audio_start_callback
        self._push_chunk_callback = push_chunk_callback
        self._audio_end_callback = audio_end_callback

    def PushAudio(self, request, context):
        instance_name = request.instance_name
        samplerate = request.samplerate
        block_until_playback_is_finished = request.block_until_playback_is_finished
        audio_data = np.frombuffer(request.audio_data, dtype=np.float32)

        logger.info(
            "PushAudio request: [instance_name = %s ; samplerate = %d ; data.shape = %s]",
            instance_name, samplerate, audio_data.shape
        )
        if self._audio_start_callback is not None:
            try:
                self._audio_start_callback(instance_name, samplerate)
            except RuntimeError as e:
                return audio2face_pb2.PushAudioResponse(success=False, message=str(e))
        if self._push_chunk_callback is not None:
            try:
                self._push_chunk_callback(instance_name, audio_data)
            except RuntimeError as e:
                return audio2face_pb2.PushAudioResponse(success=False, message=str(e))
        if self._audio_end_callback is not None:
            try:
                self._audio_end_callback(instance_name, block_until_playback_is_finished)
            except RuntimeError as e:
                return audio2face_pb2.PushAudioResponse(success=False, message=str(e))

        logger.info("PushAudio request -- DONE")
        return audio2face_pb2.PushAudioResponse(success=True, message="")

    def PushAudioStream(self, request_iterator, context):
        # The first item must have start_marker
        first_item = next(request_iterator)
        if not first_item.HasField("start_marker"):
            return audio2face_pb2.PushAudioResponse(
                success=False, message="First item in the request should contain start_marker"
            )
        instance_name = first_item.start_marker.instance_name
        samplerate = first_item.start_marker.samplerate
        block_until_playback_is_finished = first_item.start_marker.block_until_playback_is_finished

        logger.info(
            "PushAudioStream request: [instance_name = %s ; samplerate = %d]",
            instance_name, samplerate
        )

        if self._audio_start_callback is not None:
            try:
                self._audio_start_callback(instance_name, samplerate)
            except RuntimeError as e:
                return audio2face_pb2.PushAudioResponse(success=False, message=str(e))

        # Process the remaining audio chunks
        for item in request_iterator:
            audio_data = np.frombuffer(item.audio_data, dtype=np.float32)
            if self._push_chunk_callback is not None and instance_name is not None:
                try:
                    self._push_chunk_callback(instance_name, audio_data)
                except RuntimeError as e:
                    return audio2face_pb2.PushAudioResponse(success=False, message=str(e))

        if self._audio_end_callback is not None and instance_name is not None:
            try:
                self._audio_end_callback(instance_name, block_until_playback_is_finished)
            except RuntimeError as e:
                return audio2face_pb2.PushAudioResponse(success=False, message=str(e))

        logger.info("PushAudioStream request -- DONE")
        return audio2face_pb2.PushAudioResponse(success=True, message="")


class StreamingServer:
    def __init__(self):
        self._server = None
        self._max_workers = 10  # ADJUST
        self._port = "50051"  # ADJUST
        self._address = f"[::]:{self._port}"  # ADJUST

    def start(self, audio_start_callback, push_chunk_callback, audio_end_callback):
        logger.info("Starting StreamingServer on port %s", self._port)
        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=self._max_workers))
        audio2face_pb2_grpc.add_Audio2FaceServicer_to_server(
            Audio2FaceServicer(audio_start_callback, push_chunk_callback, audio_end_callback), self._server
        )
        success = _server._add_insecure_port(self._server._state, _common.encode(self._address))
        while success == 0:
            self._port = str(int(self._port) + 1)
            self._address = f"[::]:{self._port}"
            success = _server._add_insecure_port(self._server._state, _common.encode(self._address))
        self._server.start()
        logger.info("StreamingServer started on port %s", self._port)

    def shutdown(self):
        logger.info("Shutting down StreamingServer...")
        if self._server:
            self._server.stop(None)
            self._server = None
        logger.info("StreamingServer has been shut down.")

    def get_port(self):
        return self._port
