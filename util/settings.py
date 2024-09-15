import json
import os
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
        "icon_size": 100,
        "max_rows": 20,
        "max_cols": 40,
        "label_color": "white",
        "on_close": 0,
        "show_patch_notes": True,
        "keybind_minimize": 0
}
SETTINGS = None

#background_source arguments:
# first_found = First found
# both = Both
# video_only = Video only
# image_only = Image only
# none = None

    
def load_settings():
    global SETTINGS
    if os.path.exists(DIRECTORY):
        with open(DIRECTORY, "r") as f:
            SETTINGS = json.load(f)
            return SETTINGS
            
    else:
        logger.error("Error loading settings, expected file at: " + DIRECTORY )
        return {}

def get_setting(key, default=None):
    global SETTINGS
    return SETTINGS.get(key, default)

def set_setting(key, value):
    global SETTINGS
    SETTINGS[key] = value
    save_settings(SETTINGS)

def save_settings(settings):
    with open(DIRECTORY, "w") as f:
        json.dump(settings, f, indent=4)
        logger.info("Saved settings")
    # Update global SETTINGS to be up to date.
    load_settings()



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
    global SETTINGS
    new_settings = False
    load_settings()
    for key, value in DEFUALT_SETTINGS.items():
        if key not in SETTINGS:
            logger.info(f"key {key} not in settings")
            SETTINGS[key] = value
            new_settings = True
    if new_settings:
        logger.info(f"New settings before save: {SETTINGS}")
        save_settings(SETTINGS)


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
