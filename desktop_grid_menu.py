from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QCheckBox


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
        self.setWindowTitle("QLabel and QLineEdit")

        self.name_le = QLineEdit()
        self.icon_path_le = QLineEdit()
        self.exec_path_le = QLineEdit()
        self.parent().selected_border(10)
        icon_path = ""
        
        for item in config:
            
            if item['row'] == ROW and item['column'] == COL:
                self.name_le.setText(item['name'])
                print(f"super long name so that ican see it in console: {item['name']}")
                print(f"super long name so that ican see it in console: {item['icon_path']}")
                icon_path = item['icon_path']
                self.icon_path_le.setText(item['icon_path'])
                print(f"super long name so that ican see it in console: {icon_path}")
                self.exec_path_le.setText(item['executable_path'])
                break
            print(f"ICON PATH {icon_path}")
        if icon_path == "":
            self.parent().set_icon_path("add2.png")
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
        self.parent().render_icon()


    def save_config(self):
        config = self.parent().load_desktop_config()
        print(f"config before = {config}")
        if self.entry_exists(config) == True:
            new_config = self.edit_entry(config)
        else:
            new_config = self.add_entry(config)
        self.parent().save_desktop_config(new_config)
        self.close()

        
            
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