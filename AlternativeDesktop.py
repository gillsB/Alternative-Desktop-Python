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
from settings import load_settings
from PyQt5.QtWidgets import QApplication
import keyboard
from desktop import main as desktop_main

CURRENT_VERSION = "v0.0.011"
GITHUB_REPO = "gillsb/Alternative-Desktop" 
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
SETTINGS_FILE = "config/settings.json"

if __name__ == '__main__':
    settings = load_settings(SETTINGS_FILE)
    print(settings)
    if settings.get("update_on_launch", True):
        check_for_updates(CURRENT_VERSION, GITHUB_REPO, RELEASES_URL)
    
    desktop_main()
