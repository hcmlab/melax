import urllib.request
import os
import sounddevice as sd
def download_model_if_not_exists(url, file_name):
    """
    Downloads a model file from the given URL if it doesn't already exist.

    :param url: The URL to download the model from.
    :param file_name: The name to save the model file as.
    """
    if not os.path.exists(file_name):
        print(f"{file_name} not found. Downloading...")
        urllib.request.urlretrieve(url, file_name)
        print(f"Downloaded {file_name}.")
    else:
        print(f"{file_name} already exists. Skipping download.")


def list_microphones():
    devices = sd.query_devices()
    input_devices = []
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:  # Check if the device supports input
            input_devices.append((idx, device['name']))
    return input_devices
