import logging
from PySide6.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QFormLayout, QSpinBox, QLabel, QColorDialog,
                            QMessageBox, QTabWidget, QComboBox, QStyle, QFileDialog)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QColor
from PySide6.QtCore import QSize, Qt
from util.utils import ClearableLineEdit
from icon_gen.icon_utils import get_exact_img_file, make_local_icon
from icon_gen.extract_ico_file import extract_ico_file
from icon_gen.lnk_to_image import lnk_to_image
from icon_gen.exe_to_image import exe_to_image
from icon_gen.url_to_image import url_to_image
from icon_gen.icon_selection import select_icon_from_paths
from icon_gen.favicon_to_image import favicon_to_image
from icon_gen.browser_to_image import browser_to_image
from icon_gen.default_icon_to_image import default_icon_to_image
from util.config import (load_desktop_config, entry_exists, get_entry, save_config_to_file, get_data_directory, get_icon_font_size, get_icon_font_color)
from util.settings import get_setting
from menus.display_warning import display_lnk_cli_args_warning, display_icon_path_not_exist_warning, display_executable_file_path_warning, display_icon_path_already_exists_warning
import os


logger = logging.getLogger(__name__)
COL = -1
ROW = -1
LAUNCH_OPTIONS = 0


class Menu(QDialog):
    def __init__(self, urls, row = None, col = None, dropped_path = None, parent=None):
        super().__init__(parent)
        assert parent is not None
        global ROW 
        global COL 

        ROW = row
        COL = col
        self.font_size_changed = False
        self.font_color_changed = False
        # Tracker to set font_size back to default if "Reset" button pressed.
        self.reset_font_size = False
        self.reset_font_color = False

        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DesktopIcon))

        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        
        self.basic_tab = QWidget()
        self.basic_tab_layout = QFormLayout()

        self.name_le = ClearableLineEdit()
        self.icon_path_le = ClearableLineEdit()
        self.exec_path_le = ClearableLineEdit()
        self.web_link_le = ClearableLineEdit()
        #self.parent().selected_border(10)

        self.icon_path_le.textChanged.connect(self.preview_icon_path)

        self.setAcceptDrops(True)

        icon_folder_button = QPushButton(self)
        icon_folder_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        icon_folder_button.setIconSize(QSize(16,16))
        icon_folder_button.setFocusPolicy(Qt.NoFocus)
        icon_folder_button.clicked.connect(self.icon_folder_button_clicked)
        
        exec_folder_button = QPushButton(self)
        exec_folder_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        exec_folder_button.setIconSize(QSize(16,16))
        exec_folder_button.setFocusPolicy(Qt.NoFocus)
        exec_folder_button.clicked.connect(self.exec_folder_button_clicked)

        icon_folder_layout = QHBoxLayout()
        icon_folder_layout.addWidget(self.icon_path_le)
        icon_folder_layout.addWidget(icon_folder_button)

        exec_folder_layout = QHBoxLayout()
        exec_folder_layout.addWidget(self.exec_path_le)
        exec_folder_layout.addWidget(exec_folder_button)

        self.basic_tab_layout.addRow("Name: ", self.name_le)
        self.basic_tab_layout.addRow("Icon Path: ", icon_folder_layout)
        self.basic_tab_layout.addRow("Executable Path: ", exec_folder_layout)
        self.basic_tab_layout.addRow("Website Link: ", self.web_link_le)

        self.basic_tab.setLayout(self.basic_tab_layout)

        #### end of basic tab
        # Advanced tab below
        self.advanced_tab = QWidget()
        self.advanced_tab_layout = QFormLayout()
        
        self.command_args_le = QLineEdit()
        self.launch_option_cb = QComboBox()
        self.launch_option_cb.addItems(["Launch first found", "Prioritize Website links", "Ask upon launching", "Executable only", "Website Link only"])
        self.launch_option_cb.currentIndexChanged.connect(self.handle_selection_change)

        self.advanced_tab_layout.addRow("Command line arguments: ", self.command_args_le)
        self.advanced_tab_layout.addRow("Left click launch option:", self.launch_option_cb)

        self.advanced_tab.setLayout(self.advanced_tab_layout)

        ### end of Advanced tab
        # Appearance tab below
        self.appearance_tab = QWidget()
        self.appearance_tab_layout = QFormLayout()

        self.font_size_sb = QSpinBox()
        self.font_size_sb.setRange(0, 100)
        self.font_size_sb.setFixedWidth(100)

        self.reset_size_button = QPushButton("Reset")
        self.reset_size_button.setFixedWidth(75)
        self.reset_size_button.clicked.connect(self.reset_font_size_to_default)

        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(self.font_size_sb)
        font_size_layout.addWidget(self.reset_size_button)
        font_size_layout.setAlignment(Qt.AlignLeft)


        self.font_color = get_icon_font_color(ROW, COL)
        self.custom_font_color = QPushButton("", self)
        self.custom_font_color.clicked.connect(self.open_color_dialog)
        self.custom_font_color.setFixedSize(QSize(75, 30))
        self.custom_font_color.setAutoDefault(False)
        self.custom_font_color.setDefault(False)

        self.custom_bg_color_label = QLabel("Font color:")

        self.reset_color_button = QPushButton("Reset")
        self.reset_color_button.setFixedWidth(75)
        self.reset_color_button.clicked.connect(self.reset_font_color_to_default)

        font_color_layout = QHBoxLayout()
        font_color_layout.addWidget(self.custom_font_color)
        font_color_layout.addWidget(self.reset_color_button)
        font_color_layout.setAlignment(Qt.AlignLeft)

        self.appearance_tab_layout.addRow("Font size: ", font_size_layout)
        self.appearance_tab_layout.addRow(self.custom_bg_color_label, font_color_layout)
        self.appearance_tab.setLayout(self.appearance_tab_layout)


        ### end of Appearance tab
        # Combine all tabs
        self.tabs.addTab(self.basic_tab, "Basic")
        self.tabs.addTab(self.advanced_tab, "Advanced")
        self.tabs.addTab(self.appearance_tab, "Appearance")

        main_layout.addWidget(self.tabs)


        ## load already saved data for desktop_icon into fields in this menu
        self.load_data()


        # Deliberately delayed adding until after loading the value to avoid calling it when loading the value.
        self.font_size_sb.valueChanged.connect(self.font_size_changed_toggle)

        self.setWindowTitle(f"Editing [{ROW}, {COL}]: {self.name_le.text()}")
        if urls != None:
            self.get_drop(urls)

        self.parent().draw_red_border(ROW, COL)

        auto_gen_icon_button = QPushButton("Auto generate icon")
        auto_gen_icon_button.clicked.connect(self.auto_gen_button)
        main_layout.addWidget(auto_gen_icon_button)

        save_button = QPushButton("Save")
        
        save_button.clicked.connect(self.save_config)

        main_layout.addWidget(save_button)

        self.setLayout(main_layout)
        if dropped_path != None:
            self.dropped_file(dropped_path)

    
    def load_data(self):
        global LAUNCH_OPTIONS
        entry = get_entry(ROW, COL)
        if entry:
            self.name_le.setText(entry['name'])
            self.icon_path_le.setText(entry['icon_path'])
            self.exec_path_le.setText(entry['executable_path'])
            self.web_link_le.setText(entry['website_link'])
            self.command_args_le.setText(entry['command_args'])
            self.launch_option_cb.setCurrentIndex(entry['launch_option'])
            self.use_global_font_size = entry.get('use_global_font_size', True)
            self.use_global_font_color = entry.get('use_global_font_color', True)
            LAUNCH_OPTIONS = entry['launch_option']
        else:
            self.use_global_font_size = True
            self.use_global_font_color = True

        
        self.font_size_sb.setValue(get_icon_font_size(ROW, COL))
        self.font_color == get_icon_font_color(ROW, COL)
        self.custom_font_color.setStyleSheet(f"background-color: {self.font_color};")  # Apply color to button

    
    def dropped_file(self, dropped_path):
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.webp')
        # If dropped file appears to be an image file, change image_path, else set it as executable path.
        if dropped_path.lower().endswith(image_extensions):
            self.icon_path_le.setText(dropped_path)
        else:
            self.exec_path_le.setText(dropped_path)

    def closeEvent(self, event):
        logger.info("closed edit menu")
        self.parent().remove_red_border()
        self.parent().remove_temp_icon()
        self.parent().reload_icon(ROW, COL)
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            logger.info("Escape key pressed, calling closeEvent")
            self.close()  # This will trigger the closeEvent
        else:
            super().keyPressEvent(event)

    
    def preview_icon_path(self):
        if os.path.isfile(self.icon_path_le.text()):
            self.parent().set_icon_path(ROW, COL, self.icon_path_le.text())
            pass
        else:
            self.parent().set_icon_path(ROW, COL, "assets/images/unknown.png")
            pass
        # Called to paint border over the new icon path.
        self.parent().draw_red_border(ROW, COL)
    

    ## clean up common problems with file path, i.e. copying a file and pasting into exec_path produces file:///C:/...
    # the correct path for use requires just the C:/...
    def cleanup_path(self):

        #cleanup file_path
        if self.icon_path_le.text().startswith("file:///"):
            self.icon_path_le.setText(self.icon_path_le.text()[8:])  # remove "file:///"
        elif self.icon_path_le.text().startswith("file://"):
            self.icon_path_le.setText(self.icon_path_le.text()[7:])  # Remove 'file://' prefix

        #cleanup executable_path
        if self.exec_path_le.text().startswith("file:///"):
            self.exec_path_le.setText(self.exec_path_le.text()[8:])  # remove "file:///"
        elif self.exec_path_le.text().startswith("file://"):
            self.exec_path_le.setText(self.exec_path_le.text()[7:])  # Remove 'file://' prefix


    def save_config(self):
        # if exec_path is empty and web_link is empty -> save file
        if self.exec_path_le.text() == "" and self.web_link_le.text() == "":
            logger.info("Called save with exec_path empty and web_link empty, Save with no auto_gen")
            self.handle_save()
        # if icon already set, do not auto_gen_icon
        elif self.icon_path_le.text() != "":
            logger.info("Called save with existing icon_path, do not auto_gen")
            self.handle_save()
        #if exec_path is not empty check if it is a valid path then save if valid
        elif os.path.isfile(self.exec_path_le.text()) or self.web_link_le.text() != "":
            logger.info("Called save with existing exec_path or a web_link")
            logger.info(f"Arguments: valid exec_path: {os.path.isfile(self.exec_path_le.text())} {self.exec_path_le.text()}, website_link: {self.web_link_le.text() != ''}, {self.web_link_le.text()}")
            if self.exec_path_le.text() != "" and not os.path.isfile(self.exec_path_le.text()):
                # Show warning if user clicks cancel -> return and do not save, if Ok -> save
                if display_executable_file_path_warning(self.exec_path_le.text()) == QMessageBox.Yes:
                    logger.info("User chose to save regardless")
                else:
                    logger.info("User Chose to cancel Auto generating icon to fix the executable path.")
                    return
            self.auto_gen_icon()
            self.handle_save()
        # exec_path is not empty, and not a valid path. show warning (and do not close the menu)
        else:
            logger.warning(f"Called with a bad exec_path and no web_link or icon_path. exec_path = {self.exec_path_le.text()}")
            # Show warning if user clicks cancel -> return and do not save, if Ok -> save
            if display_executable_file_path_warning(self.exec_path_le.text()) == QMessageBox.Yes:
                logger.info("User chose to save regardless")
                self.handle_save()
            else:
                logger.info("User Chose to cancel saving to fix exec_path.")
                return

    def auto_gen_button(self):
        if self.icon_path_le.text() != "":
            logger.info("Pressed Auto gen icon with an existing icon path.")
            # Show warning, if user clicks cancel -> return, if Ok -> save
            if display_icon_path_already_exists_warning() == QMessageBox.Yes:
                logger.info("User chose to overwrite icon path.")
            else:    
                logger.info("User chose to keep icon path (Cancelled).")
                return
            self.icon_path_le.setText("")
            logger.info("User chose to overwrite icon (OK). Generating icon.")
        self.auto_gen_icon()
        # Called to paint the red border over the auto_gen_icon.
        self.parent().draw_red_border(ROW, COL)

    def auto_gen_icon(self):
        self.parent().set_cursor(Qt.BusyCursor) 
        data_path = self.parent().get_data_icon_dir(ROW, COL)
        icon_size = self.parent().get_autogen_icon_size()

        #default icon saves:
        # icon.png extract_ico_file, url_to_image (unique, getting image from .url file does not check for .ico files in location)
        # icon2.png exe_to_image, lnk_to_image (both share the same executable_path input so one or the other.)
        # icon3.png favicon_to_image, browser_to_image (gets favicon from website, fallback to default browser icon if no favicon found)
        # icon4.png default_icon_to_image (gets icon from default associated filetype program, only exists if exec_path is not .exe, .url, .lnk)

        icon_path = os.path.join(data_path, "icon.png")
        icon2_path = os.path.join(data_path, "icon2.png")
        icon3_path = os.path.join(data_path, "icon3.png")
        icon4_path = os.path.join(data_path, "icon4.png")

        ico_file = False
        lnk_file = False
        exe_file = False
        url_file = False
        fav_file = False
        default_file = False
        path_ico_icon = ""
        path_exe_icon = ""
        path_lnk_icon = ""
        path_url_icon = ""
        path_fav_icon = ""
        path_default_file_icon = ""

        logger.info(f"Auto gen icon called, data path = {data_path}, icon size = {icon_size}")

        if self.exec_path_le.text() != "" and os.path.isfile(self.exec_path_le.text()) and extract_ico_file(self.exec_path_le.text(), icon_path, icon_size):
            ico_file = True
            path_ico_icon = icon_path
            logger.info(f"Found .ico file in executable path location, saved to: {path_ico_icon}")

        # If no icon path and exec is .lnk
        if self.icon_path_le.text() == "" and self.exec_path_le.text().endswith(".lnk"):
            logger.info(f"Exec path is an .lnk")
            path_ico_icon, path_lnk_icon = lnk_to_image(self.exec_path_le.text(), icon2_path, icon_size)

            if path_lnk_icon != None:
                logger.info(f"Found icon from lnk target, saved to: {path_lnk_icon}")
                lnk_file = True
            if path_ico_icon != None:
                logger.info(f"Found .ico file from lnk target, saved to: {path_ico_icon}")
                ico_file = True
        
        # If no icon path and exec is .exe
        elif self.icon_path_le.text() == "" and self.exec_path_le.text().endswith(".exe"):
            logger.info("Exec path is an .exe")
            if os.path.isfile(self.exec_path_le.text()):
                path_exe_icon = exe_to_image(self.exec_path_le.text(), icon2_path, icon_size)  
                if path_exe_icon != None:
                    logger.info(f"Found icon from .exe, saved to: {path_exe_icon}")
                    exe_file = True
            else:
                logger.warning(f"Auto gen icon called on non-existing executable_path ending in .exe = {self.exec_path_le.text()}, Caught and not generating an icon for executable path.")

        # If no icon path and exec is a .url
        elif self.icon_path_le.text() == "" and self.exec_path_le.text().endswith(".url"):
            logger.info("Exec path is a .url")
            path_ico_icon = url_to_image(self.exec_path_le.text(), icon_path, icon_size)

            if path_ico_icon != None:
                logger.info(f"Found icon from .url, saved to: {path_ico_icon}")
                ico_file = True

        # If no icon path and exec_path exists
        elif self.icon_path_le.text() == "" and self.exec_path_le.text() != "":
            logger.info(f"Exec path is not .lnk or .exe: {self.exec_path_le.text()}, generating a default icon")
            if os.path.isfile(self.exec_path_le.text()):
                path_default_file_icon = default_icon_to_image(self.exec_path_le.text(), icon4_path, icon_size)
                if path_default_file_icon != None:
                    logger.info(f"Icon created from default, saved to: {path_default_file_icon}")
                    default_file = True
            else:
                logger.warning(f"Auto gen icon called on non-existing executable_path = {self.exec_path_le.text()}, Caught and not generating an icon for executable path.")

        # If Web link exists
        if self.web_link_le.text() != "":
            logger.info("Web link exists, attempting to generate icon.")
            url = self.web_link_le.text()
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            path_fav_icon = favicon_to_image(url, icon3_path, icon_size)
            if path_fav_icon != None:
                logger.info(f"Icon created from favicon, saved to {path_fav_icon}")
                fav_file = True
            #if it fails to create a favicon fallback
            else:
                #create a default browser icon for links
                path_fav_icon = browser_to_image(icon3_path, icon_size)
                if path_fav_icon != None:
                    logger.info(f"Favicon not found, created default browser image instead, saved to {path_fav_icon}")
                    fav_file = True

        # Done loading time for selection.
        self.parent().set_cursor(Qt.ArrowCursor) 

        if self.has_multiple_icons(path_ico_icon, path_exe_icon, path_lnk_icon, path_url_icon, path_fav_icon, path_default_file_icon):
            logger.info(f"Multiple icons detected: ico:{path_ico_icon}, exe:{path_exe_icon}, lnk:{path_lnk_icon}, url:{path_url_icon}, fav:{path_fav_icon}, default:{path_default_file_icon}")
            icon_selected = select_icon_from_paths(path_ico_icon, path_exe_icon, path_lnk_icon, path_url_icon, path_fav_icon, path_default_file_icon)
            logger.info(f"Icon selected by user: {icon_selected}")
            self.icon_path_le.setText(icon_selected)
        elif ico_file:
            logger.info(f"Only available icon is ico_icon: {path_ico_icon}")
            self.icon_path_le.setText(path_ico_icon)
        elif lnk_file:
            logger.info(f"Only available icon is lnk_icon: {path_lnk_icon}")
            self.icon_path_le.setText(path_lnk_icon)
        elif exe_file:
            logger.info(f"Only available icon is exe_icon: {path_exe_icon}")
            self.icon_path_le.setText(path_exe_icon)
        elif url_file:
            logger.info(f"Only available icon is url_icon: {path_url_icon}")
            self.icon_path_le.setText(path_url_icon)
        elif fav_file:
            logger.info(f"Only available icon is fav_icon: {path_fav_icon}")
            self.icon_path_le.setText(path_fav_icon)
        elif default_file:
            logger.info(f"Only available icon is default_file_icon: {path_default_file_icon}")
            self.icon_path_le.setText(path_default_file_icon)

    def has_multiple_icons(self, *variables):

        non_empty_count = sum(1 for arg in variables if arg is not None and arg != "")
        return non_empty_count >= 2


    #last minute checks before saving
    def handle_save(self):

        #ensure clean paths for icon_path and executable_path
        self.cleanup_path()

        if get_setting("local_icons"):
            if os.path.isfile(self.icon_path_le.text()) == True:
                data_directory = get_data_directory()
                # if icon does not start with the default data directory
                if not self.icon_path_le.text().startswith(data_directory):
                    new_dir = make_local_icon(self.icon_path_le.text(), self.parent().get_data_icon_dir(ROW,COL))
                    self.icon_path_le.setText(new_dir)

        #.lnks do not have command line arguments supported (possible but annoying to implement)
        if self.exec_path_le.text().endswith(".lnk") and self.command_args_le.text() != "":
            display_lnk_cli_args_warning()
            self.command_args_le.setText("")
            return
        #this can call for save even if path for icon is wrong, so do this one last as doing it before the other error checks can result in it saving THEN displaying another warning.
        #check icon_path_le if it is NOT empty AND the path to file does NOT exist (invalid path)
        if self.icon_path_le.text() != "" and os.path.isfile(self.icon_path_le.text()) != True:
            # Show warning if user clicks cancel -> return and do not save, if Ok -> save
            if display_icon_path_not_exist_warning(self.icon_path_le.text()) == QMessageBox.Yes:
                self.save()
        else:
            self.save()
                

    def save(self):
        config = load_desktop_config()

        if entry_exists(ROW, COL) == True:
            new_config = self.edit_entry(config)
        else:
            new_config = self.add_entry(config)
            
        save_config_to_file(new_config)
        self.parent().add_icon(ROW, COL)
        self.close()

            
    def add_entry(self, config):

        font_size, font_color = self.is_non_default_font()
        print(f"font_size {font_size}, font_color {font_color}")

        new_entry = {
        "row": ROW,
        "column": COL,
        "name": self.name_le.text(),
        "icon_path": self.icon_path_le.text(),
        "executable_path": self.exec_path_le.text(),
        "command_args": self.command_args_le.text(),
        "website_link": self.web_link_le.text(),
        "launch_option": self.launch_option_cb.currentIndex(),
        "font_size": self.font_size_sb.value(),
        "use_global_font_size": font_size,
        "font_color": self.font_color,
        "use_global_font_color": font_color
        }
        config.append(new_entry)
        return config


    def edit_entry(self, config):
        font_size, font_color = self.is_non_default_font()
        print(f"font_size {font_size}, font_color {font_color}")

        for item in config:
            if item['row'] == ROW and item['column'] == COL:
                item['name'] = self.name_le.text()
                item['icon_path'] = self.icon_path_le.text()
                item['executable_path'] = self.exec_path_le.text()
                item['command_args'] = self.command_args_le.text()
                item["website_link"] = self.web_link_le.text()
                item["launch_option"] = self.launch_option_cb.currentIndex()
                item['font_size'] = self.font_size_sb.value()
                item['use_global_font_size'] = font_size
                item['font_color'] = self.font_color
                item['use_global_font_color'] = font_color
                break
        return config


    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            self.get_drop(urls)
            event.acceptProposedAction()
    
    def get_drop(self, urls):
        if urls:
                file_path = urls[0].toLocalFile()
                file_name = file_path.split('/')[-1]
                file_extension = file_path.split('.')[-1].lower()

                image_extensions = {'jpg', 'jpeg', 'png', 'ico', 'bmp', 'gif', 'tiff'}
                if file_extension in image_extensions:
                    if file_extension == 'ico':
                        file_path = self.upscale_ico(file_path)
                    else:
                        self.icon_path_le.setText(file_path)
                else:
                    self.exec_path_le.setText(file_path)           

                #only change name line edit if the name is empty (i.e. take the name of the first drag and drop or do not overwrite a name already existing)
                if self.name_le.text() == "":
                    self.name_le.setText(self.remove_file_extentions(file_name))
    
    def handle_selection_change(self, index):
        global LAUNCH_OPTIONS
        LAUNCH_OPTIONS = index
        logger.info(f"Selected index: {index}, option: {self.launch_option_cb.currentText()}")
    
    def upscale_ico(self, file_path):
        data_path = self.parent().get_data_icon_dir(ROW,COL)
        output_path = os.path.join(data_path, "icon.png")
        icon_size = self.parent().get_autogen_icon_size()

        
        logger.info(f"upscale_ico() output_path: {data_path}")
        logger.info(f"upscale_ico() file_path: {file_path}")
        upscaled_icon = get_exact_img_file(file_path, output_path, icon_size)
        if(upscaled_icon):
            logger.info("upscaled .ICO file Success")
            self.icon_path_le.setText(output_path)


    def remove_file_extentions(self, file_name):
        while True:
            file_name, extension = os.path.splitext(file_name)
            if not extension:
                break
        return file_name
    
    def exec_folder_button_clicked(self):
        file_dialog = QFileDialog()
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.exec_path_le.setText(selected_file)

    def icon_folder_button_clicked(self):
        file_dialog = QFileDialog()
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.icon_path_le.setText(selected_file)

    def font_size_changed_toggle(self):
        self.font_size_changed = True
        self.parent().preview_font_size_change(ROW, COL, self.font_size_sb.value())
        # This is to catch if user hits reset button, then changes font size.
        self.reset_font_size = False

    def reset_font_size_to_default(self):
        self.font_size_sb.setValue(get_setting("global_font_size", 10))
        self.reset_font_size = True
    def reset_font_color_to_default(self):
        print("reset font color")
        self.font_color = (get_setting("global_font_color", "#ffffff"))
        self.custom_font_color.setStyleSheet(f"background-color: {self.font_color};") 
        self.parent().preview_font_color_change(ROW, COL, self.font_color)
        self.reset_font_color = True

    def is_non_default_font(self):
        font_size = False
        font_color = False

        # If font size setting's "Reset" button was pressed and no changes after pressing reset.
        if self.reset_font_size:
            font_size = True
        # (Already Uses default_font_size) AND ((NOT changed font size spinbox) OR (Spinbox changed but reverted to initial value))
        elif self.use_global_font_size and (not self.font_size_changed or self.font_size_sb.value() == get_icon_font_size(ROW, COL)):
            font_size = True

        if self.reset_font_color:
            font_color = True
        elif self.use_global_font_color and (not self.font_color_changed or self.font_color == get_icon_font_color(ROW, COL)):
            font_color = True


        return font_size, font_color


    def open_color_dialog(self):
        color_dialog = QColorDialog(self)
        init_color = self.font_color
        color_dialog.setCurrentColor(init_color)  

        # Preview based on currently selected color in selector.
        def update_color(color):
            if color.isValid():
                new_color = color.name()
                self.font_color = new_color 
                self.custom_font_color.setStyleSheet(f"background-color: {new_color};")  # Update button background color
                self.parent().preview_font_color_change(ROW, COL, new_color)

        color_dialog.currentColorChanged.connect(update_color)

        # Accepted means full return (clicked Ok)
        if color_dialog.exec() == QDialog.Accepted:
            selected_color = color_dialog.currentColor()
            if selected_color.isValid():
                # If init color is same as saved color, font_color has not changed.
                if init_color != selected_color.name():
                    logger.info(f"User saved color selector with a different color than when opened. {selected_color.name()}")
                    self.font_color_changed = True
                self.font_color = selected_color.name()
                self.custom_font_color.setStyleSheet(f"background-color: {self.font_color};")  # Update button background color