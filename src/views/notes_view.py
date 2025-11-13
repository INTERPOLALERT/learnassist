"""
Notes View - Phase 4 Sprint 1
Advanced note-taking with rich text editor, tags, and organization
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QComboBox, QScrollArea, QFrame,
    QDialog, QDialogButtonBox, QMessageBox, QSplitter,
    QListWidget, QListWidgetItem, QCheckBox, QGridLayout,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

from features.notes.note_manager import NoteManager

logger = logging.getLogger(__name__)


class NotesView(QWidget):
    """Notes View - Note-taking with organization."""

    note_updated = pyqtSignal()

    def __init__(self, user_id: str, db_manager):
        """
        Initialize Notes View.

        Args:
            user_id: Current user ID
            db_manager: DatabaseManager instance
        """
        super().__init__()
        self.user_id = user_id
        self.db = db_manager
        self.note_manager = NoteManager(db_manager, user_id)

        # State
        self.current_note_id = None
        self.is_editing = False
        self.current_filters = {
            'folder': None,
            'subject_id': None,
            'tag': None,
            'search': None,
            'pinned_only': False,
            'favorites_only': False
        }

        # Auto-save timer
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.setInterval(5000)  # Auto-save every 5 seconds

        self._init_ui()
        self._load_notes()

        logger.info("Notes View initialized")

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Toolbar (search, filters, actions)
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Statistics bar
        self.stats_widget = self._create_statistics_widget()
        layout.addWidget(self.stats_widget)

        # Main content area (splitter with note list and editor)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # Left: Note list
        self.note_list_widget = self._create_note_list()
        splitter.addWidget(self.note_list_widget)

        # Right: Note editor
        self.editor_widget = self._create_editor()
        splitter.addWidget(self.editor_widget)

        # Set initial sizes (40% list, 60% editor)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter, 1)

    def _create_header(self) -> QWidget:
        """Create header with title and main actions."""
        header = QFrame()
        header.setStyleSheet("background: #2c3e50; border-radius: 8px; padding: 15px;")

        layout = QHBoxLayout(header)

        # Title
        title = QLabel("📝 Notes")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # New Note button
        new_btn = QPushButton("+ New Note")
        new_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        new_btn.clicked.connect(self._create_note)
        layout.addWidget(new_btn)

        return header

    def _create_toolbar(self) -> QWidget:
        """Create toolbar with search and filters."""
        toolbar = QFrame()
        toolbar.setStyleSheet("background: #ecf0f1; border-radius: 6px; padding: 10px;")

        layout = QHBoxLayout(toolbar)
        layout.setSpacing(10)

        # Search box
        search_label = QLabel("🔍")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background: white;
                min-width: 200px;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # Folder filter
        layout.addWidget(QLabel("Folder:"))
        self.folder_combo = QComboBox()
        self.folder_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background: white;
                min-width: 120px;
            }
        """)
        self.folder_combo.currentTextChanged.connect(self._on_folder_changed)
        layout.addWidget(self.folder_combo)

        # Subject filter
        layout.addWidget(QLabel("Subject:"))
        self.subject_combo = QComboBox()
        self.subject_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background: white;
                min-width: 120px;
            }
        """)
        self.subject_combo.currentTextChanged.connect(self._on_subject_changed)
        layout.addWidget(self.subject_combo)

        # Tag filter
        layout.addWidget(QLabel("Tag:"))
        self.tag_combo = QComboBox()
        self.tag_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background: white;
                min-width: 120px;
            }
        """)
        self.tag_combo.currentTextChanged.connect(self._on_tag_changed)
        layout.addWidget(self.tag_combo)

        # Pinned filter
        self.pinned_check = QCheckBox("📌 Pinned Only")
        self.pinned_check.stateChanged.connect(self._on_pinned_changed)
        layout.addWidget(self.pinned_check)

        # Favorites filter
        self.favorites_check = QCheckBox("⭐ Favorites Only")
        self.favorites_check.stateChanged.connect(self._on_favorites_changed)
        layout.addWidget(self.favorites_check)

        layout.addStretch()

        # Clear filters button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(clear_btn)

        return toolbar

    def _create_statistics_widget(self) -> QWidget:
        """Create statistics display."""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: #3498db;
                border-radius: 6px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
        """)

        layout = QHBoxLayout(stats_frame)

        self.total_label = QLabel("Total: 0")
        self.total_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.total_label)

        layout.addWidget(QLabel("|"))

        self.pinned_label = QLabel("Pinned: 0")
        layout.addWidget(self.pinned_label)

        layout.addWidget(QLabel("|"))

        self.favorites_label = QLabel("Favorites: 0")
        layout.addWidget(self.favorites_label)

        layout.addWidget(QLabel("|"))

        self.folders_label = QLabel("Folders: 0")
        layout.addWidget(self.folders_label)

        layout.addWidget(QLabel("|"))

        self.tags_label = QLabel("Tags: 0")
        layout.addWidget(self.tags_label)

        layout.addStretch()

        return stats_frame

    def _create_note_list(self) -> QWidget:
        """Create note list panel."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header
        header = QLabel("All Notes")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)

        # Scroll area for note cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: #ecf0f1;
            }
        """)

        # Container for note cards
        self.notes_container = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.setContentsMargins(10, 10, 10, 10)
        self.notes_layout.setSpacing(10)
        self.notes_layout.addStretch()

        scroll.setWidget(self.notes_container)
        layout.addWidget(scroll)

        return container

    def _create_editor(self) -> QWidget:
        """Create note editor panel."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Editor header (when note is loaded)
        self.editor_header = QFrame()
        self.editor_header.setStyleSheet("""
            QFrame {
                background: #ecf0f1;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        editor_header_layout = QHBoxLayout(self.editor_header)

        # Note title display
        self.note_title_label = QLabel("No note selected")
        self.note_title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        editor_header_layout.addWidget(self.note_title_label)

        editor_header_layout.addStretch()

        # Pin button
        self.pin_btn = QPushButton("📌 Pin")
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        self.pin_btn.clicked.connect(self._toggle_pin)
        self.pin_btn.setVisible(False)
        editor_header_layout.addWidget(self.pin_btn)

        # Favorite button
        self.favorite_btn = QPushButton("⭐ Favorite")
        self.favorite_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #e67e22;
            }
        """)
        self.favorite_btn.clicked.connect(self._toggle_favorite)
        self.favorite_btn.setVisible(False)
        editor_header_layout.addWidget(self.favorite_btn)

        # Edit button
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        self.edit_btn.clicked.connect(self._start_editing)
        self.edit_btn.setVisible(False)
        editor_header_layout.addWidget(self.edit_btn)

        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        self.delete_btn.clicked.connect(self._delete_note)
        self.delete_btn.setVisible(False)
        editor_header_layout.addWidget(self.delete_btn)

        layout.addWidget(self.editor_header)

        # Title editor (shown when editing)
        self.title_editor = QLineEdit()
        self.title_editor.setPlaceholderText("Note title...")
        self.title_editor.setStyleSheet("""
            QLineEdit {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 10px;
                font-size: 18px;
                font-weight: bold;
                background: white;
            }
        """)
        self.title_editor.setVisible(False)
        layout.addWidget(self.title_editor)

        # Content editor
        self.content_editor = QTextEdit()
        self.content_editor.setPlaceholderText("Select a note or create a new one...")
        self.content_editor.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                font-size: 14px;
                background: white;
            }
        """)
        self.content_editor.setReadOnly(True)
        self.content_editor.textChanged.connect(self._on_content_changed)
        layout.addWidget(self.content_editor)

        # Editor footer (metadata and save buttons)
        self.editor_footer = QFrame()
        self.editor_footer.setStyleSheet("""
            QFrame {
                background: #ecf0f1;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        editor_footer_layout = QHBoxLayout(self.editor_footer)

        # Metadata display
        self.metadata_label = QLabel("")
        self.metadata_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        editor_footer_layout.addWidget(self.metadata_label)

        editor_footer_layout.addStretch()

        # Save button (shown when editing)
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        self.save_btn.clicked.connect(self._save_note)
        self.save_btn.setVisible(False)
        editor_footer_layout.addWidget(self.save_btn)

        # Cancel button (shown when editing)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        self.cancel_btn.clicked.connect(self._cancel_editing)
        self.cancel_btn.setVisible(False)
        editor_footer_layout.addWidget(self.cancel_btn)

        self.editor_footer.setVisible(False)
        layout.addWidget(self.editor_footer)

        return container

    def _load_notes(self):
        """Load and display notes based on current filters."""
        try:
            # Get notes
            notes = self.note_manager.get_notes(
                folder=self.current_filters['folder'],
                subject_id=self.current_filters['subject_id'],
                tag=self.current_filters['tag'],
                search_term=self.current_filters['search'],
                pinned_only=self.current_filters['pinned_only'],
                favorites_only=self.current_filters['favorites_only']
            )

            # Clear existing note cards
            while self.notes_layout.count() > 1:  # Keep stretch at end
                item = self.notes_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Add note cards
            for note in notes:
                card = self._create_note_card(note)
                self.notes_layout.insertWidget(self.notes_layout.count() - 1, card)

            # Update filters
            self._update_filter_options()

            # Update statistics
            self._update_statistics()

            logger.debug(f"Loaded {len(notes)} notes")

        except Exception as e:
            logger.error(f"Failed to load notes: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load notes: {e}")

    def _create_note_card(self, note: Dict[str, Any]) -> QWidget:
        """Create a note card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-left: 4px solid {note.get('subject_color', '#3498db')};
                border-radius: 6px;
                padding: 10px;
            }}
            QFrame:hover {{
                background: #f8f9fa;
                border-left: 4px solid {note.get('subject_color', '#3498db')};
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        # Header row (title + badges)
        header_layout = QHBoxLayout()

        # Pin and favorite indicators
        if note.get('is_pinned'):
            pin_label = QLabel("📌")
            header_layout.addWidget(pin_label)

        if note.get('is_favorite'):
            fav_label = QLabel("⭐")
            header_layout.addWidget(fav_label)

        # Title
        title = QLabel(note['title'])
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        title.setWordWrap(True)
        header_layout.addWidget(title, 1)

        layout.addLayout(header_layout)

        # Content preview (first 100 chars)
        if note.get('content'):
            preview = note['content'][:100]
            if len(note['content']) > 100:
                preview += "..."
            content_label = QLabel(preview)
            content_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            content_label.setWordWrap(True)
            layout.addWidget(content_label)

        # Footer (metadata)
        footer_layout = QHBoxLayout()

        # Folder badge
        folder_badge = QLabel(f"📁 {note.get('folder', 'General')}")
        folder_badge.setStyleSheet("""
            background: #ecf0f1;
            color: #34495e;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
        """)
        footer_layout.addWidget(folder_badge)

        # Subject badge (if linked)
        if note.get('subject_name'):
            subject_badge = QLabel(f"📚 {note['subject_name']}")
            subject_badge.setStyleSheet(f"""
                background: {note.get('subject_color', '#3498db')};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            """)
            footer_layout.addWidget(subject_badge)

        # Tags (show first 2)
        if note.get('tags'):
            for tag in note['tags'][:2]:
                tag_badge = QLabel(f"🏷️ {tag}")
                tag_badge.setStyleSheet("""
                    background: #3498db;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 11px;
                """)
                footer_layout.addWidget(tag_badge)

            if len(note['tags']) > 2:
                more_label = QLabel(f"+{len(note['tags']) - 2}")
                more_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
                footer_layout.addWidget(more_label)

        footer_layout.addStretch()

        # Updated time
        try:
            updated = datetime.fromisoformat(note['updated_at'].replace('Z', '+00:00'))
            time_str = self._format_time_ago(updated)
            time_label = QLabel(time_str)
            time_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
            footer_layout.addWidget(time_label)
        except:
            pass

        layout.addLayout(footer_layout)

        # Connect click event
        card.mousePressEvent = lambda e: self._load_note_in_editor(note['id'])

        return card

    def _format_time_ago(self, dt: datetime) -> str:
        """Format datetime as relative time."""
        now = datetime.now()
        delta = now - dt

        if delta.days > 30:
            return f"{delta.days // 30}mo ago"
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"

    def _load_note_in_editor(self, note_id: str):
        """Load a note into the editor for viewing."""
        try:
            note = self.note_manager.get_note(note_id)
            if not note:
                return

            self.current_note_id = note_id

            # Update header
            self.note_title_label.setText(note['title'])
            self.note_title_label.setVisible(True)

            # Update buttons
            self.pin_btn.setVisible(True)
            self.favorite_btn.setVisible(True)
            self.edit_btn.setVisible(True)
            self.delete_btn.setVisible(True)

            # Update pin/favorite button states
            if note.get('is_pinned'):
                self.pin_btn.setText("📌 Unpin")
                self.pin_btn.setStyleSheet("""
                    QPushButton {
                        background: #e74c3c;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background: #c0392b;
                    }
                """)
            else:
                self.pin_btn.setText("📌 Pin")
                self.pin_btn.setStyleSheet("""
                    QPushButton {
                        background: #95a5a6;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background: #7f8c8d;
                    }
                """)

            if note.get('is_favorite'):
                self.favorite_btn.setText("⭐ Unfavorite")
                self.favorite_btn.setStyleSheet("""
                    QPushButton {
                        background: #e74c3c;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background: #c0392b;
                    }
                """)
            else:
                self.favorite_btn.setText("⭐ Favorite")
                self.favorite_btn.setStyleSheet("""
                    QPushButton {
                        background: #f39c12;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background: #e67e22;
                    }
                """)

            # Load content (read-only)
            self.content_editor.setReadOnly(True)
            self.content_editor.setText(note.get('content', ''))

            # Update metadata
            metadata_parts = []
            if note.get('folder'):
                metadata_parts.append(f"📁 {note['folder']}")
            if note.get('subject_name'):
                metadata_parts.append(f"📚 {note['subject_name']}")
            if note.get('tags'):
                metadata_parts.append(f"🏷️ {', '.join(note['tags'])}")

            try:
                created = datetime.fromisoformat(note['created_at'].replace('Z', '+00:00'))
                updated = datetime.fromisoformat(note['updated_at'].replace('Z', '+00:00'))
                metadata_parts.append(f"Created: {created.strftime('%Y-%m-%d %H:%M')}")
                metadata_parts.append(f"Updated: {updated.strftime('%Y-%m-%d %H:%M')}")
            except:
                pass

            self.metadata_label.setText(" | ".join(metadata_parts))
            self.editor_footer.setVisible(True)

        except Exception as e:
            logger.error(f"Failed to load note in editor: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load note: {e}")

    def _create_note(self):
        """Create a new note."""
        dialog = NoteDialog(self, self.note_manager, self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_data = dialog.get_note_data()
            note_id = self.note_manager.create_note(note_data)

            if note_id:
                self._load_notes()
                self._load_note_in_editor(note_id)
                self._start_editing()
                self.note_updated.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to create note")

    def _start_editing(self):
        """Start editing the current note."""
        if not self.current_note_id:
            return

        self.is_editing = True

        # Show title editor
        note = self.note_manager.get_note(self.current_note_id)
        if note:
            self.title_editor.setText(note['title'])
            self.title_editor.setVisible(True)
            self.note_title_label.setVisible(False)

        # Make content editable
        self.content_editor.setReadOnly(False)
        self.content_editor.setStyleSheet("""
            QTextEdit {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 15px;
                font-size: 14px;
                background: white;
            }
        """)

        # Show save/cancel buttons, hide other actions
        self.save_btn.setVisible(True)
        self.cancel_btn.setVisible(True)
        self.edit_btn.setVisible(False)
        self.pin_btn.setVisible(False)
        self.favorite_btn.setVisible(False)
        self.delete_btn.setVisible(False)

        # Start auto-save timer
        self.autosave_timer.start()

        self.content_editor.setFocus()

    def _save_note(self):
        """Save the current note."""
        if not self.current_note_id:
            return

        try:
            # Get data
            title = self.title_editor.text().strip()
            content = self.content_editor.toPlainText()

            if not title:
                QMessageBox.warning(self, "Warning", "Please enter a title")
                return

            # Update note
            success = self.note_manager.update_note(
                self.current_note_id,
                {
                    'title': title,
                    'content': content
                }
            )

            if success:
                self._cancel_editing()
                self._load_notes()
                self._load_note_in_editor(self.current_note_id)
                self.note_updated.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to save note")

        except Exception as e:
            logger.error(f"Failed to save note: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")

    def _cancel_editing(self):
        """Cancel editing and restore view mode."""
        self.is_editing = False

        # Stop auto-save timer
        self.autosave_timer.stop()

        # Hide title editor
        self.title_editor.setVisible(False)
        self.note_title_label.setVisible(True)

        # Make content read-only
        self.content_editor.setReadOnly(True)
        self.content_editor.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                font-size: 14px;
                background: white;
            }
        """)

        # Hide save/cancel buttons, show other actions
        self.save_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.edit_btn.setVisible(True)
        self.pin_btn.setVisible(True)
        self.favorite_btn.setVisible(True)
        self.delete_btn.setVisible(True)

        # Reload note to discard changes
        if self.current_note_id:
            self._load_note_in_editor(self.current_note_id)

    def _autosave(self):
        """Auto-save the current note."""
        if self.is_editing and self.current_note_id:
            try:
                title = self.title_editor.text().strip()
                content = self.content_editor.toPlainText()

                if title:  # Only save if has title
                    self.note_manager.update_note(
                        self.current_note_id,
                        {
                            'title': title,
                            'content': content
                        }
                    )
                    logger.debug("Auto-saved note")
            except Exception as e:
                logger.error(f"Auto-save failed: {e}")

    def _on_content_changed(self):
        """Handle content changes."""
        # Could show unsaved indicator here
        pass

    def _toggle_pin(self):
        """Toggle pin status of current note."""
        if not self.current_note_id:
            return

        note = self.note_manager.get_note(self.current_note_id)
        if note:
            new_status = not note.get('is_pinned', False)
            self.note_manager.update_note(
                self.current_note_id,
                {'is_pinned': new_status}
            )
            self._load_notes()
            self._load_note_in_editor(self.current_note_id)
            self.note_updated.emit()

    def _toggle_favorite(self):
        """Toggle favorite status of current note."""
        if not self.current_note_id:
            return

        note = self.note_manager.get_note(self.current_note_id)
        if note:
            new_status = not note.get('is_favorite', False)
            self.note_manager.update_note(
                self.current_note_id,
                {'is_favorite': new_status}
            )
            self._load_notes()
            self._load_note_in_editor(self.current_note_id)
            self.note_updated.emit()

    def _delete_note(self):
        """Delete the current note."""
        if not self.current_note_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this note? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.note_manager.delete_note(self.current_note_id):
                self.current_note_id = None
                self.content_editor.clear()
                self.note_title_label.setText("No note selected")
                self.note_title_label.setVisible(True)
                self.editor_footer.setVisible(False)
                self.pin_btn.setVisible(False)
                self.favorite_btn.setVisible(False)
                self.edit_btn.setVisible(False)
                self.delete_btn.setVisible(False)

                self._load_notes()
                self.note_updated.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete note")

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self.current_filters['search'] = text if text else None
        self._load_notes()

    def _on_folder_changed(self, folder: str):
        """Handle folder filter change."""
        if folder == "All Folders":
            self.current_filters['folder'] = None
        else:
            self.current_filters['folder'] = folder
        self._load_notes()

    def _on_subject_changed(self, subject: str):
        """Handle subject filter change."""
        if subject == "All Subjects":
            self.current_filters['subject_id'] = None
        else:
            # Find subject ID by name
            subjects = self._get_subjects()
            for s in subjects:
                if s['name'] == subject:
                    self.current_filters['subject_id'] = s['id']
                    break
        self._load_notes()

    def _on_tag_changed(self, tag: str):
        """Handle tag filter change."""
        if tag == "All Tags":
            self.current_filters['tag'] = None
        else:
            self.current_filters['tag'] = tag
        self._load_notes()

    def _on_pinned_changed(self, state):
        """Handle pinned filter change."""
        self.current_filters['pinned_only'] = bool(state)
        self._load_notes()

    def _on_favorites_changed(self, state):
        """Handle favorites filter change."""
        self.current_filters['favorites_only'] = bool(state)
        self._load_notes()

    def _clear_filters(self):
        """Clear all filters."""
        self.current_filters = {
            'folder': None,
            'subject_id': None,
            'tag': None,
            'search': None,
            'pinned_only': False,
            'favorites_only': False
        }

        self.search_input.clear()
        self.folder_combo.setCurrentIndex(0)
        self.subject_combo.setCurrentIndex(0)
        self.tag_combo.setCurrentIndex(0)
        self.pinned_check.setChecked(False)
        self.favorites_check.setChecked(False)

        self._load_notes()

    def _update_filter_options(self):
        """Update filter dropdown options."""
        # Update folders
        self.folder_combo.clear()
        self.folder_combo.addItem("All Folders")
        folders = self.note_manager.get_folders()
        self.folder_combo.addItems(folders)

        # Update subjects
        self.subject_combo.clear()
        self.subject_combo.addItem("All Subjects")
        subjects = self._get_subjects()
        for subject in subjects:
            self.subject_combo.addItem(subject['name'])

        # Update tags
        self.tag_combo.clear()
        self.tag_combo.addItem("All Tags")
        tags = self.note_manager.get_all_tags()
        self.tag_combo.addItems(tags)

    def _update_statistics(self):
        """Update statistics display."""
        try:
            stats = self.note_manager.get_statistics()

            self.total_label.setText(f"Total: {stats.get('total', 0)}")
            self.pinned_label.setText(f"Pinned: {stats.get('pinned', 0)}")
            self.favorites_label.setText(f"Favorites: {stats.get('favorites', 0)}")
            self.folders_label.setText(f"Folders: {stats.get('folders', 0)}")
            self.tags_label.setText(f"Tags: {stats.get('total_tags', 0)}")

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")

    def _get_subjects(self) -> List[Dict[str, Any]]:
        """Get list of subjects."""
        try:
            query = "SELECT id, name, color FROM subjects WHERE user_id = ? ORDER BY name"
            results = self.db.fetch_all(query, (self.user_id,))

            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'color': row[2]
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get subjects: {e}")
            return []


class NoteDialog(QDialog):
    """Dialog for creating new notes."""

    def __init__(self, parent, note_manager: NoteManager, db_manager):
        super().__init__(parent)
        self.note_manager = note_manager
        self.db = db_manager
        self.user_id = note_manager.user_id

        self.setWindowTitle("New Note")
        self.setMinimumWidth(500)
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Title
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter note title...")
        layout.addWidget(self.title_input)

        # Folder
        layout.addWidget(QLabel("Folder:"))
        folder_layout = QHBoxLayout()
        self.folder_combo = QComboBox()
        folders = self.note_manager.get_folders()
        self.folder_combo.addItems(folders)
        folder_layout.addWidget(self.folder_combo)

        new_folder_btn = QPushButton("New Folder")
        new_folder_btn.clicked.connect(self._create_folder)
        folder_layout.addWidget(new_folder_btn)
        layout.addLayout(folder_layout)

        # Subject
        layout.addWidget(QLabel("Subject (optional):"))
        self.subject_combo = QComboBox()
        self.subject_combo.addItem("-- None --", None)
        subjects = self._get_subjects()
        for subject in subjects:
            self.subject_combo.addItem(subject['name'], subject['id'])
        layout.addWidget(self.subject_combo)

        # Tags
        layout.addWidget(QLabel("Tags (comma-separated):"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g. important, study, exam")
        layout.addWidget(self.tags_input)

        # Checkboxes
        checkbox_layout = QHBoxLayout()
        self.pinned_check = QCheckBox("Pin this note")
        checkbox_layout.addWidget(self.pinned_check)

        self.favorite_check = QCheckBox("Mark as favorite")
        checkbox_layout.addWidget(self.favorite_check)
        layout.addLayout(checkbox_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_folder(self):
        """Create a new folder."""
        from PyQt6.QtWidgets import QInputDialog

        folder_name, ok = QInputDialog.getText(
            self, "New Folder", "Enter folder name:"
        )

        if ok and folder_name.strip():
            self.folder_combo.addItem(folder_name.strip())
            self.folder_combo.setCurrentText(folder_name.strip())

    def _get_subjects(self) -> List[Dict[str, Any]]:
        """Get list of subjects."""
        try:
            query = "SELECT id, name FROM subjects WHERE user_id = ? ORDER BY name"
            results = self.db.fetch_all(query, (self.user_id,))

            return [
                {'id': row[0], 'name': row[1]}
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get subjects: {e}")
            return []

    def get_note_data(self) -> Dict[str, Any]:
        """Get note data from dialog."""
        # Parse tags
        tags_text = self.tags_input.text().strip()
        tags = [t.strip() for t in tags_text.split(',') if t.strip()] if tags_text else []

        return {
            'title': self.title_input.text().strip() or "Untitled Note",
            'folder': self.folder_combo.currentText(),
            'subject_id': self.subject_combo.currentData(),
            'tags': tags,
            'is_pinned': self.pinned_check.isChecked(),
            'is_favorite': self.favorite_check.isChecked()
        }
