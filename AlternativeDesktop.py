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

CURRENT_VERSION = "v0.0.011"
GITHUB_REPO = "gillsb/Alternative-Desktop" 
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
SETTINGS_FILE = "config/settings.json"

if __name__ == '__main__':
    set_dir(SETTINGS_FILE)
    settings = load_settings(SETTINGS_FILE)
    print(settings)
    if settings.get("update_on_launch", True):
        check_for_updates(CURRENT_VERSION, GITHUB_REPO, RELEASES_URL)
    
    value = get_setting("update_on_launch")
    print(value)
    set_setting("update_on_launch", False)
    value = get_setting("update_on_launch")
    print(value)
    set_setting("update_on_launch", True)
    value = get_setting("update_on_launch")
    print(value)
    
    desktop_main()
