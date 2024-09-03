from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radio_button = None

    def mousePressEvent(self, event):
        if self.radio_button:
            self.radio_button.setChecked(True)
            self.radio_button.clicked.emit()

class IconSelectionDialog(QDialog):
    def __init__(self, icon_paths):
        super().__init__()
        self.setWindowTitle("Select an Icon")
        self.selected_icon = None 
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Prompt label
        prompt_label = QLabel("Multiple icons detected. Please select one to use:")
        main_layout.addWidget(prompt_label)
        
        # Icons layout
        icons_layout = QHBoxLayout()
        
        # Button group for radio buttons
        self.button_group = QButtonGroup(self)
        
        # Create labels and radio buttons for each icon path
        for index, icon_path in enumerate(icon_paths):
            if icon_path:
                icon_layout = QVBoxLayout()
                icon_pixmap = QPixmap(icon_path)
                icon_label = ClickableLabel()
                icon_label.setPixmap(icon_pixmap)
                icon_radio = QRadioButton(f"Option {index + 1}")
                
                # Set default selected icon
                if index == 0:
                    icon_radio.setChecked(True)
                    self.selected_icon = icon_path
                
                icon_radio.clicked.connect(lambda _, path=icon_path: self.select_icon(path))
                icon_label.radio_button = icon_radio
                self.button_group.addButton(icon_radio)
                icon_layout.addWidget(icon_label)
                icon_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
                icon_layout.addWidget(icon_radio, alignment=Qt.AlignHCenter)
                icons_layout.addLayout(icon_layout)
        
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

def select_icon_from_paths(*icon_paths):
    dialog = IconSelectionDialog([path for path in icon_paths if path])
    if dialog.exec() == QDialog.Accepted:
        return dialog.selected_icon
    return None

