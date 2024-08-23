import ctypes
from ctypes import wintypes
from PIL import Image
import os

# Constants for SHGetFileInfo function
SHGFI_ICON = 0x000000100
SHGFI_LARGEICON = 0x000000000  # Large icon
SHGFI_SMALLICON = 0x000000001  # Small icon
SHGFI_USEFILEATTRIBUTES = 0x000000010  # Retrieve icon based on file attributes

# Structures used by the Shell functions
class SHFILEINFO(ctypes.Structure):
    _fields_ = [("hIcon", wintypes.HICON),
                ("iIcon", wintypes.INT),
                ("dwAttributes", wintypes.DWORD),
                ("szDisplayName", wintypes.WCHAR * 260),
                ("szTypeName", wintypes.WCHAR * 80)]

# Define the BITMAPINFOHEADER structure
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]

# Define the BITMAPINFO structure
class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3)]

# Load the required libraries
shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def default_icon_to_image(file_path, output_path, icon_size):
    shfileinfo = SHFILEINFO()
    flags = SHGFI_ICON | SHGFI_LARGEICON | SHGFI_USEFILEATTRIBUTES
    
    # Call the SHGetFileInfo function
    res = shell32.SHGetFileInfoW(file_path, 0, ctypes.byref(shfileinfo), ctypes.sizeof(shfileinfo), flags)
    
    if res == 0:
        # Try to get the default icon for unknown file types
        file_attributes = 0x80  # FILE_ATTRIBUTE_NORMAL
        flags |= SHGFI_USEFILEATTRIBUTES
        res = shell32.SHGetFileInfoW(file_path, file_attributes, ctypes.byref(shfileinfo), ctypes.sizeof(shfileinfo), flags)
        
        if res == 0:
            raise FileNotFoundError(f"Unable to retrieve icon for: {file_path}")
    
    # Get the icon handle
    hicon = shfileinfo.hIcon
    
    # Icon dimensions (start with large icon)
    width, height = (32, 32)
    
    # Create a device context (DC) for drawing
    hdc = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc)
    
    # Create a compatible bitmap
    hbmp = gdi32.CreateCompatibleBitmap(hdc, width, height)
    old_bmp = gdi32.SelectObject(hdc_mem, hbmp)
    
    # Draw the icon into the memory device context
    user32.DrawIconEx(hdc_mem, 0, 0, hicon, width, height, 0, 0, 0x0003)
    
    # Create a buffer to store the bitmap data
    buffer = (ctypes.c_char * (width * height * 4))()
    bmp_info = BITMAPINFO()
    
    bmp_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmp_info.bmiHeader.biWidth = width
    bmp_info.bmiHeader.biHeight = -height
    bmp_info.bmiHeader.biPlanes = 1
    bmp_info.bmiHeader.biBitCount = 32
    bmp_info.bmiHeader.biCompression = 0  # BI_RGB
    
    # Get the bitmap data
    gdi32.GetDIBits(hdc_mem, hbmp, 0, height, ctypes.byref(buffer), ctypes.byref(bmp_info), 0)
    
    # Convert the buffer to an image using PIL
    img = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)
    
    # Resize the image to the specified icon_size using LANCZOS resampling
    img_resized = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    output_path = os.path.join(output_path, "icon4.png")
    
    # Save the resized image to the output path
    img_resized.save(output_path)
    
    # Clean up
    gdi32.SelectObject(hdc_mem, old_bmp)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc)
    user32.DestroyIcon(hicon)
    
    print(f"Icon saved to {output_path}")

    return output_path
