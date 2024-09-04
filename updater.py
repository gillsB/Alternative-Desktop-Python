import requests
import subprocess
import os
import sys
import logging
from PySide6.QtWidgets import (QApplication, QMessageBox, QDialog, QVBoxLayout, 
                               QLabel, QProgressBar, QPushButton)
from PySide6.QtCore import Qt, QThread, Signal

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

        if latest_version.lower() > CURRENT_VERSION.lower():
            logger.warning(f"New version available: {latest_version}")
            download_url = latest_release["assets"][0]["browser_download_url"]
            logger.info("New download link: " + download_url)
            show_update_message(download_url, latest_version)
        else:
            logger.info("You are running the latest version.")
    except requests.RequestException as e:
        logger.error(f"Error checking for updates: {e}")


def download_and_update(download_url, latest_version):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    download_window = DownloadWindow(download_url, latest_version)
    download_window.exec()

    if not QApplication.instance().closingDown():
        app.quit()

def show_update_message(download_url, latest_version):
    logger.info("Displaying show_update_message")

    # Check if QApplication instance exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    msg_box = QMessageBox()
    msg_box.setWindowTitle("Update Available")
    msg_box.setText(f"A new version is available.\n\n"
                    f"Current version: {CURRENT_VERSION}\n"
                    f"New version: {latest_version}\n\n"
                    "Would you like to install it?")
    
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.Yes)

    # Show the message box and capture the response
    response = msg_box.exec()
    if response == QMessageBox.Yes:
        logger.info("User chose to install the new version.")
        download_and_update(download_url, latest_version)
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

class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(str)

    def __init__(self, download_url, local_filename):
        super().__init__()
        self.download_url = download_url
        self.local_filename = local_filename

    def run(self):
        with requests.get(self.download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            with open(self.local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress_percentage = int((downloaded_size / total_size) * 100)
                        self.progress.emit(progress_percentage)
        self.finished.emit(self.local_filename)

class DownloadWindow(QDialog):
    def __init__(self, download_url, latest_version):
        super().__init__()
        self.setWindowTitle("Downloading Update")
        self.setWindowModality(Qt.ApplicationModal)

        self.label = QLabel(f"Downloading version {latest_version}...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

        temp_directory = os.getenv('TEMP')
        self.local_filename = os.path.join(temp_directory, f"Alternative_Desktop_update{latest_version}.exe")

        self.download_thread = DownloadThread(download_url, self.local_filename)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def download_finished(self, local_filename):
        logger.info(f"Downloaded {local_filename}")
        self.accept()  # Close the dialog
        run_installer(local_filename)

    def cancel_download(self):
        if self.download_thread.isRunning():
            self.download_thread.terminate()
            logger.info("Download canceled.")
        self.reject()  # Close the dialog without downloading