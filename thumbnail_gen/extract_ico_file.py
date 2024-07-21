import os
import shutil
from PIL import Image





def has_ico_file(source_file, target_dir):

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

            image = Image.open(target_ico_file)
            resized_image = image.resize((256,256), Image.Resampling.LANCZOS)

            resized_image.save(target_ico_file)
            found = True
            print(f"Copied {filename} to {target_dir}")
    
    return found