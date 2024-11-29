import mediapipe as mp
import numpy as np
import sounddevice as sd
from mediapipe.tasks.python import audio
from mediapipe.tasks.python.audio import AudioClassifier, AudioClassifierOptions
from mediapipe.tasks.python.components.containers import AudioData
from mediapipe.tasks.python.core.base_options import BaseOptions

RunningMode = mp.tasks.audio.RunningMode
import threading
import time

def print_result(result, timestamp_ms):
    """
    Callback function to process classification results.
    """
    print(f"AudioClassifierResult - Timestamp: {timestamp_ms} ms")
    for i, classification_result in enumerate(result.classifications):
        print(f"  ClassificationResult #{i}:")
        for j, category in enumerate(classification_result.categories):
            print(f"    Category #{j}:")
            print(f"      Name: {category.category_name}")
            print(f"      Score: {category.score:.2f}")
            print(f"      Index: {category.index}")

def run_audio_streaming(stop_event, sample_rate=16000):
    """
    Streams live audio from the microphone and performs classification
    using MediaPipe's AudioClassifier in AUDIO_STREAM mode.
    """
    # Path to the model file
    model_path = "classifier.tflite"

    # Define the callback to handle classification results
    def result_callback(result, timestamp_ms):
        for classification in result.classifications:
            top_category = classification.categories[0]
            if top_category.category_name == "Speech" and top_category.score > 0.5:
                print(f"Speech detected at {timestamp_ms} ms with confidence {top_category.score:.2f}")

    # Configure MediaPipe AudioClassifier in AUDIO_STREAM mode
    options = AudioClassifierOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=RunningMode.AUDIO_STREAM,
        max_results=5,
        result_callback=result_callback,  # Specify the callback here
    )

    # Create the classifier
    with AudioClassifier.create_from_options(options) as classifier:
        # Track timestamp based on audio samples
        start_time = time.time()
        total_samples = 0

        def audio_callback(indata, frames, time_info, status):
            nonlocal total_samples
            if status:
                print(f"Audio stream status: {status}")

            # Normalize audio data
            buffer = indata.flatten()
            normalized_buffer = buffer.astype(float) / np.iinfo(np.int16).max

            # Create AudioData
            audio_data = AudioData.create_from_array(normalized_buffer, sample_rate)

            # Calculate timestamp based on the number of samples processed
            timestamp_ms = int(start_time * 1000 + (total_samples / sample_rate) * 1000)
            total_samples += frames  # Update total samples processed

            # Classify asynchronously
            classifier.classify_async(audio_data, timestamp_ms)

        # Initialize and start the audio stream
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            callback=audio_callback,
        )

        stream.start()
        print("Audio streaming started.")
        try:
            while not stop_event.is_set():
                threading.Event().wait(0.1)  # Keep the thread alive
        except KeyboardInterrupt:
            print("Stopping audio streaming...")
        finally:
            stream.stop()
            stream.close()
            print("Audio streaming stopped.")

if __name__ == "__main__":
    # Use a threading event to manage stopping the stream
    stop_event = threading.Event()

    # Run the audio streaming in the main thread
    run_audio_streaming(stop_event)
