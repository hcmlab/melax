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
    logger.info("Listening thread stopped")


def recognize_speech(audio_queue, response_queue, stop_event):
    """
    Processes audio from the audio queue and transcribes it into text.

    Parameters:
        audio_queue (Queue): Queue containing the audio data.
        response_queue (Queue): Queue to store the transcribed text.
        stop_event (threading.Event): Event to signal the thread to stop processing.
    """
    recognizer = sr.Recognizer()

    logger.info("Recognition thread started")
    while not stop_event.is_set():
        try:
            if not audio_queue.empty():
                audio, language = audio_queue.get()  # Retrieve audio and language
                logger.info("Recognizing speech...")
                text = recognizer.recognize_google(audio, language=language)
                logger.info(f"Recognized speech: {text}")
                response_queue.put(text)
        except sr.UnknownValueError:
            logger.warning("Failed to understand audio")
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during recognition: {e}")
    logger.info("Recognition thread stopped")
