import json
import os
from pathlib import Path

DIRECTORY = None
DEFUALT_SETTINGS = {
        "update_on_launch": True,
        "desktop_keybind": "<alt>+d"
}

def load_settings(SETTINGS_FILE):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        print("Error loading settings, expected file at: " + SETTINGS_FILE )
        return {}
    
def load_local():
    if os.path.exists(DIRECTORY):
        with open(DIRECTORY, "r") as f:
            return json.load(f)
    else:
        print("Error loading settings, expected file at: " + DIRECTORY )
        return {}

def get_setting(key, default=None):
    settings = load_settings(DIRECTORY)
    return settings.get(key, default)

def set_setting(key, value):
    if DIRECTORY != None:
        settings = load_settings(DIRECTORY)
        settings[key] = value
        save_settings(settings)

def save_settings(settings):
    with open(DIRECTORY, "w") as f:
        json.dump(settings, f, indent=4)



def set_dir(directory):
    global DIRECTORY
    DIRECTORY = directory
    if os.path.exists(DIRECTORY):
        check_for_new_settings()
    else:
        build_settings()


def build_settings():
    save_settings(DEFUALT_SETTINGS)

def check_for_new_settings():
    settings = load_local()
    new_settings = False
    for key, value in DEFUALT_SETTINGS.items():
        if key not in settings:
            settings[key] = value
            new_settings = True
    if new_settings:
        save_settings(settings)
