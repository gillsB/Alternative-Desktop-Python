import os
from icon_gen.exe_to_image import exe_to_image
from icon_gen.extract_ico_file import extract_ico_file
import win32com.client
import logging

logger = logging.getLogger(__name__)

def lnk_to_image(lnk_path, output_path, icon_size):
    logger.info(f"Called with arguments: lnk_path = {lnk_path}, output_path = {output_path}, icon_size = {icon_size}")

    ico_path_exists = None

    # Get the target path and icon index
    target_path = get_lnk_target(lnk_path)
    logger.info(f"Target path = {target_path}")
    #icon_index = lnk.icon_index

    # Swapping icon2.png path (output_path) for ico's path which is icon.png
    output_path_parent = os.path.dirname(output_path)
    ico_path = os.path.join(output_path_parent, "icon.png")

    if extract_ico_file(target_path, ico_path, icon_size) == True:
        logger.info(f".ico file found copying to path = {ico_path}")
        ico_path_exists = ico_path

    if target_path != None:
        new_path = exe_to_image(target_path, output_path, icon_size)
        logger.info(f"exe_to_image returned with path = {new_path}")

    return ico_path_exists, new_path
    

def get_lnk_target(lnk_path):
    if not os.path.exists(lnk_path):
        logger.error(f"lnk_path does not exists: {lnk_path}")
        return None
    
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(lnk_path)
    target_path = shortcut.Targetpath
    
    if not os.path.exists(target_path):
        logger.error(f"target_path does not exists: {target_path}")
        return None
    
    return target_path

