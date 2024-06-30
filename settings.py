import json
import os

DIRECTORY = None

def load_settings(SETTINGS_FILE):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        print("Error loading settings, expected file at: " + SETTINGS_FILE )
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