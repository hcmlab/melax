import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import json
import socket
import struct
import numpy as np
import math

class LiveLinkWebcamStreamer:
    def __init__(self, remote_address, blendshape_port):
        self.remote_address = remote_address
        self.blendshape_port = blendshape_port
        self.blendshape_socket = None
        self.capture = cv2.VideoCapture(0)  # Initialize webcam
        self.frame_index = 0

        self.init_socket()
        self.init_face_landmarker()

    def init_socket(self):
        """Initialize the socket connection."""
        self.blendshape_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.remote_address, self.blendshape_port)
        print(f"Connecting to {server_address[0]} port {server_address[1]} for blendshape data")
        self.blendshape_socket.connect(server_address)

    def init_face_landmarker(self):
        """Initialize the Mediapipe FaceLandmarker."""
        base_options = python.BaseOptions(model_asset_path='face_landmarker_v2_with_blendshapes.task')
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def send_data(self, data):
        """Send data to the socket."""
        json_data = json.dumps(data, separators=(',', ':'))
        verify_size = struct.pack("!Q", len(json_data))
        print(json_data)
        self.blendshape_socket.sendall(verify_size + bytes(json_data, 'ascii'))

    def decompose44(self, A44):
        """Decompose 4x4 transformation matrix into translation, rotation, scaling, and shears."""
        A44 = np.asarray(A44)
        T = A44[:-1, -1]
        RZS = A44[:-1, :-1]
        # Compute scales and shears
        M0, M1, M2 = np.array(RZS).T
        # Extract x scale and normalize
        sx = math.sqrt(np.sum(M0**2))
        M0 /= sx
        # Orthogonalize M1 with respect to M0
        sx_sxy = np.dot(M0, M1)
        M1 -= sx_sxy * M0
        # Extract y scale and normalize
        sy = math.sqrt(np.sum(M1**2))
        M1 /= sy
        sxy = sx_sxy / sx
        # Orthogonalize M2 with respect to M0 and M1
        sx_sxz = np.dot(M0, M2)
        sy_syz = np.dot(M1, M2)
        M2 -= (sx_sxz * M0 + sy_syz * M1)
        # Extract z scale and normalize
        sz = math.sqrt(np.sum(M2**2))
        M2 /= sz
        sxz = sx_sxz / sx
        syz = sy_syz / sy
        # Reconstruct rotation matrix, ensure positive determinant
        Rmat = np.array([M0, M1, M2]).T
        if np.linalg.det(Rmat) < 0:
            sx *= -1
            Rmat[:, 0] *= -1
        return T, Rmat, np.array([sx, sy, sz]), np.array([sxy, sxz, syz])

    def extract_head_pose(self, transformation_matrix):
        """Extract HeadRoll, HeadPitch, and HeadYaw from the transformation matrix using decomposition."""
        _, Rmat, _, _ = self.decompose44(transformation_matrix)
        pitch = math.atan2(Rmat[2, 1], Rmat[2, 2])  # Rotation around X-axis
        yaw = math.asin(-Rmat[2, 0])            # Rotation around Y-axis
        roll = math.atan2(Rmat[1, 0], Rmat[0, 0])  # Rotation around Z-axis
        return roll, -pitch, -yaw

    def process_frame(self, frame):
        """Process a single video frame to extract blendshapes and transformation matrices."""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        detection_result = self.detector.detect(mp_image)

        if detection_result.face_blendshapes:
            blendshapes = detection_result.face_blendshapes[0]

            # Extract blendshape names and scores
            face_blendshapes_names = [face_blendshapes_category.category_name.lower() for face_blendshapes_category in
                                      blendshapes]
            face_blendshapes_scores = [face_blendshapes_category.score for face_blendshapes_category in
                                       blendshapes]

            # Required blendshape names
            required_names = [
                "eyeblinkleft", "eyelookdownleft", "eyelookinleft", "eyelookoutleft", "eyelookupleft",
                "eyesquintleft", "eyewideleft", "eyeblinkright", "eyelookdownright", "eyelookinright",
                "eyelookoutright", "eyelookupright", "eyesquintright", "eyewideright", "jawforward",
                "jawleft", "jawright", "jawopen", "mouthclose", "mouthfunnel", "mouthpucker",
                "mouthleft", "mouthright", "mouthsmileleft", "mouthsmileright", "mouthfrownleft",
                "mouthfrownright", "mouthdimpleleft", "mouthdimpleright", "mouthstretchleft",
                "mouthstretchright", "mouthrolllower", "mouthrollupper", "mouthshruglower",
                "mouthshrugupper", "mouthpressleft", "mouthpressright", "mouthlowerdownleft",
                "mouthlowerdownright", "mouthupperupleft", "mouthupperupright", "browdownleft",
                "browdownright", "browinnerup", "browouterupleft", "browouterupright", "cheekpuff",
                "cheeksquintleft", "cheeksquintright", "nosesneerleft", "nosesneerright", "tongueout",
                "headroll", "headpitch", "headyaw"
            ]

            # Map Mediapipe blendshapes to required format, ignoring non-matching names
            weights = []
            for name in required_names[:-3]:  # Exclude HeadRoll, HeadPitch, HeadYaw
                if name in face_blendshapes_names:
                    index = face_blendshapes_names.index(name)
                    weights.append(face_blendshapes_scores[index])
                else:
                    weights.append(0.0)

            # Add head poses
            head_roll, head_pitch, head_yaw = 0, 0, 0
            if detection_result.facial_transformation_matrixes:
                head_roll, head_pitch, head_yaw = self.extract_head_pose(
                    detection_result.facial_transformation_matrixes[0]
                )
            weights += [head_roll, head_pitch, head_yaw]

            data = {
                "Audio2Face": {
                    "Body": {},
                    "Facial": {
                        "Names": required_names,
                        "Weights": weights
                    },
                    "FrameTiming": {
                        "FPS": int(self.capture.get(cv2.CAP_PROP_FPS)) or 30,
                        "Index": self.frame_index
                    }
                }
            }
            self.send_data(data)

    def run(self):
        """Run the main loop for capturing webcam frames and processing."""
        while True:
            ret, frame = self.capture.read()
            if not ret:
                print("Failed to capture frame")
                break

            # Convert frame to RGB for Mediapipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.process_frame(frame_rgb)

            # Display the frame
            cv2.imshow("Webcam", frame)

            # Increment frame index
            self.frame_index += 1

            # Break on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.capture.release()
        cv2.destroyAllWindows()

    def close(self):
        """Close the socket connection."""
        if self.blendshape_socket:
            print("Closing blendshape socket")
            self.blendshape_socket.close()

if __name__ == "__main__":
    REMOTE_ADDRESS = "localhost"
    BLENDSHAPE_PORT = 12030

    streamer = LiveLinkWebcamStreamer(REMOTE_ADDRESS, BLENDSHAPE_PORT)
    try:
        streamer.run()
    except KeyboardInterrupt:
        print("Exiting...")
        streamer.close()
