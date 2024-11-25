import time
import logging
import speech_recognition as sr
import threading

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


def listen_in_background(audio_queue, stop_event, language, sample_rate, noise_reduction, sensitivity):
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
