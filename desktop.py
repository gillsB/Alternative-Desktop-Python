from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout, QLabel
from PyQt5.QtGui import QIcon
import sys
from pynput import keyboard


class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Overlay Desktop")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("Overlay Desktop", self)
        self.label.setStyleSheet("font-size: 20px;")

        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.close)
        layout.addWidget(self.label)
        layout.addWidget(self.closeButton)

    def hotkey(self):
        def on_activate():
            if not self.isMinimized:
                self.showMinimized()
                self.isMinimized = True
            else:
                self.showNormal()
                self.isMinimized = False

        def for_canonical(f):
            return lambda k: f(l.canonical(k))

        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<alt>+d'),
            on_activate
        )
        l = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)
        )
        l.start()




def main():
    app = QApplication(sys.argv)
    overlay = OverlayWidget()
    overlay.show()
    overlay.hotkey()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()