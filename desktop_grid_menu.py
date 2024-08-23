from PySide6.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QCheckBox, QToolButton,
                               QMessageBox, QTabWidget, QComboBox, QStyle, QFileDialog)
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtCore import QSize, Qt
from icon_gen.extract_ico_file import extract_ico_file
from icon_gen.lnk_to_image import lnk_to_image
from icon_gen.exe_to_image import exe_to_image
from icon_gen.url_to_image import url_to_image
from icon_gen.icon_selection import select_icon_from_paths
from icon_gen.favicon_to_image import favicon_to_image
from icon_gen.browser_to_image import browser_to_image
from icon_gen.default_icon_to_image import default_icon_to_image
from config import (load_desktop_config, entry_exists, get_entry, save_config_to_file, get_data_directory)
from settings import get_setting
import os
import shutil



COL = -1
ROW = -1
LAUNCH_OPTIONS = 0


class Menu(QDialog):
    def __init__(self, urls, parent=None):
        super().__init__(parent)

        
        global ROW 
        global COL 

        ROW = self.parent().get_row()
        COL = self.parent().get_col()

        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DesktopIcon))

        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        
        self.basic_tab = QWidget()
        self.basic_tab_layout = QFormLayout()

        

        self.name_le = ClearableLineEdit()
        self.icon_path_le = ClearableLineEdit()
        self.exec_path_le = ClearableLineEdit()
        self.web_link_le = ClearableLineEdit()
        self.parent().selected_border(10)

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

        self.tabs.addTab(self.basic_tab, "Basic")
        self.tabs.addTab(self.advanced_tab, "Advanced")

        main_layout.addWidget(self.tabs)

        global LAUNCH_OPTIONS

        ## load already saved data for desktop_icon into fields in this menu
        entry = get_entry(ROW, COL)
        if entry:
            self.name_le.setText(entry['name'])
            self.icon_path_le.setText(entry['icon_path'])
            self.exec_path_le.setText(entry['executable_path'])
            self.web_link_le.setText(entry['website_link'])
            self.command_args_le.setText(entry['command_args'])
            self.launch_option_cb.setCurrentIndex(entry['launch_option'])
            LAUNCH_OPTIONS = entry['launch_option']



        self.setWindowTitle(f"Editing [{self.parent().get_row()}, {self.parent().get_col()}]: {self.name_le.text()}")
        if urls != None:
            self.get_drop(urls)

        self.parent().edit_mode_icon()

        auto_gen_icon_button = QPushButton("Auto generate icon")
        auto_gen_icon_button.clicked.connect(self.auto_gen_button)
        main_layout.addWidget(auto_gen_icon_button)

        save_button = QPushButton("Save")
        
        save_button.clicked.connect(self.save_config)

        main_layout.addWidget(save_button)

        self.setLayout(main_layout)



    def closeEvent(self, event):
        print("closed edit menu")
        self.parent().normal_mode_icon()

    def check_valid_path(self, path):
        return os.path.isfile(path)
    

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

        # if exec_path is empty -> save file
        if self.exec_path_le.text() == "" and self.web_link_le == "":
            
            self.handle_save()
        # if icon already set, do not auto_gen_icon
        elif self.icon_path_le.text() != "":
            self.handle_save()
        #if exec_path is not empty check if it is a valid path then save if valid
        elif self.check_valid_path(self.exec_path_le.text()) or self.web_link_le != "":
            self.auto_gen_icon()
            self.handle_save()
        # exec_path is not empty, and not a valid path. show warning (and do not close the menu)
        else:
            QMessageBox.warning(self,"Error: File Path", "Error: Executable path, item at path does not exist", QMessageBox.Ok | QMessageBox.Cancel)

    def auto_gen_button(self):
        if self.icon_path_le.text() != "":
            ret = QMessageBox.warning(self,"Icon Path exists", "You already have an Icon Path set. Would you like to discard this Icon Path to generate a new one?", QMessageBox.Ok | QMessageBox.Cancel)
            if ret == QMessageBox.Cancel:
                return
            self.icon_path_le.setText("")
        self.auto_gen_icon()
        self.parent().set_icon_path(self.icon_path_le.text())
        self.parent().edit_mode_icon()

    def auto_gen_icon(self):

        data_path = self.parent().get_data_icon_dir()
        icon_size = self.parent().get_autogen_icon_size()

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

        if self.exec_path_le.text() != "" and extract_ico_file(self.exec_path_le.text(), data_path, icon_size):
            ico_file = True
            path_ico_icon = os.path.join(data_path, "icon.png")

        if self.icon_path_le.text() == "" and self.exec_path_le.text().endswith(".lnk"):

            path_ico_icon, path_lnk_icon = lnk_to_image(self.exec_path_le.text(), data_path, icon_size)

            if path_lnk_icon != None:
                lnk_file = True
            if path_ico_icon != None:
                ico_file = True
            
        elif self.icon_path_le.text() == "" and self.exec_path_le.text().endswith(".exe"):
            path_exe_icon = exe_to_image(self.exec_path_le.text(), data_path, icon_size)  
            if path_exe_icon != None:
                exe_file = True

        elif self.icon_path_le.text() == "":
            path_default_file_icon = default_icon_to_image(self.exec_path_le.text(), data_path, icon_size)
            if path_default_file_icon != None:
                default_file = True

        if self.web_link_le.text() != "":
            url = self.web_link_le.text()
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            path_fav_icon = favicon_to_image(url, data_path, icon_size)
            if path_fav_icon != None:
                fav_file = True
            #if it fails to create a favicon fallback
            else:
                #create a default browser icon for links
                path_fav_icon = browser_to_image(data_path, icon_size)
                if path_fav_icon != None:
                    fav_file = True


        
        if self.icon_path_le.text() == "" and self.exec_path_le.text().endswith(".url"):

            path_ico_icon = url_to_image(self.exec_path_le.text(), data_path, icon_size)

            if path_ico_icon != None:
                ico_file = True


        if self.has_multiple_icons(path_ico_icon, path_exe_icon, path_lnk_icon, path_url_icon, path_fav_icon, path_default_file_icon):
            icon_selected = select_icon_from_paths(path_ico_icon, path_exe_icon, path_lnk_icon, path_url_icon, path_fav_icon, path_default_file_icon)
            self.icon_path_le.setText(icon_selected)
        elif ico_file:
            self.icon_path_le.setText(path_ico_icon)
        elif lnk_file:
            self.icon_path_le.setText(path_lnk_icon)
        elif exe_file:
            self.icon_path_le.setText(path_exe_icon)
        elif url_file:
            self.icon_path_le.setText(path_url_icon)
        elif fav_file:
            self.icon_path_le.setText(path_fav_icon)
        elif default_file:
            self.icon_path_le.setText(path_default_file_icon)

    def has_multiple_icons(self, *variables):

        non_empty_count = sum(1 for arg in variables if arg is not None and arg != "")
        return non_empty_count >= 2

    def make_local_icon(self, icon_path):
        #ensure datapath for [row, col] exists
        data_path = self.parent().get_data_icon_dir()
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            
        #get original image name
        file_name = os.path.basename(icon_path)
        
        #join it to data path for full save location
        output_path = os.path.join(data_path, file_name)
        #ensure that it has a unique file name to not overwrite if named icon.png etc.
        output_path = self.get_unique_folder_name(output_path)
        
        try:
            print(f"Trying to copy {icon_path} to {output_path}")
            shutil.copy(icon_path, output_path)
            return output_path
        
        except Exception as e:
            print(f"Error copying file: {e}")
            return None
        
    #takes output path and injects _local before the file extention
    #if a copy with the same name already exists it becomes _local1, _local2, _local3 etc.
    def get_unique_folder_name(self, folder_path):
        base, ext = os.path.splitext(folder_path)
        counter = 1
        new_folder = f"{base}_local{ext}"
        
        while os.path.exists(new_folder):
            new_folder = f"{base}_local{counter}{ext}"
            counter += 1
            
        return new_folder

    #last minute checks before saving
    def handle_save(self):

        #ensure clean paths for icon_path and executable_path
        self.cleanup_path()

        if get_setting("local_icons"):
            
            data_directory = get_data_directory()
            # if icon does not start with the default data directory
            if not self.icon_path_le.text().startswith(data_directory):
                new_dir = self.make_local_icon(self.icon_path_le.text())
                self.icon_path_le.setText(new_dir)

        #.lnks do not have command line arguments supported (possible but annoying to implement)
        if self.exec_path_le.text().endswith(".lnk") and self.command_args_le.text() != "":
            QMessageBox.warning(self,"Warning .lnk", "Warning: .lnk files do not have command arguments support. Please add the command arguments to the .lnk file itself or replace the .lnk with the file it points to.", QMessageBox.Ok)
            self.command_args_le.setText("")
        #this can call for save even if path for icon is wrong, so do this one last as doing it before the other error checks can result in it saving THEN displaying another warning.
        #check icon_path_le if it is NOT empty AND the path to file does NOT exist (invalid path)
        if self.icon_path_le.text() != "" and self.check_valid_path(self.icon_path_le.text()) != True:
            ret = QMessageBox.warning(self,"Error: Icon Path", f"Error: Icon path, item at path: \n{self.icon_path_le.text()} does not exist. \nClick OK save regardless, or Cancel to continue editing.", QMessageBox.Ok | QMessageBox.Cancel)
            if ret == QMessageBox.Ok:
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
        self.close()

        
            
    def add_entry(self, config):
        new_entry = {
        "row": ROW,
        "column": COL,
        "name": self.name_le.text(),
        "icon_path": self.icon_path_le.text(),
        "executable_path": self.exec_path_le.text(),
        "command_args": self.command_args_le.text(),
        "website_link": self.web_link_le.text(),
        "launch_option": self.launch_option_cb.currentIndex()
        }
        config.append(new_entry)
        return config


    def edit_entry(self, config):
        for item in config:
            if item['row'] == ROW and item['column'] == COL:
                item['name'] = self.name_le.text()
                item['icon_path'] = self.icon_path_le.text()
                item['executable_path'] = self.exec_path_le.text()
                item['command_args'] = self.command_args_le.text()
                item["website_link"] = self.web_link_le.text()
                item["launch_option"] = self.launch_option_cb.currentIndex()
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
        print(f"Selected index: {index}, option: {self.launch_option_cb.currentText()}")
    
    def upscale_ico(self, file_path):
        data_path = self.parent().get_data_icon_dir()
        
        print(f"DATA PATH: {data_path}")
        print(f"FILE PATH: {file_path}")
        upscaled_icon = extract_ico_file(file_path, data_path)
        if(upscaled_icon):
            print("UPSCALED .ICO FILE")
            data_path = os.path.join(data_path, "icon.png")
            self.icon_path_le.setText(data_path)


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

    def text_changed(self):
        ...

    def cursor_position_changed(self, old, new):
        print("old position: ",old," New position: ",new)


    def editing_finished(self):
        print("editing finished")
    def return_pressed(self):
        print("return pressed")

    def selection_changed(self):
        ...

    def text_edited(self, new_text):
        print("text edited, new text: ", new_text)


class ClearableLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a clear button using a system default icon
        self.clear_button = QToolButton(self)
        self.clear_button.setIcon(self.style().standardIcon(QStyle.SP_LineEditClearButton))  
        self.clear_button.setCursor(Qt.ArrowCursor)
        self.clear_button.setStyleSheet("""
                QToolButton {
                    border: none;
                    padding: 0px;
                    background: transparent;  
                }
            """)

        self.clear_button.hide()

        # Setting button within frame
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet(f"padding-right: {self.clear_button.sizeHint().width() + frameWidth + 1}px;")
        self.clear_button.setFixedSize(self.sizeHint().height() - 2, self.sizeHint().height() - 2)

        self.update_clear_button_position(frameWidth)
        self.clear_button.clicked.connect(self.clear)
        self.textChanged.connect(self.update_clear_button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.update_clear_button_position(frameWidth)

    def update_clear_button_position(self, frameWidth):
        height_diff = (self.height() - self.clear_button.height()) // 2
        margin_right = 5 
        self.clear_button.move(self.rect().right() - frameWidth - self.clear_button.sizeHint().width() - margin_right,
                            height_diff)

    def update_clear_button(self, text):
        # Show clear button if line edit has text
        self.clear_button.setVisible(bool(text))