import requests
import subprocess
import os
import sys
import logging
from PySide6.QtWidgets import QApplication, QMessageBox

logger = logging.getLogger(__name__)
CURRENT_VERSION = None
RELEASES_URL = None

def check_for_updates(current_version, releases_url):
    global CURRENT_VERSION, RELEASES_URL
    CURRENT_VERSION = current_version
    RELEASES_URL = releases_url
    try:
        response = requests.get(RELEASES_URL)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release["tag_name"]

        # Replace with the current version of your app
        if latest_version.lower() > CURRENT_VERSION.lower():
            logger.warning(f"New version available: {latest_version}")
            download_url = latest_release["assets"][0]["browser_download_url"]
            logger.info("New download link: " + download_url)
            download_and_update(download_url, latest_version)
        else:
            logger.info("You are running the latest version.")
    except requests.RequestException as e:
        logger.error(f"Error checking for updates: {e}")


def download_and_update(download_url, latest_version):
    temp_directory = os.getenv('TEMP') 
    local_filename = os.path.join(temp_directory, f"update_{latest_version}.exe")
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    logger.info(f"Downloaded {local_filename}")
    show_update_message(CURRENT_VERSION, latest_version, local_filename)

def show_update_message(current_version, latest_version, local_filename):
    logger.info("Displaying show_update_message")

    # Check if QApplication instance exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    msg_box = QMessageBox()
    msg_box.setWindowTitle("Update Available")
    msg_box.setText(f"A new version has been downloaded.\n\n"
                    f"Current version: {current_version}\n"
                    f"New version: {latest_version}\n\n"
                    "Would you like to install it?")
    
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.Yes)

    # Show the message box and capture the response
    response = msg_box.exec()
    if response == QMessageBox.Yes:
        logger.info("User chose to install the new version.")
        run_installer(local_filename)
    else:
        logger.info("User chose not to install the new version.")

    # If the app was created here, quit it
    if app and not QApplication.instance().closingDown():
        app.quit()

def run_installer(installer_path):
    try:
        logger.info(f"Running installer: {installer_path}")
        subprocess.Popen([installer_path], close_fds=True)
        logger.info("Installation initiated. Closing the application.")
        sys.exit(0)
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
    except subprocess.CalledProcessError as e:
         logger.error(f"Failed to run the installer: {e}")
    finally:
        # Delete the installer after it's run
        if os.path.exists(installer_path):
            try:
                os.remove(installer_path)
                logger.info(f"Deleted installer: {installer_path}")
            except OSError as e:
                logger.error(f"Error deleting installer: {e}")
