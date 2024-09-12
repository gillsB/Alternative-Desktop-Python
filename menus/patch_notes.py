from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import QTimer
import os
import json
import logging

logger = logging.getLogger(__name__)
PATCH_NOTES = None

class PatchNotesPopup(QDialog):
    def __init__(self, current_version, parent=None):
        super().__init__(parent)
        global PATCH_NOTES
        self.setWindowTitle(f"Update to Version {current_version}")
        self.setGeometry(300, 200, 400, 300)

        layout = QVBoxLayout(self)

        # Back up load in case it is not called before init
        if PATCH_NOTES == None:
            PATCH_NOTES = load_patch_notes()

        if not PATCH_NOTES:
            logger.error(f"Error getting patch notes, Closing window.")
            QTimer.singleShot(0, self.reject)  # Schedule the dialog to close
            return

        # Show current patch notes
        self.notes_label = QLabel(f"Patch Notes for Version {current_version}:", self)
        self.notes_text = QTextEdit(self)
        if current_version in PATCH_NOTES:
            self.notes_text.setText(PATCH_NOTES[current_version]["notes"])
        else:
            self.notes_text.setText("No patch notes available for this version.")
        self.notes_text.setReadOnly(True)

        layout.addWidget(self.notes_label)
        layout.addWidget(self.notes_text)

        # Button to view previous patch notes
        self.previous_button = QPushButton("View Previous Patch Notes", self)
        self.previous_button.clicked.connect(lambda: self.show_previous_notes(PATCH_NOTES))
        layout.addWidget(self.previous_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)



    def show_previous_notes(self, patch_notes):
        previous_notes = "\n\n".join([f"Version {ver} ({patch['date']}):\n{patch['notes']}"
                                      for ver, patch in patch_notes.items()])
        self.notes_text.setText(previous_notes)


def load_patch_notes():
    global PATCH_NOTES
    patch_notes_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util', 'patch_notes.json')
    logger.info(f"Looking for patch_notes.json at {patch_notes_file}")
    try:
        with open(patch_notes_file, 'r') as f:
            PATCH_NOTES = json.load(f)
            return PATCH_NOTES
    except FileNotFoundError:
        logger.error(f"patch_notes.json not found at {patch_notes_file}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Problem decoding .json file {e}")
        return {}