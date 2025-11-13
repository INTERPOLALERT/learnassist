"""
Study Timer View - Phase 3
Pomodoro timer interface with circular progress and focus tracking
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QFrame, QTextEdit, QGroupBox, QSpinBox,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen

from features.focus.pomodoro_timer import PomodoroTimer, SessionType, TimerState
from features.focus.session_manager import SessionManager

logger = logging.getLogger(__name__)


class CircularProgress(QWidget):
    """Circular progress indicator for timer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0  # 0-100
        self.setMinimumSize(300, 300)

    def set_progress(self, value: float):
        """Set progress value (0-100)."""
        self.progress = max(0, min(100, value))
        self.update()

    def paintEvent(self, event):
        """Draw circular progress."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get dimensions
        width = self.width()
        height = self.height()
        side = min(width, height)

        # Center the circle
        painter.translate(width / 2, height / 2)
        painter.scale(side / 200.0, side / 200.0)

        # Draw background circle
        pen = QPen(QColor("#ecf0f1"))
        pen.setWidth(15)
        painter.setPen(pen)
        painter.drawEllipse(-90, -90, 180, 180)

        # Draw progress arc
        pen = QPen(QColor("#3498db"))
        pen.setWidth(15)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Progress angle (starts at top, goes clockwise)
        start_angle = 90 * 16  # Qt uses 1/16th degree units
        span_angle = -int(self.progress * 3.6 * 16)  # Negative for clockwise
        painter.drawArc(-90, -90, 180, 180, start_angle, span_angle)


class StudyTimerView(QWidget):
    """
    Study timer view with Pomodoro technique.

    Features:
    - 25-5-15 minute cycles (work-break-long break)
    - Visual circular progress
    - Session tracking
    - Focus scoring
    - Daily statistics
    - Streak tracking
    """

    session_completed = pyqtSignal(dict)  # Emits session data when completed

    def __init__(self, user_id: str, db_manager):
        """
        Initialize Study Timer View.

        Args:
            user_id: Current user ID
            db_manager: DatabaseManager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager

        # Initialize managers
        self.timer = PomodoroTimer()
        self.session_manager = SessionManager(user_id, db_manager)

        # UI update timer
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._update_display)
        self.ui_timer.start(100)  # Update 10 times per second

        # Session data
        self.current_session_start = None
        self.interruptions = 0

        self._init_ui()
        self._load_statistics()
        self._update_display()

        logger.info(f"Study Timer View initialized for user {user_id}")

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        title = QLabel("⏱️ Focus Session")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Circular progress timer
        timer_container = QHBoxLayout()
        timer_container.addStretch()

        timer_widget = QWidget()
        timer_layout = QVBoxLayout(timer_widget)

        self.progress_circle = CircularProgress()
        timer_layout.addWidget(self.progress_circle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Time display
        self.time_label = QLabel("25:00")
        self.time_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: #2c3e50;")
        timer_layout.addWidget(self.time_label)

        # Session type label
        self.session_type_label = QLabel("WORK SESSION")
        self.session_type_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.session_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_type_label.setStyleSheet("color: #3498db;")
        timer_layout.addWidget(self.session_type_label)

        timer_container.addWidget(timer_widget)
        timer_container.addStretch()
        layout.addLayout(timer_container)

        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self._start_session)
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        controls_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._pause_session)
        self.pause_btn.setMinimumHeight(50)
        self.pause_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        controls_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._stop_session)
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        controls_layout.addWidget(self.stop_btn)

        self.skip_btn = QPushButton("⏭ Skip")
        self.skip_btn.clicked.connect(self._skip_session)
        self.skip_btn.setMinimumHeight(50)
        self.skip_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.skip_btn.setEnabled(False)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        controls_layout.addWidget(self.skip_btn)

        layout.addLayout(controls_layout)

        # Session configuration
        config_group = QGroupBox("Session Configuration")
        config_layout = QHBoxLayout()

        # Session type selector
        type_label = QLabel("Session Type:")
        config_layout.addWidget(type_label)

        self.session_type_combo = QComboBox()
        self.session_type_combo.addItems(["Work", "Short Break", "Long Break"])
        self.session_type_combo.currentTextChanged.connect(self._on_session_type_changed)
        config_layout.addWidget(self.session_type_combo)

        # Duration spin box
        duration_label = QLabel("Duration (min):")
        config_layout.addWidget(duration_label)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 120)
        self.duration_spin.setValue(25)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        config_layout.addWidget(self.duration_spin)

        # Subject selector
        subject_label = QLabel("Subject:")
        config_layout.addWidget(subject_label)

        self.subject_combo = QComboBox()
        self.subject_combo.addItem("No Subject", None)
        self._load_subjects()
        config_layout.addWidget(self.subject_combo)

        # Assignment selector
        assignment_label = QLabel("Assignment:")
        config_layout.addWidget(assignment_label)

        self.assignment_combo = QComboBox()
        self.assignment_combo.addItem("No Assignment", None)
        self._load_assignments()
        config_layout.addWidget(self.assignment_combo)

        config_layout.addStretch()
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Statistics panel
        stats_group = QGroupBox("📊 Today's Statistics")
        stats_layout = QHBoxLayout()

        self.study_time_label = QLabel("Study Time: 0h 0m")
        self.study_time_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.study_time_label)

        self.sessions_label = QLabel("Sessions: 0")
        self.sessions_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.sessions_label)

        self.focus_score_label = QLabel("Focus Score: 100%")
        self.focus_score_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.focus_score_label)

        self.streak_label = QLabel("Streak: 0 days 🔥")
        self.streak_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.streak_label)

        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Session notes
        notes_group = QGroupBox("Session Notes")
        notes_layout = QVBoxLayout()

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("What did you accomplish in this session?")
        self.notes_input.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_input)

        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Interruption tracker
        interrupt_layout = QHBoxLayout()

        interrupt_label = QLabel("Interruptions:")
        interrupt_layout.addWidget(interrupt_label)

        self.interrupt_count_label = QLabel("0")
        self.interrupt_count_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.interrupt_count_label.setStyleSheet("color: #e74c3c;")
        interrupt_layout.addWidget(self.interrupt_count_label)

        interrupt_btn = QPushButton("+ Add Interruption")
        interrupt_btn.clicked.connect(self._add_interruption)
        interrupt_layout.addWidget(interrupt_btn)

        interrupt_layout.addStretch()
        layout.addLayout(interrupt_layout)

        layout.addStretch()
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

    def _load_assignments(self):
        """Load assignments for dropdown."""
        try:
            query = """
                SELECT id, title
                FROM assignments
                WHERE user_id = ? AND status NOT IN ('completed', 'submitted')
                ORDER BY due_date ASC
                LIMIT 20
            """
            assignments = self.db.fetch_all(query, (self.user_id,))

            for assignment in assignments:
                self.assignment_combo.addItem(assignment[1], assignment[0])

        except Exception as e:
            logger.error(f"Failed to load assignments: {e}")

    def _load_statistics(self):
        """Load and display today's statistics."""
        try:
            stats = self.session_manager.get_today_summary()

            # Study time
            total_minutes = stats.get('total_minutes', 0)
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            self.study_time_label.setText(f"Study Time: {hours}h {minutes}m")

            # Sessions
            session_count = stats.get('session_count', 0)
            self.sessions_label.setText(f"Sessions: {session_count}")

            # Focus score
            focus_score = stats.get('avg_focus_score', 100)
            self.focus_score_label.setText(f"Focus Score: {focus_score:.0f}%")

            # Streak
            streak = self.session_manager.calculate_streak()
            self.streak_label.setText(f"Streak: {streak} days 🔥")

            if streak > 0:
                self.streak_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

        except Exception as e:
            logger.error(f"Failed to load statistics: {e}")

    def _update_display(self):
        """Update timer display."""
        # Get current time remaining
        remaining = self.timer.get_time_remaining()
        total = self.timer.get_total_duration()

        # Format time
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

        # Update progress
        if total > 0:
            progress = ((total - remaining) / total) * 100
            self.progress_circle.set_progress(progress)
        else:
            self.progress_circle.set_progress(0)

        # Update session type label
        session_type = self.timer.current_session_type
        if session_type == SessionType.WORK:
            self.session_type_label.setText("WORK SESSION")
            self.session_type_label.setStyleSheet("color: #3498db; font-weight: bold;")
        elif session_type == SessionType.SHORT_BREAK:
            self.session_type_label.setText("SHORT BREAK")
            self.session_type_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif session_type == SessionType.LONG_BREAK:
            self.session_type_label.setText("LONG BREAK")
            self.session_type_label.setStyleSheet("color: #9b59b6; font-weight: bold;")

        # Check if session completed
        if self.timer.state == TimerState.COMPLETED:
            self._on_session_completed()

        # Update button states
        state = self.timer.state
        self.start_btn.setEnabled(state in [TimerState.IDLE, TimerState.PAUSED])
        self.pause_btn.setEnabled(state == TimerState.RUNNING)
        self.stop_btn.setEnabled(state in [TimerState.RUNNING, TimerState.PAUSED])
        self.skip_btn.setEnabled(state in [TimerState.RUNNING, TimerState.PAUSED])

    def _on_session_type_changed(self, text: str):
        """Handle session type change."""
        if text == "Work":
            self.duration_spin.setValue(25)
            self.timer.set_session_type(SessionType.WORK)
        elif text == "Short Break":
            self.duration_spin.setValue(5)
            self.timer.set_session_type(SessionType.SHORT_BREAK)
        elif text == "Long Break":
            self.duration_spin.setValue(15)
            self.timer.set_session_type(SessionType.LONG_BREAK)

    def _on_duration_changed(self, value: int):
        """Handle duration change."""
        # Update timer duration if not running
        if self.timer.state == TimerState.IDLE:
            self.timer.work_duration = value if self.timer.current_session_type == SessionType.WORK else self.timer.work_duration
            self.timer.short_break_duration = value if self.timer.current_session_type == SessionType.SHORT_BREAK else self.timer.short_break_duration
            self.timer.long_break_duration = value if self.timer.current_session_type == SessionType.LONG_BREAK else self.timer.long_break_duration

    def _start_session(self):
        """Start timer session."""
        if self.timer.state == TimerState.IDLE:
            self.current_session_start = datetime.now()
            self.interruptions = 0
            self.interrupt_count_label.setText("0")

        self.timer.start()
        logger.info("Session started")

    def _pause_session(self):
        """Pause timer session."""
        self.timer.pause()
        logger.info("Session paused")

    def _stop_session(self):
        """Stop timer session."""
        reply = QMessageBox.question(
            self,
            "Stop Session",
            "Are you sure you want to stop this session?\n\nProgress will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.timer.stop()
            self.interruptions = 0
            self.interrupt_count_label.setText("0")
            self.notes_input.clear()
            logger.info("Session stopped")

    def _skip_session(self):
        """Skip to next session."""
        reply = QMessageBox.question(
            self,
            "Skip Session",
            "Skip to the next session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Save current session as completed
            if self.timer.state in [TimerState.RUNNING, TimerState.PAUSED]:
                self._save_session(completed=True)

            self.timer.skip_to_next()
            logger.info("Session skipped")

    def _add_interruption(self):
        """Add an interruption."""
        if self.timer.state == TimerState.RUNNING:
            self.interruptions += 1
            self.interrupt_count_label.setText(str(self.interruptions))
            logger.info(f"Interruption added: {self.interruptions}")

    def _on_session_completed(self):
        """Handle session completion."""
        logger.info("Session completed")

        # Play notification sound (placeholder)
        # TODO: Add audio notification

        # Show completion message
        session_type = self.timer.current_session_type
        if session_type == SessionType.WORK:
            message = "✅ Work session completed!\n\nTime for a break."
        elif session_type == SessionType.SHORT_BREAK:
            message = "✅ Break completed!\n\nReady for another work session?"
        else:
            message = "✅ Long break completed!\n\nFeeling refreshed?"

        QMessageBox.information(self, "Session Complete", message)

        # Save session
        self._save_session(completed=True)

        # Auto-start next session (optional)
        auto_start = False  # TODO: Make this a setting
        if auto_start:
            self.timer.start_next_session()
        else:
            self.timer.state = TimerState.IDLE

        # Reload statistics
        self._load_statistics()

    def _save_session(self, completed: bool = True):
        """
        Save session to database.

        Args:
            completed: Whether session was completed
        """
        try:
            if self.current_session_start is None:
                return

            end_time = datetime.now()
            duration = (end_time - self.current_session_start).total_seconds() / 60

            # Calculate focus score
            base_score = 100.0
            interruption_penalty = self.interruptions * 5  # -5% per interruption
            focus_score = max(0, base_score - interruption_penalty)

            # Prepare session data
            session_data = {
                'user_id': self.user_id,
                'session_type': self.timer.current_session_type.value,
                'start_time': self.current_session_start.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': int(duration),
                'completed': completed,
                'interruptions': self.interruptions,
                'focus_score': focus_score,
                'session_notes': self.notes_input.toPlainText().strip()
            }

            # Add subject if selected
            subject_id = self.subject_combo.currentData()
            if subject_id:
                session_data['subject'] = subject_id

            # Add assignment if selected (task_id in database)
            assignment_id = self.assignment_combo.currentData()
            if assignment_id:
                session_data['task_id'] = assignment_id

            # Save to database
            result = self.session_manager.save_session(session_data)
            logger.info(f"Session saved: {result.get('id')}")

            # Emit signal
            self.session_completed.emit(session_data)

            # Clear notes
            self.notes_input.clear()

            # Reset interruptions
            self.interruptions = 0
            self.interrupt_count_label.setText("0")

            # Reset session start
            self.current_session_start = None

        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save session: {str(e)}")
