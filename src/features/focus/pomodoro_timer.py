"""
Academic Command Center - Focus Mode - Pomodoro Timer
Implements Pomodoro Technique with 25-minute work sessions and breaks.
"""

import logging
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SessionType(Enum):
    """Types of Pomodoro sessions."""
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class TimerState(Enum):
    """Timer states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class PomodoroTimer:
    """
    Pomodoro timer implementing the Pomodoro Technique.

    Default timing:
    - Work session: 25 minutes
    - Short break: 5 minutes
    - Long break: 15 minutes
    - Long break after: 4 work sessions
    """

    # Default timings (in minutes)
    DEFAULT_WORK_DURATION = 25
    DEFAULT_SHORT_BREAK = 5
    DEFAULT_LONG_BREAK = 15
    SESSIONS_BEFORE_LONG_BREAK = 4

    def __init__(
        self,
        work_duration: int = DEFAULT_WORK_DURATION,
        short_break: int = DEFAULT_SHORT_BREAK,
        long_break: int = DEFAULT_LONG_BREAK
    ):
        """
        Initialize Pomodoro timer.

        Args:
            work_duration: Work session length in minutes
            short_break: Short break length in minutes
            long_break: Long break length in minutes
        """
        self.work_duration = work_duration
        self.short_break = short_break
        self.long_break = long_break

        # Timer state
        self.state = TimerState.IDLE
        self.current_session_type = SessionType.WORK
        self.sessions_completed = 0

        # Current session tracking
        self.session_id: Optional[str] = None
        self.task_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.elapsed_seconds = 0
        self.target_seconds = 0
        self.interruption_count = 0

        # Callbacks
        self.on_tick: Optional[Callable[[int], None]] = None  # Called every second with remaining seconds
        self.on_complete: Optional[Callable[[Dict[str, Any]], None]] = None  # Called when session completes
        self.on_state_change: Optional[Callable[[TimerState], None]] = None  # Called when state changes

        logger.info("Pomodoro timer initialized")

    def start_session(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new Pomodoro session.

        Args:
            task_id: Optional task ID to link session to

        Returns:
            Session info
        """
        if self.state == TimerState.RUNNING:
            return {
                'success': False,
                'error': 'Session already running'
            }

        # Create new session
        self.session_id = str(uuid.uuid4())
        self.task_id = task_id
        self.start_time = datetime.now()
        self.pause_time = None
        self.end_time = None
        self.elapsed_seconds = 0
        self.interruption_count = 0

        # Set duration based on session type
        if self.current_session_type == SessionType.WORK:
            duration_minutes = self.work_duration
        elif self.current_session_type == SessionType.SHORT_BREAK:
            duration_minutes = self.short_break
        else:  # LONG_BREAK
            duration_minutes = self.long_break

        self.target_seconds = duration_minutes * 60

        # Update state
        self._set_state(TimerState.RUNNING)

        logger.info(f"Started {self.current_session_type.value} session: {self.session_id}")

        return {
            'success': True,
            'session_id': self.session_id,
            'session_type': self.current_session_type.value,
            'duration_minutes': duration_minutes,
            'task_id': self.task_id
        }

    def pause_session(self) -> Dict[str, Any]:
        """
        Pause current session.

        Returns:
            Pause result
        """
        if self.state != TimerState.RUNNING:
            return {
                'success': False,
                'error': 'No session running'
            }

        self.pause_time = datetime.now()
        self._set_state(TimerState.PAUSED)

        logger.info(f"Paused session: {self.session_id}")

        return {
            'success': True,
            'elapsed_seconds': self.elapsed_seconds,
            'remaining_seconds': self.target_seconds - self.elapsed_seconds
        }

    def resume_session(self) -> Dict[str, Any]:
        """
        Resume paused session.

        Returns:
            Resume result
        """
        if self.state != TimerState.PAUSED:
            return {
                'success': False,
                'error': 'Session not paused'
            }

        self.pause_time = None
        self._set_state(TimerState.RUNNING)

        logger.info(f"Resumed session: {self.session_id}")

        return {'success': True}

    def stop_session(self, completed: bool = False) -> Dict[str, Any]:
        """
        Stop current session.

        Args:
            completed: Whether session was completed or abandoned

        Returns:
            Session summary
        """
        if self.state == TimerState.IDLE:
            return {
                'success': False,
                'error': 'No session running'
            }

        self.end_time = datetime.now()
        self._set_state(TimerState.COMPLETED if completed else TimerState.IDLE)

        # Calculate focus score (0-100)
        focus_score = self._calculate_focus_score()

        session_data = {
            'session_id': self.session_id,
            'session_type': self.current_session_type.value,
            'task_id': self.task_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.elapsed_seconds // 60,
            'completed': completed,
            'interruptions': self.interruption_count,
            'focus_score': focus_score
        }

        # If completed, update session counter and determine next session type
        if completed:
            if self.current_session_type == SessionType.WORK:
                self.sessions_completed += 1

                # Determine next session type
                if self.sessions_completed % self.SESSIONS_BEFORE_LONG_BREAK == 0:
                    self.current_session_type = SessionType.LONG_BREAK
                else:
                    self.current_session_type = SessionType.SHORT_BREAK
            else:
                # After break, go back to work
                self.current_session_type = SessionType.WORK

        # Call completion callback
        if self.on_complete:
            self.on_complete(session_data)

        # Reset for next session
        if not completed:
            self._reset()

        logger.info(f"Stopped session: {self.session_id}, completed={completed}")

        return {
            'success': True,
            **session_data,
            'next_session_type': self.current_session_type.value,
            'sessions_completed': self.sessions_completed
        }

    def tick(self) -> Dict[str, Any]:
        """
        Update timer (call this every second).

        Returns:
            Current timer state
        """
        if self.state != TimerState.RUNNING:
            return {
                'success': False,
                'error': 'Session not running'
            }

        self.elapsed_seconds += 1
        remaining_seconds = self.target_seconds - self.elapsed_seconds

        # Call tick callback
        if self.on_tick:
            self.on_tick(remaining_seconds)

        # Check if session completed
        if remaining_seconds <= 0:
            self.stop_session(completed=True)
            return {
                'success': True,
                'completed': True,
                'remaining_seconds': 0
            }

        return {
            'success': True,
            'elapsed_seconds': self.elapsed_seconds,
            'remaining_seconds': remaining_seconds,
            'percentage': (self.elapsed_seconds / self.target_seconds) * 100
        }

    def log_interruption(self, category: str = "other") -> Dict[str, Any]:
        """
        Log an interruption during session.

        Args:
            category: Interruption category (social_media, email, phone, other)

        Returns:
            Result
        """
        if self.state != TimerState.RUNNING:
            return {
                'success': False,
                'error': 'No session running'
            }

        self.interruption_count += 1

        logger.info(f"Logged interruption ({category}) in session {self.session_id}")

        return {
            'success': True,
            'interruption_count': self.interruption_count,
            'category': category
        }

    def skip_break(self) -> Dict[str, Any]:
        """
        Skip current break and start work session.

        Returns:
            Result
        """
        if self.current_session_type == SessionType.WORK:
            return {
                'success': False,
                'error': 'Not in break session'
            }

        # Stop current break
        if self.state == TimerState.RUNNING:
            self.stop_session(completed=False)

        # Set to work session
        self.current_session_type = SessionType.WORK

        logger.info("Skipped break, moving to work session")

        return {
            'success': True,
            'next_session_type': SessionType.WORK.value
        }

    def get_remaining_time(self) -> Dict[str, Any]:
        """
        Get remaining time in current session.

        Returns:
            Time info
        """
        if self.state == TimerState.IDLE:
            return {
                'success': False,
                'error': 'No session active'
            }

        remaining_seconds = self.target_seconds - self.elapsed_seconds
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        return {
            'success': True,
            'remaining_seconds': remaining_seconds,
            'minutes': minutes,
            'seconds': seconds,
            'percentage': (self.elapsed_seconds / self.target_seconds) * 100 if self.target_seconds > 0 else 0
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current timer status.

        Returns:
            Status info
        """
        return {
            'state': self.state.value,
            'session_type': self.current_session_type.value,
            'sessions_completed': self.sessions_completed,
            'session_id': self.session_id,
            'task_id': self.task_id,
            'elapsed_seconds': self.elapsed_seconds,
            'target_seconds': self.target_seconds,
            'interruption_count': self.interruption_count,
            'next_long_break_in': self.SESSIONS_BEFORE_LONG_BREAK - (self.sessions_completed % self.SESSIONS_BEFORE_LONG_BREAK)
        }

    def _calculate_focus_score(self) -> float:
        """
        Calculate focus score (0-100) based on interruptions.

        Returns:
            Focus score
        """
        if self.interruption_count == 0:
            return 100.0

        # Each interruption reduces score
        # 1 interruption = 90
        # 2 interruptions = 80
        # 3+ interruptions = 70 and decreasing
        score = max(50.0, 100.0 - (self.interruption_count * 10))

        return round(score, 1)

    def _set_state(self, new_state: TimerState):
        """
        Set timer state and trigger callback.

        Args:
            new_state: New timer state
        """
        old_state = self.state
        self.state = new_state

        logger.debug(f"State changed: {old_state.value} → {new_state.value}")

        if self.on_state_change:
            self.on_state_change(new_state)

    def _reset(self):
        """Reset timer to initial state."""
        self.state = TimerState.IDLE
        self.session_id = None
        self.task_id = None
        self.start_time = None
        self.pause_time = None
        self.end_time = None
        self.elapsed_seconds = 0
        self.target_seconds = 0
        self.interruption_count = 0
        self.current_session_type = SessionType.WORK
        self.sessions_completed = 0


if __name__ == "__main__":
    print("Testing Pomodoro Timer...")

    def on_tick_callback(remaining):
        print(f"Remaining: {remaining//60}:{remaining%60:02d}")

    def on_complete_callback(data):
        print(f"Session completed: {data}")

    timer = PomodoroTimer()
    timer.on_tick = on_tick_callback
    timer.on_complete = on_complete_callback

    # Start work session
    result = timer.start_session()
    print(f"Started: {result}")

    # Simulate some ticks
    for _ in range(5):
        timer.tick()

    # Pause
    timer.pause_session()
    print("Paused")

    # Resume
    timer.resume_session()
    print("Resumed")

    # Get status
    status = timer.get_status()
    print(f"Status: {status}")

    print("\nPomodoro Timer validated!")
