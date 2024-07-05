import subprocess
import time
import pyautogui
import os
import requests
import sys
import shutil
import zipfile
import json
from updater import check_for_updates
from settings import load_settings, set_dir, get_setting, set_setting
from PyQt5.QtWidgets import QApplication
import keyboard
from desktop import main as desktop_main

CURRENT_VERSION = "v0.0.012"
GITHUB_REPO = "gillsb/Alternative-Desktop" 
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
SETTINGS_FILE = None

if __name__ == '__main__':

    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create app_data directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    # Append /config/settings.json to the AppData path
    config_path = os.path.join(app_data_path, 'config', 'settings.json')

    #create the /config/settings.json if they do not exist already.
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    print(f"Configuration file path: {config_path}")
    SETTINGS_FILE = config_path

    print(SETTINGS_FILE)
    set_dir(SETTINGS_FILE)
    settings = load_settings()
    print(settings)
    if settings.get("update_on_launch", True):
       check_for_updates(CURRENT_VERSION, GITHUB_REPO, RELEASES_URL)
    
    desktop_main()
