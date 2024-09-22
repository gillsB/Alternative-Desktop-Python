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
        "on_close": 1,
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

#on_close: default set to 1 (terminate the program)

    
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


# Depreciated was originally used for pynput keyboard library. But has since moved to base keyboard library which does not use this <> formatting.
def add_angle_brackets(text):
    modifiers = {"alt", "ctrl", "shift"}  # Define the modifier keys
    special_keys = {
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
        "left", "right", "up", "down",  # Arrow keys
        "insert", "delete", "home", "end", "pageup", "pagedown",  # Navigation keys
        "numpad0", "numpad1", "numpad2", "numpad3", "numpad4", "numpad5", "numpad6", "numpad7", "numpad8", "numpad9",  # Numpad keys
        "enter", "space", "tab", "esc"  # Other keys
    }
    
    # Combine modifiers and special keys into a single dictionary with their lengths
    all_keys = {**{mod: len(mod) for mod in modifiers}, **{key: len(key) for key in special_keys}}
    
    result = []
    i = 0
    
    while i < len(text):
        found_key = False
        
        # Check for all keys in descending order of length
        for key, length in sorted(all_keys.items(), key=lambda x: -x[1]):
            if text[i:i + length].lower() == key:
                result.append(f"<{text[i:i + length]}>")
                i += length
                found_key = True
                break
        
        if not found_key:
            # Append regular characters
            result.append(text[i])
            i += 1

    return ''.join(result)