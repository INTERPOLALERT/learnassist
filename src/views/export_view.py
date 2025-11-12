"""
Export View - Phase 6 Sprint 1
PyQt6 interface for essay export functionality.

Features:
- Export to multiple formats (DOCX, PDF, LaTeX, Markdown, HTML, TXT)
- Template selection (APA, MLA, Chicago, Harvard, Generic)
- Export options configuration
- Export history viewing
- Batch export support

Author: Academic Command Center
Phase: 6 Sprint 1
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QTextEdit,
    QGroupBox, QCheckBox, QSpinBox, QProgressBar,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any, Optional, List
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from features.export.export_manager import ExportManager, ExportFormat, ExportTemplate
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ExportWorker(QThread):
    """Worker thread for export operations."""

    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        export_manager: ExportManager,
        essay_ids: List[str],
        format: str,
        template: Optional[str],
        output_dir: str,
        options: Dict[str, Any]
    ):
        """Initialize export worker."""
        super().__init__()
        self.export_manager = export_manager
        self.essay_ids = essay_ids
        self.format = format
        self.template = template
        self.output_dir = output_dir
        self.options = options

    def run(self):
        """Run export operation."""
        try:
            if len(self.essay_ids) == 1:
                # Single export
                result = self.export_manager.export_essay(
                    essay_id=self.essay_ids[0],
                    format=self.format,
                    template=self.template,
                    output_path=None,  # Auto-generate
                    options=self.options
                )
                self.finished.emit(result)
            else:
                # Batch export
                result = self.export_manager.batch_export(
                    essay_ids=self.essay_ids,
                    format=self.format,
                    template=self.template,
                    options=self.options
                )
                self.finished.emit(result)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.error.emit(str(e))


class ExportView(QWidget):
    """
    Export View - Main interface for essay export.
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize export view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.export_manager = ExportManager(user_id, self.db)

        self.current_worker = None

        self._init_ui()
        self._load_essays()

    def _init_ui(self):
        """Initialize user interface."""

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Export Essays")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Export
        export_tab = self._create_export_tab()
        tabs.addTab(export_tab, "Export")

        # Tab 2: History
        history_tab = self._create_history_tab()
        tabs.addTab(history_tab, "Export History")

        layout.addWidget(tabs)

        self.setLayout(layout)

    def _create_export_tab(self) -> QWidget:
        """Create export configuration tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Essay selection
        essay_group = QGroupBox("Select Essays")
        essay_layout = QVBoxLayout()

        self.essay_list = QListWidget()
        self.essay_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        essay_layout.addWidget(self.essay_list)

        # Select all/none buttons
        select_buttons = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.essay_list.selectAll)
        select_buttons.addWidget(select_all_btn)

        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.essay_list.clearSelection)
        select_buttons.addWidget(select_none_btn)

        essay_layout.addLayout(select_buttons)
        essay_group.setLayout(essay_layout)
        layout.addWidget(essay_group)

        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "DOCX (Microsoft Word)",
            "PDF (Portable Document)",
            "LaTeX (TeX source)",
            "Markdown (.md)",
            "HTML (Web page)",
            "Plain Text (.txt)"
        ])
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Template selection
        template_group = QGroupBox("Academic Template")
        template_layout = QVBoxLayout()

        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "APA 7th Edition",
            "MLA 9th Edition",
            "Chicago Style",
            "Harvard Style",
            "Generic"
        ])
        template_layout.addWidget(self.template_combo)

        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.include_title_page_cb = QCheckBox("Include title page")
        self.include_title_page_cb.setChecked(True)
        options_layout.addWidget(self.include_title_page_cb)

        self.include_references_cb = QCheckBox("Include references")
        self.include_references_cb.setChecked(True)
        options_layout.addWidget(self.include_references_cb)

        self.page_numbers_cb = QCheckBox("Add page numbers")
        self.page_numbers_cb.setChecked(True)
        options_layout.addWidget(self.page_numbers_cb)

        # Line spacing
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Line spacing:"))
        self.line_spacing_spin = QSpinBox()
        self.line_spacing_spin.setMinimum(1)
        self.line_spacing_spin.setMaximum(3)
        self.line_spacing_spin.setValue(2)
        spacing_layout.addWidget(self.line_spacing_spin)
        spacing_layout.addStretch()
        options_layout.addLayout(spacing_layout)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output directory:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(os.path.join(os.getcwd(), "exports"))
        output_layout.addWidget(self.output_dir_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(browse_btn)

        layout.addLayout(output_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Export button
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_history_tab(self) -> QWidget:
        """Create export history tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Refresh button
        refresh_btn = QPushButton("Refresh History")
        refresh_btn.clicked.connect(self._load_history)
        layout.addWidget(refresh_btn)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Essay", "Format", "Template", "File Size", "Path"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.history_table)

        widget.setLayout(layout)

        # Load history
        self._load_history()

        return widget

    def _load_essays(self):
        """Load essays from database."""
        try:
            query = """
            SELECT id, title, status, current_word_count
            FROM essays
            WHERE user_id = ?
            ORDER BY created_at DESC
            """

            essays = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_all=True
            )

            self.essay_list.clear()

            for essay in essays or []:
                essay_id, title, status, word_count = essay
                display_text = f"{title} ({word_count} words) - {status}"

                item = self.essay_list.addItem(display_text)
                # Store essay_id in item data
                self.essay_list.item(self.essay_list.count() - 1).setData(
                    Qt.ItemDataRole.UserRole,
                    essay_id
                )

            logger.info(f"Loaded {len(essays or [])} essays")

        except Exception as e:
            logger.error(f"Failed to load essays: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load essays: {e}")

    def _load_history(self):
        """Load export history."""
        try:
            result = self.export_manager.get_export_history(limit=100)

            if not result.get('success'):
                QMessageBox.warning(self, "Error", f"Failed to load history: {result.get('error')}")
                return

            history = result.get('history', [])

            self.history_table.setRowCount(len(history))

            for row, record in enumerate(history):
                # Date
                date_item = QTableWidgetItem(record.get('exported_at', ''))
                self.history_table.setItem(row, 0, date_item)

                # Essay (would need to fetch title from ID)
                essay_item = QTableWidgetItem(record.get('essay_id', '')[:8])
                self.history_table.setItem(row, 1, essay_item)

                # Format
                format_item = QTableWidgetItem(record.get('format', '').upper())
                self.history_table.setItem(row, 2, format_item)

                # Template
                template_item = QTableWidgetItem(record.get('template', 'N/A'))
                self.history_table.setItem(row, 3, template_item)

                # File size
                file_size = record.get('file_size', 0)
                size_str = self._format_file_size(file_size)
                size_item = QTableWidgetItem(size_str)
                self.history_table.setItem(row, 4, size_item)

                # Path
                path_item = QTableWidgetItem(record.get('file_path', ''))
                self.history_table.setItem(row, 5, path_item)

            logger.info(f"Loaded {len(history)} history records")

        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load history: {e}")

    def _on_format_changed(self, index: int):
        """Handle format selection change."""
        # Enable/disable template based on format
        format_supports_template = index in [0, 1, 2]  # DOCX, PDF, LaTeX
        self.template_combo.setEnabled(format_supports_template)

    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_edit.text()
        )

        if directory:
            self.output_dir_edit.setText(directory)

    def _export(self):
        """Execute export operation."""
        # Get selected essays
        selected_items = self.essay_list.selectedItems()

        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one essay to export.")
            return

        # Get essay IDs
        essay_ids = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in selected_items
        ]

        # Get format
        format_index = self.format_combo.currentIndex()
        format_map = {
            0: ExportFormat.DOCX,
            1: ExportFormat.PDF,
            2: ExportFormat.LATEX,
            3: ExportFormat.MARKDOWN,
            4: ExportFormat.HTML,
            5: ExportFormat.TXT
        }
        export_format = format_map[format_index]

        # Get template
        template_index = self.template_combo.currentIndex()
        template_map = {
            0: ExportTemplate.APA,
            1: ExportTemplate.MLA,
            2: ExportTemplate.CHICAGO,
            3: ExportTemplate.HARVARD,
            4: ExportTemplate.GENERIC
        }
        template = template_map[template_index] if self.template_combo.isEnabled() else None

        # Get options
        options = {
            'include_title_page': self.include_title_page_cb.isChecked(),
            'include_references': self.include_references_cb.isChecked(),
            'page_numbers': self.page_numbers_cb.isChecked(),
            'line_spacing': float(self.line_spacing_spin.value())
        }

        # Get output directory
        output_dir = self.output_dir_edit.text()

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Create worker thread
        self.current_worker = ExportWorker(
            self.export_manager,
            essay_ids,
            export_format,
            template,
            output_dir,
            options
        )

        self.current_worker.finished.connect(self._on_export_finished)
        self.current_worker.error.connect(self._on_export_error)

        # Start export
        self.current_worker.start()

        logger.info(f"Started export of {len(essay_ids)} essays to {export_format}")

    def _on_export_finished(self, result: Dict[str, Any]):
        """Handle export completion."""
        self.progress_bar.setVisible(False)

        if result.get('success'):
            if 'total' in result:
                # Batch export
                message = (
                    f"Batch export complete!\n\n"
                    f"Total: {result['total']}\n"
                    f"Successful: {result['successful']}\n"
                    f"Failed: {result['failed']}"
                )
            else:
                # Single export
                message = (
                    f"Export successful!\n\n"
                    f"File: {result.get('file_path', 'Unknown')}\n"
                    f"Size: {self._format_file_size(result.get('file_size', 0))}"
                )

            QMessageBox.information(self, "Export Complete", message)

            # Refresh history
            self._load_history()
        else:
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Export failed: {result.get('error', 'Unknown error')}"
            )

    def _on_export_error(self, error_message: str):
        """Handle export error."""
        self.progress_bar.setVisible(False)

        QMessageBox.critical(
            self,
            "Export Error",
            f"Export error: {error_message}"
        )

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
