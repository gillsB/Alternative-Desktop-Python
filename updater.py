import requests
import subprocess
import os
import sys


def check_for_updates(CURRENT_VERSION, RELEASES_URL):
    try:
        response = requests.get(RELEASES_URL)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release["tag_name"]

        # Replace with the current version of your app
        if latest_version.lower() > CURRENT_VERSION.lower():
            print(f"New version available: {latest_version}")
            download_url = latest_release["assets"][0]["browser_download_url"]
            print("New download link: " + download_url)
            download_and_update(download_url, latest_version)
        else:
            print("You are running the latest version.")
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")


def download_and_update(download_url, latest_version):
    temp_directory = os.getenv('TEMP') 
    local_filename = os.path.join(temp_directory, f"update_{latest_version}.exe")
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded {local_filename}")
    run_installer(local_filename)


def run_installer(installer_path):
    try:
        print(f"Running installer: {installer_path}")
        subprocess.Popen([installer_path], close_fds=True)
        print("Installation initiated. Closing the application.")
        sys.exit(0)
    except PermissionError as e:
        print(f"Permission error: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run the installer: {e}")
    finally:
        # Delete the installer after it's run
        if os.path.exists(installer_path):
            try:
                os.remove(installer_path)
                print(f"Deleted installer: {installer_path}")
            except OSError as e:
                print(f"Error deleting installer: {e}")
