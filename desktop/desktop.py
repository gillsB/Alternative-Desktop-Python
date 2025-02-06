from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtCore import Qt, QEvent, QRect, QTimer
from PySide6.QtGui import QIcon, QIcon, QAction, QColor
import sys
from util.settings import get_setting, set_setting
from menus.settings_menu import SettingsDialog
from menus.display_warning import display_settings_not_saved
import qt_material
from qt_material import apply_stylesheet
from util.hotkey_handler import HotkeyHandler
from menus.patch_notes import PatchNotesPopup, patch_notes_exist
from util.updater import changes_from_older_versions
import os
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)
APP = None

class OverlayWidget(QWidget):
    def __init__(self, current_version, args):
        super().__init__()

        self.version = current_version
        if get_setting("show_patch_notes") and patch_notes_exist():
            set_setting("show_patch_notes", False)
            # Fix some problems caused by updating from older versions (setting changed order etc.)
            changes_from_older_versions()
            QTimer.singleShot(1000, self.show_patch_notes)

        self.settings_dialog = None

        APP.aboutToQuit.connect(self.cleanup)
        #self.setAttribute(Qt.WA_TranslucentBackground)
        window_opacity = get_setting("window_opacity", -1)
        window_opacity = float(window_opacity/100)
        self.setWindowOpacity(window_opacity)
        self.setWindowTitle(f"Alternative Desktop {current_version}")
        self.current_screen_name = self.screen().name()
        self.showMaximized()

        # Create the system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("alt.ico"))

        # Create the tray menu
        tray_menu = QMenu()

        tray_menu.setStyle(QApplication.style())
        
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.show_window)
        tray_menu.addAction(restore_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        
        self.tray_icon.show()

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.primary_color = None
        self.primary_light_color = None
        self.secondary_color = None
        self.secondary_light_color = None
        self.secondary_dark_color = None
        self.primary_text_color = None
        self.secondary_text_color = None

        # first_restore is set to run a 1 time first restore code
        self.first_restore = True
        self.restored_window = False
        self.first_resize = True

        self.theme_name = get_setting("theme")
        self.apply_theme(self.theme_name)

        self.hotkey_handler = HotkeyHandler(self)
        self.hotkey_handler.toggle_signal.connect(self.toggle_window_state)

        # See commit from 8/26/2024 ~10:14pm Pacific time about this import. Basically must be imported after init or it breaks the logging.
        from desktop.desktop_grid import DesktopGrid
        self.grid_widget = DesktopGrid(parent=self, args=args)
        layout.addWidget(self.grid_widget)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)

    def show_patch_notes(self):
        patch_notes_menu = PatchNotesPopup(self)
        patch_notes_menu.exec()

    def close_settings(self):
        self.settings_dialog = None
        self.grid_widget.redraw_all_icons()
        logger.info(f"Closed settings, settings_dialog = {self.settings_dialog} (this should be None)")

        
    # Override base CloseEvent to just hide it. (Tray item already exists)
    def closeEvent(self, event):
        # if "On closing the program" set to "terminate the program"
        if get_setting("on_close", 0) == 0:
            if self.settings_dialog:
                reply = display_settings_not_saved()
                if reply == QMessageBox.Yes:
                    logger.info("User chose to close the settings menu and revert the changes")
                else:
                    event.ignore()
                    return
            logger.info("Program closing by closeEvent with on_close set to 'Terminiate the program' on close.")
            self.cleanup()
            super(OverlayWidget, self).closeEvent(event)
        else:
            event.ignore()
            self.minimize_to_tray()

    def minimize_to_tray(self):
        self.restored_window = True
        if self.isMinimized:
            # Showing these as Maximized/Normal is important for actually bringing them back up in a single toggle_window_state() call.
            # Otherwise it would take multiple calls or bring it up in the background (non focused).
            if self.is_maximized == True:
                logger.info("Quickly showing window as Maximized before hiding")
                self.showMaximized()
            else:
                logger.info("Quickly showing window as normal before closing")
                self.showNormal()
        

        self.hide()

    # This is only the tray icon -> Restore menu. Running self.toggle_window_state() makes it the same as keybind restore.
    # Or can always override this say for instance if you want it to always restore to maximized.
    def show_window(self):
        self.toggle_window_state()
        #self.showNormal()
        #self.showMaximized()

    # Complete quit from Tray menu.
    def close_application(self):
        self.cleanup()
        QApplication.instance().quit()

    def cleanup(self):
        if self.settings_dialog is not None and self.settings_dialog.isVisible():
            self.settings_dialog.main_window_closing = True
            logger.info("Signal sent to settings_dialog to close regardless of changes")
        # Explicitly delete the QSystemTrayIcon
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.tray_icon = None
            logger.info("Finished cleaning up tray_icon")

    def set_theme_colors(self, theme_colors):
        if theme_colors == None:
            logger.info("Setting variables for theme colors to None.")
            self.primary_color = None
            self.primary_light_color = None
            self.secondary_color = None
            self.secondary_light_color = None
            self.secondary_dark_color = None
            self.primary_text_color = None
            self.secondary_text_color = None
        else:
            logger.info("Setting variables for theme colors to match theme.")
            self.primary_color = theme_colors.get('primaryColor')
            self.primary_light_color = theme_colors.get('primaryLightColor')
            self.secondary_color = theme_colors.get('secondaryColor')
            self.secondary_light_color = theme_colors.get('secondaryLightColor')
            self.secondary_dark_color = theme_colors.get('secondaryDarkColor')
            self.primary_text_color = theme_colors.get('primaryTextColor')
            self.secondary_text_color = theme_colors.get('secondaryTextColor')

            bright_color = QColor(self.primary_light_color)
            self.light_desktop_color = QColor(bright_color.lighter(120))
        
    def apply_theme(self, theme_name):
        self.theme_name = theme_name
        if theme_name.startswith("none"):
            global APP
            APP.setStyleSheet("")
            self.set_theme_colors(None)
        try:
            # load_theme_colors excpects no file extention. so remove it before calling
            no_ext = theme_name.replace('.xml', '')
            
            theme_colors = self.load_theme_colors(no_ext)
            self.set_theme_colors(theme_colors)
            logger.info(f"Theme Colors Found:  {theme_colors}")


        except FileNotFoundError as e:
            logger.error(e)
        if theme_name.startswith("dark"):
            # Text override as some themes like dark_cyan default the text color to black on a very dark gray background for stuff like LineEdit/DropDown.
            # Setting text color to white maintains readability for these poorly designed default themes.
            self.primary_text_color = '#ffffff'
            apply_stylesheet(QApplication.instance(), theme=theme_name, invert_secondary=False, extra={'primaryTextColor': self.primary_text_color})
        else:
            apply_stylesheet(QApplication.instance(), theme=theme_name, invert_secondary=True)

    def change_theme(self, theme_name):
        logger.info(f"Changed theme to = {theme_name}")
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
        self.settings_dialog = SettingsDialog(parent=self)
        self.settings_dialog.finished.connect(self.close_settings)
        self.settings_dialog.show()
    
    def change_opacity(self ,i):
        logger.info(f"Change opacity = {float(i/100)}")
        self.setWindowOpacity(float(i/100))

    def toggle_window_state(self):
        logger.info("toggle_window_state called")
        current_state = self.windowState()
        logger.info(f"cur state = {current_state}")
        
        if current_state & Qt.WindowMinimized or not self.isVisible():
            
            # self.is_maximized holds whether the last active state of the window was maximized.
            if self.is_maximized == True: # Restore window as maximized. showNormal() is required for proper scaling.
                if self.first_restore and self.restored_window:
                    self.showNormal()
                    self.first_restore = False
                logger.info("Showing window as maximized")
                self.showMaximized()

            else: # Restore window as normal non-maximized
                logger.info("Showing window as normal")
                self.showNormal()
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
            
        else:
            if self.isActiveWindow():
                # If "When in focus Keybind" setting is set to "Hide Window" (1)
                if get_setting("keybind_minimize") == 1:
                    logger.info("Minimizing to tray because user has keybind_minimize setting == Hide window")
                    self.minimize_to_tray()
                else:
                    logger.info("Window is in focus, minimizing")
                    self.setWindowState(Qt.WindowMinimized)
            # If the window is already visible (maximized or normal), bring it to the front
            elif current_state & Qt.WindowMaximized:
                logger.info("Window not in focus but maximized, bringing to top.")
                self.raise_()
                self.activateWindow()
            elif current_state == Qt.WindowNoState:
                logger.info("Window not in focus but non-maximized (NoState), bringing to top.")
                self.raise_()
                self.activateWindow()
            else:
                logger.error("Unknown window state and not active, minimizing window.")
                self.setWindowState(Qt.WindowMinimized)


    def changeEvent(self, event):


        # Check if the window state is changing
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMaximized:
                self.is_maximized = True
                logger.info("Window is maximized")
            elif self.windowState() == Qt.WindowNoState:
                if self.first_resize:
                    # Always resize down to under the screens max resolution to ensure the screen will at least fit on the screen.
                    available_geometry = self.screen().availableGeometry()
                    new_size = self.size().boundedTo(available_geometry.size())
                    if new_size != self.size():
                        self.resize(new_size)
                    current_screen = self.screen()
                    if current_screen:
                        screen_geometry = current_screen.availableGeometry()

                        # Calculate 75% of the maximized width and height
                        new_width = int(screen_geometry.width() * 0.75)
                        new_height = int(screen_geometry.height() * 0.75)

                        # Calculate the top-left point to centralize the window on the current screen
                        new_x = (screen_geometry.width() - new_width) // 2 + screen_geometry.x()
                        new_y = screen_geometry.y() + 40

                        # Move and resize the window to the center of the current screen with the new size
                        self.setGeometry(QRect(new_x, new_y, new_width, new_height))
                        self.first_resize = False

                self.is_maximized = False
                logger.info("Window is in normal state")
        super().changeEvent(event)

    def set_hotkey(self):
        self.hotkey_handler.stop_listener()
        self.hotkey_handler.set_hotkey()
        
    def moveEvent(self, event):
        # Detect if the window has moved to a different monitor
        new_screen_name = self.screen().name()

        if new_screen_name != self.current_screen_name:
            # If the window moved to a new monitor, reset first_resize
            logger.info("Moved program to another monitor, reset self.first_resize to True")
            self.current_screen_name = new_screen_name
            self.first_resize = True

        super().moveEvent(event)


def create_app():
    global APP
    if APP is None:
        APP = QApplication(sys.argv)

def main(current_version, args):
    create_app()
    overlay = OverlayWidget(current_version, args)
    overlay.setWindowIcon(QIcon('alt.ico'))
    overlay.setMinimumSize(100, 100)
    overlay.show()
    sys.exit(APP.exec())

if __name__ == "__main__":
    main()