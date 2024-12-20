import sys
from openai import  OpenAI, OpenAIError
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from ui_form import Ui_MainWindow  # Assuming the UI file is converted to a Python file named `ui_form.py`
import os
from PySide6.QtCore import QFile, QIODevice
from pathlib import Path
from PySide6.QtGui import QFont
class MainWindow(QMainWindow):
    # macros
    API_MESSAGE_DEFAULT = "Enter here or set as OPENAI_API_KEY variable"
    API_MESSAGE_FOUND_ENV = "Found it in env variables"
    API_MESSAGE_MISSING = "lease enter your key here or set OPENAI_API_KEY as an environment variable."
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        #self.apply_stylesheet()
        #self.apply_stylesheet_file()
        self.stylesheets_folder = Path(__file__).parent / "stylesheets"
        self.setup_theme_selection()



        # Initialize OpenAI settings
        #self.API_MESSAGE = "Enter here or set as OPENAI_API_KEY variable"
        self.api_key = self.API_MESSAGE_DEFAULT
        self.context = [{"role": "system", "content": "You are a helpful assistant."}]
        self.models = ["gpt-4o-mini", "gpt-3.5-turbo"]  # Add more models as required

        # Populate model combo box
        self.ui.llmMBOX.addItems(self.models)
        self.ui.llmMBOX.setCurrentText("gpt-4o-mini")

        # Set default API key placeholder
        self.ui.openaiAPIKey.setText(self.api_key)
        self.ui.systemPromptEdit.setText("You are a helpful assistant")
        self.system_prompt = None
        self.context = None

        # Hide chat-related widgets initially
        self.ui.groupBoxChat.hide()
        #self.ui.contextTextBrowser.hide()

        # Connect buttons
        self.ui.testConnectionOpenAI.clicked.connect(self.test_connection)
        self.ui.resetDefaultsOpenAI.clicked.connect(self.reset_defaults)
        self.ui.resetContextOpenAI.clicked.connect(self.reset_context)
        self.ui.sendUserInputOpenAI.clicked.connect(self.send_user_input)
        self.ui.chatModeOpenAI.stateChanged.connect(self.toggle_chat_mode)

    def setup_theme_selection(self):
        """
        Setup theme selection combobox and populate it with available stylesheets.
        """
        self.ui.themeComboBox.clear()
        themes = self.get_available_themes()
        self.ui.themeComboBox.addItems(themes)

        # Connect the combo box selection event to apply the selected theme
        self.ui.themeComboBox.currentIndexChanged.connect(self.apply_selected_theme)

        # Apply the default or first theme
        if themes:
            self.apply_stylesheet_file(themes[0])

    def get_available_themes(self):
        """
        Get a list of available themes (QSS files) from the stylesheets folder.
        """
        if self.stylesheets_folder.exists():
            return [f.name for f in self.stylesheets_folder.glob("*.qss")]
        return []

    def apply_stylesheet_file(self, theme_name):
        """
        Apply the selected stylesheet.
        """
        stylesheet_path = self.stylesheets_folder / theme_name

        if stylesheet_path.exists():
            try:
                with stylesheet_path.open("r", encoding="utf-8") as file:
                    stylesheet = file.read()
                    self.setStyleSheet(stylesheet)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to apply theme {theme_name}. Error: {e}")
        else:
            QMessageBox.warning(self, "Error", f"Stylesheet file not found: {stylesheet_path}")

    def apply_selected_theme(self):
        """
        Apply the theme selected in the combo box.
        """
        selected_theme = self.ui.themeComboBox.currentText()
        self.apply_stylesheet_file(selected_theme)

    def initialise_openai(self):
        self.api_key = self.ui.openaiAPIKey.text().strip()

        if not self.api_key or self.api_key in [self.API_MESSAGE_DEFAULT, self.API_MESSAGE_FOUND_ENV]:
            env_api_key = os.getenv('OPENAI_API_KEY')
            if env_api_key:
                self.api_key = env_api_key
                self.ui.openaiAPIKey.setText(self.API_MESSAGE_FOUND_ENV)
            else:
                QMessageBox.warning(self, "API Key Missing", self.API_MESSAGE_MISSING)
                return

        self.openai_client = OpenAI(api_key=self.api_key)


        if self.context is None:
            self.system_prompt = self.ui.systemPromptEdit.toPlainText().strip()
            self.context = [{"role": "system", "content": self.system_prompt}]

    def test_connection(self):
        """
        Test the connection to OpenAI using the provided API key.
        """
        self.initialise_openai()

        model = self.ui.llmMBOX.currentText()
        try:

            # Test connection with a simple "Hello"
            self.context.append({"role": "user", "content": "Hello"})
            response = self.openai_client.chat.completions.create(
                model=model,
                messages= self.context,
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
        #self.api_key = os.getenv('OPENAI_API_KEY') or "enter your api"

        #self.ui.systemPromptEdit.setText("You are a helpful assistant")
        #self.context = [{"role": "system", "content": self.system_prompt}]
        self.ui.temperatureOpenAI.setValue(70)
        self.ui.maxTokenOpenAI.setValue(1024)
        self.ui.contextBrowserOpenAI.clear()
        self.ui.llmMBOX.setCurrentText("gpt-4o-mini")
        self.context = [{"role": "system", "content": self.system_prompt}]

        QMessageBox.information(self, "Defaults Reset", "All settings have been reset to defaults.")

    def reset_context(self):
        """
        Reset the conversation context.
        """
        if self.system_prompt is None:
            self.initialise_openai()
        else:
            self.context = [{"role": "system", "content": self.system_prompt}]
            self.ui.contextBrowserOpenAI.clear()
        QMessageBox.information(self, "Context Reset", "Conversation context has been reset.")

    def toggle_chat_mode(self, state):
        """
        Toggle chat mode visibility.
        """
        if state == 2:  # Checkbox checked
            self.ui.groupBoxChat.show()
        else:
            self.ui.groupBoxChat.hide()


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
        self.initialise_openai()
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
