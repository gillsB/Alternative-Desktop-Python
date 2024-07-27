import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QGridLayout, QVBoxLayout, QDialog, QSizePolicy, QMessageBox, QMenu
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtCore import Qt
import os
import json
import subprocess
import shlex
from desktop_grid_menu import Menu





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
    "row": 0,
    "column": 0,
    "name": "",
    "icon_path": "",
    "executable_path": "",
    "command_args": "",
    "website_link": "",
    "left_click": 0
}

#left_click options:
#0 First come first serve (down the list) i.e. executable_path, then if none -> website_link
#1 Website link first
#2 Maybe a popup to select?




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
        num_rows = max(1, window_height // (LABEL_SIZE + LABEL_VERT_PAD)) 

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
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        
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
        if os.path.isfile(icon_path) == False:
            if entry_exists(self.desktop_icon.row, self.desktop_icon.col) and is_default(self.desktop_icon.row, self.desktop_icon.col) == False:
                icon_path = "assets/images/unknown.png"
        pixmap = QPixmap(icon_path).scaled(LABEL_SIZE-2, LABEL_SIZE-2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.desktop_icon.icon_path == "assets/images/add.png":
            menu = Menu(parent=self)
            menu.exec()
        #if icon has an executable_path already (icon exists with path)
        elif event.button() == Qt.LeftButton and self.desktop_icon.executable_path != "":
            self.run_program()

    def showContextMenu(self, pos):
            context_menu = QMenu(self)

            self.edit_mode_icon()
            
            print(f"Row: {self.desktop_icon.row}, Column: {self.desktop_icon.col}, Name: {self.desktop_icon.name}, Icon_path: {self.desktop_icon.icon_path}, Exec Path: {self.desktop_icon.executable_path}, Command args: {self.desktop_icon.command_args}")
            
            edit_action = QAction('Edit Icon', self)
            edit_action.triggered.connect(self.edit_triggered)
            context_menu.addAction(edit_action)

            context_menu.addSeparator()

            icon_path_action = QAction('Open Icon Location', self)
            icon_path_action.triggered.connect(lambda: self.path_triggered(self.desktop_icon.icon_path))
            context_menu.addAction(icon_path_action)

            exec_path_action = QAction('Open Executable Location', self)
            exec_path_action.triggered.connect(lambda: self.path_triggered(self.desktop_icon.executable_path))
            context_menu.addAction(exec_path_action)
            
            context_menu.addSeparator()

            delte_action = QAction('Delete Icon', self)
            delte_action.triggered.connect(self.delete_triggered)
            context_menu.addAction(delte_action)
            
            context_menu.aboutToHide.connect(self.context_menu_closed)
            context_menu.exec(self.mapToGlobal(pos))
    
    def context_menu_closed(self):
        print("Context menu closed without selecting any action")
        self.normal_mode_icon()

    def edit_triggered(self):

            menu = Menu(parent=self)
            menu.exec()
    def path_triggered(self, path):
        if not os.path.exists(path):
            QMessageBox.warning(self, "Path does not exist",
                                    f"File at location: {path}\n does not exist, please check the location.",
                                    QMessageBox.Ok)
            return
        # Open the folder and select the file in Explorer
        subprocess.run(['explorer', '/select,', os.path.normpath(path)])
    
    def delete_triggered(self):
        ret = QMessageBox.warning(self, "Delete Icon",
                                    f"Are you sure you wish to delete \"{self.desktop_icon.name}\" at: [{self.desktop_icon.row},{self.desktop_icon.col}]?",
                                    QMessageBox.Ok| QMessageBox.Cancel)
        if ret == QMessageBox.Ok:   
            self.set_entry_to_default(self.desktop_icon.row, self.desktop_icon.col)
    

    #mousover icon
    def enterEvent(self, event):
        if self.desktop_icon.icon_path == "assets/images/blank.png":
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
    def set_command_args(self, command_args):
        self.desktop_icon.command_args = command_args


    # returns base DATA_DIRECTORY/[row, col]
    def get_data_icon_dir(self):
        data_path = os.path.join(DATA_DIRECTORY, f'[{self.desktop_icon.row}, {self.desktop_icon.col}]')
        #make file if no file (new)
        if not os.path.exists(data_path):
            print("makedir")
            os.makedirs(data_path)
        print(f"get_data_icon_path: {data_path}")
        return data_path
        


    #
    #
    # This is required to run in order for any client sided (non restart) edit to appear/work as normal
    #
    #
    def render_icon(self):

        if entry_exists(self.desktop_icon.row, self.desktop_icon.col):
            for item in JSON:
                if item['row'] == self.desktop_icon.row and item['column'] == self.desktop_icon.col:
                    self.set_name(item['name'])
                    self.set_icon_path(item['icon_path'])
                    self.set_executable_path(item['executable_path'])
                    self.set_command_args(item['command_args'])
                    break
        else:
            self.set_name("")
            self.set_icon_path("")
            self.set_executable_path("")
            self.set_command_args("")
            

    def load_config(self):
        return load_desktop_config()
    
    #set icon into edit mode: red selected border, if icon is originally blank, set it to "add2.png"
    def edit_mode_icon(self):
        if self.desktop_icon.icon_path == "" or entry_exists(self.desktop_icon.row, self.desktop_icon.col) == False:
            self.set_icon_path("assets/images/add2.png")
        self.selected_border(10)
    
    #return icon into normal mode: (remove red select border) revert back to blank if icon was "add2.png"
    def normal_mode_icon(self):
        self.default_border()
        #revert add
        if self.get_icon_path() == "assets/images/add2.png":
            self.set_icon_path("assets/images/blank.png")

        self.render_icon()

    
        

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
                try:
                    
                    #when shell=True exceptions like FileNotFoundError are no longer raised but put into stderr
                    process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    stdout, stderr = process.communicate(timeout=0.5)


                    text = stderr.decode('utf-8')
                    if "is not recognized as an internal or external command" in text:
                        QMessageBox.warning(self, "Error Opening File",
                                    "The file could not be opened.\nPlease check that the file exists at the specified location or ensure there is a default application set to open this file type.",
                                    QMessageBox.Ok)
                    
                #kill the connection between this process and the subprocess we just launched.
                #this will not kill the subprocess but just set it free from the connection
                except Exception as e:
                    print("killing connection to new subprocess")
                    process.kill()
                    
        except Exception as e:
            print(f"An error occurred: {e}")
        

    
    def get_dir(self):
        return DESKTOP_CONFIG_DIRECTORY
    def get_json(self):
        return JSON

    #updates the entry at row,col to DEFAULT_DESKTOP fields (except row/column)
    def set_entry_to_default(self, row, col):
        config = load_desktop_config()
        for entry in config:
            if entry.get('row') == row and entry.get('column') == col:
                for key in DEFAULT_DESKTOP:
                    if key not in ['row', 'column']:
                        entry[key] = DEFAULT_DESKTOP[key]
                break
        self.save_desktop_config(config)




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

def is_default(row, col):
    config = load_desktop_config()
    for item in config:
        if item['row'] == row and item['column'] == col:
            if (item.get('name', "") == DEFAULT_DESKTOP['name'] and
                item.get('icon_path', "") == DEFAULT_DESKTOP['icon_path'] and
                item.get('executable_path', "") == DEFAULT_DESKTOP['executable_path'] and
                item.get('command_args', "") == DEFAULT_DESKTOP['command_args'] and
                item.get('website_link', "") == DEFAULT_DESKTOP['website_link'] and
                item.get('left_click', 1) == DEFAULT_DESKTOP['left_click']):
                return True
    return False



def entry_exists(row, col):
    config = load_desktop_config()
    for item in config:
        if item['row'] == row and item['column'] == col:
            return True
    return False



#this would be passed by AlternativeDesktop.py or one of the main program files (settings.py etc.)
def create_data_path():

    global DATA_DIRECTORY
    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create app_data directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    # Append /config/data.json to the AppData path
    data_path = os.path.join(app_data_path, 'data')
    if not os.path.exists(data_path):
        print("makedir")
        os.makedirs(data_path)
    
    DATA_DIRECTORY = data_path


#this would also be done by AlternativeDesktop.py or main program files (possibly settings.py)
def create_config_path():

    global DESKTOP_CONFIG_DIRECTORY
    global DEFAULT_DESKTOP
    global JSON
    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create app_data directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)

    # Append /config/desktop.json to the AppData path
    config_path = os.path.join(app_data_path, 'config', 'desktop.json')
    #create the /config/desktop.json if they do not exist already.
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
        JSON = [DEFAULT_DESKTOP]
        with open(DESKTOP_CONFIG_DIRECTORY, "w") as f:
            json.dump([DEFAULT_DESKTOP], f, indent=4)







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