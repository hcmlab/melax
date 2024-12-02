import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue


class ThreadSafeLogger:
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
