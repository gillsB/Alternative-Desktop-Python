from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QCheckBox

class Menu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        layout = QFormLayout()
        self.setLayout(layout)
        self.setWindowTitle("QLabel and QLineEdit")

        self.name_le = QLineEdit()
        self.icon_path_le = QLineEdit()
        self.exec_path_le = QLineEdit()
        
        

        button = QPushButton("save")
        button.clicked.connect(self.button_clicked)

        layout.addRow("Name: ", self.name_le)
        layout.addRow("Icon Path: ", self.icon_path_le)
        layout.addRow("Executable Path: ", self.exec_path_le)

        save_button = QPushButton("Save")
        #save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)






    def button_clicked(self):
        ...

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