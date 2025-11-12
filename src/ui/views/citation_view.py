"""
Academic Command Center - Citation Manager View
UI for managing academic sources and citations.
"""

import logging
import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QDialog, QFormLayout,
    QSpinBox, QDialogButtonBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.citations.citation_manager import CitationManager, SourceType
from features.citations.citation_formatter import CitationFormatter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AddSourceDialog(QDialog):
    """Dialog for adding/editing a source."""

    def __init__(self, parent=None, source_data=None):
        """
        Initialize add source dialog.

        Args:
            parent: Parent widget
            source_data: Existing source data for editing (None for new)
        """
        super().__init__(parent)

        self.source_data = source_data
        self.is_edit_mode = source_data is not None

        self.setWindowTitle("Edit Source" if self.is_edit_mode else "Add New Source")
        self.setMinimumWidth(600)

        self._init_ui()

        # Populate fields if editing
        if self.is_edit_mode:
            self._populate_fields()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Form
        form_layout = QFormLayout()

        # Source type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Book", "Journal Article", "Website", "Lecture", "Other"])
        form_layout.addRow("Source Type:", self.type_combo)

        # Title (required)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Required")
        form_layout.addRow("Title*:", self.title_input)

        # Author
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Last name, First name")
        form_layout.addRow("Author:", self.author_input)

        # Year
        self.year_input = QSpinBox()
        self.year_input.setRange(1000, 2100)
        self.year_input.setValue(2024)
        form_layout.addRow("Year:", self.year_input)

        # Publication/Journal
        self.publication_input = QLineEdit()
        self.publication_input.setPlaceholderText("Journal or publication name")
        form_layout.addRow("Publication:", self.publication_input)

        # Publisher
        self.publisher_input = QLineEdit()
        self.publisher_input.setPlaceholderText("Publisher name")
        form_layout.addRow("Publisher:", self.publisher_input)

        # Pages
        self.pages_input = QLineEdit()
        self.pages_input.setPlaceholderText("e.g., 123-145")
        form_layout.addRow("Pages:", self.pages_input)

        # URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        form_layout.addRow("URL:", self.url_input)

        # DOI
        self.doi_input = QLineEdit()
        self.doi_input.setPlaceholderText("10.1234/example")
        form_layout.addRow("DOI:", self.doi_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Personal notes about this source...")
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_fields(self):
        """Populate form fields with existing source data."""
        if not self.source_data:
            return

        # Map source type to combo box index
        type_map = {
            'book': 0,
            'journal_article': 1,
            'website': 2,
            'lecture': 3,
            'other': 4
        }
        self.type_combo.setCurrentIndex(type_map.get(self.source_data.get('source_type', 'other'), 4))

        self.title_input.setText(self.source_data.get('title', ''))
        self.author_input.setText(self.source_data.get('author', ''))

        if self.source_data.get('year'):
            self.year_input.setValue(self.source_data['year'])

        self.publication_input.setText(self.source_data.get('publication', ''))
        self.publisher_input.setText(self.source_data.get('publisher', ''))
        self.pages_input.setText(self.source_data.get('pages', ''))
        self.url_input.setText(self.source_data.get('url', ''))
        self.doi_input.setText(self.source_data.get('doi', ''))
        self.notes_input.setPlainText(self.source_data.get('notes', ''))

    def get_source_data(self):
        """
        Get source data from form.

        Returns:
            Dictionary of source data
        """
        type_map = {
            0: 'book',
            1: 'journal_article',
            2: 'website',
            3: 'lecture',
            4: 'other'
        }

        return {
            'source_type': type_map[self.type_combo.currentIndex()],
            'title': self.title_input.text().strip(),
            'author': self.author_input.text().strip() or None,
            'year': self.year_input.value() if self.year_input.value() > 1000 else None,
            'publication': self.publication_input.text().strip() or None,
            'publisher': self.publisher_input.text().strip() or None,
            'pages': self.pages_input.text().strip() or None,
            'url': self.url_input.text().strip() or None,
            'doi': self.doi_input.text().strip() or None,
            'notes': self.notes_input.toPlainText().strip() or None
        }


class CitationView(QWidget):
    """
    Citation Manager view.

    Features:
    - Source list
    - Add/edit/delete sources
    - Search sources
    - View citations in different styles
    - Generate bibliography
    - Copy citations to clipboard
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize citation view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize backend
        self.citation_manager = CitationManager(self.user_id, self.db)
        self.formatter = CitationFormatter()

        # Current selection
        self.current_source_id = None

        # Initialize UI
        self._init_ui()

        # Load sources
        self.refresh()

        logger.info("Citation view initialized")

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📚 Citation Manager")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add source button
        add_btn = QPushButton("➕ Add Source")
        add_btn.clicked.connect(self._on_add_source_clicked)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        header_layout.addWidget(add_btn)

        main_layout.addLayout(header_layout)

        # Statistics bar
        self.stats_label = QLabel("Loading...")
        self.stats_label.setStyleSheet("background-color: #ecf0f1; padding: 10px; border-radius: 5px; font-size: 13px;")
        main_layout.addWidget(self.stats_label)

        # Search bar
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search sources by title, author, or publication...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear_search)
        search_layout.addWidget(clear_btn)

        main_layout.addLayout(search_layout)

        # Main content (two columns)
        content_layout = QHBoxLayout()

        # Left: Source list
        list_section = self._create_list_section()
        content_layout.addWidget(list_section, stretch=1)

        # Right: Citation display
        citation_section = self._create_citation_section()
        content_layout.addWidget(citation_section, stretch=1)

        main_layout.addLayout(content_layout)

    def _create_list_section(self) -> QFrame:
        """Create source list section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("Your Sources")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Source list
        self.source_list = QListWidget()
        self.source_list.itemSelectionChanged.connect(self._on_source_selected)
        layout.addWidget(self.source_list)

        # Action buttons
        button_layout = QHBoxLayout()

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self._on_edit_source_clicked)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self._on_delete_source_clicked)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        return section

    def _create_citation_section(self) -> QFrame:
        """Create citation display section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title_layout = QHBoxLayout()

        title = QLabel("Citations")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Citation style selector
        style_label = QLabel("Style:")
        title_layout.addWidget(style_label)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["Harvard", "APA", "MLA"])
        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        title_layout.addWidget(self.style_combo)

        layout.addLayout(title_layout)

        # Citation display (tabbed for different styles)
        self.harvard_display = QTextEdit()
        self.harvard_display.setReadOnly(True)
        self.harvard_display.setPlaceholderText("Select a source to view citation")
        layout.addWidget(self.harvard_display)

        # Copy button
        copy_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy Citation")
        copy_btn.clicked.connect(self._on_copy_citation)
        copy_layout.addWidget(copy_btn)

        generate_bib_btn = QPushButton("📄 Generate Bibliography")
        generate_bib_btn.clicked.connect(self._on_generate_bibliography)
        copy_layout.addWidget(generate_bib_btn)

        copy_layout.addStretch()

        layout.addLayout(copy_layout)

        # Source details
        details_label = QLabel("Source Details")
        details_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        details_label.setStyleSheet("margin-top: 15px;")
        layout.addWidget(details_label)

        self.details_display = QTextEdit()
        self.details_display.setReadOnly(True)
        self.details_display.setMaximumHeight(150)
        self.details_display.setPlaceholderText("Select a source to view details")
        layout.addWidget(self.details_display)

        return section

    def _on_add_source_clicked(self):
        """Handle add source button click."""
        dialog = AddSourceDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            source_data = dialog.get_source_data()

            if not source_data['title']:
                QMessageBox.warning(self, "Validation Error", "Title is required!")
                return

            # Add source
            result = self.citation_manager.add_source(**source_data)

            if result['success']:
                QMessageBox.information(self, "Success", "Source added successfully!")
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"Failed to add source: {result.get('error')}")

    def _on_edit_source_clicked(self):
        """Handle edit source button click."""
        if not self.current_source_id:
            QMessageBox.warning(self, "No Selection", "Please select a source to edit")
            return

        # Get current source
        result = self.citation_manager.get_source(self.current_source_id)

        if not result['success']:
            QMessageBox.critical(self, "Error", "Failed to load source details")
            return

        dialog = AddSourceDialog(self, result['source'])

        if dialog.exec() == QDialog.DialogCode.Accepted:
            source_data = dialog.get_source_data()

            update_result = self.citation_manager.update_source(self.current_source_id, source_data)

            if update_result['success']:
                QMessageBox.information(self, "Success", "Source updated successfully!")
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"Failed to update source: {update_result.get('error')}")

    def _on_delete_source_clicked(self):
        """Handle delete source button click."""
        if not self.current_source_id:
            QMessageBox.warning(self, "No Selection", "Please select a source to delete")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this source?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.citation_manager.delete_source(self.current_source_id)

            if result['success']:
                self.current_source_id = None
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete source: {result.get('error')}")

    def _on_source_selected(self):
        """Handle source selection change."""
        items = self.source_list.selectedItems()

        if not items:
            self.current_source_id = None
            self._clear_citation_display()
            return

        # Get source ID from item data
        self.current_source_id = items[0].data(Qt.ItemDataRole.UserRole)

        # Load source details
        result = self.citation_manager.get_source(self.current_source_id)

        if result['success']:
            self._display_source_citation(result['source'])
            self._display_source_details(result['source'])

    def _on_search(self):
        """Handle search."""
        search_term = self.search_input.text().strip()

        if not search_term:
            self.refresh()
            return

        result = self.citation_manager.search_sources(search_term)

        if result['success']:
            self._populate_source_list(result['sources'])

    def _on_clear_search(self):
        """Handle clear search."""
        self.search_input.clear()
        self.refresh()

    def _on_style_changed(self):
        """Handle citation style change."""
        if self.current_source_id:
            result = self.citation_manager.get_source(self.current_source_id)
            if result['success']:
                self._display_source_citation(result['source'])

    def _on_copy_citation(self):
        """Handle copy citation button click."""
        citation_text = self.harvard_display.toPlainText()

        if citation_text and not citation_text.startswith("Select"):
            clipboard = QApplication.clipboard()
            clipboard.setText(citation_text)
            QMessageBox.information(self, "Copied", "Citation copied to clipboard!")

    def _on_generate_bibliography(self):
        """Handle generate bibliography button click."""
        style_map = {0: 'harvard', 1: 'apa', 2: 'mla'}
        style = style_map[self.style_combo.currentIndex()]

        result = self.citation_manager.generate_bibliography(citation_style=style)

        if result['success']:
            # Show bibliography in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Bibliography ({style.upper()})")
            dialog.setMinimumSize(700, 500)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(result['bibliography'])
            layout.addWidget(text_edit)

            # Copy button
            button_layout = QHBoxLayout()

            copy_btn = QPushButton("📋 Copy All")
            copy_btn.clicked.connect(lambda: self._copy_bibliography(result['bibliography']))
            button_layout.addWidget(copy_btn)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)

            button_layout.addStretch()

            layout.addLayout(button_layout)

            dialog.exec()
        else:
            QMessageBox.critical(self, "Error", f"Failed to generate bibliography: {result.get('error')}")

    def _copy_bibliography(self, text: str):
        """Copy bibliography to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Bibliography copied to clipboard!")

    def _display_source_citation(self, source: dict):
        """Display source citation in selected style."""
        style_map = {0: 'citation_harvard', 1: 'citation_apa', 2: 'citation_mla'}
        citation_field = style_map[self.style_combo.currentIndex()]

        citation = source.get(citation_field, "Citation not available")
        self.harvard_display.setPlainText(citation)

    def _display_source_details(self, source: dict):
        """Display source details."""
        details = []

        if source.get('author'):
            details.append(f"<b>Author:</b> {source['author']}")

        if source.get('year'):
            details.append(f"<b>Year:</b> {source['year']}")

        if source.get('publication'):
            details.append(f"<b>Publication:</b> {source['publication']}")

        if source.get('publisher'):
            details.append(f"<b>Publisher:</b> {source['publisher']}")

        if source.get('pages'):
            details.append(f"<b>Pages:</b> {source['pages']}")

        if source.get('url'):
            details.append(f"<b>URL:</b> {source['url']}")

        if source.get('doi'):
            details.append(f"<b>DOI:</b> {source['doi']}")

        if source.get('notes'):
            details.append(f"<b>Notes:</b> {source['notes']}")

        details.append(f"<b>Times Cited:</b> {source.get('times_cited', 0)}")

        self.details_display.setHtml("<br>".join(details))

    def _clear_citation_display(self):
        """Clear citation display."""
        self.harvard_display.setPlainText("Select a source to view citation")
        self.details_display.setPlainText("Select a source to view details")

    def _populate_source_list(self, sources: list):
        """Populate source list widget."""
        self.source_list.clear()

        for source in sources:
            # Format list item
            title = source.get('title', 'Untitled')
            author = source.get('author', 'Unknown')
            year = source.get('year', 'n.d.')

            item_text = f"{author} ({year}) - {title}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, source['id'])

            self.source_list.addItem(item)

    def refresh(self):
        """Refresh the view."""
        logger.info("Refreshing citations...")

        # Update statistics
        stats = self.citation_manager.get_citation_statistics()

        if stats['success']:
            stats_text = f"📊 Total Sources: {stats['total_sources']} | " \
                        f"Books: {stats['by_type'].get('books', 0)} | " \
                        f"Journals: {stats['by_type'].get('journals', 0)} | " \
                        f"Websites: {stats['by_type'].get('websites', 0)}"
            self.stats_label.setText(stats_text)

        # Load all sources
        result = self.citation_manager.get_all_sources()

        if result['success']:
            self._populate_source_list(result['sources'])

        logger.info("Citations refreshed")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    view = CitationView(user_id="test_user")
    view.setGeometry(100, 100, 1200, 800)
    view.show()

    sys.exit(app.exec())
