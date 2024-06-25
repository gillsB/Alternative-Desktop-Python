import subprocess
import time
import pyautogui
import os
import requests
import sys
import shutil
import zipfile

GITHUB_REPO = "gillsb/Alternative-Desktop" 
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION = "v0.0.001"

def launch_notepad():
    # Launch Notepad
    notepad_process = subprocess.Popen(['notepad.exe'])

    # Wait for Notepad to open
    time.sleep(2)

    # Type "Hello, World!"
    pyautogui.typewrite(CURRENT_VERSION, interval=0.1)

    # Wait for 5 seconds
    time.sleep(5)

    # Terminate Notepad
    notepad_process.terminate()

def check_for_updates():
    try:
        response = requests.get(RELEASES_URL)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release["tag_name"]
        
          # Replace with the current version of your app

        if latest_version > CURRENT_VERSION:
            print(f"New version available: {latest_version}")
            download_url = latest_release["assets"][0]["browser_download_url"]
            print("new download link = " + download_url)
        else:
            print("You are running the latest version.")
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")

if __name__ == '__main__':
    check_for_updates()
    launch_notepad()