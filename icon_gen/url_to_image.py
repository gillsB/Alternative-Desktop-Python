import os
import configparser
from PIL import Image
import shutil
import stat
from icon_gen.extract_ico_file import remove_hidden_attribute

ICON_SIZE = 0

def url_to_image(url_path, output_path, icon_size):
    global ICON_SIZE
    ICON_SIZE = icon_size

    config = configparser.ConfigParser()
    config.read(url_path)

    
    ico_path = None
    
    try:
        # Assuming the icon file path is stored in the "IconFile" key
        icon_file = config.get('InternetShortcut', 'IconFile')
        icon_index = config.get('InternetShortcut', 'IconIndex', fallback=0)
        
        if get_ico_file(icon_file, output_path):
            ico_path = os.path.join(output_path, "icon.png")
            print("Copying .ico file directly")
            
    except (configparser.NoOptionError, configparser.NoSectionError):
        print("No icon information found in the .url file")

    return ico_path


def get_ico_file(source_file, target_dir):

    found = False

    # Ensure target directory exists, create if it doesn't
    if os.path.exists(target_dir) and os.path.isfile(target_dir):
        ...
    else:
        os.makedirs(target_dir, exist_ok=True)
    
    # Check if the source file exists and is an .ico file
    if os.path.isfile(source_file) and source_file.endswith(".ico"):
        print(".ico file has been found")
        
        # Name of the target file
        target_ico_file = os.path.join(target_dir, "icon.png")
        shutil.copy2(source_file, target_ico_file)
        
        # Remove permissions and remove hidden attribute from our version of the .ico
        try:
            os.chmod(target_ico_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            remove_hidden_attribute(target_ico_file)
        except FileNotFoundError as e:
            print(f"Error: File not found after copying to data directory. Error: {e}")

        image = Image.open(target_ico_file)
        resized_image = image.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        resized_image.save(target_ico_file)
        found = True
        print(f"Copied {source_file} to {target_dir}")
    
    return found