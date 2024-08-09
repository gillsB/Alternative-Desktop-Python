import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def favicon_to_image(url, output_path):
    # Ensure target directory exists, create if it doesn't
    if os.path.exists(output_path) and os.path.isfile(output_path):
        ...
    else:
        os.makedirs(output_path, exist_ok=True)

    output_path = os.path.join(output_path, "icon3.png")
    favicon_url = get_favicon_url(url)
    if favicon_url:
        path = save_favicon(favicon_url, output_path)
        return path
    return

def get_favicon_url(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for the link tags that might contain the favicon
        icon_link = soup.find("link", rel=lambda value: value and "icon" in value.lower())
        if icon_link:
            icon_url = icon_link.get("href")
            # Join with the base URL to get the absolute path
            return urljoin(url, icon_url)

        # Fallback to common favicon location if no link tag is found
        parsed_url = urlparse(url)
        fallback_icon_url = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
        return fallback_icon_url

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def save_favicon(favicon_url, save_path):
    try:
        response = requests.get(favicon_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Favicon saved as {save_path}")
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the favicon: {e}")
    return

