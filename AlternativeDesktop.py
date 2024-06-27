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
CURRENT_VERSION = "v0.0.005"

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
            download_and_update(download_url, latest_version)
        else:
            print("You are running the latest version.")
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")

def download_and_update(download_url, latest_version):
    local_filename = f"update_{latest_version}.exe"
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded {local_filename}")
    run_installer(local_filename)

def run_installer(installer_path):
    try:
        print(f"Running installer: {installer_path}")
        subprocess.run([installer_path], check=True)
        print("Installation complete. Please restart the application.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run the installer: {e}")

if __name__ == '__main__':
    check_for_updates()
    launch_notepad()