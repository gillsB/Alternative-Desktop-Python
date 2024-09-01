import os
import requests
from PIL import Image
import logging

FAVICON_SIZE = 128

logger = logging.getLogger(__name__)

def favicon_to_image(url, output_path, icon_size):
    logger.info(f"Called with arguments: url = {url}, output_path = {output_path}, icon_size = {icon_size}")
    # attempt to get favicon from google favicon service
    google_api = f"https://www.google.com/s2/favicons?domain={url}&sz={FAVICON_SIZE}"
    try:
        saved_path = save_favicon(google_api, output_path, icon_size)
        logger.info(f"Saved path set to: {saved_path}")
        return saved_path
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Google favicon: {e}")


    

def save_favicon(favicon_url, save_path, icon_size):
    logger.info(f"save_favicon called with: favicon_url = {favicon_url}, save_path = {save_path}, icon_size = {icon_size}")
    try:
        response = requests.get(favicon_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        logger.info(f"Favicon saved as {save_path}")
        
        # Resize the image to 128x128
        image = Image.open(save_path)
        resized_image = image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        resized_image.save(save_path)
        logger.info(f"icon resized to {icon_size}")
        
        return save_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading the favicon: {e}")
    except Exception as e:
        logger.error(f"Other unknown error: {e}")
    return None


