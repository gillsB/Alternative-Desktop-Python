import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QGridLayout, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
import json

MAX_LABELS = None
MAX_ROWS = 10 #only used for now to get max_labels
MAX_COLS = 20
DESKTOP_CONFIG_DIRECTORY = None
JSON = None

DEFAULT_DESKTOP = [
    {
        "row": 0,
        "column": 0,
        "name": "App1",
        "icon_path": "icon.png",
        "executable_path": "a.exe"
    },
    {
        "row": 0,
        "column": 1,
        "name": "App2",
        "icon_path": "floor.png",
        "executable_path": "app2.exe"
    }
]




class Grid(QWidget):
    def __init__(self):
        super().__init__()

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.setLayout(self.grid_layout)

        self.labels = []
        self.label_size = 50

        #set MAX_LABELS to the maximum amount of items you would need based on rows/cols
        MAX_LABELS = MAX_ROWS * MAX_COLS


        #use MAX_COLS to diffrentiate when to add a new row.
        '''for i in range(MAX_LABELS):
            row = i // MAX_COLS
            col = i % MAX_COLS
            name = "app.sc"
            icon_path = ""
            executable_path = "app.exe"
            desktop_icon = DesktopIcon(row, col, name, icon_path, executable_path)
            label = ClickableLabel(desktop_icon)
            self.labels.append(label)
            self.grid_layout.addWidget(label, row, col)
        '''
        for i in range(MAX_LABELS):
            row = i // MAX_COLS
            col = i % MAX_COLS
            name = self.get_name(row,col)
            icon_path = self.get_icon_path(row,col)
            executable_path = self.get_exectuable_path(row,col)
            desktop_icon = DesktopIcon(row, col, name, icon_path, executable_path)
            label = ClickableLabel(desktop_icon)
            self.labels.append(label)
            self.grid_layout.addWidget(label, row, col)

        print(self.get_icon_path(0, 1))
        
    def get_icon_path(self, row, column):
        for item in JSON:
            if item['row'] == row and item['column'] == column:
                return item['icon_path']
        return ""
    def get_name(self, row, column):
        for item in JSON:
            if item['row'] == row and item['column'] == column:
                return item['name']
        return ""
    def get_exectuable_path(self, row, column):
        for item in JSON:
            if item['row'] == row and item['column'] == column:
                return item['executable_path']
        return ""
    
    
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.draw_labels()

    def draw_labels(self):
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()

        

        num_columns = max(1, window_width // self.label_size)
        num_rows = max(1, window_height // self.label_size)

        print(f"window dimensions : {window_width}x{window_height}")
        print(f"window num_rows : {num_rows}")
        print(f"window num_cols : {num_columns}")

        for label in self.labels:
            row = label.desktop_icon.row
            col = label.desktop_icon.col

            if col < num_columns and row < num_rows:
                label.show()
            else:
                label.hide()


class ClickableLabel(QLabel):
    def __init__(self, desktop_icon, parent=None):
        super().__init__(parent)
        self.desktop_icon = desktop_icon
        self.setFixedSize(50, 50)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.set_icon(self.desktop_icon.icon_path)

        layout = QVBoxLayout(self)
        layout.addWidget(self.icon_label)
        layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(layout)

    def set_icon(self, icon_path):
        pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print(f"Row: {self.desktop_icon.row}, Column: {self.desktop_icon.col}, Name: {self.desktop_icon.name}, Icon_path: {self.desktop_icon.icon_path}, Exec Path: {self.desktop_icon.executable_path}")
            #set all icons clicked to default icon.png (for ensuring that clickable keeps working.)
            new_icon_path = "icon.png"  
            self.desktop_icon.icon_path = new_icon_path
            self.set_icon(new_icon_path)

    def get_row(self):
        return self.desktop_icon.row
    def get_col(self):
        return self.desktop_icon.col
    def get_coord(self):
        return f"Row: {self.desktop_icon.row}, Column: {self.desktop_icon.col}"


class DesktopIcon:
    def __init__(self, row, col, name, icon_path, executable_path):
        self.row = row
        self.col = col
        self.name = name
        self.icon_path = icon_path
        self.executable_path = executable_path




if __name__ == "__main__":


    ### code within these are temporary, since i am running this as a main file
    # would instead be setup like settings where i just call this file and pass it the DESKTOP_CONFIG_DIRECTORY
    
    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create app_data directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    # Append /config/settings.json to the AppData path
    config_path = os.path.join(app_data_path, 'config', 'desktop.json')

    #create the /config/settings.json if they do not exist already.
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        print("makedir")
        os.makedirs(config_dir)

    print(f"Configuration file path: {config_path}")
    DESKTOP_CONFIG_DIRECTORY = config_path

    if os.path.exists(DESKTOP_CONFIG_DIRECTORY):
        with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
            JSON = json.load(f)
    else:
        print("Error loading settings, expected file at: " + DESKTOP_CONFIG_DIRECTORY )
        
    with open(DESKTOP_CONFIG_DIRECTORY, "w") as f:
        json.dump(DEFAULT_DESKTOP, f, indent=4)

    
    ###


    app = QApplication(sys.argv)
    widget = Grid()
    widget.setMinimumSize(100, 100)  
    widget.resize(1920, 1000)
    widget.draw_labels()
    widget.show()
    sys.exit(app.exec())