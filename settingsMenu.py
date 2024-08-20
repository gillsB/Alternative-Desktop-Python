from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QDialog, QFormLayout, QLineEdit, QKeySequenceEdit, QDialogButtonBox, QSlider, QComboBox, QStyle, QFileDialog
from PySide6.QtCore import Qt, QEvent, QKeyCombination, QSize
from PySide6.QtGui import QIcon, QKeySequence
import sys
from pynput import keyboard
from settings import get_setting, set_setting, load_settings, save_settings, add_angle_brackets
from desktop_grid_menu import ClearableLineEdit
import os

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

        self.toggle_overlay_keybind_button = KeybindButton()
        self.toggle_overlay_keybind_button.setText(settings.get("toggle_overlay_keybind", "alt+d"))
        layout.addRow("Toggle Overlay Keybind", self.toggle_overlay_keybind_button)

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

        self.theme_selector = QComboBox()
        self.color_selector = QComboBox()

        # Add theme options
        self.theme_selector.addItems(['Dark', 'Light'])

        # Add color options
        self.colors = ['Amber', 'Blue', 'Cyan', 'Lightgreen', 'Pink', 'Purple', 'Red', 'Teal', 'Yellow']
        self.color_selector.addItems(self.colors)

        self.set_theme = get_setting("theme")
        if '_' in self.set_theme:
            split_theme = self.set_theme.rsplit('.', 1)[0]
            theme, color = split_theme.split('_', 1)

            if theme.capitalize() in ['Dark', 'Light']:
                self.theme_selector.setCurrentText(theme.capitalize())

            if color.capitalize() in self.colors:
                self.color_selector.setCurrentText(color.capitalize())
        else:
            print("Theme format is invalid. Themes will be set to default.")

        self.theme_selector.currentIndexChanged.connect(self.update_theme)
        self.color_selector.currentIndexChanged.connect(self.update_theme)

        layout.addRow("Theme", self.theme_selector)
        layout.addRow("", self.color_selector)

        self.background_selector = QComboBox()
        background_options = ['First found', "Both", "Video only", "Image only", "None"]
        self.background_selector.addItems(background_options)
        layout.addRow("Background sourcing:", self.background_selector)
        
        set_bg_option = get_setting("background_source")
        # format for background_source is no capitalize and "_" instead of " " therefore revert both
        self.background_selector.setCurrentText(set_bg_option.replace("_", " ").capitalize())


        # background path clearable line edits
        self.background_video = ClearableLineEdit()
        self.background_image = ClearableLineEdit()
        self.background_video.setText(settings.get("background_video", ""))
        self.background_image.setText(settings.get("background_image", ""))


        # folder buttons to open path in fileDialog
        video_folder_button = QPushButton(self)
        video_folder_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        video_folder_button.setIconSize(QSize(16,16))
        video_folder_button.setFocusPolicy(Qt.NoFocus)
        video_folder_button.clicked.connect(self.video_folder_button_clicked)
        image_folder_button = QPushButton(self)
        image_folder_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        image_folder_button.setIconSize(QSize(16,16))
        image_folder_button.setFocusPolicy(Qt.NoFocus)
        image_folder_button.clicked.connect(self.image_folder_button_clicked)
    
        # layouts to add folder buttons
        video_folder_layout = QHBoxLayout()
        video_folder_layout.addWidget(self.background_video)
        video_folder_layout.addWidget(video_folder_button)
        image_folder_layout = QHBoxLayout()
        image_folder_layout.addWidget(self.background_image)
        image_folder_layout.addWidget(image_folder_button)

        layout.addRow("Background Video path:", video_folder_layout)
        layout.addRow("Background Image path:", image_folder_layout)

        self.local_icons_cb = QCheckBox()
        self.local_icons_cb.setChecked(settings.get("local_icons", True))
        self.local_icons_cb.clicked.connect(self.set_changed)
        layout.addRow("Save icons locally", self.local_icons_cb)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def update_theme(self):
        category = self.theme_selector.currentText().lower()
        color = self.color_selector.currentText().lower()
        theme = f"{category}_{color}.xml"
        print(f"Selected theme: {theme}")
        self.parent().change_theme(theme)
        self.is_changed = True

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

        #cleanup background paths
        self.cleanup_bg_paths()
        if self.background_video.text() != "" and os.path.exists(self.background_video.text()) == False:
            ret = QMessageBox.warning(self, "Video does not exist",
                                    f"Video at path: {self.background_video.text()} Does Not Exist. Are you sure you want to save with an incorrect video file?",
                                    QMessageBox.Ok| QMessageBox.Cancel)
            if ret == QMessageBox.Cancel:   
                return
        if self.background_image.text() != "" and os.path.exists(self.background_image.text())  == False:
            ret = QMessageBox.warning(self, "Image does not exist",
                                    f"Image at path: {self.background_image.text()} Does Not Exist. Are you sure you want to save with an incorrect image file?",
                                    QMessageBox.Ok| QMessageBox.Cancel)
            if ret == QMessageBox.Cancel:   
                return


        settings = load_settings()
        settings["update_on_launch"] = self.update_on_launch_cb.isChecked()
        settings["toggle_overlay_keybind"] = self.toggle_overlay_keybind_button.get_keybind()
        settings["window_opacity"] = self.window_opacity_slider.value()
        settings["theme"] = f"{self.theme_selector.currentText().lower()}_{self.color_selector.currentText().lower()}.xml"
        settings["background_source"] = self.background_selector.currentText().lower().replace(" ", "_")
        settings["background_video"] = self.background_video.text()
        settings["background_image"] = self.background_image.text()
        settings["local_icons"] = self.local_icons_cb.isChecked()
        save_settings(settings)
        if self.parent():
            self.parent().set_hotkey()
            self.parent().grid_widget.render_bg()
            self.parent().grid_widget.set_bg(self.background_video.text(), self.background_image.text())
        self.accept()
    def closeEvent(self, event):
        # Function to run before closing the dialog
        settings = load_settings()
        
        if self.is_changed == False:
            print("no changes made in settings")
            event.accept()
        else:
            ret = QMessageBox.warning(self,"Settings NOT saved", "Do you wish to discard these changes?", QMessageBox.Ok | QMessageBox.Cancel)
            if ret == QMessageBox.Ok:
                self.on_close()
                event.accept()
            else:
                event.ignore()
    
    def set_changed(self):
        print("Settings changed")
        self.is_changed = True

    def cleanup_bg_paths(self):

        #cleanup background_video
        if self.background_video.text().startswith("file:///"):
            self.background_video.setText(self.background_video.text()[8:])  # remove "file:///"
        elif self.background_video.text().startswith("file://"):
            self.background_video.setText(self.background_video.text()[7:])  # Remove 'file://' prefix

        #cleanup background_image
        if self.background_image.text().startswith("file:///"):
            self.background_image.setText(self.background_image.text()[8:])  # remove "file:///"
        elif self.background_image.text().startswith("file://"):
            self.background_image.setText(self.background_image.text()[7:])  # Remove 'file://' prefix

    def on_close(self):
        settings = load_settings()
        save_settings(settings)
        window_opacity = get_setting("window_opacity", -1)
        self.parent().change_opacity(window_opacity)
        self.parent().change_theme(self.set_theme)

    def change_button(self, text):
        self.toggle_overlay_keybind_button.setText(text)

    def video_folder_button_clicked(self):
        file_dialog = QFileDialog()
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.background_video.setText(selected_file)

    def image_folder_button_clicked(self):
        file_dialog = QFileDialog()
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.background_image.setText(selected_file)

class KeybindButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__( parent)
        self.listening = False
        self.clicked.connect(self.enable_listening)
        self.installEventFilter(self)
    def enable_listening(self):
        self.listening = True
        self.setText("Press a key")

    def keyPressEvent(self, event):
        if self.listening and event.key() <= 16000000:
            self.listening = False
            key = event.key()
            modifiers = event.modifiers()

            key_name = QKeySequence(key).toString()
            modifier_names = []

            if modifiers & Qt.ShiftModifier:
                modifier_names.append("Shift")
            if modifiers & Qt.ControlModifier:
                modifier_names.append("Ctrl")
            if modifiers & Qt.AltModifier:
                modifier_names.append("Alt")
            if modifiers & Qt.MetaModifier:
                modifier_names.append("Meta")

            full_key_name = "+".join(modifier_names + [key_name])
            self.parent().set_changed()
            self.setText(full_key_name)
        else:
            super().keyPressEvent(event)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and self.listening:
            self.keyPressEvent(event)
            return True
        return super().eventFilter(source, event)
    
    def get_keybind(self):
        return self.text()

    
