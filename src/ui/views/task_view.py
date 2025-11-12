"""
Academic Command Center - Task View
List and manage tasks with priority sorting.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QComboBox,
    QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.task_manager.task_manager import TaskManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TaskView(QWidget):
    """Task list and management view."""

    def __init__(self, user_id: str, db_manager: DatabaseManager):
        """
        Initialize task view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager

        self.current_filter = 'all'  # all, research, writing
        self.current_status = 'pending'  # pending, completed

        self._init_ui()
        self.refresh()

    def _init_ui(self):
        """Initialize user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Tasks")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Filter dropdown
        filter_label = QLabel("Type:")
        header_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Tasks", "Research Tasks", "Writing Tasks"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.filter_combo)

        # Status dropdown
        status_label = QLabel("Status:")
        header_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pending", "Completed"])
        self.status_combo.currentIndexChanged.connect(self._on_status_changed)
        header_layout.addWidget(self.status_combo)

        main_layout.addLayout(header_layout)

        # Summary stats
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        main_layout.addWidget(self.stats_label)

        # Task list container (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.task_list_layout = QVBoxLayout(scroll_content)
        self.task_list_layout.setSpacing(10)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def refresh(self):
        """Refresh task list."""
        logger.info("Refreshing task list...")

        # Clear existing
        self._clear_layout(self.task_list_layout)

        # Build query based on filters
        query_parts = ["SELECT * FROM tasks WHERE user_id = ?"]
        params = [self.user_id]

        # Status filter
        if self.current_status == 'pending':
            query_parts.append("AND status = 'pending'")
        elif self.current_status == 'completed':
            query_parts.append("AND status = 'completed'")

        # Type filter
        if self.current_filter == 'research':
            query_parts.append("AND task_type = 'research'")
        elif self.current_filter == 'writing':
            query_parts.append("AND task_type = 'writing'")

        # Order by priority
        query_parts.append("ORDER BY priority_score DESC, created_at DESC")

        query = " ".join(query_parts)

        try:
            tasks = self.db.execute_query(query, tuple(params), fetch_all=True)

            if not tasks:
                no_data = QLabel("No tasks found")
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data.setStyleSheet("color: #95a5a6; font-size: 16px; font-style: italic; margin-top: 50px;")
                self.task_list_layout.addWidget(no_data)

                self.stats_label.setText("0 tasks")
                return

            # Update stats
            total_tasks = len(tasks)
            total_minutes = sum(t.get('estimated_minutes', 0) for t in tasks)
            total_hours = round(total_minutes / 60, 1)

            self.stats_label.setText(
                f"{total_tasks} tasks • {total_hours} hours estimated"
            )

            # Create task cards
            for task in tasks:
                task_card = self._create_task_card(task)
                self.task_list_layout.addWidget(task_card)

            # Stretch to push cards to top
            self.task_list_layout.addStretch()

        except Exception as e:
            logger.error(f"Failed to refresh tasks: {e}")
            error_label = QLabel(f"Error loading tasks: {str(e)}")
            error_label.setStyleSheet("color: #e74c3c;")
            self.task_list_layout.addWidget(error_label)

    def _create_task_card(self, task: dict) -> QFrame:
        """Create task card widget."""
        card = QFrame()

        # Priority-based styling
        priority = task.get('priority_score', 50)
        if priority >= 80:
            border_color = "#e74c3c"
            priority_label = "Critical"
            priority_bg = "#e74c3c"
        elif priority >= 65:
            border_color = "#f39c12"
            priority_label = "High"
            priority_bg = "#f39c12"
        elif priority >= 45:
            border_color = "#3498db"
            priority_label = "Medium"
            priority_bg = "#3498db"
        else:
            border_color = "#95a5a6"
            priority_label = "Low"
            priority_bg = "#95a5a6"

        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 5px solid {border_color};
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)

        # Top row: title and priority
        top_layout = QHBoxLayout()

        # Checkbox for completion
        checkbox = QCheckBox()
        checkbox.setChecked(task.get('status') == 'completed')
        checkbox.stateChanged.connect(lambda state: self._on_task_checked(task['id'], state))
        top_layout.addWidget(checkbox)

        # Title
        title_label = QLabel(task['title'])
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        if task.get('status') == 'completed':
            title_label.setStyleSheet("text-decoration: line-through; color: #95a5a6;")
        top_layout.addWidget(title_label, stretch=1)

        # Priority badge
        priority_badge = QLabel(priority_label)
        priority_badge.setStyleSheet(f"""
            background-color: {priority_bg};
            color: white;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        """)
        priority_badge.setFixedWidth(80)
        priority_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(priority_badge)

        layout.addLayout(top_layout)

        # Description
        if task.get('description'):
            desc_label = QLabel(task['description'])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-top: 5px;")
            layout.addWidget(desc_label)

        # Bottom row: metadata
        bottom_layout = QHBoxLayout()

        # Category badge
        category = task.get('task_category', 'unknown').replace('_', ' ').title()
        category_badge = QLabel(category)
        category_badge.setStyleSheet("""
            background-color: #ecf0f1;
            color: #34495e;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
        """)
        bottom_layout.addWidget(category_badge)

        # Time estimate
        minutes = task.get('estimated_minutes', 0)
        if minutes >= 60:
            time_text = f"⏱️ {minutes//60}h {minutes%60}m"
        else:
            time_text = f"⏱️ {minutes}m"

        time_label = QLabel(time_text)
        time_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        bottom_layout.addWidget(time_label)

        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

        return card

    def _on_task_checked(self, task_id: str, state: int):
        """Handle task checkbox state change."""
        try:
            if state == Qt.CheckState.Checked.value:
                # Mark as completed
                self.db.execute_query(
                    "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), task_id)
                )
                logger.info(f"Task {task_id} marked as completed")
            else:
                # Mark as pending
                self.db.execute_query(
                    "UPDATE tasks SET status = 'pending', completed_at = NULL WHERE id = ?",
                    (task_id,)
                )
                logger.info(f"Task {task_id} marked as pending")

            # Refresh view
            self.refresh()

        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update task:\n{str(e)}")

    def _on_filter_changed(self, index: int):
        """Handle filter dropdown change."""
        filters = ['all', 'research', 'writing']
        self.current_filter = filters[index]
        self.refresh()

    def _on_status_changed(self, index: int):
        """Handle status dropdown change."""
        statuses = ['pending', 'completed']
        self.current_status = statuses[index]
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
    from datetime import datetime
    import sys

    app = QApplication(sys.argv)

    db = DatabaseManager()
    view = TaskView("test_user", db)
    view.show()

    sys.exit(app.exec())
