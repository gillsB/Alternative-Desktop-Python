from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QLabel, QCheckBox, QDialog, QFormLayout, QLineEdit, QKeySequenceEdit, QDialogButtonBox, QSlider
from PySide6.QtCore import Qt, QEvent, QKeyCombination
from PySide6.QtGui import QIcon, QKeySequence
import sys
from pynput import keyboard
from settings import get_setting, set_setting, load_settings, save_settings, add_angle_brackets
from settingsMenu import SettingsDialog



class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        #self.setAttribute(Qt.WA_TranslucentBackground)
        window_opacity = get_setting("window_opacity", -1)
        window_opacity = float(window_opacity/100)
        self.setWindowOpacity(window_opacity)
        self.setWindowTitle("Overlay Desktop")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.label = QLabel("Overlay Desktop", self)
        self.label.setStyleSheet("font-size: 20px;")

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        

        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.close)
        

        layout.addWidget(self.label)
        layout.addWidget(settings_button)
        layout.addWidget(self.closeButton)
        self.listener = None
        self.set_hotkey()

    def show_settings(self):
        dialog = SettingsDialog(parent=self)
        dialog.exec()
    
    def set_hotkey(self):
        def on_activate():
            if not self.isMinimized:
                self.showMinimized()
                self.isMinimized = True
            else:
                self.showNormal()
                self.isMinimized = False
        
        def for_canonical(f):
            return lambda k: f(self.listener.canonical(k))
        
        if self.listener is not None:
            self.listener.stop()
            self.listener.join()
        
        # Create the HotKey object with the current hotkey setting
        self.hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(add_angle_brackets(get_setting("toggle_overlay_keybind"))),
            on_activate
        )
        # Create a listener for the HotKey
        self.listener = keyboard.Listener(
            on_press=for_canonical(self.hotkey.press),
            on_release=for_canonical(self.hotkey.release)
        )
        
        self.listener.start()
    def change_opacity(self ,i):
        print("change_opacity = ")
        print(float(i/100))
        self.setWindowOpacity(float(i/100))
    

def main():
    app = QApplication(sys.argv)
    overlay = OverlayWidget()
    overlay.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()