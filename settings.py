import json
import os
from pathlib import Path

DIRECTORY = None
DEFUALT_SETTINGS = {
        "update_on_launch": True,
        "toggle_overlay_keybind": "Alt+d",
        "window_opacity": 100
}

    
def load_settings():
    if os.path.exists(DIRECTORY):
        with open(DIRECTORY, "r") as f:
            return json.load(f)
    else:
        print("Error loading settings, expected file at: " + DIRECTORY )
        return {}

def get_setting(key, default=None):
    settings = load_settings()
    return settings.get(key, default)

def set_setting(key, value):
    if DIRECTORY != None:
        settings = load_settings()
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
    current_directory = os.getcwd()
    config_file = os.path.join(current_directory, "config")
    try:
        os.mkdir(config_file)
    except FileExistsError:
        print("Config file already exists")
    except:
        print("Error creating config file.")
    save_settings(DEFUALT_SETTINGS)

def check_for_new_settings():
    settings = load_settings()
    new_settings = False
    for key, value in DEFUALT_SETTINGS.items():
        if key not in settings:
            settings[key] = value
            new_settings = True
    if new_settings:
        save_settings(settings)


def add_angle_brackets(text):
    modifiers = {"alt", "ctrl", "shift"}  # Define the modifier keys
    result = []
    i = 0
    while i < len(text):
        found_modifier = False
        for modifier in modifiers:
            if text[i:i+len(modifier)].lower() == modifier:  # Check for modifier keys (case insensitive)
                result.append("<" + text[i:i+len(modifier)] + ">")
                i += len(modifier)
                found_modifier = True
                break
        if not found_modifier:
            result.append(text[i])
            i += 1
    return ''.join(result)
