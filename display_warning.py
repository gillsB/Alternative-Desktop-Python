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