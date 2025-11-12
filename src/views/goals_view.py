"""
Goals Management View - Phase 6 Sprint 4
SMART goal creation, tracking, and management interface.

Features:
- Create SMART goals
- Use goal templates
- Track progress
- View active and completed goals
- Update goal progress
- Delete goals

Author: Academic Command Center
Phase: 6 Sprint 4
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QDialog, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDateEdit, QDialogButtonBox, QMessageBox, QProgressBar,
    QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from typing import Optional
from datetime import datetime, timedelta
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database import DatabaseManager
from features.analytics.goal_system import GoalSystem

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CreateGoalDialog(QDialog):
    """Dialog for creating a new goal."""

    def __init__(self, goal_system: GoalSystem, parent=None):
        super().__init__(parent)
        self.goal_system = goal_system
        self._init_ui()

    def _init_ui(self):
        """Initialize dialog UI."""

        self.setWindowTitle("Create New Goal")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Goal Title:")
        layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Complete 4 focus sessions daily")
        layout.addWidget(self.title_input)

        # Description
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Describe your goal in detail...")
        layout.addWidget(self.description_input)

        # Goal type
        type_label = QLabel("Goal Type:")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "study_habit",
            "academic",
            "grade",
            "completion",
            "custom"
        ])
        layout.addWidget(self.type_combo)

        # Target value
        target_layout = QHBoxLayout()

        target_label = QLabel("Target:")
        target_layout.addWidget(target_label)

        self.target_input = QSpinBox()
        self.target_input.setMinimum(1)
        self.target_input.setMaximum(10000)
        self.target_input.setValue(10)
        target_layout.addWidget(self.target_input)

        # Unit
        unit_label = QLabel("Unit:")
        target_layout.addWidget(unit_label)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["hours", "sessions", "assignments", "percentage", "points"])
        target_layout.addWidget(self.unit_combo)

        layout.addLayout(target_layout)

        # Target date
        date_label = QLabel("Target Date:")
        layout.addWidget(date_label)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate().addDays(30))
        self.date_input.setMinimumDate(QDate.currentDate())
        layout.addWidget(self.date_input)

        # Category
        category_label = QLabel("Category:")
        layout.addWidget(category_label)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["short_term", "long_term", "habit"])
        layout.addWidget(self.category_combo)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._create_goal)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _create_goal(self):
        """Create the goal."""

        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        goal_type = self.type_combo.currentText()
        target_value = self.target_input.value()
        unit = self.unit_combo.currentText()
        target_date = self.date_input.date().toString("yyyy-MM-dd")
        category = self.category_combo.currentText()

        if not title:
            QMessageBox.warning(self, "Invalid Input", "Please enter a goal title")
            return

        if not description:
            QMessageBox.warning(self, "Invalid Input", "Please enter a description")
            return

        result = self.goal_system.create_goal(
            title=title,
            description=description,
            goal_type=goal_type,
            target_value=float(target_value),
            unit=unit,
            target_date=target_date,
            category=category
        )

        if result.get('success'):
            is_smart = result.get('is_smart', False)
            if is_smart:
                QMessageBox.information(
                    self,
                    "Goal Created",
                    f"SMART goal created successfully!\n\nGoal ID: {result['goal_id']}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Goal Created (Not SMART)",
                    "Goal created, but it doesn't meet all SMART criteria.\n"
                    "Consider making it more Specific, Measurable, Achievable, Relevant, and Time-bound."
                )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create goal:\n{result.get('error', 'Unknown error')}"
            )


class TemplateGoalDialog(QDialog):
    """Dialog for creating goal from template."""

    def __init__(self, goal_system: GoalSystem, parent=None):
        super().__init__(parent)
        self.goal_system = goal_system
        self._init_ui()

    def _init_ui(self):
        """Initialize dialog UI."""

        self.setWindowTitle("Create Goal from Template")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()

        # Template selector
        template_label = QLabel("Select Template:")
        layout.addWidget(template_label)

        self.template_combo = QComboBox()
        templates = self.goal_system.get_templates()
        if templates.get('success'):
            for template in templates['templates']:
                self.template_combo.addItem(
                    f"{template['name']} ({template['suggested_target']} {template['unit']})",
                    template
                )
        layout.addWidget(self.template_combo)

        # Template description
        self.template_desc = QLabel()
        self.template_desc.setWordWrap(True)
        self.template_desc.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(self.template_desc)

        # Custom target (optional)
        custom_label = QLabel("Custom Target (optional):")
        layout.addWidget(custom_label)

        self.custom_target = QSpinBox()
        self.custom_target.setMinimum(1)
        self.custom_target.setMaximum(10000)
        self.custom_target.setSpecialValueText("Use suggested value")
        self.custom_target.setValue(0)
        layout.addWidget(self.custom_target)

        # Custom duration (optional)
        duration_label = QLabel("Duration (days, optional):")
        layout.addWidget(duration_label)

        self.custom_duration = QSpinBox()
        self.custom_duration.setMinimum(1)
        self.custom_duration.setMaximum(365)
        self.custom_duration.setSpecialValueText("Use suggested duration")
        self.custom_duration.setValue(0)
        layout.addWidget(self.custom_duration)

        # Update description when template changes
        self.template_combo.currentIndexChanged.connect(self._update_description)
        self._update_description()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._create_from_template)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _update_description(self):
        """Update template description."""

        template = self.template_combo.currentData()
        if template:
            self.template_desc.setText(
                f"{template['description']}\n"
                f"Suggested: {template['suggested_target']} {template['unit']} "
                f"in {template['duration_days']} days"
            )

    def _create_from_template(self):
        """Create goal from selected template."""

        template = self.template_combo.currentData()
        if not template:
            return

        target_value = self.custom_target.value() if self.custom_target.value() > 0 else None
        duration = self.custom_duration.value() if self.custom_duration.value() > 0 else None

        result = self.goal_system.create_from_template(
            template_name=template['name'],
            target_value=target_value,
            custom_duration=duration
        )

        if result.get('success'):
            QMessageBox.information(
                self,
                "Goal Created",
                f"Goal created from template!\n\nGoal ID: {result['goal_id']}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create goal:\n{result.get('error', 'Unknown error')}"
            )


class GoalsView(QWidget):
    """
    Goals Management View - Create and track SMART goals.
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Goals View.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize goal system
        self.goal_system = GoalSystem(user_id, self.db)

        self._init_ui()
        self._load_goals()

    def _init_ui(self):
        """Initialize user interface."""

        layout = QVBoxLayout()

        # Title and actions
        header_layout = QHBoxLayout()

        title_label = QLabel("Goals")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Create goal button
        create_btn = QPushButton("Create Goal")
        create_btn.clicked.connect(self._show_create_dialog)
        create_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 8px 16px; }"
        )
        header_layout.addWidget(create_btn)

        # Template button
        template_btn = QPushButton("Use Template")
        template_btn.clicked.connect(self._show_template_dialog)
        template_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "font-weight: bold; padding: 8px 16px; }"
        )
        header_layout.addWidget(template_btn)

        layout.addLayout(header_layout)

        # Statistics
        stats_group = self._create_statistics_section()
        layout.addWidget(stats_group)

        # Tabs
        tabs = QTabWidget()

        # Active goals tab
        active_tab = self._create_active_goals_tab()
        tabs.addTab(active_tab, "Active Goals")

        # Completed goals tab
        completed_tab = self._create_completed_goals_tab()
        tabs.addTab(completed_tab, "Completed Goals")

        layout.addWidget(tabs)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_goals)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)

    def _create_statistics_section(self) -> QGroupBox:
        """Create goal statistics section."""

        group = QGroupBox("Goal Statistics")
        layout = QHBoxLayout()

        self.total_label = QLabel("Total: 0")
        self.completed_label = QLabel("Completed: 0")
        self.in_progress_label = QLabel("In Progress: 0")
        self.completion_rate_label = QLabel("Completion Rate: 0%")

        layout.addWidget(self.total_label)
        layout.addWidget(self.completed_label)
        layout.addWidget(self.in_progress_label)
        layout.addWidget(self.completion_rate_label)

        group.setLayout(layout)
        return group

    def _create_active_goals_tab(self) -> QWidget:
        """Create active goals tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        self.active_goals_list = QListWidget()
        self.active_goals_list.itemClicked.connect(self._show_goal_details)
        layout.addWidget(self.active_goals_list)

        # Actions
        actions_layout = QHBoxLayout()

        update_btn = QPushButton("Update Progress")
        update_btn.clicked.connect(self._update_goal_progress)
        actions_layout.addWidget(update_btn)

        delete_btn = QPushButton("Delete Goal")
        delete_btn.clicked.connect(self._delete_goal)
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        actions_layout.addWidget(delete_btn)

        layout.addLayout(actions_layout)

        widget.setLayout(layout)
        return widget

    def _create_completed_goals_tab(self) -> QWidget:
        """Create completed goals tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        self.completed_goals_list = QListWidget()
        layout.addWidget(self.completed_goals_list)

        widget.setLayout(layout)
        return widget

    def _load_goals(self):
        """Load goals data."""

        try:
            # Get statistics
            stats = self.goal_system.get_goal_statistics()
            if stats.get('success'):
                self.total_label.setText(f"Total: {stats['total']}")
                self.completed_label.setText(f"Completed: {stats['completed']}")
                self.in_progress_label.setText(f"In Progress: {stats['in_progress']}")
                self.completion_rate_label.setText(f"Completion Rate: {stats['completion_rate']:.0f}%")

            # Load active goals
            self._load_active_goals()

            # Load completed goals
            self._load_completed_goals()

        except Exception as e:
            logger.error(f"Failed to load goals: {e}")

    def _load_active_goals(self):
        """Load active goals."""

        try:
            self.active_goals_list.clear()

            goals_data = self.goal_system.get_active_goals()
            if goals_data.get('success'):
                goals = goals_data['goals']

                for goal in goals:
                    # Create list item
                    item_widget = QWidget()
                    item_layout = QVBoxLayout()

                    # Title
                    title_label = QLabel(goal['title'])
                    title_font = QFont()
                    title_font.setBold(True)
                    title_label.setFont(title_font)
                    item_layout.addWidget(title_label)

                    # Progress
                    progress_layout = QHBoxLayout()

                    progress_label = QLabel(f"{goal['current_value']}/{goal['target_value']} {goal['unit']}")
                    progress_layout.addWidget(progress_label)

                    progress_bar = QProgressBar()
                    progress_bar.setMaximum(100)
                    progress_bar.setValue(int(goal['progress_percentage']))
                    progress_bar.setTextVisible(True)
                    progress_bar.setFormat(f"{goal['progress_percentage']:.0f}%")
                    progress_layout.addWidget(progress_bar)

                    item_layout.addLayout(progress_layout)

                    # Deadline
                    deadline_label = QLabel(f"Deadline: {goal['target_date']}")
                    deadline_label.setStyleSheet("font-size: 10px; color: gray;")
                    item_layout.addWidget(deadline_label)

                    item_widget.setLayout(item_layout)

                    # Add to list
                    item = QListWidgetItem()
                    item.setSizeHint(item_widget.sizeHint())
                    item.setData(Qt.ItemDataRole.UserRole, goal)
                    self.active_goals_list.addItem(item)
                    self.active_goals_list.setItemWidget(item, item_widget)

                if not goals:
                    self.active_goals_list.addItem("No active goals. Create one to get started!")

        except Exception as e:
            logger.error(f"Failed to load active goals: {e}")

    def _load_completed_goals(self):
        """Load completed goals."""

        try:
            self.completed_goals_list.clear()

            goals_data = self.goal_system.get_completed_goals(30)
            if goals_data.get('success'):
                goals = goals_data['goals']

                for goal in goals:
                    item_text = f" {goal['title']} - Completed: {goal['updated_at'][:10]}"
                    item = QListWidgetItem(item_text)
                    item.setForeground(QColor("#4CAF50"))
                    self.completed_goals_list.addItem(item)

                if not goals:
                    self.completed_goals_list.addItem("No completed goals yet")

        except Exception as e:
            logger.error(f"Failed to load completed goals: {e}")

    def _show_create_dialog(self):
        """Show create goal dialog."""

        dialog = CreateGoalDialog(self.goal_system, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_goals()

    def _show_template_dialog(self):
        """Show template selection dialog."""

        dialog = TemplateGoalDialog(self.goal_system, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_goals()

    def _show_goal_details(self, item: QListWidgetItem):
        """Show goal details."""

        goal = item.data(Qt.ItemDataRole.UserRole)
        if goal:
            details = (
                f"Title: {goal['title']}\n"
                f"Description: {goal['description']}\n"
                f"Type: {goal['goal_type']}\n"
                f"Progress: {goal['current_value']}/{goal['target_value']} {goal['unit']}\n"
                f"Status: {goal['status']}\n"
                f"Target Date: {goal['target_date']}\n"
                f"Created: {goal['created_at'][:10]}"
            )

            QMessageBox.information(self, "Goal Details", details)

    def _update_goal_progress(self):
        """Update goal progress."""

        selected_items = self.active_goals_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a goal to update")
            return

        goal = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not goal:
            return

        # Simple dialog for progress update
        from PyQt6.QtWidgets import QInputDialog

        new_value, ok = QInputDialog.getDouble(
            self,
            "Update Progress",
            f"Current: {goal['current_value']}/{goal['target_value']} {goal['unit']}\n"
            f"Enter new value:",
            goal['current_value'],
            0,
            goal['target_value'] * 2,
            1
        )

        if ok:
            result = self.goal_system.update_goal_progress(goal['id'], new_value)
            if result.get('success'):
                QMessageBox.information(
                    self,
                    "Progress Updated",
                    f"Progress updated to {new_value}/{goal['target_value']}\n"
                    f"Completion: {result['progress_percentage']:.0f}%"
                )
                self._load_goals()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to update progress:\n{result.get('error', 'Unknown error')}"
                )

    def _delete_goal(self):
        """Delete selected goal."""

        selected_items = self.active_goals_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a goal to delete")
            return

        goal = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not goal:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this goal?\n\n{goal['title']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.goal_system.delete_goal(goal['id'])
            if result.get('success'):
                QMessageBox.information(self, "Goal Deleted", "Goal deleted successfully")
                self._load_goals()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete goal:\n{result.get('error', 'Unknown error')}"
                )


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = GoalsView(user_id="test_user")
    window.resize(800, 700)
    window.show()
    sys.exit(app.exec())
