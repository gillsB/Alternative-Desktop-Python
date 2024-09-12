from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QScrollArea, QSizePolicy, QWidget
from PySide6.QtCore import QTimer, Qt
import os
import json
import logging
import markdown

logger = logging.getLogger(__name__)


class PatchNotesPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patch Notes")
        self.resize(600, 500)
        
        self.layout = QVBoxLayout(self)
        
        self.notes = load_all_patch_notes()
        self.current_index = 0
        
        self.scroll_area = QScrollArea(self)
        self.scroll_content = QWidget()
        self.scroll_content_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)
        
        self.notes_text = QTextEdit(self.scroll_content)
        self.notes_text.setReadOnly(True)
        self.scroll_content_layout.addWidget(self.notes_text)
        
        self.layout.addWidget(self.scroll_area)
        
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.accept)
        self.layout.addWidget(self.close_button)
        
        self.load_initial_notes()
        self.center_on_screen()
        
        # Connect scroll event
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_scroll_position)
    
    def load_initial_notes(self):
        self.notes_text.clear()
        self.current_index = 0
        self.load_more_notes()
        QTimer.singleShot(0, self.ensure_top_scroll)
    
    def load_more_notes(self):
        if self.current_index >= len(self.notes):
            return
        
        for _ in range(2):
            if self.current_index >= len(self.notes):
                break
            patch = self.notes[self.current_index]
            html_content = markdown.markdown(patch['notes'])
            self.notes_text.append(f"<h3>Version {patch['version']} ({patch['date']})</h3>\n{html_content}\n<hr>\n")
            self.current_index += 1
    
    def check_scroll_position(self, value):
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum() - 50:  # Load more when near the bottom
            self.load_more_notes()
    
    def ensure_top_scroll(self):
        self.scroll_area.verticalScrollBar().setValue(0)
        self.notes_text.verticalScrollBar().setValue(0)
    
    def center_on_screen(self):
        screen_geometry = self.screen().geometry()
        dialog_geometry = self.geometry()
        x = (screen_geometry.width() - dialog_geometry.width()) // 2
        y = (screen_geometry.height() - dialog_geometry.height()) // 2
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.ensure_top_scroll)

def patch_notes_exist():
    return os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util', 'patch_notes', 'patch_notes.json'))

def load_all_patch_notes():
    patch_notes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util', 'patch_notes', 'patch_notes.json')
    
    try:
        with open(patch_notes_path, 'r') as f:
            patch_notes_metadata = json.load(f)
            
            notes = []
            for version, metadata in sorted(patch_notes_metadata.items(), key=lambda x: x[0], reverse=True):
                notes_file = metadata['notes_file']
                notes_file_path = os.path.join(os.path.dirname(patch_notes_path), notes_file)
                
                try:
                    with open(notes_file_path, 'r') as notes_f:
                        notes.append({
                            'version': version,
                            'date': metadata['date'],
                            'notes': notes_f.read()
                        })
                except FileNotFoundError:
                    logger.error(f"Patch notes file for version {version} not found: {notes_file_path}")
            
            return notes
    
    except FileNotFoundError:
        logger.error(f"patch_notes.json not found at {patch_notes_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Problem decoding patch_notes.json: {e}")
        return []