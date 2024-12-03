import sys
from openai import  OpenAI, OpenAIError
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from ui_form import Ui_MainWindow  # Assuming the UI file is converted to a Python file named `ui_form.py`

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize OpenAI settings
        self.api_key = "enter your api"
        self.context = [{"role": "system", "content": "You are a helpful assistant."}]
        self.models = ["gpt-4o-mini", "gpt-3.5-turbo"]  # Add more models as required

        # Populate model combo box
        self.ui.llmMBOX.addItems(self.models)
        self.ui.llmMBOX.setCurrentText("gpt-4o-mini")

        # Set default API key placeholder
        self.ui.openaiAPIKey.setText(self.api_key)

        # Hide chat-related widgets initially
        self.ui.groupBoxChat.hide()
        #self.ui.contextTextBrowser.hide()

        # Connect buttons
        self.ui.testConnectionOpenAI.clicked.connect(self.test_connection)
        self.ui.resetDefaultsOpenAI.clicked.connect(self.reset_defaults)
        self.ui.resetContextOpenAI.clicked.connect(self.reset_context)
        self.ui.sendUserInputOpenAI.clicked.connect(self.send_user_input)
        self.ui.chatModeOpenAI.stateChanged.connect(self.toggle_chat_mode)

    def test_connection(self):
        """
        Test the connection to OpenAI using the provided API key.
        """
        self.api_key = self.ui.openaiAPIKey.text().strip()

        if not self.api_key or self.api_key == "enter your api":
            QMessageBox.warning(self, "API Key Missing", "Please enter your OpenAI API key.")
            return


        model = self.ui.llmMBOX.currentText()
        system_prompt = self.ui.systemPromptEdit.toPlainText().strip() or "You are a helpful assistant."

        try:
            self.openai_client = OpenAI(api_key=self.api_key)
            # Test connection with a simple "Hello"
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            assistant_message = response.choices[0].message.content.strip()
            QMessageBox.information(self, "Connection Successful", f"OpenAI Replied: {assistant_message}")
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to OpenAI. Error: {e}")

    def reset_defaults(self):
        """
        Reset all OpenAI-related settings to their default values.
        """
        self.api_key = "enter your api"
        self.context = [{"role": "system", "content": "You are a helpful assistant."}]
        self.ui.openaiAPIKey.setText(self.api_key)
        self.ui.systemPromptEdit.clear()
        self.ui.temperatureOpenAI.setValue(70)
        self.ui.maxTokenOpenAI.setValue(1024)
        self.ui.contextBrowserOpenAI.clear()
        self.ui.llmMBOX.setCurrentText("gpt-4o-mini")
        QMessageBox.information(self, "Defaults Reset", "All settings have been reset to defaults.")

    def reset_context(self):
        """
        Reset the conversation context.
        """
        self.context = [{"role": "system", "content": "You are a helpful assistant."}]
        self.ui.contextBrowserOpenAI.clear()
        QMessageBox.information(self, "Context Reset", "Conversation context has been reset.")

    def toggle_chat_mode(self, state):
        """
        Toggle chat mode visibility.
        """
        if state == 2:  # Checkbox checked
            self.ui.groupBoxChat.show()
            #self.ui.contextTextBrowser.show()
        else:
            self.ui.groupBoxChat.hide()
            #self.ui.contextTextBrowser.hide()

    def update_context_browser(self):
        """
        Update the context text browser with the current conversation history.
        """
        formatted_context = "\n".join(
            f"{entry['role'].capitalize()}: {entry['content']}" for entry in self.context
        )
        self.ui.contextBrowserOpenAI.setText(formatted_context)

    def send_user_input(self):
        """
        Handle user input, send it to OpenAI, and display the response.
        """
        user_input = self.ui.userInputOpenAI.toPlainText().strip()
        if not user_input:
            QMessageBox.warning(self, "Input Missing", "Please enter a message to send.")
            return

        # Add user input to context
        self.context.append({"role": "user", "content": user_input})
        self.ui.userInputOpenAI.clear()
        self.update_context_browser()

        model = self.ui.llmMBOX.currentText()
        temperature = self.ui.temperatureOpenAI.value() / 100.0
        max_tokens = self.ui.maxTokenOpenAI.value()

        try:
            # Send to OpenAI
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=self.context,
                max_tokens=max_tokens,
                temperature=temperature
            )
            assistant_message = response.choices[0].message.content.strip()
            self.context.append({"role": "assistant", "content": assistant_message})
            self.update_context_browser()
        except Exception as e:
            QMessageBox.critical(self, "OpenAI Error", f"Failed to get a response. Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
