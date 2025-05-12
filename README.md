
# 🚀 Omniverse & Melax Setup Guide

## 🎮 Omniverse Installation & Configuration

1. **Download Omniverse Launcher**
   - From: [wingetgui.com](https://www.wingetgui.com/apps/Nvidia-Omniverse)

2. **Create & Log in to NVIDIA Account**
   - Sign up or log in as required.

3. **Set Path Configuration**
   ```txt
   Library Path: C:\Users\YourName\AppData\Local\ov\pkg
   DATA Path: C:\Users\YourName\AppData\Local\ov\data
   Content Path: C:\Users\YourName\Downloads
   CACHE Path: C:\Users\YourName\AppData\Local\ov\cache
   ```

4. **Launch Omniverse**

5. **Install Audio2Face**
   - Navigate to **Exchange** → Search for `Audio2Face`
   - Download version `2023.1.1`

6. **Run Audio2Face in Headless Mode**
   - Edit `start_headless.bat` with the correct path:
     ```bat
     set TARGET_BATCH="C:\Users\YourName\AppData\Local\ov\pkg\audio2face-2023.1.1\audio2face_headless.bat"
     ```

---

## 🧠 Melax Setup

1. **clone from** https://github.com/hcmlab/melax.git

2. **Run Installer**
   - Execute `MeLaX_ACE_A2F_Only.exe`

3. **Network Permissions**
   - On first run, allow access on **Public**, **Private**, and **Domain** networks.

4. **Download Ollama**
   - Ensure it is installed on your system.

---

## 🐍 Running `mainwindow.py`

1. **Install Python Packages**
   - From `requirements_python3_11.txt` (for Python 3.11)

2. **Install `ffmpeg`** if not already installed

3. **Run the GUI**
   ```bash
   python gui.py
   ```
