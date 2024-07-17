from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QCheckBox, QMessageBox
from PySide6.QtGui import QDragEnterEvent, QDropEvent


import json
import os




COL = -1
ROW = -1
ICON_PATH = ""

class Menu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)



        global ROW 
        global COL 


        config = self.parent().load_desktop_config()
        ROW = self.parent().get_row()
        COL = self.parent().get_col()


        self.setWindowTitle("Settings")
        layout = QFormLayout()
        self.setLayout(layout)
        self.setWindowTitle(f"Editing [{self.parent().get_row()}, {self.parent().get_col()}]")

        self.name_le = QLineEdit()
        self.icon_path_le = QLineEdit()
        self.exec_path_le = QLineEdit()
        self.parent().selected_border(10)
        icon_path = ""

        self.setAcceptDrops(True)
        
        for item in config:
            
            if item['row'] == ROW and item['column'] == COL:
                self.name_le.setText(item['name'])
                icon_path = item['icon_path']
                self.icon_path_le.setText(item['icon_path'])
                self.exec_path_le.setText(item['executable_path'])
                break
            print(f"ICON PATH {icon_path}")
        if icon_path == "":
            self.parent().set_icon_path("assets/images/add2.png")
        self.parent().selected_border(10)


        layout.addRow("Name: ", self.name_le)
        layout.addRow("Icon Path: ", self.icon_path_le)
        layout.addRow("Executable Path: ", self.exec_path_le)


        save_button = QPushButton("Save")
        
        save_button.clicked.connect(self.save_config)

        layout.addWidget(save_button)



    def closeEvent(self, event):
        print("closed")
        self.parent().default_border()
        print(f"closing get item_path = {self.parent().get_icon_path()}")
        #revert add
        if self.parent().get_icon_path() == "assets/images/add2.png":
            self.parent().set_icon_path("assets/images/blank.png")

        self.parent().render_icon()

    def check_valid_path(self, path):
        return os.path.isfile(path)
    

    ## clean up common problems with file path, i.e. copying a file and pasting into exec_path produces file:///C:/...
    # the correct path for use requires just the C:/...
    def cleanup_exec_path(self):
        if self.exec_path_le.text().startswith("file:///"):
            self.exec_path_le.setText(self.exec_path_le.text()[8:])  # remove "file:///"
        elif self.exec_path_le.text().startswith("file://"):
            self.exec_path_le.setText(self.exec_path_le.text()[7:])  # Remove 'file://' prefix


    def save_config(self):
        config = self.parent().load_desktop_config()
        print(f"config before = {config}")
        self.cleanup_exec_path()

        # if exec_path is empty save file
        if self.exec_path_le.text() == "":
            new_config = self.edit_entry(config)
            self.parent().save_desktop_config(new_config)
            self.close()
        #if exec_path is not empty check if it is a valid path then save if valid
        elif self.check_valid_path(self.exec_path_le.text()):
            if self.entry_exists(config) == True:
                new_config = self.edit_entry(config)
            else:
                new_config = self.add_entry(config)
            self.parent().save_desktop_config(new_config)
            self.close()
        # exec_path is not empty, and not a valid path. show warning (and do not close the menu)
        else:
            QMessageBox.warning(self,"Error: File Path", "Error: Executable path, item at path does not exist", QMessageBox.Ok | QMessageBox.Cancel)
        
            
    def add_entry(self, config):
        new_entry = {
        "row": ROW,
        "column": COL,
        "name": self.name_le.text(),
        "icon_path": self.icon_path_le.text(),
        "executable_path": self.exec_path_le.text()
        }
        config.append(new_entry)
        return config


    def edit_entry(self, config):
        
        for item in config:
            if item['row'] == ROW and item['column'] == COL:
                item['name'] = self.name_le.text()
                item['icon_path'] = self.icon_path_le.text()
                item['executable_path'] = self.exec_path_le.text()
                #print(f"Json updated: {config}")
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
                exec_path = urls[0].toLocalFile()
                name = exec_path.split('/')[-1]
                self.exec_path_le.setText(exec_path)
                self.name_le.setText(name)
                self.icon_path_le.setText("")
                event.acceptProposedAction()

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