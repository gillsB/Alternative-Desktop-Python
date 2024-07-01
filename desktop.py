from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QLabel, QCheckBox, QDialog, QFormLayout, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import sys
from pynput import keyboard
from settings import get_setting, set_setting, load_settings, save_settings


class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        #self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.setWindowTitle("Overlay Desktop")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()
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

    def hotkey(self):
        def on_activate():
            if not self.isMinimized:
                self.showMinimized()
                self.isMinimized = True
            else:
                self.showNormal()
                self.isMinimized = False

        def for_canonical(f):
            return lambda k: f(l.canonical(k))

        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(get_setting("toggle_overlay_keybind")),
            on_activate
        )
        l = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)
        )
        l.start()

    def show_settings(self):
        dialog = SettingsDialog()
        dialog.exec_()

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Settings")
        layout = QFormLayout()
        self.setLayout(layout)

        # Checkbox for update on launch
        self.update_on_launch_cb = QCheckBox()
        settings = load_settings()
        self.update_on_launch_cb.setChecked(settings.get("update_on_launch", True))
        layout.addRow("Update on Launch", self.update_on_launch_cb)

        # Line edit for toggle overlay keybind
        self.toggle_overlay_keybind_le = QLineEdit()
        self.toggle_overlay_keybind_le.setText(settings.get("toggle_overlay_keybind", "<alt>+d"))
        layout.addRow("Toggle Overlay Keybind", self.toggle_overlay_keybind_le)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def save_settings(self):
        settings = load_settings()
        settings["update_on_launch"] = self.update_on_launch_cb.isChecked()
        settings["toggle_overlay_keybind"] = self.toggle_overlay_keybind_le.text()
        save_settings(settings)
        self.accept()




def main():
    app = QApplication(sys.argv)
    overlay = OverlayWidget()
    overlay.show()
    overlay.hotkey()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()