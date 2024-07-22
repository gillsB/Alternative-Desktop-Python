from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QCheckBox, QMessageBox, QTabWidget
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from thumbnail_gen.extract_ico_file import has_ico_file


import json
import os




COL = -1
ROW = -1


class Menu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)


        global ROW 
        global COL 

        config = self.parent().load_config()
        ROW = self.parent().get_row()
        COL = self.parent().get_col()

        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        
        self.basic_tab = QWidget()
        self.basic_tab_layout = QFormLayout()

        self.setWindowTitle(f"Editing [{self.parent().get_row()}, {self.parent().get_col()}]")

        self.name_le = QLineEdit()
        self.icon_path_le = QLineEdit()
        self.exec_path_le = QLineEdit()
        self.command_args_le = QLineEdit()
        self.parent().selected_border(10)
        icon_path = ""

        self.setAcceptDrops(True)
        



        self.basic_tab_layout.addRow("Name: ", self.name_le)
        self.basic_tab_layout.addRow("Icon Path: ", self.icon_path_le)
        self.basic_tab_layout.addRow("Executable Path: ", self.exec_path_le)
        #self.basic_tab_layout.addRow("Command line arguments: ", self.command_args_le)

        self.basic_tab.setLayout(self.basic_tab_layout)

        #### end of basic tab
        self.advanced_tab = QWidget()
        self.advanced_tab_layout = QFormLayout()
        
        self.advanced_setting_le = QLineEdit()
        self.advanced_tab_layout.addRow("Command line arguments: ", self.command_args_le)

        self.advanced_tab.setLayout(self.advanced_tab_layout)

        self.tabs.addTab(self.basic_tab, "Basic")
        self.tabs.addTab(self.advanced_tab, "Advanced")

        main_layout.addWidget(self.tabs)


        ## load already saved data for desktop_icon into fields in this menu
        for item in config:
            
            if item['row'] == ROW and item['column'] == COL:
                self.name_le.setText(item['name'])
                icon_path = item['icon_path']
                self.icon_path_le.setText(item['icon_path'])
                self.exec_path_le.setText(item['executable_path'])
                self.command_args_le.setText(item['command_args'])
                break
        if icon_path == "":
            self.parent().set_icon_path("assets/images/add2.png")
        self.parent().selected_border(10)

        save_button = QPushButton("Save")
        
        save_button.clicked.connect(self.save_config)

        main_layout.addWidget(save_button)

        self.setLayout(main_layout)



    def closeEvent(self, event):
        print("closed edit menu")
        self.parent().default_border()
        #revert add
        if self.parent().get_icon_path() == "assets/images/add2.png":
            self.parent().set_icon_path("assets/images/blank.png")

        self.parent().render_icon()

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
        if self.exec_path_le.text() == "":
            self.handle_save()
        #if exec_path is not empty check if it is a valid path then save if valid
        elif self.check_valid_path(self.exec_path_le.text()):
            self.handle_save()
        # exec_path is not empty, and not a valid path. show warning (and do not close the menu)
        else:
            QMessageBox.warning(self,"Error: File Path", "Error: Executable path, item at path does not exist", QMessageBox.Ok | QMessageBox.Cancel)

    #exec_path is "" or valid so now save
    def handle_save(self):
        config = self.parent().load_config()
        print(f"config before = {config}")
        self.cleanup_path()

        if self.entry_exists(config) == True:
            new_config = self.edit_entry(config)
        else:
            new_config = self.add_entry(config)

        # display a warning if user wants to save a .lnk exec_path WITH command arguments (not supported, possible to support but for 99.9% of users wouldn't be worth the time)
        if self.exec_path_le.text().endswith(".lnk") and self.command_args_le.text() != "":
            QMessageBox.warning(self,"Warning .lnk", "Warning: .lnk files do not have command arguments support. Please add the command arguments to the .lnk file itself or replace the .lnk with the file it points to.", QMessageBox.Ok)
            self.command_args_le.setText("")
        else:
            self.parent().save_desktop_config(new_config)
            self.close()
        
            
    def add_entry(self, config):
        new_entry = {
        "row": ROW,
        "column": COL,
        "name": self.name_le.text(),
        "icon_path": self.icon_path_le.text(),
        "executable_path": self.exec_path_le.text(),
        "command_args": self.command_args_le.text()
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
                break
        return config
        
    def entry_exists(self, config):
        for item in config:
            if item['row'] == ROW and item['column'] == COL:
                return True
        return False



    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
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
                event.acceptProposedAction()
    
    def upscale_ico(self, file_path):
        data_path = self.parent().get_data_icon_dir()
        
        print(f"DATA PATH: {data_path}")
        print(f"FILE PATH: {file_path}")
        upscaled_icon = has_ico_file(file_path, data_path)
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