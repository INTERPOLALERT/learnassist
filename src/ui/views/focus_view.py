"""
Academic Command Center - Focus View
Pomodoro timer and focus session tracking interface.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QComboBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.focus.pomodoro_timer import PomodoroTimer, TimerState, SessionType
from features.focus.session_manager import SessionManager
from features.focus.distraction_logger import DistractionLogger, DistractionCategory

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FocusView(QWidget):
    """Focus mode view with Pomodoro timer."""

    def __init__(self, user_id: str, db_manager: DatabaseManager):
        """
        Initialize focus view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager

        # Initialize focus components
        self.pomodoro = PomodoroTimer()
        self.session_manager = SessionManager(user_id, db_manager)
        self.distraction_logger = DistractionLogger(user_id, db_manager)

        # Setup callbacks
        self.pomodoro.on_tick = self._on_timer_tick
        self.pomodoro.on_complete = self._on_session_complete
        self.pomodoro.on_state_change = self._on_state_change

        # QTimer for updating UI
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._update_timer)
        self.ui_timer.setInterval(1000)  # 1 second

        # Current task
        self.current_task_id: Optional[str] = None
        self.current_task_title: str = "No task selected"

        self._init_ui()
        self.refresh()

    def _init_ui(self):
        """Initialize user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Page title
        title = QLabel("Focus Mode")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Timer section
        timer_section = self._create_timer_section()
        main_layout.addWidget(timer_section)

        # Controls section
        controls_section = self._create_controls_section()
        main_layout.addWidget(controls_section)

        # Stats section
        stats_section = self._create_stats_section()
        main_layout.addWidget(stats_section)

        # Today's sessions section
        sessions_section = self._create_sessions_section()
        main_layout.addWidget(sessions_section)

        # Stretch
        main_layout.addStretch()

    def _create_timer_section(self) -> QFrame:
        """Create timer display section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 15px;
                padding: 40px;
            }
        """)

        layout = QVBoxLayout(section)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Session type label
        self.session_type_label = QLabel("WORK SESSION")
        self.session_type_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.session_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_type_label.setStyleSheet("color: #3498db;")
        layout.addWidget(self.session_type_label)

        # Timer display (large)
        self.timer_display = QLabel("25:00")
        self.timer_display.setFont(QFont("Arial", 72, QFont.Weight.Bold))
        self.timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_display)

        # Current task
        self.current_task_label = QLabel("No task selected")
        self.current_task_label.setFont(QFont("Arial", 14))
        self.current_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_task_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.current_task_label)

        # Progress indicator
        progress_layout = QHBoxLayout()

        self.progress_label = QLabel("Session: 0 of 4")
        self.progress_label.setFont(QFont("Arial", 12))
        progress_layout.addWidget(self.progress_label)

        progress_layout.addStretch()

        self.focus_score_label = QLabel("Focus: 100%")
        self.focus_score_label.setFont(QFont("Arial", 12))
        self.focus_score_label.setStyleSheet("color: #27ae60;")
        progress_layout.addWidget(self.focus_score_label)

        layout.addLayout(progress_layout)

        return section

    def _create_controls_section(self) -> QFrame:
        """Create control buttons section."""
        section = QFrame()
        section.setStyleSheet("QFrame { border: none; }")

        layout = QHBoxLayout(section)
        layout.setSpacing(15)

        # Task selector
        task_layout = QVBoxLayout()
        task_label = QLabel("Select Task:")
        task_label.setFont(QFont("Arial", 10))
        task_layout.addWidget(task_label)

        self.task_combo = QComboBox()
        self.task_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        self.task_combo.currentIndexChanged.connect(self._on_task_selected)
        task_layout.addWidget(self.task_combo)

        layout.addLayout(task_layout)

        layout.addStretch()

        # Start button
        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_btn)

        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setEnabled(False)
        layout.addWidget(self.pause_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        # Distraction button
        self.distraction_btn = QPushButton("😐 Distraction")
        self.distraction_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 15px 20px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.distraction_btn.clicked.connect(self._on_distraction_clicked)
        self.distraction_btn.setEnabled(False)
        layout.addWidget(self.distraction_btn)

        return section

    def _create_stats_section(self) -> QFrame:
        """Create statistics section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QHBoxLayout(section)

        # Today's stats
        stats = [
            ("today_sessions", "0", "Sessions Today"),
            ("focus_time", "0h", "Focus Time"),
            ("avg_focus", "100%", "Avg Focus"),
            ("streak", "0", "Day Streak")
        ]

        for key, value, label in stats:
            stat_widget = self._create_stat_widget(value, label)
            setattr(self, f"{key}_label", stat_widget[0])
            layout.addWidget(stat_widget[1])

        return section

    def _create_stat_widget(self, value: str, label: str) -> tuple:
        """Create a stat widget."""
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("color: #3498db;")
        layout.addWidget(value_label)

        text_label = QLabel(label)
        text_label.setFont(QFont("Arial", 10))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(text_label)

        return (value_label, container)

    def _create_sessions_section(self) -> QFrame:
        """Create today's sessions list section."""
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

        # Title
        title = QLabel("Today's Completed Sessions")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Scrollable session list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll.setMaximumHeight(200)

        scroll_content = QWidget()
        self.sessions_layout = QVBoxLayout(scroll_content)
        self.sessions_layout.setSpacing(8)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return section

    def _load_pending_tasks(self):
        """Load pending tasks into combo box."""
        try:
            self.task_combo.clear()
            self.task_combo.addItem("No task", None)

            query = """
            SELECT id, title FROM tasks
            WHERE user_id = ? AND status = 'pending'
            ORDER BY priority_score DESC
            LIMIT 20
            """

            tasks = self.db.execute_query(query, (self.user_id,), fetch_all=True)

            if tasks:
                for task in tasks:
                    self.task_combo.addItem(task['title'], task['id'])

        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")

    def _on_task_selected(self, index: int):
        """Handle task selection."""
        self.current_task_id = self.task_combo.itemData(index)
        self.current_task_title = self.task_combo.currentText()

    def _on_start_clicked(self):
        """Handle start button click."""
        result = self.pomodoro.start_session(self.current_task_id)

        if result['success']:
            self.ui_timer.start()
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.distraction_btn.setEnabled(True)
            self.task_combo.setEnabled(False)

            # Update current task label
            self.current_task_label.setText(self.current_task_title)

            logger.info("Started focus session")
        else:
            QMessageBox.warning(self, "Error", result.get('error', 'Failed to start session'))

    def _on_pause_clicked(self):
        """Handle pause button click."""
        if self.pomodoro.state == TimerState.RUNNING:
            self.pomodoro.pause_session()
            self.pause_btn.setText("Resume")
            self.ui_timer.stop()
        else:
            self.pomodoro.resume_session()
            self.pause_btn.setText("Pause")
            self.ui_timer.start()

    def _on_stop_clicked(self):
        """Handle stop button click."""
        reply = QMessageBox.question(
            self,
            "Stop Session",
            "Are you sure you want to stop this session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.pomodoro.stop_session(completed=False)
            self.ui_timer.stop()
            self._reset_ui()

    def _on_distraction_clicked(self):
        """Handle distraction button click."""
        self.pomodoro.log_interruption(DistractionCategory.OTHER)
        self.distraction_logger.log_distraction(
            self.pomodoro.session_id,
            DistractionCategory.OTHER
        )

        # Update focus score
        score = self.pomodoro._calculate_focus_score()
        self.focus_score_label.setText(f"Focus: {score:.0f}%")
        self.focus_score_label.setStyleSheet(
            f"color: {'#e74c3c' if score < 70 else '#f39c12' if score < 85 else '#27ae60'};"
        )

    def _update_timer(self):
        """Update timer display (called every second)."""
        self.pomodoro.tick()

    def _on_timer_tick(self, remaining_seconds: int):
        """Callback when timer ticks."""
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self.timer_display.setText(f"{minutes:02d}:{seconds:02d}")

    def _on_session_complete(self, session_data: dict):
        """Callback when session completes."""
        self.ui_timer.stop()

        # Save to database
        self.session_manager.save_session(session_data)
        self.distraction_logger.clear_session_cache()

        # Show completion message
        session_type = session_data.get('session_type', 'work')
        if session_type == 'work':
            QMessageBox.information(
                self,
                "Session Complete!",
                f"Great work! You completed a {session_data['duration_minutes']}-minute session.\n"
                f"Focus Score: {session_data['focus_score']:.0f}%\n\n"
                f"Next: {self.pomodoro.current_session_type.value.replace('_', ' ').title()}"
            )
        else:
            QMessageBox.information(
                self,
                "Break Over!",
                f"Break time complete. Ready for your next work session?"
            )

        # Reset UI
        self._reset_ui()

        # Refresh stats
        self.refresh()

    def _on_state_change(self, new_state: TimerState):
        """Callback when timer state changes."""
        logger.debug(f"Timer state changed to: {new_state.value}")

    def _reset_ui(self):
        """Reset UI to initial state."""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("Pause")
        self.stop_btn.setEnabled(False)
        self.distraction_btn.setEnabled(False)
        self.task_combo.setEnabled(True)

        # Update display
        session_type = self.pomodoro.current_session_type.value.replace('_', ' ').upper()
        self.session_type_label.setText(session_type)

        duration = {
            SessionType.WORK: self.pomodoro.work_duration,
            SessionType.SHORT_BREAK: self.pomodoro.short_break,
            SessionType.LONG_BREAK: self.pomodoro.long_break
        }.get(self.pomodoro.current_session_type, 25)

        self.timer_display.setText(f"{duration}:00")
        self.current_task_label.setText("No task selected")
        self.focus_score_label.setText("Focus: 100%")
        self.focus_score_label.setStyleSheet("color: #27ae60;")

    def refresh(self):
        """Refresh view data."""
        logger.info("Refreshing focus view...")

        # Load pending tasks
        self._load_pending_tasks()

        # Update stats
        self._update_stats()

        # Update progress
        self._update_progress()

        # Load today's sessions
        self._load_today_sessions()

    def _update_stats(self):
        """Update statistics labels."""
        try:
            today = self.session_manager.get_today_sessions()

            self.today_sessions_label.setText(str(today.get('work_sessions', 0)))
            self.focus_time_label.setText(f"{today.get('total_focus_time', 0) // 60}h")
            self.avg_focus_label.setText(f"{today.get('average_focus_score', 100):.0f}%")

            streak = self.session_manager.calculate_streak()
            self.streak_label.setText(str(streak.get('current_streak', 0)))

        except Exception as e:
            logger.error(f"Failed to update stats: {e}")

    def _update_progress(self):
        """Update progress indicator."""
        sessions_completed = self.pomodoro.sessions_completed % self.pomodoro.SESSIONS_BEFORE_LONG_BREAK
        self.progress_label.setText(f"Session: {sessions_completed} of 4")

    def _load_today_sessions(self):
        """Load today's completed sessions."""
        try:
            # Clear existing
            while self.sessions_layout.count():
                item = self.sessions_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            today = self.session_manager.get_today_sessions()
            sessions = today.get('sessions', [])

            if not sessions:
                no_data = QLabel("No sessions completed today")
                no_data.setStyleSheet("color: #95a5a6; font-style: italic;")
                self.sessions_layout.addWidget(no_data)
                return

            for session in sessions[:10]:  # Show last 10
                if session.get('session_type') == 'work':
                    session_widget = self._create_session_item(session)
                    self.sessions_layout.addWidget(session_widget)

            self.sessions_layout.addStretch()

        except Exception as e:
            logger.error(f"Failed to load today's sessions: {e}")

    def _create_session_item(self, session: dict) -> QFrame:
        """Create session item widget."""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-left: 3px solid #2ecc71;
                padding: 8px;
                margin: 2px 0;
            }
        """)

        layout = QHBoxLayout(item)

        # Time
        from datetime import datetime
        start_time = datetime.fromisoformat(session['start_time'])
        time_label = QLabel(start_time.strftime("%I:%M %p"))
        time_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(time_label)

        # Duration
        duration_label = QLabel(f"{session.get('duration_minutes', 0)} min")
        duration_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(duration_label)

        layout.addStretch()

        # Focus score
        score = session.get('focus_score', 100)
        score_label = QLabel(f"{score:.0f}%")
        score_label.setStyleSheet(
            f"color: {'#e74c3c' if score < 70 else '#f39c12' if score < 85 else '#27ae60'}; "
            f"font-weight: bold;"
        )
        layout.addWidget(score_label)

        return item


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    db = DatabaseManager()
    view = FocusView("test_user", db)
    view.show()

    sys.exit(app.exec())
