from PySide6.QtWidgets import (QGraphicsWidget, QGraphicsProxyWidget, QPushButton,
                              QVBoxLayout, QWidget)
from PySide6.QtGui import QIcon


class Shelf(QGraphicsWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create the toggle button
        button_widget = QWidget()
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(QIcon.fromTheme("go-previous"))
        self.toggle_button.setFixedSize(30, 80)
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.toggle_button)
        
        # Create a proxy for the button
        self.button_proxy = QGraphicsProxyWidget(self)
        self.button_proxy.setWidget(button_widget)

        self.toggle_button.clicked.connect(self.toggle_shelf)
    
    def position_at_right(self, view_width, view_height):
        button_width = self.button_proxy.size().width()

        center_y = (view_height - self.button_proxy.size().height()) / 2

        self.button_proxy.setPos(0, 0)
        self.setPos(view_width - button_width, center_y)


    
    def toggle_shelf(self):
        print("Toggle shelf called")

