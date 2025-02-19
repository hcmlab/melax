import socket
import threading

try:
    from lxml import etree

    print("AffectWorker running with lxml.etree")
except ImportError:
    import xml.etree.ElementTree as etree

    print("AffectWorker running with Python's xml.etree.ElementTree")


class AffectWorker:

    def __init__(self, ip='127.0.0.1', port='5006'):
        self.read_loop = None
        self.sock = None
        self.UDP_IP = ip
        self.UDP_PORT = port

        self.valence = 0.0
        self.arousal = 0.0
        self.dominance = 0.0

    def bind(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, int(self.UDP_PORT)))
        print(f"Listening for UDP packets from AffectToolbox on {self.UDP_IP}:{self.UDP_PORT}")

    def start(self):
        data, addr = self.sock.recvfrom(64000)
        if data is not None:
            root = etree.fromstring(str(data, 'UTF-8'))
            for element in root.iter():
                # print(f"{element.tag} - {element.text}")
                if element.tag == 'm_f':
                    # print(element.text)
                    fusion_tuple = element.text[1:-1].split(',')
                    fusion_tuple = [float(i) for i in fusion_tuple]
                    print(f"Valence: {fusion_tuple[0]}\nArousal: {fusion_tuple[1]}\nDominance: {fusion_tuple[2]}\n")
                    self.valence = fusion_tuple[0]
                    self.arousal = fusion_tuple[1]
                    self.dominance = fusion_tuple[2]
        self.read_loop = threading.Timer(0.1, self.start)
        self.read_loop.start()

    def stop(self):
        if self.read_loop is not None:
            self.read_loop.cancel()
