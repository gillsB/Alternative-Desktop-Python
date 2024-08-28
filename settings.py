import json
import os
from pathlib import Path
import logging


logger = logging.getLogger(__name__)
DIRECTORY = None
DEFUALT_SETTINGS = {
        "update_on_launch": True,
        "toggle_overlay_keybind": "Alt+d",
        "window_opacity": 100,
        "theme" : "dark_cyan.xml",
        "background_source": "first_found",
        "background_video": "",
        "background_image": "",
        "local_icons": True,
        "icon_size": 100
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
        logger.error("Error loading settings, expected file at: " + DIRECTORY )
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
        logger.info("Saved settings")



def set_dir(directory):
    global DIRECTORY
    DIRECTORY = directory
    if os.path.exists(DIRECTORY):
        logger.info("checking for new settings")
        check_for_new_settings()
    else:
        logger.info("build new")
        save_settings(DEFUALT_SETTINGS)



def check_for_new_settings():
    settings = load_settings()
    new_settings = False
    for key, value in DEFUALT_SETTINGS.items():
        if key not in settings:
            logger.info(f"key {key} not in settings")
            settings[key] = value
            new_settings = True
    if new_settings:
        logger.info(f"New settings before save: {settings}")
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
