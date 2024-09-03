import os
import shutil
from PIL import Image
import stat
import ctypes
import logging
from icon_gen.icon_utils import remove_hidden_attribute

logger = logging.getLogger(__name__)

#Returns true if found and copied to target_dir, returns false if no .ico found
def extract_ico_file(source_file, output_path, icon_size):
    logger.info(f"Called with arguments: source_file = {source_file}, output_path = {output_path}, icon_size = {icon_size}")

    found = False
    
    # Extract the directory path of the source file
    source_dir = os.path.dirname(source_file)
    
    logger.info(f"searching directory: {source_file}")
    # Iterate over files in the directory containing source_file
    for filename in os.listdir(source_dir):
        if filename.endswith(".ico"):

            logger.info(".ico file has been found")
            source_ico_file = os.path.join(source_dir, filename)

            shutil.copy2(source_ico_file, output_path)
            
            #remove permissions and remove hidden attribute from our version of the .ico
            try:
                os.chmod(output_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                remove_hidden_attribute(output_path)
                logger.info(f"Removed hidden attributes on local icon")
            except FileNotFoundError as e:
                logger.error(f"Error: File not found after copying to data directory error: {e}")

            image = Image.open(output_path)
            resized_image = image.resize((icon_size,icon_size), Image.Resampling.LANCZOS)

            resized_image.save(output_path)
            found = True
            logger.info(f"Copied {filename} to {output_path}")

    
    return found






