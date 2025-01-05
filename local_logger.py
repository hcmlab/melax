import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker
import datetime
import threading

class ThreadSafeLogger(QObject):
    """
    A thread-safe logger that writes to a file *and* emits a signal
    so the GUI can show logs in real time.
    """
    log_emitted = Signal(str)  # <-- A signal that carries the log text

    def __init__(self, filename="app.log"):
        super().__init__()
        self.filename = filename
        self.mutex = QMutex()

    def _write_to_file(self, message: str):
        with QMutexLocker(self.mutex):
            with open(self.filename, "a", encoding="utf-8") as file:
                file.write(message + "\n")

    def log_info(self, message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[INFO] {timestamp} - {message}"
        self._write_to_file(formatted)
        self.log_emitted.emit(formatted)  # <-- Emit the signal

    def log_error(self, message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[ERROR] {timestamp} - {message}"
        self._write_to_file(formatted)
        self.log_emitted.emit(formatted)

    def log_debug(self, message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[DEBUG] {timestamp} - {message}"
        self._write_to_file(formatted)
        self.log_emitted.emit(formatted)


class ThreadSafeLoggerNoQt:
    def __init__(self, log_file="application.log"):
        self.log_queue = Queue()
        self.logger = logging.getLogger("ASRLogger")
        self.logger.setLevel(logging.DEBUG)

        # File Handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Log Format
        formatter = logging.Formatter(
            "%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Queue Handler and Listener
        queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(queue_handler)
        self.listener = QueueListener(self.log_queue, file_handler, console_handler)

        # Start Listener
        self.listener.start()

    def log_info(self, message):
        self.logger.info(message)

    def log_debug(self, message):
        self.logger.debug(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)

    def shutdown(self):
        self.listener.stop()
