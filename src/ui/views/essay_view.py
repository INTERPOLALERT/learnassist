"""
Academic Command Center - Essay View
List and manage essays.
"""

import logging
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QTextEdit,
    QDialog, QDialogButtonBox, QLineEdit, QDateEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.essay_parser.parser import EssayParser
from features.task_manager.task_manager import TaskManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EssayView(QWidget):
    """Essay list and management view."""

    def __init__(self, user_id: str, db_manager: DatabaseManager):
        """
        Initialize essay view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager

        self._init_ui()
        self.refresh()

    def _init_ui(self):
        """Initialize user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Essays")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add essay button
        add_btn = QPushButton("+ Add Essay")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        add_btn.clicked.connect(self._show_add_essay_dialog)
        header_layout.addWidget(add_btn)

        main_layout.addLayout(header_layout)

        # Essay list container (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.essay_list_layout = QVBoxLayout(scroll_content)
        self.essay_list_layout.setSpacing(15)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def refresh(self):
        """Refresh essay list."""
        logger.info("Refreshing essay list...")

        # Clear existing
        self._clear_layout(self.essay_list_layout)

        # Get essays
        try:
            query = """
            SELECT id, title, course_name, due_date, word_count_min, word_count_max, created_at
            FROM essays
            WHERE user_id = ?
            ORDER BY created_at DESC
            """

            essays = self.db.execute_query(query, (self.user_id,), fetch_all=True)

            if not essays:
                no_data = QLabel("No essays yet. Click '+ Add Essay' to get started!")
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data.setStyleSheet("color: #95a5a6; font-size: 16px; font-style: italic; margin-top: 50px;")
                self.essay_list_layout.addWidget(no_data)
                return

            for essay in essays:
                essay_card = self._create_essay_card(essay)
                self.essay_list_layout.addWidget(essay_card)

            # Stretch to push cards to top
            self.essay_list_layout.addStretch()

        except Exception as e:
            logger.error(f"Failed to refresh essays: {e}")
            error_label = QLabel(f"Error loading essays: {str(e)}")
            error_label.setStyleSheet("color: #e74c3c;")
            self.essay_list_layout.addWidget(error_label)

    def _create_essay_card(self, essay: dict) -> QFrame:
        """Create essay card widget."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 20px;
            }
            QFrame:hover {
                border-color: #3498db;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        """)

        layout = QVBoxLayout(card)

        # Title and course
        header_layout = QHBoxLayout()

        title_label = QLabel(essay['title'])
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        if essay.get('course_name'):
            course_badge = QLabel(essay['course_name'])
            course_badge.setStyleSheet("""
                background-color: #ecf0f1;
                color: #34495e;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
            """)
            header_layout.addWidget(course_badge)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Details
        details_layout = QHBoxLayout()

        # Word count
        word_min = essay.get('word_count_min', 0)
        word_max = essay.get('word_count_max', 0)
        if word_min and word_max:
            word_text = f"📏 {word_min}-{word_max} words"
        elif word_min:
            word_text = f"📏 {word_min}+ words"
        else:
            word_text = "📏 Word count not specified"

        word_label = QLabel(word_text)
        word_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        details_layout.addWidget(word_label)

        # Due date
        if essay.get('due_date'):
            try:
                due_date = datetime.fromisoformat(essay['due_date'])
                days_until = (due_date - datetime.now()).days

                if days_until < 0:
                    due_text = f"🔴 Overdue ({abs(days_until)}d ago)"
                    due_color = "#e74c3c"
                elif days_until <= 3:
                    due_text = f"🔴 Due in {days_until}d"
                    due_color = "#e74c3c"
                elif days_until <= 7:
                    due_text = f"🟡 Due in {days_until}d"
                    due_color = "#f39c12"
                else:
                    due_text = f"🟢 Due in {days_until}d"
                    due_color = "#27ae60"

                due_label = QLabel(due_text)
                due_label.setStyleSheet(f"color: {due_color}; font-size: 12px; font-weight: bold;")
                details_layout.addWidget(due_label)

            except Exception as e:
                logger.warning(f"Failed to parse due date: {e}")

        details_layout.addStretch()

        layout.addLayout(details_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # View details button
        view_btn = QPushButton("View Details")
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        view_btn.clicked.connect(lambda: self._view_essay_details(essay['id']))
        button_layout.addWidget(view_btn)

        # Generate tasks button
        tasks_btn = QPushButton("Generate Tasks")
        tasks_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        tasks_btn.clicked.connect(lambda: self._generate_tasks(essay['id']))
        button_layout.addWidget(tasks_btn)

        layout.addLayout(button_layout)

        return card

    def _show_add_essay_dialog(self):
        """Show dialog to add new essay."""
        dialog = AddEssayDialog(self.user_id, self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _view_essay_details(self, essay_id: str):
        """View essay details."""
        # TODO: Show detailed view
        QMessageBox.information(self, "View Details", f"Details for essay {essay_id}\n(Feature coming soon!)")

    def _generate_tasks(self, essay_id: str):
        """Generate tasks for essay."""
        try:
            # Show progress
            QMessageBox.information(self, "Generating Tasks", "Generating tasks for this essay...\nThis may take a moment.")

            # Generate tasks
            task_manager = TaskManager(self.user_id, self.db)
            result = task_manager.generate_all_tasks(essay_id)

            if result['success']:
                QMessageBox.information(
                    self,
                    "Tasks Generated",
                    f"Successfully generated {result['count']} tasks!\n\n"
                    f"Research tasks: {result['summary']['breakdown']['research_tasks']}\n"
                    f"Writing tasks: {result['summary']['breakdown']['writing_tasks']}\n"
                    f"Total time: {result['summary']['time_estimate']['total_hours']} hours"
                )
            else:
                QMessageBox.warning(self, "Error", f"Failed to generate tasks:\n{result.get('error')}")

        except Exception as e:
            logger.error(f"Failed to generate tasks: {e}")
            QMessageBox.critical(self, "Error", f"Error generating tasks:\n{str(e)}")

    def _clear_layout(self, layout: QVBoxLayout):
        """Clear all widgets from layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


class AddEssayDialog(QDialog):
    """Dialog for adding a new essay."""

    def __init__(self, user_id: str, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)

        self.user_id = user_id
        self.db = db_manager

        self.setWindowTitle("Add New Essay")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._init_ui()

    def _init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel("Paste your essay instructions below:")
        instructions.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(instructions)

        # Course name
        course_layout = QHBoxLayout()
        course_label = QLabel("Course:")
        self.course_input = QLineEdit()
        self.course_input.setPlaceholderText("e.g., ENGL 101")
        course_layout.addWidget(course_label)
        course_layout.addWidget(self.course_input)
        layout.addLayout(course_layout)

        # Due date
        date_layout = QHBoxLayout()
        date_label = QLabel("Due Date:")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate().addDays(14))
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Essay instructions text area
        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText(
            "Paste your essay instructions here...\n\n"
            "Example:\n"
            "Essay 1: Cultural Analysis\n"
            "Write a 2500-word essay analyzing the impact of postmodernism...\n"
            "Due: March 15th\n"
            "Requirements: 5+ academic sources, Harvard citation style"
        )
        layout.addWidget(self.instructions_input)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._process_essay)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _process_essay(self):
        """Process and save essay."""
        try:
            raw_instructions = self.instructions_input.toPlainText().strip()

            if not raw_instructions:
                QMessageBox.warning(self, "Error", "Please paste essay instructions")
                return

            course_name = self.course_input.text().strip()
            due_date = self.date_input.date().toPyDate()

            # Parse essay
            parser = EssayParser(self.user_id, self.db)

            # Show progress
            QMessageBox.information(self, "Processing", "Parsing essay instructions...\nThis may take a moment.")

            result = parser.parse(
                raw_instructions=raw_instructions,
                source_type='manual',
                canvas_assignment_id=None,
                course_name=course_name or None
            )

            if not result['success']:
                QMessageBox.critical(self, "Error", f"Failed to parse essay:\n{result.get('error')}")
                return

            # Update due date if provided
            essay_id = result['essay_id']
            if due_date:
                self.db.execute_query(
                    "UPDATE essays SET due_date = ? WHERE id = ?",
                    (due_date.isoformat(), essay_id)
                )

            QMessageBox.information(
                self,
                "Success",
                f"Essay '{result['title']}' added successfully!\n\n"
                f"Next: Click 'Generate Tasks' to create your task list."
            )

            self.accept()

        except Exception as e:
            logger.error(f"Failed to process essay: {e}")
            QMessageBox.critical(self, "Error", f"Error processing essay:\n{str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    db = DatabaseManager()
    view = EssayView("test_user", db)
    view.show()

    sys.exit(app.exec())
