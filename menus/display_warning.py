from PySide6.QtWidgets import QMessageBox, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import QTimer, Qt
import logging

logger = logging.getLogger(__name__)

def show_highlightable_message_box(title, message, standard_buttons=QMessageBox.Ok):
    # Create a QMessageBox
    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setIcon(QMessageBox.Warning)
    
    # Set the standard buttons passed as an argument
    msg_box.setStandardButtons(standard_buttons)

    # Create a QLabel for the message and make the text selectable
    label = QLabel(message)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    label.setWordWrap(True)
    label.setMinimumWidth(300)

    # Remove default message box but get it's layout
    layout = msg_box.layout()

    # Problem: QSpacerItem horiz_size, vert_size, do not seem to matter but adding them does a bit of padding to the left of the message text
    # which actually does what I wanted.... but should probably come back and fix this whole layout setting to be more defined.
    left_spacer = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
    layout.addItem(left_spacer, 0, 0, 1, 1)
    layout.addWidget(label, 0, 1, 1, layout.columnCount(), Qt.AlignCenter)

    # Show the message box and return the user's choice
    return msg_box.exec()

def display_bad_overlay_keybind_warning(hotkey):
    def show_warning():
        logger.warning("Displaying warning: Bad Toggle Overlay Keybind")
        show_highlightable_message_box(
            "Bad Toggle Overlay Keybind",
            f"There was a problem assigning your toggle overlay to the keybind: '{hotkey}'. Has been reset to default: Alt+d. Please update the keybind in settings."
        )
    
    # QTimer to not block main thread. (Async)
    QTimer.singleShot(1000, show_warning)

def display_lnk_cli_args_warning():
    logger.warning("Displaying warning: LNK with CLI arguments (unsupported) warning")
    show_highlightable_message_box(
        "Warning .lnk",
        "Warning: .lnk files (Shortcuts) do not have command arguments support.\n\nPlease add the command arguments to the .lnk file itself or replace the .lnk with the file it points to and add the command line arguments to that."
    )
    
def display_icon_path_not_exist_warning(icon_path):
    return show_highlightable_message_box(
        "Error: Icon Path",
        f"Error: Icon path, item at path: \n{icon_path}\ndoes not exist. \nClick Yes save regardless, or Cancel to continue editing.",
        QMessageBox.Yes | QMessageBox.Cancel
    )

def display_executable_file_path_warning(exec_path):
    return show_highlightable_message_box(
        "Warning: Executable File Path", 
        f"Warning: Executable path: '{exec_path}'\nitem does not exist. \nWould you like to continue saving with a bad exectuable path?",
        QMessageBox.Yes | QMessageBox.Cancel
    )

def display_icon_path_already_exists_warning():
    return show_highlightable_message_box(
        "Icon Path exists",
        "You already have an Icon Path set. Would you like to discard this Icon Path to generate a new one?",
        QMessageBox.Yes | QMessageBox.Cancel
    )

def display_path_and_parent_not_exist_warning(normalized_path):
    show_highlightable_message_box( "Path does not exist",
        f"Neither the file at '{normalized_path}'\nnor its parent directory exist. Please check the location."
    )

def display_delete_icon_warning(name, row, col):
    logger.info(f"Displaying delete confirmation warning for {name}, at {row},{col}")
    return show_highlightable_message_box("Delete Icon",
        f"Are you sure you wish to delete \"{name}\" at: [{row},{col}]?",
        QMessageBox.Yes | QMessageBox.Cancel
    )

def display_drop_error(position):
    show_highlightable_message_box(
        "Drop Error",
        f"Error dropping item at position {position}."
    )

def display_failed_cleanup_warning(folder):
    show_highlightable_message_box(
        "Failed cleanup",
        f"Temp file found: {folder}\n which was not removed after the last cleanup. Check the file if it contains anything important and delete it after. \nIf this pops up again in a repeatable way (after deleting the _temp folder) please contact the dev."
    )

def display_no_successful_launch_error():
    show_highlightable_message_box(
        "No Successful launch",
        f"No Successful launch detected, please check the icon's Executable path or Website Link"
        )
    
def display_file_not_found_error(path):
    show_highlightable_message_box(
        "Error Opening File",
        f"The file could not be opened.\nFile path: ' {path} '\nPlease check that the file exists at the specified location.",
    )

def display_no_default_type_error(path):
    show_highlightable_message_box(
        "Error Opening File",
        f"The file could not be opened.\nFile path:{path}\nPlease ensure there is a default application set to open this file type."
    )

def display_bg_video_not_exist(bg_video_path):
    logger.warning("Displaying warning for bg video does not exist")
    return show_highlightable_message_box(
        "Video does not exist",
        f"Video at path: ' {bg_video_path} ' \nDoes Not Exist. Are you sure you want to save with an incorrect video file?",
        QMessageBox.Yes | QMessageBox.Cancel
    )

def display_bg_image_not_exist(bg_image_path):
    logger.warning("Displaying warning for bg image does not exist")
    return show_highlightable_message_box(
        "BG image does not exist",
        f"Image at path: ' {bg_image_path} '\nDoes Not Exist. Are you sure you want to save with an incorrect image file?",
        QMessageBox.Yes | QMessageBox.Cancel
    )

def display_settings_not_saved():
    logger.warning("Displaying warning for settings not saved")
    return show_highlightable_message_box(
        "Settings NOT saved", 
        "Do you wish to discard these changes?", 
        QMessageBox.Yes | QMessageBox.Cancel
    )

def display_keybind_not_supported(keybind):
    logger.warning("Displaying keybind not supported warning")
    def show_warning():
        show_highlightable_message_box(
            "Keybind not supported",
            f"Keybind: ' {keybind} ' \nReturned scan code far out of normal scan code range. This keybind is not fully supported, it might also respond to different keys, or not be picked up at all. \nKnown conflicting keys ' / '   ' num / '   ' menu ' If your key is different please report it."
        )

    # QTimer to not block main thread. (Async)
    QTimer.singleShot(0, show_warning)
    
def display_multiple_working_keybind_warning(keybind):
    logger.warning("Displaying warning that multiple keys may respond to selected keybind.")
    def show_warning():
        show_highlightable_message_box(
            "Multple keybinds may work",
            f"Keybind: ' {keybind} ' \nis known to have multiple variants which return the same value as the key set. For instance ' enter/return ' and ' num enter/return ' will both trigger this keybind."
        )
    # QTimer to not block main thread. (Async)
    QTimer.singleShot(0, show_warning)

def display_cannot_swap_icons_warning(error):
    logger.warning("Displaying warning Cannot swap icons")
    return show_highlightable_message_box(
        "Cannot swap icons", 
        f"An error occurred upon trying to swap folders for icons, to ensure icon paths do not get corrupted, the swap has been cancelled. \nError: {error}"
    )

def display_reset_default_font_size_warning():
    logger.warning("Displaying Warning to reset all fonts to Default font size in settings.")
    return show_highlightable_message_box(
        "Reset the Font Size for ALL Icons", 
        "This will reset <b>ALL</b> font sizes for <b>ALL</b> icons. ", 
        QMessageBox.Ok | QMessageBox.Cancel
    )
def display_reset_default_font_color_warning():
    logger.warning("Displaying Warning to reset all Icon Name colors to the Name Font Color in settings.")
    return show_highlightable_message_box(
        "Reset the Icon Name color for ALL Icons.", 
        "This will reset <b>ALL</b> Icon Name Colors for <b>ALL</b> icons. ", 
        QMessageBox.Ok | QMessageBox.Cancel
    )