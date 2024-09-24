from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QLabel, QApplication, QGraphicsRectItem
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QPainter, QColor
import sys

class DesktopIcon(QGraphicsItem):
    def __init__(self, icon_text, icon_size=64):
        super().__init__()
        self.icon_text = icon_text
        self.icon_size = icon_size
        self.setAcceptHoverEvents(True)
        
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.icon_size, self.icon_size + 20) 

    def paint(self, painter: QPainter, option, widget=None):
        
        painter.setBrush(QColor(200, 200, 255))  # Light blue background
        painter.drawRect(0, 0, self.icon_size, self.icon_size)

        
        painter.drawText(0, self.icon_size + 15, self.icon_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)

    def mouseDoubleClickEvent(self, event):
        print(f"Opening {self.icon_text}...")
        

class DesktopGrid(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Desktop Grid Prototype')
        self.setMinimumSize(400, 400)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.populate_icons()

    def populate_icons(self):
        """ Add desktop icons to the scene """
        for i in range(5):  
            icon_item = DesktopIcon(f"Icon {i + 1}")
            icon_item.setPos(i * (icon_item.icon_size + 10), 10)  
            self.scene.addItem(icon_item)

    def resizeEvent(self, event):
        """ Adjust the view when the window is resized """
        super().resizeEvent(event)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DesktopGrid()
    window.show()
    sys.exit(app.exec())
