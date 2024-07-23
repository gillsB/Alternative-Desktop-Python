from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
import sys

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radio_button = None

    def mousePressEvent(self, event):
        if self.radio_button:
            self.radio_button.setChecked(True)
            self.radio_button.clicked.emit()

class IconSelectionDialog(QDialog):
    def __init__(self, icon1_path, icon2_path):
        super().__init__()
        self.setWindowTitle("Select an Icon")
        self.selected_icon = icon1_path  # Default to the first icon
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Prompt label
        prompt_label = QLabel("Multiple icons detected. Please select one to use:")
        main_layout.addWidget(prompt_label)
        
        # Icons layout
        icons_layout = QHBoxLayout()
        
        # Button group for radio buttons
        self.button_group = QButtonGroup(self)

        print(f"ICON1 PATH = {icon1_path}")
        print(f"ICON2 PATH = {icon2_path}")
        
        # Icon 1
        icon1_layout = QVBoxLayout()
        icon1_pixmap = QPixmap(icon1_path)
        icon1_label = ClickableLabel()
        icon1_label.setPixmap(icon1_pixmap)
        icon1_radio = QRadioButton("Option 1")
        icon1_radio.setChecked(True)
        icon1_radio.clicked.connect(lambda: self.select_icon(icon1_path))
        icon1_label.radio_button = icon1_radio
        self.button_group.addButton(icon1_radio)
        icon1_layout.addWidget(icon1_label)
        icon1_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        icon1_layout.addWidget(icon1_radio, alignment=Qt.AlignHCenter)
        icons_layout.addLayout(icon1_layout)
        
        # Icon 2
        icon2_layout = QVBoxLayout()
        icon2_pixmap = QPixmap(icon2_path)
        icon2_label = ClickableLabel()
        icon2_label.setPixmap(icon2_pixmap)
        icon2_radio = QRadioButton("Option 2")
        icon2_radio.clicked.connect(lambda: self.select_icon(icon2_path))
        icon2_label.radio_button = icon2_radio
        self.button_group.addButton(icon2_radio)
        icon2_layout.addWidget(icon2_label)
        icon2_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        icon2_layout.addWidget(icon2_radio, alignment=Qt.AlignHCenter)
        icons_layout.addLayout(icon2_layout)
        
        main_layout.addLayout(icons_layout)
        
        # Add padding between the icons layout and the confirm button
        main_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Confirm button
        confirm_button = QPushButton("Confirm Selection")
        confirm_button.clicked.connect(self.accept)
        main_layout.addWidget(confirm_button)
        
        self.setLayout(main_layout)
    
    def select_icon(self, icon_path):
        self.selected_icon = icon_path

def select_icon_from_paths(icon1_path, icon2_path):
    dialog = IconSelectionDialog(icon1_path, icon2_path)
    if dialog.exec() == QDialog.Accepted:
        return dialog.selected_icon
    return None