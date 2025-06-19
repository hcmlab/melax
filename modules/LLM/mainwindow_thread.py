from PySide6.QtCore import QObject, QThread, Signal
from openai import OpenAI, OpenAIError

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QThread, Slot
from ui_form import Ui_MainWindow
import os, sys



class OpenAIWorker(QObject):
    responseReady = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, api_key):
        super(OpenAIWorker, self).__init__()
        self.api_key = api_key
        self.openai_client = OpenAI(api_key=self.api_key)
        self.is_running = True

    def process_request(self, model, context, max_tokens, temperature):
        if not self.is_running:
            return

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=context,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            assistant_message = response.choices[0].message.content.strip()
            self.responseReady.emit(assistant_message)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    def stop(self):
        self.is_running = False
class MainWindow(QMainWindow):
    API_MESSAGE_DEFAULT = "Enter here or set as OPENAI_API_KEY variable"
    API_MESSAGE_FOUND_ENV = "Found it in env variables"
    API_MESSAGE_MISSING = "Please enter your key here or set OPENAI_API_KEY as an environment variable."

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize variables
        self.api_key = self.API_MESSAGE_DEFAULT
        self.models = ["gpt-4o-mini", "gpt-3.5-turbo"]

        # Populate model combo box
        self.ui.llmMBOX.addItems(self.models)
        self.ui.llmMBOX.setCurrentText("gpt-4o-mini")

        # Set default API key placeholder
        self.ui.openaiAPIKey.setText(self.api_key)
        self.ui.systemPromptEdit.setText("You are a helpful assistant")

        # Initialize OpenAI worker and thread
        self.openai_thread = QThread()
        self.openai_worker = OpenAIWorker(self.get_api_key())
        self.openai_worker.moveToThread(self.openai_thread)

        # Connect signals and slots
        self.ui.testConnectionOpenAI.clicked.connect(self.test_connection)
        self.ui.sendUserInputOpenAI.clicked.connect(self.send_user_input)
        self.ui.resetContextOpenAI.clicked.connect(self.reset_context)
        self.openai_worker.responseReady.connect(self.handle_response)
        self.openai_worker.errorOccurred.connect(self.handle_error)

        # Start the thread
        self.openai_thread.start()

    def get_api_key(self):
        self.api_key = self.ui.openaiAPIKey.text().strip()

        if not self.api_key or self.api_key in [self.API_MESSAGE_DEFAULT, self.API_MESSAGE_FOUND_ENV]:
            env_api_key = os.getenv('OPENAI_API_KEY')
            if env_api_key:
                self.api_key = env_api_key
                self.ui.openaiAPIKey.setText(self.API_MESSAGE_FOUND_ENV)
            else:
                QMessageBox.warning(self, "API Key Missing", self.API_MESSAGE_MISSING)
        return self.api_key

    @Slot()
    def send_user_input(self):
        user_input = self.ui.userInputOpenAI.toPlainText().strip()
        if not user_input:
            QMessageBox.warning(self, "Input Missing", "Please enter a message to send.")
            return

        # Prepare OpenAI request parameters
        model = self.ui.llmMBOX.currentText()
        temperature = self.ui.temperatureOpenAI.value() / 100.0
        max_tokens = self.ui.maxTokenOpenAI.value()
        context = [
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input},
        ]

        # Send request to the worker
        self.ui.userInputOpenAI.clear()
        self.openai_worker.process_request(model, context, max_tokens, temperature)

    @Slot()
    def test_connection(self):
        model = "gpt-3.5-turbo"
        context = [
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ]
        max_tokens = 10
        temperature = 0.7

        self.openai_worker.process_request(model, context, max_tokens, temperature)

    @Slot()
    def reset_context(self):
        self.ui.contextBrowserOpenAI.clear()

    @Slot(str)
    def handle_response(self, message):
        self.ui.contextBrowserOpenAI.append(f"Assistant: {message}")

    @Slot(str)
    def handle_error(self, error_message):
        QMessageBox.critical(self, "OpenAI Error", f"Error: {error_message}")

    def closeEvent(self, event):
        # Stop the OpenAI worker thread
        self.openai_worker.stop()
        self.openai_thread.quit()
        self.openai_thread.wait()
        super(MainWindow, self).closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

