import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QGridLayout, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

MAX_LABELS = 4900
MAX_ROWS = 40
MAX_COLS = 40


class Grid(QWidget):
    def __init__(self):
        super().__init__()

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.setLayout(self.grid_layout)

        self.labels = []
        self.label_size = 50
        

        for i in range(MAX_LABELS):
            row = i // MAX_ROWS
            col = i % MAX_COLS
            icon_path = ""
            info = f"Item {i}"
            desktop_icon = DesktopIcon(row, col, icon_path, info)
            label = ClickableLabel(desktop_icon)
            self.labels.append(label)
            self.grid_layout.addWidget(label, row, col)

        
        #for i in range(MAX_LABELS):
        #    print(self.labels[i].get_coord())

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
            print(f"Row: {self.desktop_icon.row}, Column: {self.desktop_icon.col}, Info: {self.desktop_icon.info}")
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
    def __init__(self, row, col, icon_path, info):
        self.row = row
        self.col = col
        self.icon_path = icon_path
        self.info = info



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Grid()
    widget.setMinimumSize(100, 100)  # Set a minimum size to ensure window can be small enough to hide labels
    widget.resize(1920, 1000)
    widget.draw_labels()
    widget.show()
    sys.exit(app.exec())