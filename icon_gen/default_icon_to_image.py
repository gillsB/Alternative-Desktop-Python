import ctypes
from ctypes import wintypes
from PIL import Image
import logging

# Constants for SHGetFileInfo function
SHGFI_ICON = 0x000000100
SHGFI_LARGEICON = 0x000000000  # Large icon
SHGFI_SMALLICON = 0x000000001  # Small icon
SHGFI_USEFILEATTRIBUTES = 0x000000010  # Retrieve icon based on file attributes

logger = logging.getLogger(__name__)

class SHFILEINFO(ctypes.Structure):
    _fields_ = [("hIcon", wintypes.HICON),
                ("iIcon", wintypes.INT),
                ("dwAttributes", wintypes.DWORD),
                ("szDisplayName", wintypes.WCHAR * 260),
                ("szTypeName", wintypes.WCHAR * 80)]
    
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

class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3)]

# Load the required libraries
shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

logger.info("Loaded shell32, user32, and gdi32 libraries.")

def default_icon_to_image(file_path, output_path, icon_size, retries=5):
    logger.info(f"Called with arguments: file_path = {file_path} output_path = {output_path}, icon_size = {icon_size} retries = {retries}")
    
    def get_icon_handle():
        shfileinfo = SHFILEINFO()
        flags = SHGFI_ICON | SHGFI_LARGEICON | SHGFI_USEFILEATTRIBUTES
        res = shell32.SHGetFileInfoW(file_path, 0, ctypes.byref(shfileinfo), ctypes.sizeof(shfileinfo), flags)
        
        if res == 0:
            logger.warning(f"Failed to retrieve icon for {file_path} using default attributes.")
            file_attributes = 0x80  # FILE_ATTRIBUTE_NORMAL
            flags |= SHGFI_USEFILEATTRIBUTES
            res = shell32.SHGetFileInfoW(file_path, file_attributes, ctypes.byref(shfileinfo), ctypes.sizeof(shfileinfo), flags)
            
            if res == 0:
                logger.error(f"Unable to retrieve icon for {file_path}.")
                return None
        
        return shfileinfo.hIcon
    
    hicon = None
    for attempt in range(retries):
        logger.info(f"Attempt {attempt + 1} to retrieve icon handle.")
        hicon = get_icon_handle()
        if hicon and 0 <= hicon <= 2**32-1:
            logger.info("Successfully retrieved icon handle.")
            break
        else:
            logger.warning(f"Invalid icon handle received on attempt {attempt + 1}.")
            hicon = None

    if not hicon:
        logger.error(f"Unable to retrieve a valid icon handle after {retries} attempts. Returning with a basic unknown.png")
        return "assets/images/unknown.png"
        
        
    
    width, height = (32, 32)
    logger.info(f"Creating device context for icon of size {width}x{height}.")

    hdc = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc)

    hbmp = gdi32.CreateCompatibleBitmap(hdc, width, height)
    if not hbmp:
        logger.error("Failed to create a compatible bitmap.")
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc)
        raise ValueError("Failed to create a compatible bitmap.")

    old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

    try:
        logger.info("Drawing icon onto the bitmap.")
        success = user32.DrawIconEx(hdc_mem, 0, 0, hicon, width, height, 0, 0, 0x0003)
        if not success:
            logger.error("Failed to draw icon.")
            raise ctypes.WinError(ctypes.get_last_error())

        buffer = (ctypes.c_char * (width * height * 4))()
        bmp_info = BITMAPINFO()

        bmp_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmp_info.bmiHeader.biWidth = width
        bmp_info.bmiHeader.biHeight = -height
        bmp_info.bmiHeader.biPlanes = 1
        bmp_info.bmiHeader.biBitCount = 32
        bmp_info.bmiHeader.biCompression = 0  # BI_RGB

        gdi32.GetDIBits(hdc_mem, hbmp, 0, height, ctypes.byref(buffer), ctypes.byref(bmp_info), 0)
        logger.info("Successfully retrieved bitmap data.")

        img = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)
        img_resized = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

        img_resized.save(output_path)
        logger.info(f"Icon saved to {output_path}")

    finally:
        gdi32.SelectObject(hdc_mem, old_bmp)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc)

        if hicon and 0 <= hicon <= 2**32-1:
            try:
                user32.DestroyIcon(hicon)
                logger.info("Icon handle destroyed successfully.")
            except Exception as e:
                logger.warning(f"Failed to destroy icon handle: {e}")

    return output_path