import pylnk3
import os
from icon_gen.exe_to_image import exe_to_image
from icon_gen.extract_ico_file import extract_ico_file


def lnk_to_image(lnk_path, output_path, icon_size):
    # Read the .lnk file

    ico_path = None

    # Get the target path and icon index
    target_path = get_target_path(lnk_path)
    print(f"TARGET PATH = {target_path}")
    #icon_index = lnk.icon_index

    if extract_ico_file(target_path, output_path, icon_size) == True:
        ico_path = os.path.join(output_path, "icon.png")
        print("Copying .ico file directly")

    new_path = exe_to_image(target_path, output_path, icon_size)

    return ico_path, new_path
    

def get_target_path(lnk_path):
    lnk = pylnk3.parse(lnk_path)
    

    # Get the relative path
    relative_path = lnk.relative_path if hasattr(lnk, 'relative_path') else None

    # Get the base path (usually points to the Users directory)
    base_path = lnk.target if hasattr(lnk, 'target') else None

    if relative_path and base_path:
        # Combine base path with relative path
        full_path = os.path.normpath(os.path.join(os.path.dirname(base_path), relative_path))
    elif base_path:
        full_path = os.path.normpath(base_path)
    elif relative_path:
        # If we only have the relative path, try to resolve it from the LNK file location
        lnk_dir = os.path.dirname(lnk_path)
        full_path = os.path.normpath(os.path.join(lnk_dir, relative_path))
    else:
        full_path = None

    return full_path

