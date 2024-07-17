from icoextract import IconExtractor, IconExtractorError
from PIL import Image
import os



def extract_ico_from_exe(lnk_path, output_path):
    try:
        extractor = IconExtractor(lnk_path)

        # Export the first group icon to a .ico file
        extractor.export_icon(os.path.join(output_path, "icon.png"), num=0)

        # Or read the .ico into a buffer, to pass it into other code
        data = extractor.get_icon(num=0)

        #from PIL import Image
        im = Image.open(data)
        img_resized = im.resize((256, 256), Image.Resampling.LANCZOS)

        # Save the resized image to the output path
        img_resized.save(os.path.join(output_path, "icon.png"))
        # ... manipulate a copy of the icon

    except IconExtractorError:
        # No icons available, or the icon resource is malformed
        pass