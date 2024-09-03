import os
import shutil
import stat
from PIL import Image
import logging
import ctypes

logger = logging.getLogger(__name__)



def get_exact_img_file(source_file, output_path, icon_size):
    logger.info(f"get_exact_img_file called with arguments: source_file = {source_file}, output_path = {output_path}, icon_size = {icon_size}")

    found = False
    
    try:
        # Copy the .ico file to the output path
        shutil.copy2(source_file, output_path)
        
        # Remove permissions and remove hidden attribute from our version of the .ico
        os.chmod(output_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        remove_hidden_attribute(output_path)
        logger.info("Removed hidden attributes on local icon")
        
        # Resize the image
        image = Image.open(output_path)
        resized_image = image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        resized_image.save(output_path)

        found = True
        logger.info(f"Copied {os.path.basename(source_file)} to {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Error: File not found after copying to data directory: {e}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")


    return found

def remove_hidden_attribute(file_path):
    # Define the Windows constants for attributes
    FILE_ATTRIBUTE_HIDDEN = 0x2

    # Get the current attributes of the file
    attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)

    if attrs == -1:
        logger.error(f"File not found when removing hidden attributes: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Remove the hidden attribute
    new_attrs = attrs & ~FILE_ATTRIBUTE_HIDDEN
    ctypes.windll.kernel32.SetFileAttributesW(file_path, new_attrs)