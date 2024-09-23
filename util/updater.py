import requests
import subprocess
import os
import sys
import logging
from PySide6.QtWidgets import (QApplication, QMessageBox, QDialog, QVBoxLayout, 
                               QLabel, QProgressBar, QPushButton)
from PySide6.QtCore import Qt, QThread, Signal
from util.settings import set_setting

logger = logging.getLogger(__name__)
CURRENT_VERSION = None
RELEASES_URL = None
LATEST_VERSION = None
FILE_NAME = None
FULL_LOCAL_PATH = None

def check_for_updates(current_version, releases_url):
    global CURRENT_VERSION, RELEASES_URL, FILE_NAME, FULL_LOCAL_PATH, LATEST_VERSION
    CURRENT_VERSION = current_version
    RELEASES_URL = releases_url
    try:
        response = requests.get(RELEASES_URL)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release["tag_name"]

        if latest_version.lower() > CURRENT_VERSION.lower():
            logger.warning(f"New version available: {latest_version}")
            download_url = latest_release["assets"][0]["browser_download_url"]
            logger.info("New download link: " + download_url)
            LATEST_VERSION = latest_version
            FILE_NAME = f"Alternative_Desktop_update{latest_version}.exe"
            temp_directory = os.getenv('TEMP')
            FULL_LOCAL_PATH = os.path.join(temp_directory, FILE_NAME)
            show_update_message(download_url)
        else:
            logger.info("You are running the latest version.")
    except requests.RequestException as e:
        logger.error(f"Error checking for updates: {e}")


def download_and_update(download_url):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    download_window = DownloadWindow(download_url)
    download_window.exec()

    if not QApplication.instance().closingDown():
        app.quit()

def show_update_message(download_url):
    logger.info("Displaying show_update_message")

    # Check if QApplication instance exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    msg_box = QMessageBox()
    msg_box.setWindowTitle("Update Available")
    msg_box.setText(f"A new version is available.\n\n"
                    f"Current version: {CURRENT_VERSION}\n"
                    f"New version: {LATEST_VERSION}\n\n"
                    "Would you like to install it?")
    
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.Yes)

    # Show the message box and capture the response
    response = msg_box.exec()
    if response == QMessageBox.Yes:
        logger.info("User chose to install the new version.")
        set_setting("show_patch_notes", True)

        # Check if file already in temp (downloaded but canceled/stopped installer)

        if file_in_temp():
            logger.info(f"Update file seems to have been found in temp folder {FULL_LOCAL_PATH}")
            install_or_redownload_menu(download_url)
        else:
            download_and_update(download_url)
    else:
        logger.info("User chose not to install the new version.")

    # If the app was created here, quit it
    if app and not QApplication.instance().closingDown():
        app.quit()

def file_in_temp():
    if os.path.exists(FULL_LOCAL_PATH):
        return True
    return False

def install_or_redownload_menu(download_url):
    logger.info("Displaying install or redownload menu")

    # Check if QApplication instance exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    msg_box = QMessageBox()
    msg_box.setWindowTitle("Update downloaded")
    msg_box.setText(f"Update {LATEST_VERSION} seems to have already been downloaded.\n\n"
                    f"Current version: {CURRENT_VERSION}\n"
                    f"New version: {LATEST_VERSION}\n\n"
                    "If you do not remember downloading it, or think something might be wrong with it, please redownload and install.")
    
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Retry | QMessageBox.Cancel)
    msg_box.setDefaultButton(QMessageBox.Yes)
    msg_box.button(QMessageBox.Yes).setText("Install")
    msg_box.button(QMessageBox.Retry).setText("Redownload and Install")

    result = msg_box.exec()
    if result == QMessageBox.Yes:
        run_installer()
    elif result == QMessageBox.Retry:
        download_and_update(download_url)
    else:
        if app and not QApplication.instance().closingDown():
            app.quit()

def run_installer():
    try:
        logger.info(f"Running installer: {FULL_LOCAL_PATH}")
        process = subprocess.Popen([FULL_LOCAL_PATH], close_fds=True)
        sys.exit(0)
        # Exit the program upon launching installer as the installer cannot install while program running.
        # If I want to do cleanup etc. I need to do it on next launch not, leaving the program running.
        # I think this setup only works if you have the dependencies to have it running installed i.e. worked on my main setup at the time.

        #process.wait()  # Wait for the installer to finish
        #logger.info("Installation completed. Closing the application.")
        
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run the installer: {e}")
    #finally:
        # Delete the installer after it's run
        #if os.path.exists(installer_path):
        #    try:
        #        os.remove(installer_path)
        #        logger.info(f"Deleted installer: {installer_path}")
        #    except OSError as e:
        #        logger.error(f"Error deleting installer: {e}")

class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

    def run(self):
        with requests.get(self.download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            with open(FULL_LOCAL_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress_percentage = int((downloaded_size / total_size) * 100)
                        self.progress.emit(progress_percentage)
        self.finished.emit(FULL_LOCAL_PATH)

class DownloadWindow(QDialog):
    def __init__(self, download_url):
        super().__init__()
        self.setWindowTitle("Downloading Update")
        self.setWindowModality(Qt.ApplicationModal)

        self.label = QLabel(f"Downloading version {LATEST_VERSION}...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

        self.download_thread = DownloadThread(download_url)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def download_finished(self):
        logger.info(f"Downloaded {FULL_LOCAL_PATH}")
        self.accept()  # Close the dialog
        run_installer()

    def cancel_download(self):
        if self.download_thread.isRunning():
            self.download_thread.terminate()
            logger.info("Download canceled.")
        self.reject()  # Close the dialog without downloading