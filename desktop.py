import sys
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QDialog, QFormLayout)
from PyQt5.QtCore import Qt
import keyboard


SETTINGS_FILE = "config/settings.json"

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Settings")
        layout = QFormLayout()
        self.setLayout(layout)

        self.update_on_launch_cb = QCheckBox()
        settings = load_settings()
        self.update_on_launch_cb.setChecked(settings.get("update_on_launch", True))

        layout.addRow("Update on Launch", self.update_on_launch_cb)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def save_settings(self):
        settings = {
            "update_on_launch": self.update_on_launch_cb.isChecked()
        }
        save_settings(settings)
        self.accept()

class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        #self.setAttribute(Qt.WA_TranslucentBackground)
        #self.setWindowOpacity(0.8)  # Semi-transparent

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel("Overlay Desktop")
        label.setStyleSheet("color: white; font-size: 20px;")
        layout.addWidget(label)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setGeometry(300, 300, 300, 200)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def show_settings(self):
        dialog = SettingsDialog()
        dialog.exec_()

def show_overlay():
    overlay = OverlayWidget()
    overlay.show()
    return overlay

def main():
    app = QApplication(sys.argv)

    keyboard.add_hotkey("Alt+d", show_overlay())

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()