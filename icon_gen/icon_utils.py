import os
import shutil
import stat
from PIL import Image
import logging
import ctypes

logger = logging.getLogger(__name__)


# Copy exact image file to local directory and upscale it.
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

# Does not upscale, just a direct copy paste.
def make_local_icon(icon_path, data_path):
    #ensure datapath for [row, col] exists
    if not os.path.exists(data_path):
        os.makedirs(data_path)
        
    #get original image name
    file_name = os.path.basename(icon_path)
    
    #join it to data path for full save location
    output_path = os.path.join(data_path, file_name)
    #ensure that it has a unique file name to not overwrite if named icon.png etc.
    output_path = get_unique_folder_name(output_path)
    
    try:
        logger.info(f"Trying to copy {icon_path} to {output_path}")
        shutil.copy(icon_path, output_path)
        return output_path
    
    except Exception as e:
        logger.error(f"Error copying file: {e}")
        return None
    
#takes output path and injects _local before the file extention
#if a copy with the same name already exists it becomes _local1, _local2, _local3 etc.
def get_unique_folder_name(folder_path):
    base, ext = os.path.splitext(folder_path)
    counter = 1
    new_folder = f"{base}_local{ext}"
    
    while os.path.exists(new_folder):
        new_folder = f"{base}_local{counter}{ext}"
        counter += 1
        
    return new_folder