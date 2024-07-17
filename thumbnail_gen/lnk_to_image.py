import pylnk3
from PIL import Image
from win32 import win32gui
import win32ui
import os
import shutil
from thumbnail_gen.exe_to_image import extract_ico_from_exe

def extract_icon_from_lnk(lnk_path, output_path):
    # Read the .lnk file
    lnk = pylnk3.parse(lnk_path)

    # Get the target path and icon index
    target_path = lnk.path
    icon_index = lnk.icon_index

    extract_ico_from_exe(target_path, output_path)
    



