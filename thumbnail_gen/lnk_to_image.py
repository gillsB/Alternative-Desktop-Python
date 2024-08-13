import pylnk3
import os
from thumbnail_gen.exe_to_image import exe_to_image
from thumbnail_gen.extract_ico_file import has_ico_file


def extract_icon_from_lnk(lnk_path, output_path, icon_size):
    # Read the .lnk file
    lnk = pylnk3.parse(lnk_path)

    ico_path = None

    # Get the target path and icon index
    target_path = lnk.path
    icon_index = lnk.icon_index

    if has_ico_file(target_path, output_path) == True:
        ico_path = os.path.join(output_path, "icon.png")
        print("Copying .ico file directly")

    new_path = exe_to_image(target_path, output_path, icon_size)

    return ico_path, new_path
    



