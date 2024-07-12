import pylnk3
from PIL import Image
import win32gui
import win32ui
import win32con

def extract_icon_from_lnk(lnk_path, output_path):
    # Read the .lnk file
    lnk = pylnk3.parse(lnk_path)

    # Get the target path and icon index
    target_path = lnk.path
    icon_index = lnk.icon_index

    # Get the icon handle
    large, small = win32gui.ExtractIconEx(target_path, icon_index)

    # Ensure the handle is valid
    if large:
        hicon = large[0]
    elif small:
        hicon = small[0]
    else:
        raise ValueError("No icon found in the .lnk file")

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

