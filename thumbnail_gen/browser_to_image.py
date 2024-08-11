import winreg
import os
from PIL import Image
from icoextract import IconExtractor, IconExtractorError

def browser_to_image(output_path):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
        prog_id = winreg.QueryValueEx(key, 'ProgId')[0]
    
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, fr"{prog_id}\shell\open\command") as key:
        command = winreg.QueryValueEx(key, None)[0]
    
    path = command.split('"')[1]
    return get_icon(path, output_path)

def get_icon(path, output_path):
    try:
        extractor = IconExtractor(path)

        output_path = os.path.join(output_path, "icon4.png")

        # Export the first group icon to a .ico file
        extractor.export_icon(output_path, num=0)

        # Or read the .ico into a buffer, to pass it into other code
        data = extractor.get_icon(num=0)

        #from PIL import Image
        im = Image.open(data)
        img_resized = im.resize((256, 256), Image.Resampling.LANCZOS)

        # Save the resized image to the output path
        img_resized.save(output_path)
        # ... manipulate a copy of the icon

        return output_path

    except IconExtractorError:
        # No icons available, or the icon resource is malformed
        pass



