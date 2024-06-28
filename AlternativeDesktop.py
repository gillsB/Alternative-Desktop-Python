import subprocess
import time
import pyautogui
import os
import requests
import sys
import shutil
import zipfile
from updater import check_for_updates


CURRENT_VERSION = "v0.0.009"
GITHUB_REPO = "gillsb/Alternative-Desktop" 
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def launch_notepad():
    # Launch Notepad
    notepad_process = subprocess.Popen(['notepad.exe'])

    # Wait for Notepad to open
    time.sleep(2)

    # Type "Hello, World!"
    pyautogui.typewrite(CURRENT_VERSION + "hi", interval=0.1)

    # Wait for 5 seconds
    time.sleep(5)

    # Terminate Notepad
    notepad_process.terminate()

if __name__ == '__main__':
    check_for_updates(CURRENT_VERSION, GITHUB_REPO, RELEASES_URL)
    launch_notepad()