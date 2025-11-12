"""
Academic Command Center - Dashboard View
Overview of all essays, tasks, and deadlines.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DashboardView(QWidget):
    """Dashboard showing overview statistics and upcoming tasks."""

    def __init__(self, user_id: str, db_manager: DatabaseManager):
        """
        Initialize dashboard view.

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

        # Page title
        title = QLabel("Dashboard")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Statistics cards
        stats_layout = QHBoxLayout()
        main_layout.addLayout(stats_layout)

        # Stat card containers
        self.stat_cards = {}
        stat_keys = [
            ('essays', 'Essays', '#3498db'),
            ('tasks', 'Pending Tasks', '#e74c3c'),
            ('materials', 'Materials', '#2ecc71'),
            ('hours', 'Est. Hours', '#f39c12')
        ]

        for key, label, color in stat_keys:
            card = self._create_stat_card(label, "0", color)
            self.stat_cards[key] = card
            stats_layout.addWidget(card)

        # Upcoming deadlines section
        deadlines_section = self._create_section("Upcoming Deadlines")
        main_layout.addWidget(deadlines_section)
        self.deadlines_container = deadlines_section.findChild(QVBoxLayout)

        # High priority tasks section
        priority_section = self._create_section("High Priority Tasks")
        main_layout.addWidget(priority_section)
        self.priority_container = priority_section.findChild(QVBoxLayout)

        # Stretch to push everything to top
        main_layout.addStretch()

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """
        Create a statistics card.

        Args:
            title: Card title
            value: Card value
            color: Background color

        Returns:
            Card widget
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 20px;
            }}
            QLabel {{
                color: white;
            }}
        """)
        card.setFixedHeight(120)

        layout = QVBoxLayout(card)

        # Value label (large)
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        # Title label
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Store references for updating
        card.value_label = value_label
        card.title_label = title_label

        return card

    def _create_section(self, title: str) -> QFrame:
        """
        Create a section with title.

        Args:
            title: Section title

        Returns:
            Section widget
        """
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #dcdcdc;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Content container (to be filled)
        content_layout = QVBoxLayout()
        layout.addLayout(content_layout)

        return section

    def refresh(self):
        """Refresh dashboard data."""
        logger.info("Refreshing dashboard...")

        # Update statistics
        self._update_statistics()

        # Update deadlines
        self._update_deadlines()

        # Update priority tasks
        self._update_priority_tasks()

    def _update_statistics(self):
        """Update statistics cards."""
        try:
            # Count essays
            essay_count = self.db.execute_query(
                "SELECT COUNT(*) as count FROM essays WHERE user_id = ?",
                (self.user_id,),
                fetch_one=True
            )
            essays = essay_count['count'] if essay_count else 0

            # Count pending tasks
            task_count = self.db.execute_query(
                "SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND status = 'pending'",
                (self.user_id,),
                fetch_one=True
            )
            tasks = task_count['count'] if task_count else 0

            # Count materials
            material_count = self.db.execute_query(
                "SELECT COUNT(*) as count FROM materials WHERE user_id = ?",
                (self.user_id,),
                fetch_one=True
            )
            materials = material_count['count'] if material_count else 0

            # Calculate estimated hours
            time_sum = self.db.execute_query(
                "SELECT SUM(estimated_minutes) as total FROM tasks WHERE user_id = ? AND status = 'pending'",
                (self.user_id,),
                fetch_one=True
            )
            total_minutes = time_sum['total'] if time_sum and time_sum['total'] else 0
            hours = round(total_minutes / 60, 1)

            # Update cards
            self.stat_cards['essays'].value_label.setText(str(essays))
            self.stat_cards['tasks'].value_label.setText(str(tasks))
            self.stat_cards['materials'].value_label.setText(str(materials))
            self.stat_cards['hours'].value_label.setText(str(hours))

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")

    def _update_deadlines(self):
        """Update upcoming deadlines list."""
        try:
            # Clear existing
            self._clear_layout(self.deadlines_container)

            # Get essays with deadlines in next 14 days
            now = datetime.now()
            two_weeks = now + timedelta(days=14)

            query = """
            SELECT id, title, course_name, due_date
            FROM essays
            WHERE user_id = ? AND due_date IS NOT NULL
            AND due_date BETWEEN ? AND ?
            ORDER BY due_date ASC
            LIMIT 5
            """

            essays = self.db.execute_query(
                query,
                (self.user_id, now.isoformat(), two_weeks.isoformat()),
                fetch_all=True
            )

            if not essays:
                no_data = QLabel("No upcoming deadlines in the next 2 weeks")
                no_data.setStyleSheet("color: #95a5a6; font-style: italic;")
                self.deadlines_container.addWidget(no_data)
                return

            for essay in essays:
                deadline_widget = self._create_deadline_item(essay)
                self.deadlines_container.addWidget(deadline_widget)

        except Exception as e:
            logger.error(f"Failed to update deadlines: {e}")

    def _create_deadline_item(self, essay: dict) -> QWidget:
        """Create deadline item widget."""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-left: 4px solid #e74c3c;
                padding: 10px;
                margin: 5px 0;
            }
        """)

        layout = QHBoxLayout(item)

        # Essay info
        info_layout = QVBoxLayout()

        title_label = QLabel(essay['title'])
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(title_label)

        if essay.get('course_name'):
            course_label = QLabel(essay['course_name'])
            course_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            info_layout.addWidget(course_label)

        layout.addLayout(info_layout, stretch=1)

        # Due date
        try:
            due_date = datetime.fromisoformat(essay['due_date'])
            days_until = (due_date - datetime.now()).days

            date_label = QLabel(due_date.strftime("%b %d, %Y"))
            date_label.setFont(QFont("Arial", 11))
            layout.addWidget(date_label)

            # Days until badge
            if days_until <= 3:
                badge_color = "#e74c3c"
                badge_text = f"{days_until}d"
            elif days_until <= 7:
                badge_color = "#f39c12"
                badge_text = f"{days_until}d"
            else:
                badge_color = "#3498db"
                badge_text = f"{days_until}d"

            badge = QLabel(badge_text)
            badge.setStyleSheet(f"""
                background-color: {badge_color};
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            """)
            badge.setFixedWidth(50)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(badge)

        except Exception as e:
            logger.warning(f"Failed to parse due date: {e}")

        return item

    def _update_priority_tasks(self):
        """Update high priority tasks list."""
        try:
            # Clear existing
            self._clear_layout(self.priority_container)

            # Get high priority tasks
            query = """
            SELECT id, title, task_category, priority_score, estimated_minutes
            FROM tasks
            WHERE user_id = ? AND status = 'pending'
            AND priority_score >= 70
            ORDER BY priority_score DESC
            LIMIT 5
            """

            tasks = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_all=True
            )

            if not tasks:
                no_data = QLabel("No high priority tasks")
                no_data.setStyleSheet("color: #95a5a6; font-style: italic;")
                self.priority_container.addWidget(no_data)
                return

            for task in tasks:
                task_widget = self._create_task_item(task)
                self.priority_container.addWidget(task_widget)

        except Exception as e:
            logger.error(f"Failed to update priority tasks: {e}")

    def _create_task_item(self, task: dict) -> QWidget:
        """Create task item widget."""
        item = QFrame()

        # Color based on priority
        priority = task.get('priority_score', 50)
        if priority >= 80:
            border_color = "#e74c3c"
        elif priority >= 65:
            border_color = "#f39c12"
        else:
            border_color = "#3498db"

        item.setStyleSheet(f"""
            QFrame {{
                background-color: #f8f9fa;
                border-left: 4px solid {border_color};
                padding: 10px;
                margin: 5px 0;
            }}
        """)

        layout = QHBoxLayout(item)

        # Task info
        info_layout = QVBoxLayout()

        title_label = QLabel(task['title'])
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(title_label)

        category_label = QLabel(task['task_category'].replace('_', ' ').title())
        category_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        info_layout.addWidget(category_label)

        layout.addLayout(info_layout, stretch=1)

        # Time estimate
        minutes = task.get('estimated_minutes', 0)
        if minutes >= 60:
            time_text = f"{minutes//60}h {minutes%60}m"
        else:
            time_text = f"{minutes}m"

        time_label = QLabel(time_text)
        time_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(time_label)

        return item

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
    view = DashboardView("test_user", db)
    view.show()

    sys.exit(app.exec())
