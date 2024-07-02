from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QLabel, QCheckBox, QDialog, QFormLayout, QLineEdit, QKeySequenceEdit, QDialogButtonBox, QSlider
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon, QKeySequence
import sys
from pynput import keyboard
from settings import get_setting, set_setting, load_settings, save_settings, add_angle_brackets



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
        dialog.exec_()
    
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
    

class KeybindLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Click to set keybind")
        self.setReadOnly(True)
        self.key_sequence = []
        self.allow_input = True

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.clear()
        self.key_sequence = []
        self.allow_input = True

    def keyPressEvent(self, event):
        if not self.allow_input:
            return
        print(event.key())
        if event.key() <=16000000: # weird bug where it takes a modifier with no key pressed as a modifier + a bugged key input
            key = event.key()
            modifiers = event.modifiers()
            key_string = QKeySequence(modifiers | key).toString(QKeySequence.NativeText)
            print(key_string)
            if key_string not in self.key_sequence:
                self.key_sequence.append(key_string)
                print(self.key_sequence)
                self.allow_input = False
        
        self.setText("+".join(self.key_sequence))


    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.allow_input = False

    def get_keybind(self):
        return self.text()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.toggle_overlay_keybind_le = KeybindLineEdit()
        self.toggle_overlay_keybind_le.setText(settings.get("toggle_overlay_keybind", "alt+d"))
        layout.addRow("Toggle Overlay Keybind", self.toggle_overlay_keybind_le)

        self.window_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_opacity_slider.setMinimum(30)
        self.window_opacity_slider.setMaximum(100)
        self.window_opacity_slider.setSingleStep(1)
        self.window_opacity_slider.setSliderPosition(settings.get("window_opacity", 100))
        self.window_opacity_slider.valueChanged.connect(self.value_changed)
        self.window_opacity_slider.sliderMoved.connect(self.slider_position)
        self.window_opacity_slider.sliderPressed.connect(self.slider_pressed)
        self.window_opacity_slider.sliderReleased.connect(self.slider_released)

        
        layout.addRow("Overlay Opacity", self.window_opacity_slider)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def value_changed(self, i):
        print(i)
        if self.parent():
            self.parent().change_opacity(i)
        self.setWindowOpacity(1.0)

    def slider_position(self, p):
        print("position", p)

    def slider_pressed(self):
        print("Pressed!")

    def slider_released(self):
        print("Released")

    def save_settings(self):
        settings = load_settings()
        settings["update_on_launch"] = self.update_on_launch_cb.isChecked()
        settings["toggle_overlay_keybind"] = self.toggle_overlay_keybind_le.get_keybind()
        settings["window_opacity"] = self.window_opacity_slider.value()
        save_settings(settings)
        if self.parent():
            self.parent().set_hotkey()
        self.accept()
    def closeEvent(self, event):
        # Function to run before closing the dialog
        self.on_close()
        event.accept()  # Accept the event to close the window
    
    def on_close(self):
        settings = load_settings()
        save_settings(settings)
        window_opacity = get_setting("window_opacity", -1)
        self.parent().change_opacity(window_opacity)

def main():
    app = QApplication(sys.argv)
    overlay = OverlayWidget()
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()