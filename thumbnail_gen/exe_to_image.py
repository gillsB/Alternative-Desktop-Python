from icoextract import IconExtractor, IconExtractorError
from PIL import Image
import os
from thumbnail_gen.extract_ico_file import has_ico_file



def exe_to_image(lnk_path, output_path):


    try:
        extractor = IconExtractor(lnk_path)

        output_path = os.path.join(output_path, "icon2.png")

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