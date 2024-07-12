from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QCheckBox


import json
import os


JSON = "empty"

COL = -1
ROW = -1

class Menu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)



        global ROW 
        global COL 
        global JSON
        
        ROW = self.parent().get_row()
        COL = self.parent().get_col()
        JSON = self.parent().get_json()

        self.setWindowTitle("Settings")
        layout = QFormLayout()
        self.setLayout(layout)
        self.setWindowTitle("QLabel and QLineEdit")

        self.name_le = QLineEdit()
        self.icon_path_le = QLineEdit()
        self.exec_path_le = QLineEdit()
        
        


        layout.addRow("Name: ", self.name_le)
        layout.addRow("Icon Path: ", self.icon_path_le)
        layout.addRow("Executable Path: ", self.exec_path_le)

        #self.parent().set_icon_path("floor.png")

        save_button = QPushButton("Save")
        #save_button.clicked.connect(self.save_settings)
        
        save_button.clicked.connect(self.save_config)

        layout.addWidget(save_button)




    def save_config(self):
        print(JSON)
        print("save")
        if self.entry_exists() == True:
            self.edit_entry()
        else:
            self.add_entry()
        self.update_clickable_item()
        self.parent().save_json(JSON)
        self.close()
        
            
    def add_entry(self):
        new_entry = {
        "row": ROW,
        "column": COL,
        "name": self.name_le.text(),
        "icon_path": self.icon_path_le.text(),
        "executable_path": self.exec_path_le.text()
        }
        JSON.append(new_entry)
        
    def update_clickable_item(self):
        self.parent().set_name(self.name_le.text())
        self.parent().set_icon_path(self.icon_path_le.text())
        self.parent().set_executable_path(self.exec_path_le.text())

    def edit_entry(self):
        print(f"Json: {JSON}")
        for item in JSON:
            if item['row'] == ROW and item['column'] == COL:
                item['name'] = self.name_le.text()
                item['icon_path'] = self.icon_path_le.text()
                item['executable_path'] = self.exec_path_le.text()
                print(f"Json updated: {JSON}")
                break


    def entry_exists(self):
        for item in JSON:
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