from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QFormLayout, QCheckBox

class Menu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        layout = QFormLayout()

        self.setWindowTitle("QLabel and QLineEdit")
        self.setFixedSize(300, 200)

        name = QLabel("Name : ")
        self.name_le = QLineEdit()

        icon_path = QLabel("Icon Path : ")
        self.icon_path_le = QLineEdit()

        exec_path = QLabel("Executable Path: ")
        self.exec_path_le = QLineEdit()
        
        
        
        
        '''
        self.line_edit.textChanged.connect(self.text_changed)
        self.line_edit.cursorPositionChanged.connect(self.cursor_position_changed)

        self.line_edit.returnPressed.connect(self.return_pressed)

        self.line_edit.selectionChanged.connect(self.selection_changed)

        self.line_edit.textEdited.connect(self.text_edited)

        '''

        button = QPushButton("save")
        button.clicked.connect(self.button_clicked)
        

        name_layout = QHBoxLayout()
        name_layout.addWidget(name)
        name_layout.addWidget(self.name_le)

        icon_path_layout = QHBoxLayout()
        icon_path_layout.addWidget(icon_path)
        icon_path_layout.addWidget(self.icon_path_le)

        exec_path_layout = QHBoxLayout()
        exec_path_layout.addWidget(exec_path)
        exec_path_layout.addWidget(self.exec_path_le)

        v_layout = QVBoxLayout()
        v_layout.addLayout(name_layout)
        v_layout.addLayout(icon_path_layout)
        v_layout.addLayout(exec_path_layout)
        v_layout.addWidget(button)

        self.setLayout(v_layout)


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