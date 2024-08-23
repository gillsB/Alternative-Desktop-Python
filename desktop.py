from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QLabel, QCheckBox, QDialog, QFormLayout, QLineEdit, QKeySequenceEdit, QDialogButtonBox, QSlider, QComboBox
from PySide6.QtCore import Qt, QEvent, QKeyCombination
from PySide6.QtGui import QIcon, QKeySequence
import sys
from settings import get_setting, set_setting, load_settings, save_settings, add_angle_brackets
from settings_menu import SettingsDialog
import qt_material
from qt_material import apply_stylesheet
from desktop_grid import Grid
from hotkey_handler import HotkeyHandler
import os
import xml.etree.ElementTree as ET



class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        #self.setAttribute(Qt.WA_TranslucentBackground)
        window_opacity = get_setting("window_opacity", -1)
        window_opacity = float(window_opacity/100)
        self.setWindowOpacity(window_opacity)
        self.setWindowTitle("Alternative Desktop V0.0.014")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.grid_widget = Grid()
        layout.addWidget(self.grid_widget)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        

        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.close)
        

        layout.addWidget(settings_button)
        layout.addWidget(self.closeButton)


        self.hotkey_handler = HotkeyHandler(self)
        self.hotkey_handler.toggle_signal.connect(self.toggle_window_state)

        start_theme= get_setting("theme")
        self.apply_theme(start_theme)

    def apply_theme(self, theme_name):
        try:
            # load_theme_colors excpects no file extention. so remove it before calling
            no_ext = theme_name.replace('.xml', '')
            
            self.theme_colors = self.load_theme_colors(no_ext)
            print("Theme Colors Found:", self.theme_colors)
            #save all colors to variables to be able to access them from child grid
            self.primary_color = self.theme_colors.get('primaryColor')
            self.primary_light_color = self.theme_colors.get('primaryLightColor')
            self.secondary_color = self.theme_colors.get('secondaryColor')
            self.secondary_light_color = self.theme_colors.get('secondaryLightColor')
            self.secondary_dark_color = self.theme_colors.get('secondaryDarkColor')
            self.primary_text_color = self.theme_colors.get('primaryTextColor')
            self.secondary_text_color = self.theme_colors.get('secondaryTextColor')

        except FileNotFoundError as e:
            print(e)
        if theme_name.startswith("dark"):
            #these two color overrides make certain fields way more readable on dark mode (when not selected) than the base themes while still maintaining a good look.
            #for instance lineEdits with black text on a dark gray (secondary color) is hard to tell if there is anything in the line edit at all without clicking on it.
            self.secondary_color = '#4c5559'  
            self.secondary_dark_color = '#2c3135'
            apply_stylesheet(QApplication.instance(), theme=theme_name, invert_secondary=False, extra={'secondaryColor': self.secondary_color, 'secondaryDarkColor': self.secondary_dark_color})
        else:
            apply_stylesheet(QApplication.instance(), theme=theme_name, invert_secondary=True)

    def change_theme(self, theme_name):
        self.grid_widget.pause_video()
        QApplication.processEvents()

        # Apply the new theme
        self.apply_theme(theme_name)

        self.grid_widget.play_video()

    def load_theme_colors(self, theme_name):
        # Construct the file path for the XML file (qt_material/themes)
        theme_path = os.path.join(os.path.dirname(qt_material.__file__), 'themes', f'{theme_name}.xml')
        
        if not os.path.exists(theme_path):
            raise FileNotFoundError(f"Theme file '{theme_name}.xml' not found at {theme_path}")

        # Parse the XML file
        tree = ET.parse(theme_path)
        root = tree.getroot()

        # Initialize a dictionary to store theme colors
        theme_colors = {}

        # Extract color properties from the XML
        for color in root.findall("color"):
            color_name = color.get("name")
            color_value = color.text
            theme_colors[color_name] = color_value

        return theme_colors



    def show_settings(self):
        dialog = SettingsDialog(parent=self)
        dialog.exec()
    
    def change_opacity(self ,i):
        print("change_opacity = ")
        print(float(i/100))
        self.setWindowOpacity(float(i/100))

    def toggle_window_state(self):
        if self.isMinimized():
            # Restore to the last visible state
            if self.last_visible_state == Qt.WindowFullScreen:
                self.showFullScreen()
            elif self.last_visible_state == Qt.WindowMaximized:
                self.showMaximized()
            else:
                self.showNormal()
            self.grid_widget.play_video()
        else:
            # Save the current state before minimizing
            if self.isFullScreen():
                self.last_visible_state = Qt.WindowFullScreen
            elif self.isMaximized():
                self.last_visible_state = Qt.WindowMaximized
            else:
                self.last_visible_state = Qt.WindowNoState
            self.showMinimized()
            self.grid_widget.pause_video()
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if not self.isMinimized():
                # Update last_visible_state when window state changes (except for minimization)
                if self.isFullScreen():
                    self.last_visible_state = Qt.WindowFullScreen
                elif self.isMaximized():
                    self.last_visible_state = Qt.WindowMaximized
                else:
                    self.last_visible_state = Qt.WindowNoState
        super().changeEvent(event)
    def set_hotkey(self):
        self.hotkey_handler.set_hotkey()
        
    

def main():
    app = QApplication(sys.argv)
    overlay = OverlayWidget()
    overlay.setMinimumSize(100, 100)  
    overlay.resize(1760, 990)
    overlay.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()