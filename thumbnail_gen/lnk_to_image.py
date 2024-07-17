import pylnk3
from PIL import Image
from win32 import win32gui
import win32ui
import os

def extract_icon_from_lnk(lnk_path, output_path):
    # Read the .lnk file
    lnk = pylnk3.parse(lnk_path)

    # Get the target path and icon index
    target_path = lnk.path
    icon_index = lnk.icon_index

    # Try to extract the icon from the target executable
    large, small = win32gui.ExtractIconEx(target_path, icon_index)
    
    # If icon extraction fails, search for .ico file in the same directory
    if not large and not small:
        target_dir = os.path.dirname(target_path)
        ico_files = [file for file in os.listdir(target_dir) if file.lower().endswith('.ico')]
        if ico_files:
            fallback_icon_path = os.path.join(target_dir, ico_files[0])
            large, small = win32gui.ExtractIconEx(fallback_icon_path, 0)

    # Ensure the handle is valid
    if large:
        hicon = large[0]
    elif small:
        hicon = small[0]
    else:
        raise ValueError("No icon found in the .lnk file and no .ico file found in the target directory")

    # Create a device context
    dc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
    dc_with_icon = dc.CreateCompatibleDC()

    # Create a bitmap
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(dc, 32, 32)
    dc_with_icon.SelectObject(bmp)

    # Draw the icon into the bitmap
    dc_with_icon.DrawIcon((0, 0), hicon)

    # Get the bitmap as a PIL Image
    bmp_info = bmp.GetInfo()
    bmp_bits = bmp.GetBitmapBits(True)
    image = Image.frombuffer('RGBA', (bmp_info['bmWidth'], bmp_info['bmHeight']), bmp_bits, 'raw', 'BGRA', 0, 1)

    # Save the icon as an image file
    image.save(output_path)

    # Clean up
    dc_with_icon.DeleteDC()
    win32gui.DeleteObject(bmp.GetHandle())
    win32gui.DestroyIcon(hicon)

    print(f"Icon saved to {output_path}")