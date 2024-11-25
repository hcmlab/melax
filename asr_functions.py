# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
import speech_recognition as sr
import time
import logging

# Global flag for listening state
is_listening = False
# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define global variables for recognizer and microphone
recognizer = sr.Recognizer()
microphone = sr.Microphone()

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
        print(f"Error: {e}")

# Listening in the background
def listen_in_background(audio_queue):
    global is_listening
    logger.info("Listening thread started")
    while True:
        with microphone as source:
            if is_listening:
                logger.info("Microphone listening...")
                audio = recognizer.listen(source)
                audio_queue.put(audio)
            else:
                time.sleep(0.1)

# Recognize speech from the audio queue
def recognize_speech(audio_queue, response_queue):
    global is_listening
    logger.info("Recognition thread started")
    while True:
        audio = audio_queue.get()
        if is_listening:
            try:
                logger.info("Recognizing speech...")
                text = recognizer.recognize_google(audio)
                logger.info(f"Recognized speech: {text}")
                response_queue.put(text)
            except sr.UnknownValueError:
                logger.warning("Failed to understand audio")
            except sr.RequestError as e:
                logger.error(f"Recognition service error: {e}")
