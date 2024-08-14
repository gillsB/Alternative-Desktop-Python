from PySide6.QtCore import Signal, QObject
from pynput import keyboard
from settings import add_angle_brackets, get_setting






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

        self.hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(add_angle_brackets(get_setting("toggle_overlay_keybind"))),
            on_activate
        )

        self.listener = keyboard.Listener(
            on_press=for_canonical(self.hotkey.press),
            on_release=for_canonical(self.hotkey.release)
        )
        
        self.listener.start()


    def stop_listener(self):
        if self.listener:
            self.listener.stop()