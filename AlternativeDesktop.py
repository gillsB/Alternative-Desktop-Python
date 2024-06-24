import subprocess
import time
import pyautogui
import os

def launch_notepad():
    # Launch Notepad
    notepad_process = subprocess.Popen(['notepad.exe'])

    # Wait for Notepad to open
    time.sleep(2)

    # Type "Hello, World!"
    pyautogui.typewrite('Hello, World!', interval=0.1)

    # Wait for 5 seconds
    time.sleep(5)

    # Terminate Notepad
    notepad_process.terminate()

if __name__ == '__main__':
    launch_notepad()