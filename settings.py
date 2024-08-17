import json
import os
from pathlib import Path

DIRECTORY = None
DEFUALT_SETTINGS = {
        "update_on_launch": True,
        "toggle_overlay_keybind": "Alt+d",
        "window_opacity": 100,
        "theme" : "dark_cyan.xml",
        "background_source": "first_found"
}

#background_source arguments:
# first_found = First found
# both = Both
# video_only = Video only
# image_only = Image only
# none = None

    
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
        print("checking for new settings")
        check_for_new_settings()
    else:
        print("build new")
        build_settings()

#100% does not work with basic install of program files (x86) could modify it to build at app_data
#however at the same time in AlternativeDesktop.py I explicitly create the directories if they do not exist
#in app_data so this should be redundant???
def build_settings():
    '''current_directory = os.getcwd()
    config_file = os.path.join(current_directory, "config")
    print(config_file)
    try:
        os.mkdir(config_file)
    except FileExistsError:
        print("Config file already exists")
    except:
        print("Error creating config file.")'''
    save_settings(DEFUALT_SETTINGS)

def check_for_new_settings():
    settings = load_settings()
    new_settings = False
    for key, value in DEFUALT_SETTINGS.items():
        if key not in settings:
            print("key not in settings")
            settings[key] = value
            new_settings = True
    if new_settings:
        print("new settings")
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
