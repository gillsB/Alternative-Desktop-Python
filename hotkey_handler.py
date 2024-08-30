from PySide6.QtCore import Signal, QObject
from pynput import keyboard
from settings import add_angle_brackets, get_setting
from display_warning import display_bad_overlay_keybind_warning
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
            self.toggle_signal.emit()

        def for_canonical(f):
            return lambda k: f(self.listener.canonical(k))

        if self.listener is not None:
            self.listener.stop()

        try: # Try setting the hotkey 
            hotkey_str = get_setting("toggle_overlay_keybind")
            parsed_hotkey = keyboard.HotKey.parse(add_angle_brackets(hotkey_str))
            # Hotkey is a valid hotkey, now set it.
            self.hotkey = keyboard.HotKey(parsed_hotkey, on_activate)

        except ValueError as e:
            # Handle invalid hotkey by setting it to default and logging the error
            logger.error(f"Invalid hotkey '{hotkey_str}': {e}. Setting to default 'alt+d'.")
            display_bad_overlay_keybind_warning(hotkey_str)
            parsed_hotkey = keyboard.HotKey.parse(add_angle_brackets("alt+d"))
            self.hotkey = keyboard.HotKey(parsed_hotkey, on_activate)

        self.listener = keyboard.Listener(
            on_press=for_canonical(self.hotkey.press),
            on_release=for_canonical(self.hotkey.release)
        )
        
        self.listener.start()


    def stop_listener(self):
        if self.listener:
            self.listener.stop()