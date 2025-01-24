import tkinter as tk
from tkinter import ttk
import json
import socket
import struct

class LiveLinkController:
    def __init__(self, json_file_path, remote_address, blendshape_port):
        self.json_file_path = json_file_path
        self.remote_address = remote_address
        self.blendshape_port = blendshape_port
        self.data = self.load_json()
        self.blendshape_socket = None
        self.send_mode = "Both"  # Default send mode

        self.init_socket()
        self.root = tk.Tk()
        self.root.title("LiveLink Controller")

        self.create_ui()

    def load_json(self):
        """Load the JSON data from the file."""
        with open(self.json_file_path, 'r') as f:
            return json.load(f)

    def init_socket(self):
        """Initialize the socket connection."""
        self.blendshape_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.remote_address, self.blendshape_port)
        print(f"Connecting to {server_address[0]} port {server_address[1]} for blendshape data")
        self.blendshape_socket.connect(server_address)

    def send_data(self, data):
        """Send data to the socket."""
        json_data = json.dumps(data, separators=(',', ':'))
        verify_size = struct.pack("!Q", len(json_data))
        print(json_data)
        self.blendshape_socket.sendall(verify_size + bytes(json_data, 'ascii'))

    def create_ui(self):
        """Create the UI with sliders for Body and Face values."""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', pady=5)

        # Dropdown menu to select send mode
        ttk.Label(control_frame, text="Send Mode:").pack(side="left", padx=5)
        send_mode_menu = ttk.Combobox(control_frame, values=["Both", "Body", "Facial"], state="readonly")
        send_mode_menu.set(self.send_mode)
        send_mode_menu.pack(side="left")
        send_mode_menu.bind("<<ComboboxSelected>>", self.change_send_mode)

        # Scrollable frame for sliders
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True)

        canvas = tk.Canvas(container)
        scrollbar_v = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        notebook = ttk.Notebook(scrollable_frame)
        notebook.pack(fill='both', expand=True)

        # Body tab
        body_tab = ttk.Frame(notebook)
        notebook.add(body_tab, text="Body")
        self.create_body_sliders(body_tab)

        # Face tab
        face_tab = ttk.Frame(notebook)
        notebook.add(face_tab, text="Face")
        self.create_face_sliders(face_tab)

    def change_send_mode(self, event):
        """Change the send mode based on user selection."""
        self.send_mode = event.widget.get()
        print(f"Send mode changed to: {self.send_mode}")

    def create_body_sliders(self, parent):
        """Create sliders for the Body data."""
        body_frame = self.data['Audio2Face']['Body']

        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill='both', expand=True, padx=5, pady=5)

        for index, entry in enumerate(body_frame):
            group_frame = ttk.LabelFrame(grid_frame, text=entry['Name'])
            group_frame.grid(row=index // 4, column=index % 4, padx=5, pady=5, sticky="nsew")

            for key in ['Location', 'Rotation']:
                label = ttk.Label(group_frame, text=key)
                label.pack(anchor='w')

                for i, value in enumerate(entry[key]):
                    slider = tk.Scale(group_frame, from_=-100, to=100, orient='horizontal', length=150)
                    slider.set(value)
                    slider.pack(anchor='w')
                    slider.bind("<ButtonRelease-1>", lambda event, entry=entry, key=key, i=i: self.update_body(entry, key, i, event.widget.get()))

    def create_face_sliders(self, parent):
        """Create sliders for the Face data."""
        facial_data = self.data['Audio2Face']['Facial']
        names = facial_data['Names']
        weights = facial_data['Weights']

        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill='both', expand=True, padx=5, pady=5)

        for index, (name, weight) in enumerate(zip(names, weights)):
            frame = ttk.Frame(grid_frame)
            frame.grid(row=index // 3, column=index % 3, padx=5, pady=5)

            label = ttk.Label(frame, text=name)
            label.pack()

            slider = tk.Scale(frame, from_=0, to=1, resolution=0.01, orient='horizontal', length=150)
            slider.set(weight)
            slider.pack()
            slider.bind("<ButtonRelease-1>", lambda event, index=index: self.update_face(index, event.widget.get()))

    def update_body(self, entry, key, index, value):
        """Update the Body data and send the entire message."""
        if self.send_mode in ["Both", "Body"]:
            self.data['Audio2Face']['Body'] = [{
                "Name": e["Name"],
                "ParentName": e["ParentName"],
                "Location": e["Location"],
                "Rotation": e["Rotation"]
            } for e in self.data['Audio2Face']['Body']]

            body_data = {
                "Body": self.data['Audio2Face']['Body'],
                "FrameTiming": self.data['Audio2Face'].get('FrameTiming', {})
            }
            self.send_data({"Audio2Face": {**body_data}})
            print(f"Updated Body: {entry['Name']} {key}[{index}] = {value}")

    def update_face(self, index, value):
        """Update the Face data and send it."""
        if self.send_mode in ["Both", "Facial"]:
            self.data['Audio2Face']['Facial']['Weights'][index] = value
            facial_data = {
                "Facial": self.data['Audio2Face']['Facial'],
                "FrameTiming": self.data['Audio2Face'].get('FrameTiming', {})
            }
            self.send_data({"Audio2Face": {**facial_data}})
            print(f"Updated Face: {self.data['Audio2Face']['Facial']['Names'][index]} = {value}")

    def close(self):
        """Close the socket connection."""
        if self.blendshape_socket:
            print("Closing blendshape socket")
            self.blendshape_socket.close()

    def run(self):
        """Run the main loop."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        """Handle the window close event."""
        self.close()
        self.root.destroy()

if __name__ == "__main__":
    JSON_FILE_PATH = "one_frame.json"
    REMOTE_ADDRESS = "localhost"
    BLENDSHAPE_PORT = 12030

    controller = LiveLinkController(JSON_FILE_PATH, REMOTE_ADDRESS, BLENDSHAPE_PORT)
    controller.run()
