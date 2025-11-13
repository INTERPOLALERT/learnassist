"""
Assignments View - Phase 2 Sprint 1
Complete assignment tracking interface with Canvas sync
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QScrollArea, QFrame, QDialog,
    QTextEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
    QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from features.assignments.assignment_manager import AssignmentManager

logger = logging.getLogger(__name__)


class AssignmentsView(QWidget):
    """
    Assignments tracking view.

    Displays all assignments with filtering, search, and Canvas sync.
    """

    assignment_updated = pyqtSignal()  # Signal when assignment changes

    def __init__(self, user_id: str, db_manager):
        """
        Initialize Assignments View.

        Args:
            user_id: Current user ID
            db_manager: DatabaseManager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager
        self.assignment_manager = AssignmentManager(db_manager, user_id)

        # Current filters
        self.current_status_filter = "all"
        self.current_subject_filter = None
        self.current_search = ""

        self._init_ui()
        self._load_assignments()

        logger.info(f"Assignments View initialized for user {user_id}")

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📚 Assignments")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Action buttons
        self.new_btn = QPushButton("➕ New Assignment")
        self.new_btn.clicked.connect(self._show_create_dialog)
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        header_layout.addWidget(self.new_btn)

        self.sync_btn = QPushButton("🔄 Sync Canvas")
        self.sync_btn.clicked.connect(self._sync_canvas)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(self.sync_btn)

        layout.addLayout(header_layout)

        # Statistics bar
        self.stats_widget = self._create_statistics_widget()
        layout.addWidget(self.stats_widget)

        # Filters and search
        filter_layout = QHBoxLayout()

        # Status filter
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "All", "Pending", "In Progress", "Completed", "Overdue"
        ])
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.status_combo)

        # Subject filter
        self.subject_combo = QComboBox()
        self.subject_combo.addItem("All Subjects")
        self._load_subjects()
        self.subject_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.subject_combo)

        # Priority filter
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["All Priorities", "High", "Medium", "Low"])
        self.priority_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.priority_combo)

        filter_layout.addStretch()

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search assignments...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setMinimumWidth(250)
        filter_layout.addWidget(self.search_input)

        layout.addLayout(filter_layout)

        # Assignments list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.assignments_container = QWidget()
        self.assignments_layout = QVBoxLayout(self.assignments_container)
        self.assignments_layout.setSpacing(10)
        self.assignments_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.assignments_container)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def _create_statistics_widget(self) -> QWidget:
        """Create statistics bar widget."""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.StyledPanel)
        widget.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QHBoxLayout(widget)

        self.total_label = QLabel("Total: 0")
        self.pending_label = QLabel("Pending: 0")
        self.completed_label = QLabel("Completed: 0")
        self.overdue_label = QLabel("Overdue: 0")
        self.gpa_label = QLabel("GPA: 0.0")

        for label in [self.total_label, self.pending_label, self.completed_label,
                     self.overdue_label, self.gpa_label]:
            label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            layout.addWidget(label)
            layout.addStretch()

        return widget

    def _load_subjects(self):
        """Load subjects for filter dropdown."""
        try:
            query = """
                SELECT id, name, color
                FROM subjects
                WHERE user_id = ? AND is_active = 1
                ORDER BY name
            """
            subjects = self.db.fetch_all(query, (self.user_id,))

            for subject in subjects:
                self.subject_combo.addItem(subject[1], subject[0])  # name, id

        except Exception as e:
            logger.error(f"Failed to load subjects: {e}")

    def _load_assignments(self):
        """Load and display assignments based on current filters."""
        try:
            # Clear existing assignments
            while self.assignments_layout.count():
                item = self.assignments_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get filter values
            status_filter = None
            if self.current_status_filter != "all":
                status_map = {
                    "pending": "pending",
                    "in progress": "in_progress",
                    "completed": "completed",
                    "overdue": None  # Handle separately
                }
                status_filter = status_map.get(self.current_status_filter.lower())

            overdue_only = self.current_status_filter.lower() == "overdue"

            # Get assignments
            assignments = self.assignment_manager.get_assignments(
                status=status_filter,
                subject_id=self.current_subject_filter,
                overdue_only=overdue_only,
                search_term=self.current_search if self.current_search else None
            )

            # Display assignments
            if assignments:
                for assignment in assignments:
                    card = self._create_assignment_card(assignment)
                    self.assignments_layout.addWidget(card)
            else:
                empty_label = QLabel("No assignments found")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet("color: #7f8c8d; font-size: 16px; padding: 40px;")
                self.assignments_layout.addWidget(empty_label)

            self.assignments_layout.addStretch()

            # Update statistics
            self._update_statistics()

            logger.debug(f"Loaded {len(assignments)} assignments")

        except Exception as e:
            logger.error(f"Failed to load assignments: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load assignments: {str(e)}")

    def _create_assignment_card(self, assignment: Dict[str, Any]) -> QWidget:
        """
        Create an assignment card widget.

        Args:
            assignment: Assignment data dictionary

        Returns:
            QWidget containing the assignment card
        """
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)

        # Color based on priority and status
        if assignment.get('is_overdue'):
            border_color = "#e74c3c"  # Red for overdue
        elif assignment.get('status') == 'completed':
            border_color = "#27ae60"  # Green for completed
        else:
            border_color = assignment.get('priority_color', '#3498db')

        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 5px solid {border_color};
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame:hover {{
                background-color: #f8f9fa;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # Top row: Title, type, priority
        top_layout = QHBoxLayout()

        # Subject color dot
        if assignment.get('subject_color'):
            color_dot = QLabel("●")
            color_dot.setStyleSheet(f"color: {assignment['subject_color']}; font-size: 20px;")
            top_layout.addWidget(color_dot)

        # Title
        title = QLabel(assignment.get('title', 'Untitled'))
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setWordWrap(True)
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Type badge
        type_badge = QLabel(assignment.get('assignment_type', 'homework').upper())
        type_badge.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        top_layout.addWidget(type_badge)

        # Priority badge
        priority = assignment.get('priority', 'medium').upper()
        priority_colors = {'HIGH': '#e74c3c', 'MEDIUM': '#f39c12', 'LOW': '#95a5a6'}
        priority_badge = QLabel(priority)
        priority_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {priority_colors.get(priority, '#f39c12')};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        top_layout.addWidget(priority_badge)

        layout.addLayout(top_layout)

        # Subject name
        if assignment.get('subject_name'):
            subject_label = QLabel(f"📚 {assignment['subject_name']}")
            subject_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            layout.addWidget(subject_label)

        # Description (if any)
        if assignment.get('description'):
            desc = QLabel(assignment['description'][:100] + "..." if len(assignment.get('description', '')) > 100 else assignment['description'])
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #34495e; font-size: 12px; margin-top: 5px;")
            layout.addWidget(desc)

        # Due date and status row
        info_layout = QHBoxLayout()

        # Due date with icon
        due_icon = "🔴" if assignment.get('is_overdue') else "🟡" if assignment.get('days_until_due', 999) < 3 else "🟢"
        due_text = f"{due_icon} {assignment.get('time_remaining', 'No due date')}"
        if assignment.get('due_date'):
            due_date = datetime.fromisoformat(assignment['due_date'].replace('Z', '+00:00'))
            due_text += f" ({due_date.strftime('%b %d, %Y')})"

        due_label = QLabel(due_text)
        due_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        info_layout.addWidget(due_label)

        info_layout.addStretch()

        # Grade (if recorded)
        if assignment.get('grade') is not None:
            grade_text = f"Grade: {assignment['grade']}/{assignment.get('max_grade', 100)} ({assignment.get('grade_letter', 'N/A')})"
            grade_label = QLabel(grade_text)
            grade_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")
            info_layout.addWidget(grade_label)
        elif assignment.get('status') == 'completed':
            not_graded = QLabel("Not graded yet")
            not_graded.setStyleSheet("color: #95a5a6; font-size: 12px;")
            info_layout.addWidget(not_graded)

        layout.addLayout(info_layout)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)

        if assignment.get('status') != 'completed':
            complete_btn = QPushButton("✓ Complete")
            complete_btn.clicked.connect(lambda: self._mark_completed(assignment['id']))
            complete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            buttons_layout.addWidget(complete_btn)

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(lambda: self._show_edit_dialog(assignment))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(lambda: self._delete_assignment(assignment['id']))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return card

    def _update_statistics(self):
        """Update statistics display."""
        try:
            stats = self.assignment_manager.get_statistics()

            self.total_label.setText(f"Total: {stats.get('total', 0)}")
            self.pending_label.setText(f"Pending: {stats.get('pending', 0)}")
            self.completed_label.setText(f"Completed: {stats.get('completed', 0)}")

            overdue = stats.get('overdue', 0)
            self.overdue_label.setText(f"Overdue: {overdue}")
            if overdue > 0:
                self.overdue_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                self.overdue_label.setStyleSheet("color: #27ae60; font-weight: bold;")

            gpa = stats.get('gpa', 0.0)
            self.gpa_label.setText(f"GPA: {gpa:.2f}")
            if gpa >= 3.5:
                self.gpa_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            elif gpa >= 3.0:
                self.gpa_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            else:
                self.gpa_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")

    def _on_filter_changed(self):
        """Handle filter change."""
        # Update current filters
        status_text = self.status_combo.currentText().lower()
        self.current_status_filter = status_text

        subject_index = self.subject_combo.currentIndex()
        if subject_index > 0:  # Not "All Subjects"
            self.current_subject_filter = self.subject_combo.currentData()
        else:
            self.current_subject_filter = None

        self._load_assignments()

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self.current_search = text
        self._load_assignments()

    def _show_create_dialog(self):
        """Show create assignment dialog."""
        dialog = AssignmentDialog(self, self.db, self.user_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            assignment_id = self.assignment_manager.create_assignment(data)

            if assignment_id:
                QMessageBox.information(self, "Success", "Assignment created successfully!")
                self._load_assignments()
                self.assignment_updated.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to create assignment")

    def _show_edit_dialog(self, assignment: Dict[str, Any]):
        """Show edit assignment dialog."""
        dialog = AssignmentDialog(self, self.db, self.user_id, assignment)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            if self.assignment_manager.update_assignment(assignment['id'], data):
                QMessageBox.information(self, "Success", "Assignment updated successfully!")
                self._load_assignments()
                self.assignment_updated.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to update assignment")

    def _mark_completed(self, assignment_id: str):
        """Mark assignment as completed."""
        # Ask for grade (optional)
        reply = QMessageBox.question(
            self,
            "Complete Assignment",
            "Do you want to record a grade?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        grade = None
        if reply == QMessageBox.StandardButton.Yes:
            from PyQt6.QtWidgets import QInputDialog
            grade_value, ok = QInputDialog.getDouble(
                self,
                "Enter Grade",
                "Grade:",
                0.0, 0.0, 100.0, 1
            )
            if ok:
                grade = grade_value

        if self.assignment_manager.mark_completed(assignment_id, grade):
            QMessageBox.information(self, "Success", "Assignment marked as completed!")
            self._load_assignments()
            self.assignment_updated.emit()
        else:
            QMessageBox.critical(self, "Error", "Failed to mark assignment as completed")

    def _delete_assignment(self, assignment_id: str):
        """Delete an assignment."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this assignment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.assignment_manager.delete_assignment(assignment_id):
                QMessageBox.information(self, "Success", "Assignment deleted!")
                self._load_assignments()
                self.assignment_updated.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete assignment")

    def _sync_canvas(self):
        """Sync assignments from Canvas LMS."""
        # TODO: Implement Canvas sync
        QMessageBox.information(
            self,
            "Canvas Sync",
            "Canvas sync will be implemented soon!\n\n"
            "This will import all your Canvas assignments automatically."
        )


class AssignmentDialog(QDialog):
    """
    Dialog for creating/editing assignments.
    """

    def __init__(self, parent, db_manager, user_id: str, assignment: Optional[Dict[str, Any]] = None):
        """
        Initialize assignment dialog.

        Args:
            parent: Parent widget
            db_manager: DatabaseManager instance
            user_id: Current user ID
            assignment: Existing assignment data (None for create)
        """
        super().__init__(parent)

        self.db = db_manager
        self.user_id = user_id
        self.assignment = assignment
        self.is_edit = assignment is not None

        self.setWindowTitle("Edit Assignment" if self.is_edit else "New Assignment")
        self.setMinimumWidth(600)
        self.setMinimumHeight(650)

        self._init_ui()
        if self.is_edit:
            self._populate_fields()

    def _init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Title *")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter assignment title...")
        layout.addWidget(self.title_input)

        # Description
        desc_label = QLabel("Description")
        desc_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter assignment description...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)

        # Row 1: Type, Priority, Subject
        row1 = QHBoxLayout()

        # Type
        type_group = QVBoxLayout()
        type_label = QLabel("Type *")
        type_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        type_group.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Homework", "Quiz", "Exam", "Project", "Lab", "Other"])
        type_group.addWidget(self.type_combo)
        row1.addLayout(type_group)

        # Priority
        priority_group = QVBoxLayout()
        priority_label = QLabel("Priority *")
        priority_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        priority_group.addWidget(priority_label)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.priority_combo.setCurrentText("Medium")
        priority_group.addWidget(self.priority_combo)
        row1.addLayout(priority_group)

        # Subject
        subject_group = QVBoxLayout()
        subject_label = QLabel("Subject")
        subject_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        subject_group.addWidget(subject_label)

        self.subject_combo = QComboBox()
        self.subject_combo.addItem("No Subject", None)
        self._load_subjects()
        subject_group.addWidget(self.subject_combo)
        row1.addLayout(subject_group)

        layout.addLayout(row1)

        # Row 2: Due Date, Status
        row2 = QHBoxLayout()

        # Due Date
        due_group = QVBoxLayout()
        due_label = QLabel("Due Date")
        due_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        due_group.addWidget(due_label)

        self.due_date_input = QDateTimeEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDateTime(QDateTime.currentDateTime().addDays(7))
        due_group.addWidget(self.due_date_input)

        self.no_due_date_check = QCheckBox("No due date")
        self.no_due_date_check.stateChanged.connect(self._toggle_due_date)
        due_group.addWidget(self.no_due_date_check)

        row2.addLayout(due_group)

        # Status
        status_group = QVBoxLayout()
        status_label = QLabel("Status *")
        status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_group.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pending", "In Progress", "Completed", "Submitted"])
        status_group.addWidget(self.status_combo)
        row2.addLayout(status_group)

        layout.addLayout(row2)

        # Grading section
        grade_group = QGroupBox("Grading")
        grade_layout = QHBoxLayout()

        grade_label = QLabel("Grade:")
        grade_layout.addWidget(grade_label)

        self.grade_input = QDoubleSpinBox()
        self.grade_input.setRange(0, 999)
        self.grade_input.setValue(0)
        self.grade_input.setSpecialValueText("Not graded")
        grade_layout.addWidget(self.grade_input)

        max_label = QLabel("out of:")
        grade_layout.addWidget(max_label)

        self.max_grade_input = QDoubleSpinBox()
        self.max_grade_input.setRange(1, 999)
        self.max_grade_input.setValue(100)
        grade_layout.addWidget(self.max_grade_input)

        grade_layout.addStretch()
        grade_group.setLayout(grade_layout)
        layout.addWidget(grade_group)

        # Notes
        notes_label = QLabel("Notes")
        notes_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(notes_label)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Add any additional notes...")
        self.notes_input.setMaximumHeight(80)
        layout.addWidget(self.notes_input)

        layout.addStretch()

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if self.is_edit else "Create")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def _load_subjects(self):
        """Load subjects for dropdown."""
        try:
            query = """
                SELECT id, name
                FROM subjects
                WHERE user_id = ? AND is_active = 1
                ORDER BY name
            """
            subjects = self.db.fetch_all(query, (self.user_id,))

            for subject in subjects:
                self.subject_combo.addItem(subject[1], subject[0])

        except Exception as e:
            logger.error(f"Failed to load subjects: {e}")

    def _toggle_due_date(self, state):
        """Toggle due date input."""
        self.due_date_input.setEnabled(not state)

    def _populate_fields(self):
        """Populate fields with existing assignment data."""
        if not self.assignment:
            return

        self.title_input.setText(self.assignment.get('title', ''))
        self.description_input.setPlainText(self.assignment.get('description', ''))

        # Type
        type_value = self.assignment.get('assignment_type', 'homework').capitalize()
        index = self.type_combo.findText(type_value, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        # Priority
        priority = self.assignment.get('priority', 'medium').capitalize()
        index = self.priority_combo.findText(priority, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)

        # Subject
        if self.assignment.get('subject_id'):
            index = self.subject_combo.findData(self.assignment['subject_id'])
            if index >= 0:
                self.subject_combo.setCurrentIndex(index)

        # Due date
        if self.assignment.get('due_date'):
            due_dt = QDateTime.fromString(self.assignment['due_date'], Qt.DateFormat.ISODate)
            self.due_date_input.setDateTime(due_dt)
        else:
            self.no_due_date_check.setChecked(True)

        # Status
        status = self.assignment.get('status', 'pending')
        status_map = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'submitted': 'Submitted'
        }
        status_text = status_map.get(status, 'Pending')
        index = self.status_combo.findText(status_text, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        # Grade
        if self.assignment.get('grade') is not None:
            self.grade_input.setValue(self.assignment['grade'])

        if self.assignment.get('max_grade'):
            self.max_grade_input.setValue(self.assignment['max_grade'])

        # Notes
        self.notes_input.setPlainText(self.assignment.get('notes', ''))

    def get_data(self) -> Dict[str, Any]:
        """
        Get form data as dictionary.

        Returns:
            Dictionary of assignment data
        """
        data = {
            'title': self.title_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'assignment_type': self.type_combo.currentText().lower(),
            'priority': self.priority_combo.currentText().lower(),
            'status': self.status_combo.currentText().lower().replace(' ', '_'),
            'max_grade': self.max_grade_input.value(),
            'notes': self.notes_input.toPlainText().strip()
        }

        # Subject
        subject_id = self.subject_combo.currentData()
        if subject_id:
            data['subject_id'] = subject_id

        # Due date
        if not self.no_due_date_check.isChecked():
            data['due_date'] = self.due_date_input.dateTime().toString(Qt.DateFormat.ISODate)

        # Grade (only if not 0)
        if self.grade_input.value() > 0:
            data['grade'] = self.grade_input.value()

        return data
