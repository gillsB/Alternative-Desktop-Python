from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve, QPointF
from PySide6.QtWidgets import (QGraphicsWidget, QGraphicsProxyWidget, QPushButton, QGraphicsRectItem,
                              QVBoxLayout, QWidget, QLabel)
from PySide6.QtGui import QIcon


class Shelf(QGraphicsWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_open = False
        self._content_width = 250
        
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

        # Create content widget
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        
        # Add sample content
        shelf_label = QLabel("Shelf Content")
        shelf_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(shelf_label)
        
        sample_button = QPushButton("Sample Button")
        content_layout.addWidget(sample_button)
        content_layout.addStretch()
        sample_button.clicked.connect(self.sample_button_clicked)
        
        # Create a proxy for the content
        self.content_proxy = QGraphicsProxyWidget(self)
        self.content_proxy.setWidget(self.content_widget)
        self.content_proxy.setMinimumWidth(0)
        self.content_proxy.setMaximumWidth(0)
        
        # Position content to the right of button at the same height
        button_width = self.button_proxy.size().width()
        self.content_proxy.setPos(button_width, 0)  # Same vertical position as button

        # Connect the button to toggle action
        self.toggle_button.clicked.connect(self.toggle_shelf)

        # Set up animation for content
        self.content_animation = QPropertyAnimation(self, b"content_width")
        self.content_animation.setDuration(300)
        self.content_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.content_animation.finished.connect(self.update_content_position)
        
        # Set up animation for shelf position
        self.shelf_animation = QPropertyAnimation(self, b"pos")
        self.shelf_animation.setDuration(300)
        self.shelf_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.setAcceptHoverEvents(True)
        self.center_y = 0
        self.setZValue(1)

    def get_content_width(self):
        return self.content_proxy.size().width()

    def set_content_width(self, width):
        self.content_proxy.setMinimumWidth(width)
        self.content_proxy.setMaximumWidth(width)
        self.update_content_position()

    content_width = Property(int, get_content_width, set_content_width)
    
    def update_content_position(self):
        # Position content to the right of button at the same vertical position
        button_width = self.button_proxy.size().width()
        self.content_proxy.setPos(button_width, 0)
    
    def position_at_right(self, view_width, view_height):
        button_width = self.button_proxy.size().width()
        content_width = self.content_proxy.size().width()
        
        self.center_y = (view_height - self.button_proxy.size().height()) / 2

        if not self.is_open:
            self.setPos(view_width - button_width, self.center_y)
        else:
            self.setPos(view_width - button_width - content_width, self.center_y)

        self.update_content_position()

    def show_button(self, show):
        if show or self.is_open:
            self.show()
        else:
            self.hide()

    def close_shelf(self):
        if self.is_open:
            self.hide()
            self.toggle_button.setIcon(QIcon.fromTheme("go-previous"))
            self.is_open = False

    def toggle_shelf(self):
        # Get the view width from parent scene and view
        scene = self.scene()
        if scene and len(scene.views()) > 0:
            view = scene.views()[0]
            view_width = view.viewport().width()
            if not self.is_open:
                # Opening shelf
                current_pos_x = self.pos().x()
                target_pos_x = view_width - self._content_width - self.button_proxy.size().width()

                self.shelf_animation.setStartValue(QPointF(current_pos_x, self.center_y))
                self.shelf_animation.setEndValue(QPointF(target_pos_x, self.center_y))

                self.content_animation.setStartValue(0)
                self.content_animation.setEndValue(self._content_width)

                self.toggle_button.setIcon(QIcon.fromTheme("go-next"))
            else:
                # Closing shelf
                current_pos_x = self.pos().x()
                button_width = self.button_proxy.size().width()
                target_pos_x = view_width - button_width

                self.shelf_animation.setStartValue(QPointF(current_pos_x, self.center_y))
                self.shelf_animation.setEndValue(QPointF(target_pos_x, self.center_y))

                self.content_animation.setStartValue(self.content_proxy.size().width())
                self.content_animation.setEndValue(0)

                self.toggle_button.setIcon(QIcon.fromTheme("go-previous"))

                # Connect the finished signal of shelf animation to hide the button after close
                self.shelf_animation.finished.connect(self.hide_button_after_close)

            # Start both animations
            self.shelf_animation.start()
            self.content_animation.start()

            self.is_open = not self.is_open

    def sample_button_clicked(self):
        print("sample button clicked")

    def hide_button_after_close(self):
        self.show_button(self.is_open)

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