import os
import requests
from PIL import Image
from bs4 import BeautifulSoup

ICON_SIZE = 128

def favicon_to_image(url, output_path):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        

        # attempt to get favicon from google favicon service
        google_api = f"https://www.google.com/s2/favicons?domain={url}&sz={ICON_SIZE}"
        try:
            output_path = os.path.join(output_path, "icon3.png")
            saved_path = save_favicon(google_api, output_path)
            return saved_path
        except requests.RequestException as e:
            print(f"Failed to fetch Google favicon: {e}")


        # Search for Apple Touch Icon or larger icon links on website
        icon_link = (
            soup.find("link", rel="apple-touch-icon") or
            soup.find("link", rel="apple-touch-icon-precomposed") or
            soup.find("link", rel="icon") or
            soup.find("link", rel="shortcut icon")
        )
        if icon_link:
            icon_url = icon_link.get("href")
            if not icon_url.startswith("http"):
                icon_url = url.rstrip("/") + "/" + icon_url.lstrip("/")
            saved_path = save_favicon(icon_url, output_path)
            return saved_path


    except requests.RequestException as e:
        print(f"Failed to fetch favicon: {e}")
        return None
    

def save_favicon(favicon_url, save_path):
    try:
        response = requests.get(favicon_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Favicon saved as {save_path}")
        
        # Resize the image to 128x128
        image = Image.open(save_path)
        resized_image = image.resize((128, 128), Image.Resampling.LANCZOS)
        resized_image.save(save_path)
        
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the favicon: {e}")
    return None


