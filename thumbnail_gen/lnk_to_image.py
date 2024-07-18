import pylnk3
from thumbnail_gen.exe_to_image import extract_ico_from_exe
from thumbnail_gen.extract_ico_file import has_ico_file

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
    



