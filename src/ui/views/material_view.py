"""
Academic Command Center - Material View
Upload and manage materials.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QFileDialog,
    QLineEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.materials.materials_manager import MaterialsManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MaterialView(QWidget):
    """Material library and management view."""

    def __init__(self, user_id: str, db_manager: DatabaseManager):
        """
        Initialize material view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager
        self.materials_manager = MaterialsManager(user_id, db_manager=db_manager)

        self.current_filter_type = 'all'

        self._init_ui()
        self.refresh()

    def _init_ui(self):
        """Initialize user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Materials Library")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Filter
        filter_label = QLabel("Type:")
        header_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Lecture Notes", "Textbook", "Article", "Other"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.filter_combo)

        # Upload button
        upload_btn = QPushButton("+ Upload Material")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        upload_btn.clicked.connect(self._upload_material)
        header_layout.addWidget(upload_btn)

        main_layout.addLayout(header_layout)

        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        main_layout.addWidget(self.stats_label)

        # Material list container (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.material_list_layout = QVBoxLayout(scroll_content)
        self.material_list_layout.setSpacing(15)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def refresh(self):
        """Refresh material list."""
        logger.info("Refreshing material list...")

        # Clear existing
        self._clear_layout(self.material_list_layout)

        # Get materials
        try:
            filter_type = None
            if self.current_filter_type != 'all':
                filter_type = self.current_filter_type.lower().replace(' ', '_')

            result = self.materials_manager.list_materials(material_type=filter_type)

            if not result['success']:
                error_label = QLabel(f"Error: {result.get('error')}")
                error_label.setStyleSheet("color: #e74c3c;")
                self.material_list_layout.addWidget(error_label)
                return

            materials = result['materials']

            if not materials:
                no_data = QLabel("No materials yet. Click '+ Upload Material' to get started!")
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data.setStyleSheet("color: #95a5a6; font-size: 16px; font-style: italic; margin-top: 50px;")
                self.material_list_layout.addWidget(no_data)

                self.stats_label.setText("0 materials")
                return

            # Update stats
            total_materials = len(materials)
            total_words = sum(m.get('word_count', 0) for m in materials)

            self.stats_label.setText(
                f"{total_materials} materials • {total_words:,} words total"
            )

            # Create material cards
            for material in materials:
                material_card = self._create_material_card(material)
                self.material_list_layout.addWidget(material_card)

            # Stretch to push cards to top
            self.material_list_layout.addStretch()

        except Exception as e:
            logger.error(f"Failed to refresh materials: {e}")
            error_label = QLabel(f"Error loading materials: {str(e)}")
            error_label.setStyleSheet("color: #e74c3c;")
            self.material_list_layout.addWidget(error_label)

    def _create_material_card(self, material: dict) -> QFrame:
        """Create material card widget."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 20px;
            }
            QFrame:hover {
                border-color: #2ecc71;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        """)

        layout = QVBoxLayout(card)

        # Top row: filename and type
        top_layout = QHBoxLayout()

        # File icon based on type
        file_type = material.get('file_type', 'unknown')
        icons = {
            'pdf': '📄',
            'docx': '📝',
            'pptx': '📊',
            'txt': '📃',
            'png': '🖼️',
            'jpg': '🖼️'
        }
        icon = icons.get(file_type, '📎')

        filename_label = QLabel(f"{icon} {material['file_name']}")
        filename_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        top_layout.addWidget(filename_label, stretch=1)

        # Type badge
        material_type = material.get('material_type', 'general').replace('_', ' ').title()
        type_badge = QLabel(material_type)
        type_badge.setStyleSheet("""
            background-color: #ecf0f1;
            color: #34495e;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 11px;
        """)
        top_layout.addWidget(type_badge)

        layout.addLayout(top_layout)

        # Summary
        if material.get('content_summary'):
            summary_label = QLabel(material['content_summary'])
            summary_label.setWordWrap(True)
            summary_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-top: 8px;")
            layout.addWidget(summary_label)

        # Tags
        import json
        tags_json = material.get('tags', '[]')
        try:
            tags = json.loads(tags_json)
            if tags:
                tags_text = ", ".join(tags[:8])  # Show first 8 tags
                if len(tags) > 8:
                    tags_text += f" +{len(tags)-8} more"

                tags_label = QLabel(f"🏷️ {tags_text}")
                tags_label.setStyleSheet("color: #95a5a6; font-size: 11px; margin-top: 5px;")
                layout.addWidget(tags_label)
        except:
            pass

        # Bottom row: metadata and actions
        bottom_layout = QHBoxLayout()

        # Word count
        word_count = material.get('word_count', 0)
        words_label = QLabel(f"{word_count:,} words")
        words_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        bottom_layout.addWidget(words_label)

        # Course
        if material.get('course_name'):
            course_label = QLabel(f"• {material['course_name']}")
            course_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            bottom_layout.addWidget(course_label)

        bottom_layout.addStretch()

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_material(material['id']))
        bottom_layout.addWidget(delete_btn)

        layout.addLayout(bottom_layout)

        return card

    def _upload_material(self):
        """Upload new material."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Material to Upload",
            "",
            "All Supported Files (*.pdf *.docx *.pptx *.txt *.md *.png *.jpg);;PDF Files (*.pdf);;Word Documents (*.docx);;PowerPoint (*.pptx);;Text Files (*.txt *.md);;Images (*.png *.jpg)"
        )

        if not file_path:
            return

        try:
            # Show progress
            QMessageBox.information(
                self,
                "Processing",
                "Processing material...\nThis may take a moment for large files."
            )

            # Upload material
            result = self.materials_manager.upload_material(
                file_path=file_path,
                course_name=None,
                material_type='general'
            )

            if result['success']:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Material '{result['file_name']}' uploaded successfully!\n\n"
                    f"Extracted: {result['word_count']} words\n"
                    f"Concepts: {len(result['concepts'])} key concepts identified"
                )

                self.refresh()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to upload material:\n{result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Failed to upload material: {e}")
            QMessageBox.critical(self, "Error", f"Error uploading material:\n{str(e)}")

    def _delete_material(self, material_id: str):
        """Delete material."""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this material?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.materials_manager.delete_material(material_id)

                if result['success']:
                    QMessageBox.information(self, "Success", "Material deleted")
                    self.refresh()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete:\n{result.get('error')}")

            except Exception as e:
                logger.error(f"Failed to delete material: {e}")
                QMessageBox.critical(self, "Error", f"Error deleting material:\n{str(e)}")

    def _on_filter_changed(self, index: int):
        """Handle filter dropdown change."""
        filters = ['all', 'lecture_notes', 'textbook', 'article', 'other']
        self.current_filter_type = filters[index]
        self.refresh()

    def _clear_layout(self, layout: QVBoxLayout):
        """Clear all widgets from layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    db = DatabaseManager()
    view = MaterialView("test_user", db)
    view.show()

    sys.exit(app.exec())
