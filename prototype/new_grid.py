from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QApplication
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics
import sys

# Global Padding Variables
TOP_PADDING = 20  # Padding from the top of the window
SIDE_PADDING = 20  # Padding from the left side of the window
VERTICAL_PADDING = 40  # Padding between icons

class DesktopGrid(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Desktop Grid Prototype')
        self.setMinimumSize(400, 400)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Disable scroll bars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Initialize 2D array for icon items
        self.desktop_icons = []

        self.populate_icons()

        # Example of calling a function for a DesktopIcon
        self.desktop_icons[3][1].set_color("black")

        # Set the scene rectangle to be aligned with the top-left corner with padding
        self.scene.setSceneRect(0, 0, self.width(), self.height())

    def populate_icons(self):
        icon_size = 64
        self.spacing = 10
        cols = 40
        rows = 10

        # Create a 2D array for icon items
        self.desktop_icons = [[None for _ in range(cols)] for _ in range(rows)]

        for x in range(rows):
            for y in range(cols):
                icon_item = DesktopIcon(x, y, icon_size)
                # setPos uses [column, row] equivalent so flip it. i.e. SIDEPADDING + y(column) = column position.
                icon_item.setPos(SIDE_PADDING + y * (icon_size + self.spacing), 
                    TOP_PADDING + x * (icon_size + self.spacing + VERTICAL_PADDING))
                self.desktop_icons[x][y] = icon_item
                self.scene.addItem(icon_item)

        # Initially update visibility based on the current window size
        self.update_icon_visibility()



    def update_icon_color(self, x, y, color):
        if 0 <= x < len(self.desktop_icons) and 0 <= y < len(self.desktop_icons[0]):
            icon_item = self.desktop_icons[x][y]
            if icon_item:
                icon_item.set_color(color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Adjust the scene rectangle on resize
        self.scene.setSceneRect(0, 0, self.width(), self.height())
        self.update_icon_visibility()

    def update_icon_visibility(self):
        # Get the size of the visible area of the window
        view_width = self.viewport().width()
        view_height = self.viewport().height()

        # Calculate max visible row and column based on icon size + padding
        max_visible_columns = (view_width - SIDE_PADDING) // (self.desktop_icons[0][0].icon_size + self.spacing)
        max_visible_rows = (view_height - TOP_PADDING) // (self.desktop_icons[0][0].icon_size + VERTICAL_PADDING + self.spacing)
        print(f"max columns: {max_visible_columns}, max rows: {max_visible_rows}")

        # Iterate only within visible rows and columns
        for x in range(len(self.desktop_icons)):
            for y in range(len(self.desktop_icons[x])):
                icon_item = self.desktop_icons[x][y]
                if x < max_visible_rows and y < max_visible_columns:
                    icon_item.setVisible(True)
                else:
                    icon_item.setVisible(False)

    def wheelEvent(self, event):
        # Override wheel event to prevent scrolling
        event.ignore()  # Ignore the event to prevent scrolling


class DesktopIcon(QGraphicsItem):
    def __init__(self, x, y, icon_size=64):
        super().__init__()
        self.icon_text = f"icon {x},{y}\nMulti-line example"
        self.icon_size = icon_size
        self.setAcceptHoverEvents(True)
        self.padding = 30
        self.font = QFont('Arial', 10)
        self.color = QColor(200, 200, 255)  # Default color

    def set_color(self, color):
        if isinstance(color, str):
            # If the color is a hex code without '#', add the '#' symbol
            if len(color) == 6 and not color.startswith('#'):
                color = '#' + color
            self.color = QColor(color)  # QColor will interpret the color name or hex code
        elif isinstance(color, QColor):
            self.color = color
        else:
            raise ValueError("Color must be a valid color name, hex string, or QColor object.")

        self.update() 

    def boundingRect(self) -> QRectF:
        text_height = self.calculate_text_height(self.icon_text)
        return QRectF(0, 0, self.icon_size, self.icon_size + text_height + self.padding)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setBrush(self.color)
        painter.drawRect(0, 0, self.icon_size, self.icon_size)

        painter.setFont(self.font)

        lines = self.get_multiline_text(self.font, self.icon_text)
        for i, line in enumerate(lines):
            painter.drawText(0, self.icon_size + self.padding / 2 + i * 15, line)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)

    def mouseDoubleClickEvent(self, event):
        self.set_color("red")
        print(f"Opening {self.icon_text}...")

    def calculate_text_height(self, text):
        font_metrics = QFontMetrics(self.font)
        lines = self.get_multiline_text(font_metrics, text)
        return len(lines) * 15  

    def get_multiline_text(self, font, text):
        font_metrics = QFontMetrics(font)
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            # Measure the width of the current line with the new word
            new_line = current_line + " " + word if current_line else word
            if font_metrics.boundingRect(new_line).width() <= self.icon_size:
                current_line = new_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DesktopGrid()
    window.show()
    sys.exit(app.exec())
