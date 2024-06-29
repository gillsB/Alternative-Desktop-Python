import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt
import keyboard

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set up the main window
        self.setWindowTitle("Hello World Window")
        self.setGeometry(100, 100, 400, 300)
        
        # Create a label with "Hello, World!"
        self.label = QLabel("Hello, World!", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)
        
        # Register a keyboard shortcut (keybind)
        keyboard.add_hotkey('ctrl+shift+h', self.show_hello_window)
        
    def show_hello_window(self):
        self.show()

def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()