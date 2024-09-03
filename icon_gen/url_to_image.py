import os
import configparser
from PIL import Image
import shutil
import stat
from icon_gen.icon_utils import remove_hidden_attribute
import logging

logger = logging.getLogger(__name__)

def url_to_image(url_path, output_path, icon_size):
    logger.info(f"Called with arguments: url_path = {url_path}, output_path = {output_path}, icon_size = {icon_size}")

    config = configparser.ConfigParser()
    config.read(url_path)

    
    ico_path = None
    
    try:
        # Assuming the icon file path is stored in the "IconFile" key
        icon_file = config.get('InternetShortcut', 'IconFile')
        icon_index = config.get('InternetShortcut', 'IconIndex', fallback=0)
        
        if get_ico_file(icon_file, output_path, icon_size):
            ico_path = output_path
            logger.info("Copying .ico file directly")
        else:
            logger.warning("No ico file found")
            
    except (configparser.NoOptionError, configparser.NoSectionError):
        logger.error("No icon information found in the .url file")

    return ico_path


def get_ico_file(source_file, output_path, icon_size):

    found = False
    
    # Check if the source file exists and is an .ico file
    if os.path.isfile(source_file) and source_file.endswith(".ico"):
        logger.info(f".ico file has been found: {source_file}")
        
        shutil.copy2(source_file, output_path)
        logger.info(f"Copied {source_file} to {output_path}")
        
        # Remove permissions and remove hidden attribute from our version of the .ico
        try:
            os.chmod(output_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            remove_hidden_attribute(output_path)
            logger.info(f"Removed hidden attributes on local icon")
        except FileNotFoundError as e:
            logger.error(f"Error: File not found after copying to data directory error: {e}")
            return found

        image = Image.open(output_path)
        resized_image = image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        resized_image.save(output_path)
        found = True
        logger.info(f"icon resized to {icon_size}")

    
    return found