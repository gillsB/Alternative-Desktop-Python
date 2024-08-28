from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel
import sys
import logging

logger = logging.getLogger(__name__)

class RunMenuDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Select Run Option")
        self.resize(300, 150)

        layout = QVBoxLayout()

        self.run_executable_button = QPushButton("Run Executable")
        self.open_website_link_button = QPushButton("Open Website Link")

        self.run_executable_button.clicked.connect(self.accept_run_executable)
        self.open_website_link_button.clicked.connect(self.accept_open_website_link)

        layout.addWidget(self.run_executable_button)
        layout.addWidget(self.open_website_link_button)

        self.setLayout(layout)
        self.result = None

    def accept_run_executable(self):
        self.result = 'run_executable'
        logger.info("Selected run executable")
        self.accept()

    def accept_open_website_link(self):
        self.result = 'open_website_link'
        logger.info("Selected open website link")
        self.accept()

    def get_result(self):
        return self.result