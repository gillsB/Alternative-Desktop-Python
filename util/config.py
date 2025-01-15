import json
import os
import logging
from util.settings import get_setting


logger = logging.getLogger(__name__)
DESKTOP_CONFIG_DIRECTORY = None
JSON = ""
DATA_DIRECTORY = None
DESKTOP_CONFIG = None

#These are all active .json arguments and their defaults
DEFAULT_DESKTOP =  {
    "row": 0,
    "column": 0,
    "name": "",
    "icon_path": "",
    "executable_path": "",
    "command_args": "",
    "website_link": "",
    "launch_option": 0,
    "font_size": 10
}

#launch_option options:
#0 First come first serve (down the list) i.e. executable_path, then if none -> website_link
#1 Website link first
#2 Ask upon launching (run_menu_dialog)
#3 executable only
#4 website link only

#default icon saves:
# icon.png extract_ico_file, url_to_image (unique, getting image from .url file does not check for .ico files in location)
# icon2.png exe_to_image, lnk_to_image (both share the same executable_path input so one or the other.)
# icon3.png favicon_to_image, browser_to_image (gets favicon from website, fallback to default browser icon if no favicon found)
# icon4.png default_icon_to_image (gets icon from default associated filetype program, only exists if exec_path is not .exe, .url, .lnk)




def create_paths():
    create_config_path()
    logger.info("Created config path")
    create_data_path()
    logger.info("Created data path")


def create_config_path():

    global DESKTOP_CONFIG_DIRECTORY
    global DEFAULT_DESKTOP
    global JSON
    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create app_data directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    # Append /config/desktop.json to the AppData path
    config_path = os.path.join(app_data_path, 'config', 'desktop.json')
    #create the /config/desktop.json if they do not exist already.
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        logger.info(f"Making directory at: {config_dir}")
        os.makedirs(config_dir)

    logger.info(f"Configuration file path: {config_path}")
    DESKTOP_CONFIG_DIRECTORY = config_path

    if os.path.exists(DESKTOP_CONFIG_DIRECTORY) and os.path.getsize(DESKTOP_CONFIG_DIRECTORY) > 0:
        with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
            JSON = json.load(f)
    else:
        logger.info(f"Creating default settings at: {DESKTOP_CONFIG_DIRECTORY}")
        JSON = [DEFAULT_DESKTOP]
        with open(DESKTOP_CONFIG_DIRECTORY, "w") as f:
            json.dump([DEFAULT_DESKTOP], f, indent=4)

def create_data_path():

    global DATA_DIRECTORY
    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create app_data directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    # Append /data/ to the AppData path
    data_path = os.path.join(app_data_path, 'data')
    if not os.path.exists(data_path):
        logger.info(f"Making directory at {data_path}")
        os.makedirs(data_path)
    
    DATA_DIRECTORY = data_path




def get_icon_data(row, column):
    for item in JSON:
        if item['row'] == row and item['column'] == column:
            return {
                'icon_path': item.get('icon_path', ""),
                'name': item.get('name', ""),
                'executable_path': item.get('executable_path', ""),
                'command_args': item.get('command_args', ""),
                'website_link': item.get('website_link', ""),
                'launch_option': item.get('launch_option', 0),
                'font_size': item.get('font_size', get_setting("font_size", 10))
            }
    return {
        'icon_path': "",
        'name': "",
        'executable_path': "",
        'command_args': "",
        'website_link': "",
        'launch_option': 0,
        'font_size': 10
    }

def get_json():
    return JSON

def load_desktop_config():
    global DESKTOP_CONFIG
    if DESKTOP_CONFIG == None:
        if os.path.exists(DESKTOP_CONFIG_DIRECTORY):
            with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
                DESKTOP_CONFIG = json.load(f)
        else:
            logger.error(f"Error loading settings, expected file at: {DESKTOP_CONFIG_DIRECTORY}")
            return {}
    return DESKTOP_CONFIG
    
def entry_exists(row, col):
    config = load_desktop_config()
    for item in config:
        if item['row'] == row and item['column'] == col:
            return True
    return False

#entry_exists but returns item if it exists, otherwise false
def get_entry(row, col):
    config = load_desktop_config()
    for item in config:
        if item['row'] == row and item['column'] == col:
            return item
    return False

def check_for_new_config():
    config = load_desktop_config()
    new_config = False

    for entry in config:
        for key, value in DEFAULT_DESKTOP.items():
            if key not in entry:
                logger.info(f"key: {key} not in settings")
                entry[key] = value
                new_config = True

    if new_config:
        logger.info(f"Saving new settings {config}")
        save_config_to_file(config)

def save_config_to_file(config):
    logger.info("Attempting to save the desktop.json")
    global JSON
    with open(DESKTOP_CONFIG_DIRECTORY, "w") as f:
        json.dump(config, f, indent=4)
        logger.info("Successfully saved desktop.json")
    with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
        JSON = json.load(f)
        logger.info(f"reloaded JSON")

def is_default(row, col):
    config = load_desktop_config()
    
    # Assume the item is not found and thus is default
    is_default_value = True
    
    for item in config:
        if item['row'] == row and item['column'] == col:
            # If the item is found, check if it has non-default values
            if (item.get('name', "") != DEFAULT_DESKTOP['name'] or
                item.get('icon_path', "") != DEFAULT_DESKTOP['icon_path'] or
                item.get('executable_path', "") != DEFAULT_DESKTOP['executable_path'] or
                item.get('command_args', "") != DEFAULT_DESKTOP['command_args'] or
                item.get('website_link', "") != DEFAULT_DESKTOP['website_link'] or
                item.get('launch_option', 0) != DEFAULT_DESKTOP['launch_option']):
                is_default_value = False
            break

    return is_default_value

#updates the entry at row,col to DEFAULT_DESKTOP fields (except row/column)
def set_entry_to_default(row, col):
    config = load_desktop_config()
    for entry in config:
        if entry.get('row') == row and entry.get('column') == col:
            for key in DEFAULT_DESKTOP:
                if key not in ['row', 'column']:
                    entry[key] = DEFAULT_DESKTOP[key]
            break
    save_config_to_file(config)

#swap row/col between two desktop_icons
def swap_icons_by_position(row1, col1, row2, col2):
    config = load_desktop_config()
    
    # Find the items with the specified row and column values
    item1 = next((item for item in config if item['row'] == row1 and item['column'] == col1), None)
    item2 = next((item for item in config if item['row'] == row2 and item['column'] == col2), None)
    
    # if neither icons in desktop.json
    if item1 is None and item2 is None:
        logger.info("Moved undefined desktop icon with another undefined desktop icon")
        return
    #if only 2nd icon(icon dragged on top of) is in .json
    elif item1 is None:
        item2['row'] = row1
        item2['column'] =  col1
    #if only item dragged is in .json
    elif item2 is None:
        item1['row'] = row2
        item1['column'] =  col2
    #when both items are in .json
    else:
        # Swap the rows and columns of the specified items
        item1['row'], item2['row'] = item2['row'], item1['row']
        item1['column'], item2['column'] = item2['column'], item1['column']
    
    save_config_to_file(config)

def change_launch(new_launch_value, row, col):
    config = load_desktop_config()
    for entry in config:
        if entry.get('row') == row and entry.get('column') == col:
            entry['launch_option'] = new_launch_value
            break
    save_config_to_file(config)

def update_folder( new_row, new_col):
    config = load_desktop_config()

    for entry in config:
        if entry.get('row') == new_row and entry.get('column') == new_col:
            new_dir = os.path.join(DATA_DIRECTORY, f'[{new_row}, {new_col}]')
            if entry['icon_path'].startswith(DATA_DIRECTORY):
                filename = ""

                last_backslash_index = entry['icon_path'].rfind('\\')

                # Extract everything after the last backslash
                if last_backslash_index != -1:
                    filename = entry['icon_path'][last_backslash_index + 1:]
                entry['icon_path'] = os.path.join(new_dir, filename)
    
    save_config_to_file(config)
            

def get_data_directory():
    return DATA_DIRECTORY