from PySide6.QtWidgets import QToolButton, QLineEdit, QStyle
from PySide6.QtCore import Qt


class ClearableLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a clear button using a system default icon
        self.clear_button = QToolButton(self)
        self.clear_button.setIcon(self.style().standardIcon(QStyle.SP_LineEditClearButton))  
        self.clear_button.setCursor(Qt.ArrowCursor)
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

