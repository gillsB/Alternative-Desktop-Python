from PySide6.QtCore import Signal, QObject
import keyboard
from util.settings import get_setting, set_setting
from menus.display_warning import display_bad_overlay_keybind_warning, display_keybind_not_supported
import logging

logger = logging.getLogger(__name__)

MODIFIER_KEYS = {"ctrl", "shift", "alt", "windows", "cmd"}
NUMPAD_KEYS = {"num 0", "num 1", "num 2", "num 3", "num 4", "num 5", "num 6", "num 7", "num 8", "num 9"}

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

            # Separate the hotkey string into modifiers and the main key
            parts = hotkey_str.lower().split("+")
            modifiers = [mod for mod in parts if mod in MODIFIER_KEYS]
            main_key = parts[-1] if parts[-1] not in MODIFIER_KEYS else None

            if not main_key:
                raise ValueError("No valid key found in hotkey string.")

            # Convert the main key to a scan code
            try:
                if main_key in NUMPAD_KEYS:
                    # key_to_scan_codes[0] is the base number's scan code, [1] is the numpad only version
                    main_key_scan_code = keyboard.key_to_scan_codes(main_key)[1] 
                else:
                    if "num" in main_key or "/" in main_key:
                        display_keybind_not_supported(main_key)
                    # Non numpad key get the base version.
                    main_key_scan_code = keyboard.key_to_scan_codes(main_key)[0]
                logger.info(f"Main key '{main_key}' converted to scan code: {main_key_scan_code}")
            except IndexError:
                # Handle cases where no scan code is found
                logger.error(f"Scan code retrieval failed for key '{main_key}'.")
                raise ValueError(f"Key '{main_key}' does not have a valid scan code.")

            # Convert modifier keys to scan codes
            modifier_scan_codes = []
            for mod in modifiers:
                try:
                    mod_scan_code = keyboard.key_to_scan_codes(mod)[0]
                    modifier_scan_codes.append(mod_scan_code)
                    logger.info(f"Modifier '{mod}' converted to scan code: {mod_scan_code}")
                except ValueError:
                    logger.error(f"Modifier '{mod}' could not be converted to a scan code.")

            # Combine scan codes for the full hotkey
            full_scan_code_combination = modifier_scan_codes + [main_key_scan_code]
            logger.info(f"Registering hotkey with scan codes: {full_scan_code_combination}")

            # Register the hotkey using scan codes (convert list to tuple)
            keyboard.add_hotkey(tuple(full_scan_code_combination), on_activate)
            logger.info(f"Hotkey registered using scan codes: {full_scan_code_combination}")

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