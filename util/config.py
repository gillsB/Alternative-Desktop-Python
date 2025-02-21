import json
import os
import logging
from util.settings import get_setting


logger = logging.getLogger(__name__)
DESKTOP_CONFIG_DIRECTORY = None
JSON = ""
DATA_DIRECTORY = None

# Used to directly get a reference to the JSON item at ("row", "column")
ITEM_LOOKUP_TABLE = {}

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
    "font_size": -1,
    "use_global_font_size": True,
    "font_color": "#ffffff",
    "use_global_font_color": True
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

    global DESKTOP_CONFIG_DIRECTORY, DEFAULT_DESKTOP, JSON, ITEM_LOOKUP_TABLE

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
            ITEM_LOOKUP_TABLE = {(item['row'], item['column']): item for item in JSON}
    else:
        logger.info(f"Creating default settings at: {DESKTOP_CONFIG_DIRECTORY}")
        JSON = [DEFAULT_DESKTOP]
        ITEM_LOOKUP_TABLE = {(DEFAULT_DESKTOP['row'], DEFAULT_DESKTOP['column']): DEFAULT_DESKTOP}
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

def get_item(row, col):
    return ITEM_LOOKUP_TABLE.get((row, col))


def get_icon_data(row, column):
    item = get_item(row, column)
    if item:
        return {
            'icon_path': item.get('icon_path', ""),
            'name': item.get('name', ""),
            'executable_path': item.get('executable_path', ""),
            'command_args': item.get('command_args', ""),
            'website_link': item.get('website_link', ""),
            'launch_option': item.get('launch_option', 0),
            'font_size': item.get('font_size', get_setting("global_font_size", 10)),
            'use_global_font_size': item.get('use_global_font_size', True),
            'font_color': item.get('font_color', get_setting("global_font_color", 10)),
            'use_global_font_color': item.get('use_global_font_color', True)
            }
    return {
        'icon_path': "",
        'name': "",
        'executable_path': "",
        'command_args': "",
        'website_link': "",
        'launch_option': 0,
        'font_size': 10,
        'use_global_font_size': True,
        'font_color': "#ffffff",
        'use_global_font_color': True
    }


# This is an override which returns the global font_size if the DesktopIcon uses default. And the local font_size if it uses a custom font_size.
def get_icon_font_size(row, col):
    item = get_item(row, col)
    if item:
        if item.get('use_global_font_size'):
            return get_setting("global_font_size", 50)
        else:
            return item.get('font_size', get_setting("global_font_size", 10))
    # Return global font size if item not in JSON (new item)
    return get_setting("global_font_size", 10)

# This is an override which returns the global label_color if the DesktopIcon uses default. And the local font_color if it uses a custom font_color.
def get_icon_font_color(row, col):
    item = get_item(row, col)
    if item:
        if item.get('use_global_font_color'):
            return get_setting("global_font_color", "#ffffff")
        else:
            return item.get('font_color', get_setting("global_font_color", "#ffffff"))
    # Return global font color for item not in JSON (new item)
    return get_setting("global_font_color", "#ffffff")

def get_json():
    return JSON

def load_desktop_config():
    return JSON
    
def entry_exists(row, col):
    return (row, col) in ITEM_LOOKUP_TABLE

# entry_exists but returns item if it exists, otherwise false
def get_entry(row, col):
    return ITEM_LOOKUP_TABLE.get((row, col), False)

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
    
    # Sort the config by row then column
    sorted_config = sorted(config, key=lambda x: (x['row'], x['column']))

    with open(DESKTOP_CONFIG_DIRECTORY, "w") as f:
        json.dump(sorted_config, f, indent=4)
        logger.info("Successfully saved desktop.json")
    with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
        global JSON, ITEM_LOOKUP_TABLE
        JSON = sorted_config
        ITEM_LOOKUP_TABLE = {(item['row'], item['column']): item for item in sorted_config}
        logger.info("Reloaded JSON")

def is_default(row, col):
    item = get_item(row, col)
    
    if item:
        # Check only the keys that are not 'row' or 'column' and that exist in the item
        for key, default_value in DEFAULT_DESKTOP.items():
            if key not in ['row', 'column']:
                if key in item and item[key] != default_value:
                    return False

    return True


#updates the entry at row,col to DEFAULT_DESKTOP fields (except row/column)
def set_entry_to_default(row, col):
    config = load_desktop_config()
    item = get_item(row, col)
    if item:
        # Update the item to default values (except row and column)
        for key in DEFAULT_DESKTOP:
            if key not in ['row', 'column']:
                item[key] = DEFAULT_DESKTOP[key]
        save_config_to_file(config)

def delete_entry(row, col):
    global ITEM_LOOKUP_TABLE
    
    config = load_desktop_config()
    # Iterate over the list and remove the entry matching the row and column
    config = [entry for entry in config if not (entry.get('row') == row and entry.get('column') == col)]
    ITEM_LOOKUP_TABLE.pop((row, col), None)
    save_config_to_file(config)

#swap row/col between two desktop_icons
def swap_icons_by_position(row1, col1, row2, col2):
    config = load_desktop_config()
    
    # Find the items with the specified row and column values
    item1 = get_item(row1, col1)
    item2 = get_item(row2, col2)
    
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
    # Retrieve the item from the lookup table
    item = get_item(row, col)
    
    if item:
        # Update the launch_option in JSON
        item['launch_option'] = new_launch_value
        # Save the updated JSON to the file
        save_config_to_file(load_desktop_config())

def update_folder(new_row, new_col):
    item = get_item(new_row, new_col)
    
    if item:
        new_dir = os.path.join(DATA_DIRECTORY, f'[{new_row}, {new_col}]')
        if item['icon_path'].startswith(DATA_DIRECTORY):
            filename = ""
            last_backslash_index = item['icon_path'].rfind('\\')

            # Extract everything after the last backslash
            if last_backslash_index != -1:
                filename = item['icon_path'][last_backslash_index + 1:]
            item['icon_path'] = os.path.join(new_dir, filename)
        
        # Save the updated JSON to the file
        save_config_to_file(load_desktop_config())
            

def reset_all_to_default_font_size():
    for item in ITEM_LOOKUP_TABLE.values():
        item['use_global_font_size'] = True
    
    # Save the updated JSON to the file
    save_config_to_file(load_desktop_config())

def reset_all_to_default_font_color():
    for item in ITEM_LOOKUP_TABLE.values():
        item['use_global_font_color'] = True
    
    # Save the updated JSON to the file
    save_config_to_file(load_desktop_config())
            

def get_data_directory():
    return DATA_DIRECTORY