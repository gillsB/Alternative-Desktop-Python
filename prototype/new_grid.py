from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QApplication
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics
import sys

VERTICAL_PADDING = 40

class DesktopIcon(QGraphicsItem):
    def __init__(self, x, y, icon_size=64):
        super().__init__()
        self.icon_text = f"icon {x},{y}\nMulti-line example"
        self.icon_size = icon_size
        self.setAcceptHoverEvents(True)
        self.padding = 30
        self.font = QFont('Arial', 10)

    def boundingRect(self) -> QRectF:
        text_height = self.calculate_text_height(self.icon_text)
        return QRectF(0, 0, self.icon_size, self.icon_size + text_height + self.padding)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setBrush(QColor(200, 200, 255))  # Light blue background
        painter.drawRect(0, 0, self.icon_size, self.icon_size)

        painter.setFont(self.font)

        lines = self.get_multiline_text(self.font, self.icon_text)
        for i, line in enumerate(lines):
            painter.drawText(0, self.icon_size + self.padding / 2 + i * 15, line)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)

    def mouseDoubleClickEvent(self, event):
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

class DesktopGrid(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Desktop Grid Prototype')
        self.setMinimumSize(400, 400)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.populate_icons()

    def populate_icons(self):
        icon_size = 64
        spacing = 10
        cols = 5 

        for y in range(3): 
            for x in range(cols):
                icon_item = DesktopIcon(x, y, icon_size)
                icon_item.setPos(x * (icon_size + spacing), y * (icon_size + spacing + VERTICAL_PADDING)) 
                self.scene.addItem(icon_item)

    def resizeEvent(self, event):
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DesktopGrid()
    window.show()
    sys.exit(app.exec())
