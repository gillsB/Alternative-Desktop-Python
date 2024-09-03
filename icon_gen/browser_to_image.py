import winreg
import logging
from icon_gen.exe_to_image import exe_to_image

logger = logging.getLogger(__name__)


def browser_to_image(output_path, icon_size):
    logger.info(f"Called with arguments: output_path = {output_path}, icon_size = {icon_size}")
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
        prog_id = winreg.QueryValueEx(key, 'ProgId')[0]
    
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, fr"{prog_id}\shell\open\command") as key:
        command = winreg.QueryValueEx(key, None)[0]
    
    path = command.split('"')[1]
    logger.info(f"Path for default browser = {path}")
    return exe_to_image(path, output_path, icon_size)



