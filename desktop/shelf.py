from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QGraphicsWidget, QGraphicsProxyWidget, QPushButton, QGraphicsRectItem,
                              QVBoxLayout, QWidget)
from PySide6.QtGui import QIcon


class Shelf(QGraphicsWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_open = False
        
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
        
        self.setAcceptHoverEvents(True)

    
    def position_at_right(self, view_width, view_height):
        button_width = self.button_proxy.size().width()

        center_y = (view_height - self.button_proxy.size().height()) / 2

        self.button_proxy.setPos(0, 0)
        self.setPos(view_width - button_width, center_y)

    def show_button(self, show):
        if show or self.is_open:
            self.show()
        else:
            self.hide()

    def close_shelf(self):
        self.is_open = False
        self.toggle_button.setIcon(QIcon.fromTheme("go-previous"))
        self.hide()
    
    def toggle_shelf(self):
        # Open the shelf
        if not self.is_open:
            self.toggle_button.setIcon(QIcon.fromTheme("go-next"))
        # Close the shelf
        else:
            self.toggle_button.setIcon(QIcon.fromTheme("go-previous"))
        self.is_open = not self.is_open


class ShelfHoverItem(QGraphicsRectItem):
    def __init__(self, width, height, shelf: Shelf, parent=None):
        super().__init__(0, 0, 40, height)
        self.shelf = shelf 
        self.setBrush(Qt.transparent)  # Make the inside invisible/transparent
        #self.setPen(QPen(Qt.transparent))  # Eventually this will be transparent.
        self.setAcceptHoverEvents(True)
        self.is_hovered = False

    def hoverMoveEvent(self, event):
        item_area = self.boundingRect()
        button_area = self.shelf.button_proxy.boundingRect()
        if item_area.contains(event.pos()) or button_area.contains(event.pos()):
            if not self.is_hovered:
                self.is_hovered = True
                self.shelf.show_button(True)
        else:
            if self.is_hovered:
                self.is_hovered = False
                self.shelf.show_button(False)
        super().hoverMoveEvent(event)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.shelf.show_button(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Check if the mouse is still within the hover or button area before hiding the button
        item_area = self.boundingRect()
        button_area = self.shelf.button_proxy.boundingRect()
        if not item_area.contains(event.pos()) and not button_area.contains(event.pos()):
            self.is_hovered = False
            self.shelf.show_button(False)
        super().hoverLeaveEvent(event)

    def updatePosition(self, view_width, view_height):
        self.setRect(0, 0, self.rect().width(), view_height)
        self.setPos(view_width - 40, 0)