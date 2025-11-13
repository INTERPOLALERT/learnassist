"""
Calendar View - Phase 5 Sprint 1
Visual calendar showing assignments, sessions, and goals
"""
import logging
from datetime import datetime, timedelta
from calendar import monthrange, month_name, day_name
from typing import List, Dict, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGridLayout, QScrollArea, QFrame, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor

from features.calendar.calendar_manager import CalendarManager

logger = logging.getLogger(__name__)


class CalendarView(QWidget):
    """Calendar View - Visual calendar with events."""

    date_selected = pyqtSignal(QDate)

    def __init__(self, user_id: str, db_manager):
        """
        Initialize Calendar View.

        Args:
            user_id: Current user ID
            db_manager: DatabaseManager instance
        """
        super().__init__()
        self.user_id = user_id
        self.db = db_manager
        self.calendar_manager = CalendarManager(db_manager, user_id)

        # State
        self.current_date = datetime.now()
        self.selected_date = datetime.now()
        self.events_by_day = {}

        self._init_ui()
        self._load_month()

        logger.info("Calendar View initialized")

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Navigation bar
        nav_bar = self._create_navigation()
        layout.addWidget(nav_bar)

        # Statistics bar
        self.stats_widget = self._create_statistics_widget()
        layout.addWidget(self.stats_widget)

        # Main content (splitter with calendar and event details)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # Left: Calendar grid
        self.calendar_widget = self._create_calendar_grid()
        splitter.addWidget(self.calendar_widget)

        # Right: Event details for selected day
        self.details_widget = self._create_details_panel()
        splitter.addWidget(self.details_widget)

        # Set initial sizes (65% calendar, 35% details)
        splitter.setSizes([650, 350])

        layout.addWidget(splitter, 1)

    def _create_header(self) -> QWidget:
        """Create header with title."""
        header = QFrame()
        header.setStyleSheet("background: #2c3e50; border-radius: 8px; padding: 15px;")

        layout = QHBoxLayout(header)

        # Title
        title = QLabel("📅 Calendar")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Today button
        today_btn = QPushButton("Today")
        today_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        today_btn.clicked.connect(self._go_to_today)
        layout.addWidget(today_btn)

        return header

    def _create_navigation(self) -> QWidget:
        """Create month navigation bar."""
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background: #ecf0f1; border-radius: 6px; padding: 10px;")

        layout = QHBoxLayout(nav_frame)

        # Previous month button
        prev_btn = QPushButton("◀ Previous")
        prev_btn.setStyleSheet("""
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
        prev_btn.clicked.connect(self._previous_month)
        layout.addWidget(prev_btn)

        layout.addStretch()

        # Current month/year display
        self.month_label = QLabel()
        self.month_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.month_label)

        layout.addStretch()

        # Next month button
        next_btn = QPushButton("Next ▶")
        next_btn.setStyleSheet("""
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
        next_btn.clicked.connect(self._next_month)
        layout.addWidget(next_btn)

        return nav_frame

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

        self.assignments_label = QLabel("Assignments: 0")
        layout.addWidget(self.assignments_label)

        layout.addWidget(QLabel("|"))

        self.sessions_label = QLabel("Sessions: 0")
        layout.addWidget(self.sessions_label)

        layout.addWidget(QLabel("|"))

        self.goals_label = QLabel("Goals: 0")
        layout.addWidget(self.goals_label)

        layout.addWidget(QLabel("|"))

        self.overdue_label = QLabel("Overdue: 0")
        layout.addWidget(self.overdue_label)

        layout.addStretch()

        return stats_frame

    def _create_calendar_grid(self) -> QWidget:
        """Create calendar grid container."""
        container = QWidget()
        self.calendar_layout = QVBoxLayout(container)
        self.calendar_layout.setContentsMargins(0, 0, 0, 0)
        self.calendar_layout.setSpacing(10)

        return container

    def _create_details_panel(self) -> QWidget:
        """Create event details panel."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header
        self.details_header = QLabel("Select a date")
        self.details_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 6px;
        """)
        layout.addWidget(self.details_header)

        # Scroll area for events
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: #ecf0f1;
            }
        """)

        # Container for event cards
        self.events_container = QWidget()
        self.events_layout = QVBoxLayout(self.events_container)
        self.events_layout.setContentsMargins(10, 10, 10, 10)
        self.events_layout.setSpacing(10)
        self.events_layout.addStretch()

        scroll.setWidget(self.events_container)
        layout.addWidget(scroll)

        return container

    def _load_month(self):
        """Load and display the current month."""
        try:
            # Get events for month
            self.events_by_day = self.calendar_manager.get_events_for_month(
                self.current_date.year,
                self.current_date.month
            )

            # Update month label
            month_str = month_name[self.current_date.month]
            self.month_label.setText(f"{month_str} {self.current_date.year}")

            # Rebuild calendar grid
            self._build_calendar_grid()

            # Update statistics
            self._update_statistics()

            # Update selected day details
            self._update_day_details()

            logger.debug(f"Loaded calendar for {month_str} {self.current_date.year}")

        except Exception as e:
            logger.error(f"Failed to load month: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load calendar: {e}")

    def _build_calendar_grid(self):
        """Build the calendar grid for current month."""
        # Clear existing grid
        while self.calendar_layout.count():
            item = self.calendar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create grid
        grid_frame = QFrame()
        grid_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
            }
        """)

        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(1)
        grid_layout.setContentsMargins(1, 1, 1, 1)

        # Day headers (Sun-Sat)
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for col, day_name in enumerate(day_names):
            header = QLabel(day_name)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setStyleSheet("""
                QLabel {
                    background: #34495e;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    border: 1px solid #2c3e50;
                }
            """)
            grid_layout.addWidget(header, 0, col)

        # Get calendar data
        year = self.current_date.year
        month = self.current_date.month
        first_day_weekday, days_in_month = monthrange(year, month)

        # Current day for highlighting
        today = datetime.now()
        is_current_month = (today.year == year and today.month == month)

        # Fill in days
        row = 1
        col = first_day_weekday  # Start at correct weekday

        for day in range(1, days_in_month + 1):
            day_cell = self._create_day_cell(day, is_current_month and day == today.day)
            grid_layout.addWidget(day_cell, row, col)

            col += 1
            if col > 6:  # Week complete
                col = 0
                row += 1

        # Fill remaining cells with empty
        while col <= 6:
            empty_cell = QLabel()
            empty_cell.setStyleSheet("background: #ecf0f1; min-height: 100px;")
            grid_layout.addWidget(empty_cell, row, col)
            col += 1

        self.calendar_layout.addWidget(grid_frame)

    def _create_day_cell(self, day: int, is_today: bool) -> QWidget:
        """Create a day cell in the calendar."""
        cell = QFrame()
        cell.setCursor(Qt.CursorShape.PointingHandCursor)

        # Check if this day is selected
        is_selected = (day == self.selected_date.day and
                      self.current_date.month == self.selected_date.month and
                      self.current_date.year == self.selected_date.year)

        # Base style
        if is_today:
            bg_color = "#3498db"
            text_color = "white"
            border = "2px solid #2980b9"
        elif is_selected:
            bg_color = "#e8f4f8"
            text_color = "#2c3e50"
            border = "2px solid #3498db"
        else:
            bg_color = "white"
            text_color = "#2c3e50"
            border = "1px solid #ecf0f1"

        cell.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border: {border};
                min-height: 100px;
            }}
            QFrame:hover {{
                background: #f8f9fa;
                border: 2px solid #3498db;
            }}
        """)

        layout = QVBoxLayout(cell)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Day number
        day_label = QLabel(str(day))
        day_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            color: {text_color};
        """)
        layout.addWidget(day_label)

        # Event indicators (show up to 3 events)
        if day in self.events_by_day:
            events = self.events_by_day[day][:3]
            for event in events:
                event_badge = QLabel(self._truncate_text(event['title'], 15))
                event_badge.setStyleSheet(f"""
                    background: {event['color']};
                    color: white;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-size: 10px;
                """)
                event_badge.setWordWrap(True)
                layout.addWidget(event_badge)

            # Show "more" indicator if > 3 events
            if len(self.events_by_day[day]) > 3:
                more_label = QLabel(f"+{len(self.events_by_day[day]) - 3} more")
                more_label.setStyleSheet("""
                    color: #7f8c8d;
                    font-size: 9px;
                    font-style: italic;
                """)
                layout.addWidget(more_label)

        layout.addStretch()

        # Connect click event
        cell.mousePressEvent = lambda e: self._on_day_clicked(day)

        return cell

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def _on_day_clicked(self, day: int):
        """Handle day cell click."""
        self.selected_date = datetime(self.current_date.year, self.current_date.month, day)
        self._build_calendar_grid()  # Rebuild to update selection
        self._update_day_details()

    def _update_day_details(self):
        """Update the event details panel for selected day."""
        try:
            # Update header
            day_str = self.selected_date.strftime("%A, %B %d, %Y")
            self.details_header.setText(day_str)

            # Clear existing event cards
            while self.events_layout.count() > 1:  # Keep stretch at end
                item = self.events_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get events for selected day
            events = self.calendar_manager.get_events_for_date(self.selected_date)

            if not events:
                no_events_label = QLabel("No events on this day")
                no_events_label.setStyleSheet("""
                    color: #95a5a6;
                    font-style: italic;
                    padding: 20px;
                    font-size: 14px;
                """)
                no_events_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.events_layout.insertWidget(0, no_events_label)
            else:
                # Add event cards
                for event in events:
                    card = self._create_event_card(event)
                    self.events_layout.insertWidget(self.events_layout.count() - 1, card)

        except Exception as e:
            logger.error(f"Failed to update day details: {e}")

    def _create_event_card(self, event: Dict[str, Any]) -> QWidget:
        """Create an event card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-left: 4px solid {event['color']};
                border-radius: 6px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        # Title and time
        title_layout = QHBoxLayout()

        # Event type icon
        type_icons = {
            'assignment': '📚',
            'session': '⏱️',
            'goal': '🎯'
        }
        icon = type_icons.get(event['type'], '📌')

        title = QLabel(f"{icon} {event['title']}")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        title.setWordWrap(True)
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Time
        time_str = event['date'].strftime("%I:%M %p")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        title_layout.addWidget(time_label)

        layout.addLayout(title_layout)

        # Metadata
        metadata_layout = QHBoxLayout()

        # Type badge
        type_badge = QLabel(event['type'].capitalize())
        type_badge.setStyleSheet(f"""
            background: {event['color']};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
        """)
        metadata_layout.addWidget(type_badge)

        # Type-specific metadata
        if event['type'] == 'assignment':
            metadata = event['metadata']

            # Status badge
            status_colors = {
                'pending': '#95a5a6',
                'in_progress': '#3498db',
                'completed': '#27ae60',
                'submitted': '#27ae60'
            }
            status = metadata.get('status', 'pending')
            status_badge = QLabel(status.replace('_', ' ').title())
            status_badge.setStyleSheet(f"""
                background: {status_colors.get(status, '#95a5a6')};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            """)
            metadata_layout.addWidget(status_badge)

            # Priority badge
            if metadata.get('priority'):
                priority_badge = QLabel(metadata['priority'].capitalize())
                priority_colors = {
                    'low': '#95a5a6',
                    'medium': '#f39c12',
                    'high': '#e74c3c'
                }
                priority_badge.setStyleSheet(f"""
                    background: {priority_colors.get(metadata['priority'], '#95a5a6')};
                    color: white;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 11px;
                """)
                metadata_layout.addWidget(priority_badge)

        elif event['type'] == 'session':
            metadata = event['metadata']
            duration_label = QLabel(f"Duration: {metadata.get('duration', 0)} min")
            duration_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            metadata_layout.addWidget(duration_label)

        elif event['type'] == 'goal':
            metadata = event['metadata']
            status_badge = QLabel(metadata.get('status', 'active').title())
            status_colors = {
                'active': '#3498db',
                'completed': '#27ae60',
                'abandoned': '#95a5a6'
            }
            status_badge.setStyleSheet(f"""
                background: {status_colors.get(metadata.get('status'), '#3498db')};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            """)
            metadata_layout.addWidget(status_badge)

        metadata_layout.addStretch()
        layout.addLayout(metadata_layout)

        return card

    def _previous_month(self):
        """Navigate to previous month."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)

        self._load_month()

    def _next_month(self):
        """Navigate to next month."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)

        self._load_month()

    def _go_to_today(self):
        """Jump to current month and select today."""
        self.current_date = datetime.now()
        self.selected_date = datetime.now()
        self._load_month()

    def _update_statistics(self):
        """Update statistics display."""
        try:
            # Get first and last day of month
            first_day = datetime(self.current_date.year, self.current_date.month, 1)
            days_in_month = monthrange(self.current_date.year, self.current_date.month)[1]
            last_day = datetime(self.current_date.year, self.current_date.month, days_in_month, 23, 59, 59)

            stats = self.calendar_manager.get_statistics(first_day, last_day)

            self.total_label.setText(f"Total: {stats.get('total_events', 0)}")
            self.assignments_label.setText(f"Assignments: {stats.get('assignments', 0)}")
            self.sessions_label.setText(f"Sessions: {stats.get('sessions', 0)}")
            self.goals_label.setText(f"Goals: {stats.get('goals', 0)}")

            overdue_count = stats.get('overdue_assignments', 0)
            if overdue_count > 0:
                self.overdue_label.setText(f"⚠️ Overdue: {overdue_count}")
                self.overdue_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                self.overdue_label.setText("Overdue: 0")
                self.overdue_label.setStyleSheet("color: white;")

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
