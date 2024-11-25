import speech_recognition as sr


def record_audio():
    """Records audio from the microphone."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise. Please wait...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Recording... Speak now.")
        try:
            audio = recognizer.listen(source, timeout=10)
            print("Recording complete.")
            return audio
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
            return None


def test_google_asr(audio):
    """Tests Google ASR."""
    recognizer = sr.Recognizer()
    try:
        result = recognizer.recognize_google(audio)
        print(f"Google ASR recognized: {result}")
    except sr.UnknownValueError:
        print("Google ASR could not understand the audio.")
    except sr.RequestError as e:
        print(f"Google ASR request failed: {e}")


def test_whisper_asr(audio):
    """Tests Whisper ASR."""
    recognizer = sr.Recognizer()
    try:
        result = recognizer.recognize_whisper(audio, language="english")
        print(f"Whisper ASR recognized: {result}")
    except sr.UnknownValueError:
        print("Whisper ASR could not understand the audio.")
    except sr.RequestError as e:
        print(f"Whisper ASR request failed: {e}")


if __name__ == "__main__":
    # Record audio from the microphone
    audio_data = record_audio()

    if audio_data is not None:
        # Run the recorded audio through both ASR methods
        print("\nTesting Google ASR...")
        test_google_asr(audio_data)

        print("\nTesting Whisper ASR...")
        test_whisper_asr(audio_data)
