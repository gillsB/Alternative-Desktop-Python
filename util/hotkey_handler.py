from PySide6.QtCore import Signal, QObject
import keyboard
from util.settings import get_setting, set_setting
from menus.display_warning import display_bad_overlay_keybind_warning
import logging

logger = logging.getLogger(__name__)

class HotkeyHandler(QObject):
    toggle_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener = None
        self.set_hotkey()

    def set_hotkey(self):
        def on_activate():
            logger.info("Hotkey activated!")
            self.toggle_signal.emit()

        try:
            hotkey_str = get_setting("toggle_overlay_keybind")
            logger.info(f"Attempting to set hotkey: '{hotkey_str}'")

            # Check if the hotkey string specifically mentions numpad
            if "num" in hotkey_str:
                # Register numpad-specific hotkey only (will not respond to regular number keys)
                keyboard.add_hotkey(hotkey_str, on_activate)
                logger.info(f"Hotkey registered for numpad: {hotkey_str}")
            else:
                # Register hotkey for regular keys (will not respond to numpad keys)
                keyboard.add_hotkey(hotkey_str, on_activate)
                logger.info(f"Hotkey registered for regular key: {hotkey_str}")

        except ValueError as e:
            # Handle invalid hotkey by setting it to default and logging the error
            logger.error(f"Invalid hotkey '{hotkey_str}': {e}. Setting to default 'alt+d'.")
            display_bad_overlay_keybind_warning(hotkey_str)
            set_setting("toggle_overlay_keybind", "alt+d")
            keyboard.add_hotkey('alt+d', on_activate)

    def stop_listener(self):
        """Stops the hotkey listener."""
        keyboard.unhook_all_hotkeys()
        logger.info("Hotkey listener stopped.")
