from PySide6.QtCore import Signal, QObject
from pynput import keyboard
from util.settings import add_angle_brackets, get_setting, set_setting
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

        if self.listener is not None:
            self.listener.stop()

        # Define mapping for numpad keys
        numpad_keys = {
            'numpad0': 96,
            'numpad1': 97,
            'numpad2': 98,
            'numpad3': 99,
            'numpad4': 100,
            'numpad5': 101,
            'numpad6': 102,
            'numpad7': 103,
            'numpad8': 104,
            'numpad9': 105,
            'numpadadd': 107,
            'numpadsubtract': 109,
            'numpadmultiply': 106,
            'numpaddivide': 111,
            'numpadenter': 13,
        }

        try:
            hotkey_str = get_setting("toggle_overlay_keybind")
            logger.info(f"Attempting to set hotkey: '{hotkey_str}'")

            if hotkey_str.lower() in numpad_keys:
                target_vk = numpad_keys[hotkey_str.lower()]
                logger.info(f"Numpad key detected: {hotkey_str}, vk: {target_vk}")
                self.is_numpad = True
                self.target_vk = target_vk
                parsed_hotkey = {keyboard.KeyCode(vk=target_vk)}
            else:
                # For non-numpad keys, use the existing parsing logic
                parsed_hotkey_str = add_angle_brackets(hotkey_str)
                logger.info(f"Parsed hotkey string: {parsed_hotkey_str}")
                parsed_hotkey = set(keyboard.HotKey.parse(parsed_hotkey_str))
                logger.info(f"Parsed hotkey: {parsed_hotkey}")
                self.is_numpad = False

            # Create the HotKey object for both numpad and non-numpad keys
            self.hotkey = keyboard.HotKey(parsed_hotkey, on_activate)

            def on_press(key):
                logger.debug(f"Key pressed: {key}")
                if self.is_numpad:
                    if isinstance(key, keyboard.KeyCode) and key.vk == self.target_vk:
                        logger.info(f"Numpad key {hotkey_str} pressed")
                        on_activate()
                else:
                    self.hotkey.press(self.listener.canonical(key))

            def on_release(key):
                logger.debug(f"Key released: {key}")
                if not self.is_numpad:
                    self.hotkey.release(self.listener.canonical(key))

            self.listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            
            self.listener.start()
            logger.info("Listener started")

        except ValueError as e:
            # Handle invalid hotkey by setting it to default and logging the error
            logger.error(f"Invalid hotkey '{hotkey_str}': {e}. Setting to default 'alt+d'.")
            display_bad_overlay_keybind_warning(hotkey_str)
            set_setting("toggle_overlay_keybind", "alt+d")
            parsed_hotkey = set(keyboard.HotKey.parse(add_angle_brackets("alt+d")))
            self.hotkey = keyboard.HotKey(parsed_hotkey, on_activate)
            self.is_numpad = False

            self.listener = keyboard.Listener(
                on_press=lambda k: self.hotkey.press(self.listener.canonical(k)),
                on_release=lambda k: self.hotkey.release(self.listener.canonical(k))
            )
            
            self.listener.start()


    def stop_listener(self):
        if self.listener:
            self.listener.stop()