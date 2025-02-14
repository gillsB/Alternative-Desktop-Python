from PySide6.QtWidgets import QToolButton, QLineEdit, QStyle, QSlider, QSpinBox, QHBoxLayout, QVBoxLayout, QWidget, QFrame, QLabel, QSpacerItem, QSizePolicy, QGraphicsItem, QGraphicsRectItem
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QPen
import os


class TempIcon(QGraphicsItem):
    def __init__(self, col, row, new_icon_path, icon_size):
        super().__init__()
        self.icon_size = icon_size

        if os.path.exists(new_icon_path):
            self.pixmap = QPixmap(new_icon_path)
        # Grid_menu already passes back "assets/images/unknown.png" reference, if for some reason this is invalid, display a blank pixmap
        else:
            self.pixmap = QPixmap(self.icon_size, self.icon_size)
            self.pixmap.fill(Qt.transparent)
    
    def boundingRect(self):
        return QRectF(0, 0, self.icon_size, self.icon_size)
    
    def paint(self, painter, option, widget=None):
        scaled_pixmap = self.pixmap.scaled(self.icon_size, self.icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x_offset = (self.icon_size - scaled_pixmap.width()) / 2
        y_offset = (self.icon_size - scaled_pixmap.height()) / 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

class ClearableLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a clear button using a system default icon
        self.clear_button = QToolButton(self)
        self.clear_button.setIcon(self.style().standardIcon(QStyle.SP_LineEditClearButton))  
        self.clear_button.setCursor(Qt.ArrowCursor)
        self.clear_button.setFocusPolicy(Qt.NoFocus)
        self.clear_button.setStyleSheet("""
                QToolButton {
                    border: none;
                    padding: 0px;
                    background: transparent;  
                }
            """)

        self.clear_button.hide()

        # Setting button within frame
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet(f"padding-right: {self.clear_button.sizeHint().width() + frameWidth + 1}px;")
        self.clear_button.setFixedSize(self.sizeHint().height() - 2, self.sizeHint().height() - 2)

        self.update_clear_button_position(frameWidth)
        self.clear_button.clicked.connect(self.clear)
        self.textChanged.connect(self.update_clear_button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.update_clear_button_position(frameWidth)

    def update_clear_button_position(self, frameWidth):
        height_diff = (self.height() - self.clear_button.height()) // 2
        margin_right = 5 
        self.clear_button.move(self.rect().right() - frameWidth - self.clear_button.sizeHint().width() - margin_right,
                            height_diff)

    def update_clear_button(self, text):
        # Show clear button if line edit has text
        self.clear_button.setVisible(bool(text))


class SliderWithInput(QWidget):
    valueChanged = Signal(int)

    def __init__(self, min, max, step, init_value):
        super().__init__()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min, max)
        self.slider.setSingleStep(step)

        self.text_input = QSpinBox()
        self.text_input.setRange(min, max)
        self.text_input.setFixedWidth(70)
        self.text_input.setAlignment(Qt.AlignLeft)

        self.slider.setValue(init_value)
        self.text_input.setValue(int(init_value))

        layout = QHBoxLayout()
        layout.addWidget(self.slider)
        layout.addWidget(self.text_input)
        self.setLayout(layout)

        # Connect signals
        self.slider.valueChanged.connect(self.update_text_input)
        self.text_input.textChanged.connect(self.update_slider_position)

        self.slider.valueChanged.connect(self.valueChanged.emit)

    def update_text_input(self, value):
        # Update text input when the slider value changes
        self.text_input.setValue(int(value))

    def update_slider_position(self):
        # Update slider when text input changes, ensuring it's an integer
        text = self.text_input.text()
        if text:
            self.slider.setValue(int(text))

    def get_value(self):
        return self.slider.value()



def create_separator(label_text):
    vbox = QVBoxLayout()

    # Add top padding with a spacer
    top_spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
    vbox.addItem(top_spacer)

    hbox = QHBoxLayout()

    # Label for the section title
    label = QLabel(label_text)
    label.setStyleSheet("font-weight: bold; padding-right: 6px;")

    # Horizontal line
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("color: grey;")

    hbox.addWidget(label)
    hbox.addWidget(line)
    hbox.setStretch(1, 1)  # Expands the line while keeping the label fixed

    vbox.addLayout(hbox)

    bottom_spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
    vbox.addItem(bottom_spacer)

    return vbox


class ShelfHoverItem(QGraphicsRectItem):
    def __init__(self, width, height):
        super().__init__(0, 0, 40, height)
        self.setBrush(Qt.transparent)  # Make the inside invisible/transparent.
        #self.setPen(QPen(Qt.transparent))  # Eventually this will be transparent.
        self.setAcceptHoverEvents(True)

    def hoverMoveEvent(self, event):
        print("Hovering over the right side!")
        super().hoverMoveEvent(event)

    def updatePosition(self, view_width, view_height):
        self.setRect(0, 0, self.rect().width(), view_height)
        self.setPos(view_width - 40, 0)


