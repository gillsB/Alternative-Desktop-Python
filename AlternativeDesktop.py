import sys
import os
import importlib.util

def load_module(module_name, subfolder=None):
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")

    if subfolder:
        module_path = os.path.join(current_dir, subfolder, f"{module_name}.py")
    else:
        module_path = os.path.join(current_dir, f"{module_name}.py")
    print(f"Attempting to load {module_name} from: {module_path}")
    
    if os.path.exists(module_path):
        print(f"Found {module_name} at: {module_path}")
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    else:
        print(f"Could not find {module_name} at: {module_path}")
        print(f"Falling back to system import for {module_name}")
        return importlib.import_module(module_name)

# Ensure the current working directory is in sys.path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

print(f"Python path: {sys.path}")

# Load modules
updater = load_module('updater', subfolder='util')
settings = load_module('settings', subfolder='util')
desktop = load_module('desktop', subfolder='desktop')

# Now use these modules
from util.updater import check_for_updates
from util.settings import load_settings, set_dir
import logging
from util.logs import setup_logging

CURRENT_VERSION = "V0.1.000"
GITHUB_REPO = "gillsb/Alternative-Desktop"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
SETTINGS_FILE = None

if __name__ == '__main__':
    setup_logging()
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.info("Starting the application")

    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    config_path = os.path.join(app_data_path, 'config', 'settings.json')
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    logger.info(f"Configuration file path: {config_path}")
    SETTINGS_FILE = config_path

    logger.info(f"Settings file: {SETTINGS_FILE}")
    set_dir(SETTINGS_FILE)
    settings = load_settings()
    logger.info(f"settings: {settings}")

    # Must run before .main() and before any QApplication needs to be created
    # Since updater(check_for_updates) uses a QApplication we call it before so that it uses the same QApplication (cannot delete one and re-create it)
    desktop.create_app()
    if settings.get("update_on_launch", True):
        check_for_updates(CURRENT_VERSION, RELEASES_URL)
    
    desktop.main(CURRENT_VERSION)
