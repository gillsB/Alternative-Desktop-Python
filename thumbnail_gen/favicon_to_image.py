import os
import requests
from PIL import Image

FAVICON_SIZE = 128

def favicon_to_image(url, output_path, icon_size):

    # attempt to get favicon from google favicon service
    google_api = f"https://www.google.com/s2/favicons?domain={url}&sz={FAVICON_SIZE}"
    try:
        output_path = os.path.join(output_path, "icon3.png")
        saved_path = save_favicon(google_api, output_path, icon_size)
        return saved_path
    except requests.RequestException as e:
        print(f"Failed to fetch Google favicon: {e}")


    

def save_favicon(favicon_url, save_path, icon_size):
    try:
        response = requests.get(favicon_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Favicon saved as {save_path}")
        
        # Resize the image to 128x128
        image = Image.open(save_path)
        resized_image = image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        resized_image.save(save_path)
        
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the favicon: {e}")
    return None


