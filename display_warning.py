from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer
import logging

logger = logging.getLogger(__name__)


def display_bad_overlay_keybind_warning(hotkey):
    def show_warning():
        logger.warning("Displaying warning: Bad Toggle Overlay Keybind")
        QMessageBox.warning(
            None,  # Parent widget (None means no parent)
            "Bad Toggle Overlay Keybind",
            f"There was a problem assigning your toggle overlay to the keybind: '{hotkey}'. Has been reset to default: Alt+d. Please update the keybind in settings.",
            QMessageBox.Ok
        )
    
    # QTimer to not block main thread. (Async)
    QTimer.singleShot(1000, show_warning)

def display_lnk_cli_args_warning():
    logger.warning("Displaying warning: LNK with CLI arguments (unsupported) warning")
    QMessageBox.warning(
        None,
        "Warning .lnk",
        "Warning: .lnk files do not have command arguments support. Please add the command arguments to the .lnk file itself or replace the .lnk with the file it points to and add the command line arguments to that.",
        QMessageBox.Ok)
    
def display_icon_path_not_exist_warning(icon_path):
    return QMessageBox.warning(
                None,
                "Error: Icon Path",
                f"Error: Icon path, item at path: \n{icon_path}\ndoes not exist. \nClick OK save regardless, or Cancel to continue editing.",
                QMessageBox.Ok |
                QMessageBox.Cancel)

def display_executable_file_path_warning(exec_path):
    return QMessageBox.warning(
        None,
        "Warning: Executable File Path", 
        f"Warning: Executable path: '{exec_path}'\nitem does not exist. \nWould you like to continue saving with a bad exectuable path?", 
        QMessageBox.Ok | 
        QMessageBox.Cancel)