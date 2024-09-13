from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QToolButton, QLabel, QCheckBox, QDialog, QFormLayout, QLineEdit, QKeySequenceEdit, QDialogButtonBox, QSlider, QComboBox, QStyle, QFileDialog, QSpinBox, QColorDialog
from PySide6.QtCore import Qt, QEvent, QKeyCombination, QSize
from PySide6.QtGui import QIcon, QKeySequence
import sys
from pynput import keyboard
from util.utils import ClearableLineEdit
from util.settings import get_setting, set_setting, load_settings, save_settings, add_angle_brackets
from menus.display_warning import display_bg_video_not_exist, display_bg_image_not_exist, display_settings_not_saved
import os
import logging

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    is_changed = False
    def initUI(self):
        self.setWindowTitle("Settings")
        layout = QFormLayout()
        self.setLayout(layout)

        # Small optimization to load settings once for the entire file then use .get() from that
        # Instead of using get_setting() which calls a load_settings() every instance.
        self.settings = load_settings()

        # Checkbox for update on launch
        self.update_on_launch_cb = QCheckBox()

        self.update_on_launch_cb.setChecked(self.settings.get("update_on_launch", True))
        self.update_on_launch_cb.clicked.connect(self.set_changed)
        layout.addRow("Update on Launch", self.update_on_launch_cb)
    

        self.toggle_overlay_keybind_button = KeybindButton()
        self.toggle_overlay_keybind_button.setText(self.settings.get("toggle_overlay_keybind", "alt+d"))
        layout.addRow("Toggle Overlay Keybind", self.toggle_overlay_keybind_button)
        self.toggle_overlay_keybind_button.setFocusPolicy(Qt.ClickFocus)
        self.toggle_overlay_keybind_button.setAutoDefault(False)
        self.toggle_overlay_keybind_button.setDefault(False)
        

        self.window_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_opacity_slider.setMinimum(30)
        self.window_opacity_slider.setMaximum(100)
        self.window_opacity_slider.setSingleStep(1)
        self.window_opacity_slider.setSliderPosition(self.settings.get("window_opacity", 100))
        self.window_opacity_slider.valueChanged.connect(self.value_changed)
        

        
        layout.addRow("Overlay Opacity", self.window_opacity_slider)

        self.theme_selector = QComboBox()
        self.color_selector = QComboBox()

        # Add theme options including 'None'
        self.theme_selector.addItems(['None', 'Dark', 'Light'])

        # Add color options
        self.colors = ['Amber', 'Blue', 'Cyan', 'Lightgreen', 'Pink', 'Purple', 'Red', 'Teal', 'Yellow']
        self.color_selector.addItems(self.colors)

        # Retrieve and set theme from settings
        self.set_theme = self.settings.get("theme", "None")
        if '_' in self.set_theme:
            split_theme = self.set_theme.rsplit('.', 1)[0]
            theme, color = split_theme.split('_', 1)

            if theme.capitalize() in ['None', 'Dark', 'Light']:
                self.theme_selector.setCurrentText(theme.capitalize())

            if color.capitalize() in self.colors:
                self.color_selector.setCurrentText(color.capitalize())
        else:
            logger.error("Theme format is invalid. Themes will be set to default.")
            self.theme_selector.setCurrentText("None")  # Set default to 'None'

        # Connect signals for theme and color selection
        self.theme_selector.currentIndexChanged.connect(self.update_theme)
        self.color_selector.currentIndexChanged.connect(self.update_theme)

        # Add to layout
        layout.addRow("Theme", self.theme_selector)
        layout.addRow("", self.color_selector)

        self.display_theme()

        self.background_selector = QComboBox()
        background_options = ["First found", "Both", "Video only", "Image only", "None"]
        self.background_selector.addItems(background_options)
        layout.addRow("Background sourcing:", self.background_selector)
        
        set_bg_option = self.settings.get("background_source", "First found")
        # format for background_source is no capitalize and "_" instead of " " therefore revert both
        self.background_selector.setCurrentText(set_bg_option.replace("_", " ").capitalize())

        self.background_selector.currentIndexChanged.connect(self.set_changed)


        # background path clearable line edits
        self.background_video = ClearableLineEdit()
        self.background_image = ClearableLineEdit()
        self.background_video.setText(self.settings.get("background_video", ""))
        self.background_image.setText(self.settings.get("background_image", ""))
        self.background_video.textChanged.connect(self.set_changed)
        self.background_image.textChanged.connect(self.set_changed)


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
        self.local_icons_cb.setChecked(self.settings.get("local_icons", True))
        self.local_icons_cb.clicked.connect(self.set_changed)
        layout.addRow("Save icons locally", self.local_icons_cb)

        self.icon_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.icon_size_slider.setMinimum(30)
        self.icon_size_slider.setMaximum(256)
        self.icon_size_slider.setSingleStep(1)
        self.icon_size_slider.setSliderPosition(self.settings.get("icon_size", 100))
        self.icon_size_slider.valueChanged.connect(self.label_size_changed)
        layout.addRow("Desktop Icon Size: ", self.icon_size_slider)


        # Re drawing due to change in Max Rows/Cols is heavy so only redraw it if these are changed
        self.redraw_request = False

        self.max_rows_sb = QSpinBox()
        self.max_rows_sb.setValue(self.settings.get("max_rows", 20))
        self.max_rows_sb.setRange(0, 100)
        self.max_rows_sb.valueChanged.connect(self.redraw_setting_changed)
        layout.addRow("Max rows: ", self.max_rows_sb)
        self.max_cols_sb = QSpinBox()
        self.max_cols_sb.setValue(self.settings.get("max_cols", 40))
        self.max_cols_sb.setRange(0, 100)
        self.max_cols_sb.valueChanged.connect(self.redraw_setting_changed)
        layout.addRow("Max Columns: ", self.max_cols_sb)

        self.label_color = self.settings.get("label_color", "white") #default white
        
        # Flat color button, when clicked opens color dialog
        self.label_color_box = QPushButton("", self)
        self.label_color_box.clicked.connect(self.open_color_dialog)
        self.label_color_box.setFixedSize(QSize(75, 30))

        self.update_color_box(self.label_color)
        layout.addRow("Icon Name color: ", self.label_color_box)

        # On closing the program: Minimize to Tray or Terminiate the program
        self.on_close_cb = QComboBox()
        on_close_options = ['Minimize to tray', 'Terminiate the program']
        self.on_close_cb.addItems(on_close_options)
        layout.addRow("On closing the program:", self.on_close_cb)
        self.on_close_cb.setCurrentIndex(self.settings.get("on_close", 0))

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        save_button.setAutoDefault(False)
        save_button.setDefault(False)

    def open_color_dialog(self):
        self.redraw_setting_changed() # redraw or it won't update
        # Open the color dialog and get the selected color
        color = QColorDialog.getColor()

        if color.isValid():
            self.label_color = color.name()  # Get the hex code of the selected color
            self.parent().grid_widget.change_label_color(self.label_color)
            self.update_color_box(self.label_color)
            
    def update_color_box(self, color_name: str):
        logger.info(f"Updated label color box to color {color_name}")
        self.label_color_box.setStyleSheet(f"background-color: {color_name}; border: 1px solid black;")

    # Only called when a setting which requires redrawing of desktop icons is changed.
    def redraw_setting_changed(self):
        self.set_changed()
        self.redraw_request = True
        logger.info("Redraw request now set to True")
            

    def display_theme(self):
        selected_theme = self.theme_selector.currentText()
        
        if selected_theme == 'None':
            self.color_selector.hide()  # Hide color selector if 'None' is selected
        else:
            self.color_selector.show()  # Show color selector for other themes

    def update_theme(self):
        self.display_theme()
        category = self.theme_selector.currentText().lower()
        color = self.color_selector.currentText().lower()
        theme = f"{category}_{color}.xml"
        logger.info(f"Selected theme: {theme}")
        self.parent().change_theme(theme)
        self.is_changed = True

    def value_changed(self, i):
        self.set_changed()
        if self.parent():
            self.parent().change_opacity(i)
        self.setWindowOpacity(1.0)

    def label_size_changed(self, i):
        self.set_changed()
        self.parent().grid_widget.update_label_size(i)


    def save_settings(self):

        #cleanup background paths
        self.cleanup_bg_paths()
        if self.background_video.text() != "" and os.path.exists(self.background_video.text()) == False:
            logger.warning("Background Video does not exist")
            # Display warning that bg video path does not exist, cancel save if user hits cancel otherwise save.
            if display_bg_video_not_exist(self.background_video.text()) == QMessageBox.Cancel:   
                logger.info("User chose to cancel saving.")
                return
            logger.info("User chose to save regardless")
        if self.background_image.text() != "" and os.path.exists(self.background_image.text())  == False:
            logger.warning("Background Image does not exist")
            #display warning that bg image path does not exist, cancel save if user hits cancel otherwise save.
            if display_bg_image_not_exist(self.background_image.text()) == QMessageBox.Cancel:   
                logger.info("User chose to cancel saving.")
                return
            logger.info("User chose to save regardless")


        # Double check keybind is set to something. Changes it to last saved setting if not. (i.e. click button but don't press anything then hit save)
        self.good_keybind()

        # More optimized to load and modify all settings then save. Than to set_setting() for each setting as set_setting() has load and save overhead.
        settings = load_settings()
        settings["update_on_launch"] = self.update_on_launch_cb.isChecked()
        settings["toggle_overlay_keybind"] = self.toggle_overlay_keybind_button.get_keybind()
        settings["window_opacity"] = self.window_opacity_slider.value()
        settings["theme"] = f"{self.theme_selector.currentText().lower()}_{self.color_selector.currentText().lower()}.xml"
        settings["background_source"] = self.background_selector.currentText().lower().replace(" ", "_")
        settings["background_video"] = self.background_video.text()
        settings["background_image"] = self.background_image.text()
        settings["local_icons"] = self.local_icons_cb.isChecked()
        settings["icon_size"] = self.icon_size_slider.value()
        settings["max_rows"] = self.max_rows_sb.value()
        settings["max_cols"] = self.max_cols_sb.value()
        settings["label_color"] = self.label_color
        settings["on_close"] = self.on_close_cb.currentIndex()
        save_settings(settings)
        if self.parent():
            self.parent().set_hotkey()
            self.parent().grid_widget.render_bg()
            self.parent().grid_widget.set_bg(self.background_video.text(), self.background_image.text())

            # Can be a quite heavy impact so only redraw when these values have changed.
            if self.redraw_request:
                self.parent().grid_widget.change_max_rows(self.max_rows_sb.value())
                self.parent().grid_widget.change_max_cols(self.max_cols_sb.value())
        
        # No need to reload self.settings as after saving this will terminate (self.accept()) and reload settings on next launch.
        self.accept()

    def good_keybind(self):
        if self.toggle_overlay_keybind_button.get_keybind() == "Press a key":
            logger.error("Attempted to save keybind while changing keybind")
            self.toggle_overlay_keybind_button.set_keybind()

    def closeEvent(self, event):
        
        if self.is_changed == False:
            logger.info("Called close with no changes made in settings")
            event.accept()
        else:
            logger.info("Called close with changes in settings")
            if display_settings_not_saved() == QMessageBox.Yes:
                logger.info("User chose to close the settings menu and revert the changes")
                self.on_close()
                event.accept()
            else:
                logger.info("User chose to cancel the close event.")
                event.ignore()
    
    def set_changed(self):
        if not self.is_changed:
            logger.info("Settings changed")
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
        window_opacity = self.settings.get("window_opacity", -1)
        self.parent().change_opacity(window_opacity)
        self.parent().change_theme(self.set_theme)
        self.parent().grid_widget.update_label_size(self.settings.get("icon_size"))

    def change_button(self, text):
        self.toggle_overlay_keybind_button.setText(text)

    def video_folder_button_clicked(self):
        self.set_changed()
        file_dialog = QFileDialog()
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.background_video.setText(selected_file)

    def image_folder_button_clicked(self):
        self.set_changed()
        file_dialog = QFileDialog()
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.background_image.setText(selected_file)

class KeybindButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Keybind button initialized")
        self.listening = False
        self.clicked.connect(self.enable_listening)
        self.installEventFilter(self)

    def enable_listening(self):
        logger.info("Enable listening called")
        self.listening = True
        self.setText("Press a key")

    def keyPressEvent(self, event):
        if self.listening and event.key() <= 16000000:
            logger.info(f"Key press event: {event}")
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
            logger.info(f"Full key name: {full_key_name}")
            self.parent().set_changed()
            self.setText(full_key_name)
        else:
            super().keyPressEvent(event)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and self.listening:
            logger.info(f"Key press detected by event filter: {event}")
            self.keyPressEvent(event)
            return True
        return super().eventFilter(source, event)

    def get_keybind(self):
        return self.text()

    def set_keybind(self):
        logger.error("Resetting keybind to last keybind saved")
        self.setText(self.settings.get("toggle_overlay_keybind", "alt+d"))
