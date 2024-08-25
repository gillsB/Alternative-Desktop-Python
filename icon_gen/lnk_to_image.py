import os
from icon_gen.exe_to_image import exe_to_image
from icon_gen.extract_ico_file import extract_ico_file
import win32com.client


def lnk_to_image(lnk_path, output_path, icon_size):
    # Read the .lnk file

    ico_path = None

    # Get the target path and icon index
    target_path = get_lnk_target(lnk_path)
    print(f"TARGET PATH = {target_path}")
    #icon_index = lnk.icon_index

    if extract_ico_file(target_path, output_path, icon_size) == True:
        ico_path = os.path.join(output_path, "icon.png")
        print("Copying .ico file directly")

    if target_path != None:
        new_path = exe_to_image(target_path, output_path, icon_size)

    return ico_path, new_path
    

def get_lnk_target(lnk_path):
    if not os.path.exists(lnk_path):
        return None
    
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(lnk_path)
    target_path = shortcut.Targetpath
    
    if not os.path.exists(target_path):
        return None
    
    return target_path

