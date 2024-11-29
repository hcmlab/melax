import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt
import sounddevice as sd
def list_microphones():
    devices = sd.query_devices()
    input_devices = []
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:  # Check if the device supports input
            input_devices.append((idx, device['name']))
    return input_devices


class TranscriptionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Audio Transcription Panel")
        self.setGeometry(100, 100, 500, 400)

        # Main Layout
        self.main_layout = QVBoxLayout()

        # Audio Source Selection
        self.ui.microphoneMBox.clear()
        microphones = list_microphones()
        for idx, name in microphones:
            self.ui.microphoneMBox.addItem(name, userData=idx)
        self.audio_label = QLabel("Select Audio Source:")
        self.audio_source_dropdown = QComboBox()
        self.audio_source_dropdown.addItems(["Microphone 1", "Microphone 2"])  # Placeholder

        # ASR Module Selection
        self.asr_label = QLabel("Select ASR Module:")
        self.asr_dropdown = QComboBox()
        self.asr_dropdown.addItems(["Google API", "Whisper"])

        # ASR Module Configuration (Dynamic)
        self.config_layout = QVBoxLayout()
        self.google_api_key_label = QLabel("Enter Google API Key:")
        self.google_api_key_input = QLineEdit()
        self.google_api_key_input.setPlaceholderText("API Key")

        self.whisper_model_label = QLabel("Select Whisper Model:")
        self.whisper_model_dropdown = QComboBox()
        self.whisper_model_dropdown.addItems(["base", "small", "medium", "large"])

        self.device_label = QLabel("Select Device:")
        self.device_dropdown = QComboBox()
        self.device_dropdown.addItems(["CPU", "CUDA"])

        # Add initial elements (Google API by default)
        self.update_config_layout("Google API")

        # ASR Module Change Event
        self.asr_dropdown.currentTextChanged.connect(self.update_config_layout)

        # Buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.quit_button = QPushButton("Quit")
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.stop_button)
        self.button_layout.addWidget(self.quit_button)

        # Add widgets to main layout
        self.main_layout.addWidget(self.audio_label)
        self.main_layout.addWidget(self.audio_source_dropdown)
        self.main_layout.addWidget(self.asr_label)
        self.main_layout.addWidget(self.asr_dropdown)
        self.main_layout.addLayout(self.config_layout)
        self.main_layout.addLayout(self.button_layout)

        # Set main layout
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def update_config_layout(self, asr_module):
        """Update the ASR Module Configuration section dynamically."""
        # Clear current layout
        for i in reversed(range(self.config_layout.count())):
            widget = self.config_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Add relevant widgets
        if asr_module == "Google API":
            self.config_layout.addWidget(self.google_api_key_label)
            self.config_layout.addWidget(self.google_api_key_input)
        elif asr_module == "Whisper":
            self.config_layout.addWidget(self.whisper_model_label)
            self.config_layout.addWidget(self.whisper_model_dropdown)
            self.config_layout.addWidget(self.device_label)
            self.config_layout.addWidget(self.device_dropdown)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscriptionApp()
    window.show()
    sys.exit(app.exec())
