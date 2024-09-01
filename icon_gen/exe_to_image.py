from icoextract import IconExtractor, IconExtractorError
from PIL import Image
import os
import logging


logger = logging.getLogger(__name__)

def exe_to_image(exe_path, output_path, icon_size):

    logger.info(f"Called with arguments: lnk_path = {exe_path}, output_path = {output_path}, icon_size = {icon_size}")

    try:
        logger.info("Attempting to extract the icon from the path")
        extractor = IconExtractor(exe_path)
        logger.info("Extraction successful")

        # Export the first group icon to a .ico file
        #extractor.export_icon(output_path, num=0)

        # Or read the .ico into a buffer, to pass it into other code
        data = extractor.get_icon(num=0)
        logger.info("Extracted icon loaded into buffer.")

        im = Image.open(data)
        img_resized = im.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        logger.info("Resized image (still in buffer).")

        # Save the resized image to the output path
        img_resized.save(output_path)
        logger.info(f"Icon saved to path = {output_path}, now returning this path.")

        return output_path

    except IconExtractorError as e:
        # No icons available, or the icon resource is malformed
        logger.error(f"IconExtractorError occurred extracting icon: {e}")
        pass
    except Exception as e:
        logger.error(f"Other error occurred: {e}")
        pass