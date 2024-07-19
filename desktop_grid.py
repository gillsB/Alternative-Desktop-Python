import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QGridLayout, QVBoxLayout, QDialog, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
import json
import subprocess
import shlex
from desktop_grid_menu import Menu
from thumbnail_gen.lnk_to_image import extract_icon_from_lnk
from thumbnail_gen.exe_to_image import extract_ico_from_exe




MAX_LABELS = None
MAX_ROWS = 10 #only used for now to get max_labels
MAX_COLS = 20
DESKTOP_CONFIG_DIRECTORY = None
JSON = ""
DATA_DIRECTORY = None
LABEL_SIZE = 200
LABEL_VERT_PAD = 200
DEFAULT_BORDER = "border 0px"



#These are all active .json arguments and their defaults
DEFAULT_DESKTOP =  {
    "row": -1,
    "column": -1,
    "name": "",
    "icon_path": "",
    "executable_path": "",
    "command_args": ""
}




class Grid(QWidget):
    def __init__(self):
        super().__init__()

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.setLayout(self.grid_layout)

        self.labels = []

        #set MAX_LABELS to the maximum amount of items you would need based on rows/cols
        MAX_LABELS = MAX_ROWS * MAX_COLS

        check_for_new_config()
        #use MAX_COLS to diffrentiate when to add a new row.
        for i in range(MAX_LABELS):
            row = i // MAX_COLS
            col = i % MAX_COLS
            name = self.get_name(row,col)
            icon_path = self.get_icon_path(row,col)
            if icon_path == "":
                icon_path = "assets/images/blank.png"
            executable_path = self.get_exectuable_path(row,col)
            command_args = self.get_command_args(row,col)
            desktop_icon = DesktopIcon(row, col, name, icon_path, executable_path, command_args)
            label = ClickableLabel(desktop_icon, name)
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
    def get_command_args(self, row, column):
        for item in JSON:
            if item['row'] == row and item['column'] == column:
                return item['command_args']
        return ""
    
    
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.draw_labels()

    def draw_labels(self):
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()

        num_columns = max(1, window_width // LABEL_SIZE)
        num_rows = max(1, window_height // (LABEL_SIZE + LABEL_VERT_PAD)) # +10 or else the labels can become smaller than their minimum icon size

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
    def __init__(self, desktop_icon, text, parent=None):
        super().__init__(parent)
        self.desktop_icon = desktop_icon
        self.setFixedSize(LABEL_SIZE, LABEL_SIZE* 2)
        self.setAlignment(Qt.AlignCenter)
        
        
        self.icon_label = QLabel(self)
        self.icon_label.setStyleSheet(DEFAULT_BORDER)
        self.icon_label.setFixedSize(LABEL_SIZE -2, LABEL_SIZE -2)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.set_icon(self.desktop_icon.icon_path)

        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        

        layout = QVBoxLayout(self)
        layout.addWidget(self.icon_label)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        self.render_icon()

    def set_icon(self, icon_path):
        pixmap = QPixmap(icon_path).scaled(LABEL_SIZE-2, LABEL_SIZE-2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            print(f"Row: {self.desktop_icon.row}, Column: {self.desktop_icon.col}, Name: {self.desktop_icon.name}, Icon_path: {self.desktop_icon.icon_path}, Exec Path: {self.desktop_icon.executable_path}, Command args: {self.desktop_icon.command_args}")
            menu = Menu(parent=self)
            menu.exec()
        elif event.button() == Qt.LeftButton and self.desktop_icon.icon_path == "assets/images/add.png":
            menu = Menu(parent=self)
            menu.exec()
        #if icon has an executable_path already (icon exists with path)
        elif event.button() == Qt.LeftButton and self.desktop_icon.executable_path != "":
            self.run_program()
    
    #mousover icon
    def enterEvent(self, event):
        if self.desktop_icon.icon_path == "assets/images/blank.png" or self.desktop_icon.icon_path == "":
            self.set_icon_path("assets/images/add.png")

    #mouseover leaves the icon
    def leaveEvent(self, event):
        if self.desktop_icon.icon_path == "assets/images/add.png":
            self.set_icon_path("assets/images/blank.png")
    
        
    def selected_border(self, percent):
        self.icon_label.setStyleSheet(f"border: {LABEL_SIZE * (percent/100)}px solid red;")

    def default_border(self):
        self.icon_label.setStyleSheet(DEFAULT_BORDER)

    def get_row(self):
        return self.desktop_icon.row
    def get_col(self):
        return self.desktop_icon.col
    def get_coord(self):
        return f"Row: {self.desktop_icon.row}, Column: {self.desktop_icon.col}"
    
    def set_name(self, new_name):
        self.desktop_icon.name = new_name
        self.text_label.setText(new_name)
        self.update()
    def set_icon_path(self, new_icon_path):
        self.desktop_icon.icon_path = new_icon_path
        self.set_icon(new_icon_path)
        self.icon_label.setStyleSheet(DEFAULT_BORDER)
    def set_executable_path(self, new_executable_path):
        self.desktop_icon.executable_path = new_executable_path
        # if no icon set and exec file is a .lnk (shortcut file)
        if (self.desktop_icon.icon_path == "assets/images/blank.png" or self.desktop_icon.icon_path == "assets/images/unknown.png" or self.desktop_icon.icon_path == "") and new_executable_path.endswith(".lnk"):
            # point to new file called [row, col]
            data_path = os.path.join(DATA_DIRECTORY, f'[{self.desktop_icon.row}, {self.desktop_icon.col}]')
            #make file if no file (new)
            if not os.path.exists(data_path):
                print("makedir")
                os.makedirs(data_path)

            extract_icon_from_lnk(new_executable_path, data_path)
            data_path = os.path.join(data_path, "icon.png")
            self.auto_gen_icon(data_path)    
        
        elif (self.desktop_icon.icon_path == "assets/images/blank.png" or self.desktop_icon.icon_path == "assets/images/unknown.png" or self.desktop_icon.icon_path == "") and new_executable_path.endswith(".exe"):
            data_path = os.path.join(DATA_DIRECTORY, f'[{self.desktop_icon.row}, {self.desktop_icon.col}]')
            #make file if no file (new)
            if not os.path.exists(data_path):
                print("makedir")
                os.makedirs(data_path)


            extract_ico_from_exe(new_executable_path, data_path)
            data_path = os.path.join(data_path, "icon.png")
            self.auto_gen_icon(data_path)  

        elif (self.desktop_icon.icon_path == "assets/images/blank.png" or self.desktop_icon.icon_path == "") and (self.desktop_icon.name != "" or self.desktop_icon.executable_path != ""):
            self.auto_gen_icon("assets/images/unknown.png")

    def set_command_args(self, command_args):
        self.desktop_icon.command_args = command_args

    def auto_gen_icon(self, new_icon_path):
        for item in JSON:
            if item['row'] == self.desktop_icon.row and item['column'] == self.desktop_icon.col:
                item['icon_path'] = new_icon_path
                break
        self.save_desktop_config(JSON)

    

    #
    #
    # This is required to run in order for any client sided (non restart) edit to appear/work as normal
    #
    #
    def render_icon(self):

        for item in JSON:
            if item['row'] == self.desktop_icon.row and item['column'] == self.desktop_icon.col:
                self.set_name(item['name'])
                self.set_icon_path(item['icon_path'])
                self.set_executable_path(item['executable_path'])
                self.set_command_args(item['command_args'])
                break

            

    def load_config(self):
        return load_desktop_config()

    
        

    def save_desktop_config(self, config):
        save_config_to_file(config)
        self.render_icon()
    
    def get_icon_path(self):
        return self.desktop_icon.icon_path
    
    def run_program(self):
        file_path = self.desktop_icon.executable_path
        args = shlex.split(self.desktop_icon.command_args)
        command = [file_path] + args
        try:
            #if it is a .lnk file it is expected that the .lnk contains the command line arguments
            #upon which running os.startfile(file_path) runs the .lnk the same as just clicking it from a shortcut
            if file_path.lower().endswith('.lnk'):
                os.startfile(file_path)
            else:
                subprocess.Popen(command)
        except FileNotFoundError:
            print("The specified file was not found")
        except Exception as e:
            print(f"An error occurred: {e}")
        

    
    def get_dir(self):
        return DESKTOP_CONFIG_DIRECTORY
    def get_json(self):
        return JSON




class DesktopIcon:
    def __init__(self, row, col, name, icon_path, executable_path, command_args):
        self.row = row
        self.col = col
        self.name = name
        self.icon_path = icon_path
        self.executable_path = executable_path
        self.command_args = command_args

def load_desktop_config():
    if os.path.exists(DESKTOP_CONFIG_DIRECTORY):
        with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
            return json.load(f)
    else:
        print("Error loading settings, expected file at: " + DESKTOP_CONFIG_DIRECTORY )
        return {}

def check_for_new_config():
    config = load_desktop_config()
    new_config = False

    for entry in config:
        for key, value in DEFAULT_DESKTOP.items():
            if key not in entry:
                print("key not in settings")
                entry[key] = value
                new_config = True

    if new_config:
        print("new settings")
        save_config_to_file(config)


def save_config_to_file(config):
    print("ATTEMPTING TO SAVE THE DESKTOP .JSON")
    global JSON
    with open(DESKTOP_CONFIG_DIRECTORY, "w") as f:
        json.dump(config, f, indent=4)
    with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
        JSON = json.load(f)


def create_data_path():

    global DATA_DIRECTORY
    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create app_data directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    # Append /config/settings.json to the AppData path
    data_path = os.path.join(app_data_path, 'data')
    if not os.path.exists(data_path):
        print("makedir")
        os.makedirs(data_path)
    
    DATA_DIRECTORY = data_path



def create_config_path():

    global DESKTOP_CONFIG_DIRECTORY
    global DEFAULT_DESKTOP
    global JSON
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

    if os.path.exists(DESKTOP_CONFIG_DIRECTORY) and os.path.getsize(DESKTOP_CONFIG_DIRECTORY) > 0:
        with open(DESKTOP_CONFIG_DIRECTORY, "r") as f:
            JSON = json.load(f)
    else:
        print(f"Creating default settings at: {DESKTOP_CONFIG_DIRECTORY}")
        JSON = DEFAULT_DESKTOP
        with open(DESKTOP_CONFIG_DIRECTORY, "w") as f:
            json.dump(DEFAULT_DESKTOP, f, indent=4)







if __name__ == "__main__":


    ### code within these are temporary, since i am running this as a main file
    # would instead be setup like settings where i just call this file and pass it the DESKTOP_CONFIG_DIRECTORY
    


    ###
    create_config_path()
    create_data_path()
    app = QApplication(sys.argv)
    widget = Grid()
    widget.setMinimumSize(100, 100)  
    widget.resize(1920, 1000)
    widget.draw_labels()
    widget.show()
    sys.exit(app.exec())