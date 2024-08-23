import os
import shutil
from PIL import Image
import stat
import ctypes



#Returns true if found and copied to target_dir, returns false if no .ico found
def extract_ico_file(source_file, target_dir, icon_size):

    found = False
    # Ensure target directory exists, create if it doesn't
    if os.path.exists(target_dir) and os.path.isfile(target_dir):
        ...
    else:
        os.makedirs(target_dir, exist_ok=True)
    
    # Extract the directory path of the source file
    source_dir = os.path.dirname(source_file)
    
    print(f"searching directory: {source_file}")
    # Iterate over files in the directory containing source_file
    for filename in os.listdir(source_dir):
        if filename.endswith(".ico"):

            print(".ico file has been found")
            source_ico_file = os.path.join(source_dir, filename)

            print(f"target dir = {target_dir}")
            #name of file
            target_ico_file = os.path.join(target_dir, "icon.png")
            shutil.copy2(source_ico_file, target_ico_file)
            
            #remove permissions and remove hidden attribute from our version of the .ico
            try:
                os.chmod(target_ico_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                remove_hidden_attribute(target_ico_file)
            except FileNotFoundError as e:
                print(f"Error: File not found after copying to data directory error: {e}")

            image = Image.open(target_ico_file)
            resized_image = image.resize((icon_size,icon_size), Image.Resampling.LANCZOS)

            resized_image.save(target_ico_file)
            found = True
            print(f"Copied {filename} to {target_dir}")

    
    return found


def remove_hidden_attribute(file_path):
    # Define the Windows constants for attributes
    FILE_ATTRIBUTE_HIDDEN = 0x2

    # Get the current attributes of the file
    attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)

    if attrs == -1:
        raise FileNotFoundError(f"File not found: {file_path}")

    # Remove the hidden attribute
    new_attrs = attrs & ~FILE_ATTRIBUTE_HIDDEN
    ctypes.windll.kernel32.SetFileAttributesW(file_path, new_attrs)