@echo off
:: Define the path to the target batch file
set TARGET_BATCH="C:\Users\withanda\AppData\Local\ov\pkg\audio2face-2023.1.1\audio2face_headless.bat"

:: Check if the target batch file exists
if not exist %TARGET_BATCH% (
    echo Error: The target batch file does not exist at %TARGET_BATCH%.
    pause
    exit /b 1
)

:: Start the target batch file in a new console window
start "" %TARGET_BATCH%

:: Optional: Add a message or logs to confirm the batch was launched
echo Launched Audio2Face headless server.

