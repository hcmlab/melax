import unittest
from unittest.mock import patch, MagicMock
import speech_recognition as sr

class TestSpeechRecognition(unittest.TestCase):

    @patch("speech_recognition.Recognizer.recognize_google")
    @patch("speech_recognition.Recognizer.listen")
    def test_google_asr(self, mock_listen, mock_recognize_google):
        # Mock the audio input and recognition output
        mock_audio = MagicMock(name="AudioData")
        mock_listen.return_value = mock_audio
        mock_recognize_google.return_value = "hello world"

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
            result = recognizer.recognize_google(audio)

        # Assert that the Google ASR output matches the mock
        self.assertEqual(result, "hello world")
        print(f"Google ASR Test Passed: {result}")

    @patch("speech_recognition.Recognizer.recognize_whisper")
    @patch("speech_recognition.Recognizer.listen")
    def test_whisper_asr(self, mock_listen, mock_recognize_whisper):
        # Mock the audio input and recognition output
        mock_audio = MagicMock(name="AudioData")
        mock_listen.return_value = mock_audio
        mock_recognize_whisper.return_value = "test whisper recognition"

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
            result = recognizer.recognize_whisper(audio, language="english")

        # Assert that the Whisper ASR output matches the mock
        self.assertEqual(result, "test whisper recognition")
        print(f"Whisper ASR Test Passed: {result}")

if __name__ == "__main__":
    unittest.main()
