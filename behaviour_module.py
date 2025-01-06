import subprocess
import time
import sys
from PySide6.QtCore import QThread, Signal

class Audio2FaceHeadlessThread(QThread):
    """
    A QThread that runs audio2face_headless.bat, reads stdout in a loop,
    and emits log lines to the GUI.
    """

    log_line_received = Signal(str)

    def __init__(self, bat_path, parent=None):
        super().__init__(parent)
        self.bat_path = bat_path
        self._process = None
        self._stop_requested = False

    def run(self):
        """
        Launch the .bat file and continuously read its stdout until it ends or we stop it.
        """
        try:
            self._process = subprocess.Popen(
                [self.bat_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )

            # If something went wrong and we have no stdout, just return
            if not self._process or not self._process.stdout:
                self.log_line_received.emit("[Error] Could not start Audio2Face headless process.")
                return

            # Read lines until process ends or stop is requested
            for line in self._process.stdout:
                if self._stop_requested:
                    break
                # Emit the line to the main thread
                self.log_line_received.emit(line.rstrip("\n"))

            self.log_line_received.emit("Audio2Face headless server terminated.")
        except Exception as e:
            self.log_line_received.emit(f"[Error] Exception in run(): {str(e)}")
        finally:
            self._process = None

    def stop(self):
        """
        Stop the thread's loop and terminate the subprocess if still running.
        """
        self._stop_requested = True
        if self._process:
            self._process.terminate()
            self._process = None
        self.quit()
        self.wait()
