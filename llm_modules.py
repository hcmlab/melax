from PySide6.QtCore import QMetaObject, QObject
from PySide6.QtCore import QThread, Signal, Slot
from openai import OpenAI, OpenAIError
from PySide6.QtCore import QMetaObject, Qt
from queue import Queue
import openai
from ollama import chat
class OpenAIWorker(QObject):
    responseReady = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, api_key, parent=None):
        super(OpenAIWorker, self).__init__(parent)
        self.api_key = api_key
        openai.api_key = self.api_key
        self.openai_client = OpenAI(api_key=self.api_key)
        self.request_queue = Queue()
        self.is_processing = False
        self.should_exit = False  # Shutdown flag

    @Slot()
    def process_queue(self):
        if self.is_processing or self.should_exit:
            return
        if self.request_queue.empty():
            return

        self.is_processing = True
        model, context, max_tokens, temperature = self.request_queue.get()
        self._process_request(model, context, max_tokens, temperature)

    def _process_request(self, model, context, max_tokens, temperature):
        try:
            if self.should_exit:
                return
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=context,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=10  # Timeout in seconds
            )
            if self.should_exit:
                return
            assistant_message = response.choices[0].message.content.strip()
            self.responseReady.emit(assistant_message)
        except Exception as e:
            if not self.should_exit:
                self.errorOccurred.emit(str(e))
        finally:
            self.is_processing = False
            QMetaObject.invokeMethod(self, "process_queue", Qt.QueuedConnection)

    @Slot(str, list, int, float)
    def add_request(self, model, context, max_tokens, temperature):
        if self.should_exit:
            return
        self.request_queue.put((model, context, max_tokens, temperature))
        QMetaObject.invokeMethod(self, "process_queue", Qt.QueuedConnection)

    def stop(self):
        self.should_exit = True
        # Clear the request queue
        with self.request_queue.mutex:
            self.request_queue.queue.clear()



class OllamaWorker(QObject):
    responseReady = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, model_name="llama3.2", parent=None):
        """
        Initializes the OllamaWorker.

        Args:
            model_name (str): Name of the Llama model.
        """
        super(OllamaWorker, self).__init__(parent)
        self.model_name = model_name
        self.request_queue = Queue()
        self.is_processing = False
        self.should_exit = False  # Shutdown flag

    @Slot()
    def process_queue(self):
        """
        Processes the request queue.
        """
        if self.is_processing or self.should_exit:
            return
        if self.request_queue.empty():
            return

        self.is_processing = True
        messages, max_tokens, temperature = self.request_queue.get()
        self._process_request(messages, max_tokens, temperature)

    def _process_request(self, messages, max_tokens, temperature):
        """
        Processes a single request using Ollama's `chat`.

        Args:
            messages (list): List of message dictionaries (system, user, and assistant).
        """
        try:
            if self.should_exit:
                return

            # Stream assistant's response
            response_content = ""
            stream = chat(model=self.model_name,
                          messages=messages,
                          stream=True,
                          options={"temperature":temperature, "num_predict":max_tokens })

            for chunk in stream:
                response_content += chunk['message']['content']

            # Emit the final assistant message
            self.responseReady.emit(response_content)

        except Exception as e:
            if not self.should_exit:
                self.errorOccurred.emit(str(e))
        finally:
            self.is_processing = False
            QMetaObject.invokeMethod(self, "process_queue", Qt.QueuedConnection)

    @Slot(list, int, float)
    def add_request(self, messages, max_tokens, temperature):
        """
        Adds a request to the queue and triggers processing.

        Args:
            messages (list): List of message dictionaries (system, user, and assistant).
        """
        if self.should_exit:
            return
        self.request_queue.put((messages, max_tokens, temperature))
        QMetaObject.invokeMethod(self, "process_queue", Qt.QueuedConnection)

    def stop(self):
        """
        Stops the worker by clearing the queue and setting the exit flag.
        """
        self.should_exit = True
        with self.request_queue.mutex:
            self.request_queue.queue.clear()