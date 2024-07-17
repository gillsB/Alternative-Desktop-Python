import pylnk3
from PIL import Image
import os
import shutil
from thumbnail_gen.exe_to_image import extract_ico_from_exe
from PIL import Image

def extract_icon_from_lnk(lnk_path, output_path):
    # Read the .lnk file
    lnk = pylnk3.parse(lnk_path)

    # Get the target path and icon index
    target_path = lnk.path
    icon_index = lnk.icon_index

    if has_ico_file(target_path, output_path) == True:
        print("Copying .ico file directly")
    else:
        extract_ico_from_exe(target_path, output_path)
    


def has_ico_file(source_file, target_dir):
    # Ensure target directory exists, create if it doesn't
    os.makedirs(target_dir, exist_ok=True)
    
    # Extract the directory path of the source file
    source_dir = os.path.dirname(source_file)
    
    # Iterate over files in the directory containing source_file
    for filename in os.listdir(source_dir):
        if filename.endswith(".ico"):
            source_ico_file = os.path.join(source_dir, filename)

            #name of file
            target_ico_file = os.path.join(target_dir, "icon.png")
            shutil.copy2(source_ico_file, target_ico_file)

            #add code here
            image = Image.open(target_ico_file)
            resized_image = image.resize((256,256), Image.Resampling.LANCZOS)

            resized_image.save(target_ico_file)

            print(f"Copied {filename} to {target_dir}")
