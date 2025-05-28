import socket
import threading
import time
from collections import deque

try:
    from lxml import etree

    print("AffectWorker running with lxml.etree")
except ImportError:
    import xml.etree.ElementTree as etree

    print("AffectWorker running with Python's xml.etree.ElementTree")


class AffectWorker:

    def __init__(self, ip='127.0.0.1', port='5006', samplerate_s=0.1, buffer_s=3):
        self.read_loop = None
        self.sock = None
        self.UDP_IP = ip
        self.UDP_PORT = port

        self.samplerate_s = samplerate_s
        self.buffer_s = buffer_s

        self.valence = 0.0
        self.arousal = 0.0
        self.dominance = 0.0

        self.valence_windowed = 0.0
        self.arousal_windowed = 0.0
        self.dominance_windowed = 0.0

        self.valence_buffer = deque(maxlen=int(self.buffer_s * (1.0/self.samplerate_s)))
        self.arousal_buffer = deque(maxlen=int(self.buffer_s * (1.0 / self.samplerate_s)))
        self.dominance_buffer = deque(maxlen=int(self.buffer_s * (1.0 / self.samplerate_s)))

        for i in range(0, int(self.buffer_s * (1.0 / self.samplerate_s))):
            self.valence_buffer.append(0.0)
            self.arousal_buffer.append(0.0)
            self.dominance_buffer.append(0.0)

    def bind(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, int(self.UDP_PORT)))
        print(f"Listening for UDP packets from AffectToolbox on {self.UDP_IP}:{self.UDP_PORT}")

    def start(self):
        time_loop_start = time.time()
        data, addr = self.sock.recvfrom(64000)
        if data is not None:
            root = etree.fromstring(str(data, 'UTF-8'))
            for element in root.iter():
                # print(f"{element.tag} - {element.text}")
                if element.tag == 'm_f':
                    # print(element.text)
                    fusion_tuple = element.text[1:-1].split(',')
                    fusion_tuple = [float(i) for i in fusion_tuple]
                    # print(f"Valence: {fusion_tuple[0]}\nArousal: {fusion_tuple[1]}\nDominance: {fusion_tuple[2]}\n")
                    self.valence = fusion_tuple[0]
                    self.arousal = fusion_tuple[1]
                    self.dominance = fusion_tuple[2]

                    self.valence_buffer.append(self.valence)
                    self.arousal_buffer.append(self.arousal)
                    self.dominance_buffer.append(self.dominance)

            for i in range(0, int(self.buffer_s * (1.0 / self.samplerate_s))):
                self.valence_windowed = self.valence_windowed + self.valence_buffer[i]
                self.arousal_windowed = self.arousal_windowed + self.arousal_buffer[i]
                self.dominance_windowed = self.dominance_windowed + self.dominance_buffer[i]

            self.valence_windowed = self.valence_windowed / float(self.buffer_s * (1.0 / self.samplerate_s))
            self.arousal_windowed = self.arousal_windowed / float(self.buffer_s * (1.0 / self.samplerate_s))
            self.dominance_windowed = self.dominance_windowed / float(self.buffer_s * (1.0 / self.samplerate_s))

            # print(f"Valence_Windowed: {self.valence_windowed}\nArousal_Windowed: {self.arousal_windowed}\nDominance_Windowed: {self.dominance_windowed}\n")

        seconds_loop = time.time() - time_loop_start
        # print(seconds_loop)
        loop_timer = 1.0 / float(self.samplerate_s) - seconds_loop
        self.read_loop = threading.Timer(loop_timer, self.start)
        self.read_loop.start()

    def stop(self):
        if self.read_loop is not None:
            self.read_loop.cancel()
