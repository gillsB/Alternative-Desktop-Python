import json
import os

def load_settings(SETTINGS_FILE):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        print("Error loading settings, expected file at: " + SETTINGS_FILE )
        return {}
