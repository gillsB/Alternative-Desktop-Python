from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QLabel, QCheckBox, QDialog, QFormLayout, QLineEdit, QKeySequenceEdit, QDialogButtonBox, QSlider
from PySide6.QtCore import Qt, QEvent, QKeyCombination
from PySide6.QtGui import QIcon, QKeySequence
import sys
from pynput import keyboard
from settings import get_setting, set_setting, load_settings, save_settings, add_angle_brackets




class KeybindLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Click to set keybind")
        self.setReadOnly(True)
        self.key_sequence = []
        self.allow_input = True
    is_changed = False
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.clear()
        self.key_sequence = []
        self.allow_input = True

    def keyPressEvent(self, event):
        if not self.allow_input:
            return
        self.parent().set_changed()
        # Check for valid key press
        if event.key() <= 16000000:
            key = Qt.Key(event.key())
            modifiers = event.modifiers()

            # Ensure modifiers is of type Qt.KeyboardModifier
            if isinstance(modifiers, Qt.KeyboardModifier):
                key_combination = QKeyCombination(modifiers, key)
                key_sequence = QKeySequence(key_combination)

                print(key)
                print(modifiers)
                
                key_string = key_sequence.toString(QKeySequence.SequenceFormat.NativeText)
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
    is_changed = False
    def initUI(self):
        self.setWindowTitle("Settings")
        layout = QFormLayout()
        self.setLayout(layout)

        # Checkbox for update on launch
        self.update_on_launch_cb = QCheckBox()
        settings = load_settings()
        self.update_on_launch_cb.setChecked(settings.get("update_on_launch", True))
        self.update_on_launch_cb.clicked.connect(self.set_changed)
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
        self.set_changed()
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
        settings = load_settings()
        
        if self.is_changed == False:
            print("no changeds made in settings")
            event.accept()
        else:
            ret = QMessageBox.warning(self,"Settings NOT saved", "Do you wish to discard these changes?", QMessageBox.Ok | QMessageBox.Cancel)
            if ret == QMessageBox.Ok:
                self.on_close()
                event.accept()
            else:
                event.ignore()
    
    def set_changed(self):
        print("changed")
        self.is_changed = True

    def on_close(self):
        settings = load_settings()
        save_settings(settings)
        window_opacity = get_setting("window_opacity", -1)
        self.parent().change_opacity(window_opacity)