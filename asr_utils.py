import time
import logging
import speech_recognition as sr
import threading
import sounddevice as sd
from file_utils import download_model_if_not_exists
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import audio
AudioClassifier = mp.tasks.audio.AudioClassifier
AudioClassifierOptions = mp.tasks.audio.AudioClassifierOptions
AudioClassifierResult = mp.tasks.audio.AudioClassifierResult
AudioRunningMode = mp.tasks.audio.RunningMode
BaseOptions = mp.tasks.BaseOptions
AudioData = mp.tasks.components.containers.AudioData
import numpy as np
# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def populate_microphone_list(combo_box):
    """
    Populates the given QComboBox with the available microphone options.

    Parameters:
        combo_box (QComboBox): The dropdown to populate with microphone names.
    """
    try:
        # Get the list of available microphone names
        microphone_list = sr.Microphone.list_microphone_names()

        # Clear the combo box in case it's already populated
        combo_box.clear()

        # Add each microphone to the combo box
        for index, mic_name in enumerate(microphone_list):
            combo_box.addItem(f"{index}: {mic_name}")

        if not microphone_list:
            combo_box.addItem("No microphones found")
    except Exception as e:
        combo_box.addItem("Error detecting microphones")
        logger.error(f"Error: {e}")


def listen_in_background_with_sr(audio_queue, stop_event, language, sample_rate, noise_reduction, sensitivity):
    """
    Listens to the microphone in the background and puts audio data into the queue.

    Parameters:
        audio_queue (Queue): Queue to store the captured audio data.
        stop_event (threading.Event): Event to signal the thread to stop listening.
        language (str): Language code for recognition.
        sample_rate (int): Microphone sample rate.
        noise_reduction (str): Noise reduction option ('Enabled' or 'Disabled').
        sensitivity (str): Sensitivity level ('Low', 'Medium', 'High').
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone(sample_rate=sample_rate)

    # Set sensitivity
    if sensitivity == "Low":
        recognizer.energy_threshold = 300
    elif sensitivity == "Medium":
        recognizer.energy_threshold = 400
    elif sensitivity == "High":
        recognizer.energy_threshold = 500

    logger.info("Listening thread started")
    while not stop_event.is_set():
        try:
            with microphone as source:
                if noise_reduction == "Enabled":
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Microphone listening...")
                audio = recognizer.listen(source)
                audio_queue.put((audio, language))  # Pass audio with language code
        except Exception as e:
            logger.error(f"Error while listening: {e}")
            time.sleep(0.1)

        # Check for termination signal in the queue
        if not audio_queue.empty() and audio_queue.get() is None:
            break
    logger.info("Listening thread stopped")



def listen_in_background(audio_queue, stop_event, language, sample_rate, noise_reduction, sensitivity):
    """
    Streams audio data in real-time and pushes it into the audio queue using MediaPipe's AUDIO_STREAM mode.
    """
    model_url = "https://storage.googleapis.com/mediapipe-models/audio_classifier/yamnet/float32/1/yamnet.tflite"
    model_file_name = "classifier.tflite"
    download_model_if_not_exists(model_url, model_file_name)

    # Define the callback to handle classification results
    def result_callback(result, timestamp_ms):
        for classification in result.classifications:
            top_category = classification.categories[0]
            if top_category.category_name == "Speech" and top_category.score > 0.5:
                print(f"Speech detected at {timestamp_ms} ms with confidence {top_category.score:.2f}")
                audio_queue.put("Speech detected")  # Optionally, push some info to the queue

    # Configure MediaPipe AudioClassifier in AUDIO_STREAM mode
    options = AudioClassifierOptions(
        base_options=BaseOptions(model_asset_path=model_file_name),
        running_mode=AudioRunningMode.AUDIO_STREAM,
        max_results=5,
        result_callback=result_callback,  # Specify the callback here
    )

    # Create the classifier
    with AudioClassifier.create_from_options(options) as classifier:
        # Define the audio callback
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio stream status: {status}")

            # Normalize audio data
            buffer = indata.flatten()
            normalized_buffer = buffer.astype(float) / np.iinfo(np.int16).max

            # Create AudioData
            audio_data = AudioData.create_from_array(normalized_buffer, sample_rate)

            # Classify asynchronously
            classifier.classify_async(audio_data, int(time.currentTime * 1000))

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

def recognize_speech(audio_queue, response_queue, stop_event, recognizer_type, api_keys=None):
    """
    Processes audio and recognizes speech using the selected recognizer.
    """
    recognizer = sr.Recognizer()

    logger.info(f"Recognition thread started using {recognizer_type}")
    while not stop_event.is_set():
        try:
            if not audio_queue.empty():
                audio, language = audio_queue.get()

                if recognizer_type == "Google Web Speech API":
                    text = recognizer.recognize_google(audio, language=language)
                elif recognizer_type == "Google Cloud Speech API":
                    text = recognizer.recognize_google_cloud(
                        audio, credentials_json=api_keys.get("google_cloud")
                    )
                elif recognizer_type == "Whisper":
                    try:
                        result = recognizer.recognize_whisper(audio)
                        print(f"Whisper ASR recognized: {result}")
                    except sr.UnknownValueError:
                        print("Whisper ASR could not understand the audio.")
                    except sr.RequestError as e:
                        print(f"Whisper ASR request failed: {e}")
                elif recognizer_type == "Whisper API":
                    text = recognizer.recognize_whisper_api(audio, api_key=api_keys.get("openai"))
                else:
                    raise ValueError(f"Unsupported recognizer: {recognizer_type}")

                logger.info(f"Recognized speech: {text}")
                response_queue.put(text)
        except sr.UnknownValueError:
            logger.warning(f"{recognizer_type} could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Request error from {recognizer_type}: {e}")
    logger.info("Recognition thread stopped")
