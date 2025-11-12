"""
Academic Command Center - Focus Mode - Session Manager
Manages focus sessions, tracks history, and calculates statistics.
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages focus sessions and tracks productivity.

    Handles:
    - Session persistence to database
    - Session history retrieval
    - Daily/weekly summaries
    - Focus score calculation
    - Streak tracking
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize session manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Session manager initialized for user {user_id}")

    def save_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save session to database.

        Args:
            session_data: Session data from Pomodoro timer

        Returns:
            Save result
        """
        try:
            session_id = session_data.get('session_id') or str(uuid.uuid4())

            query = """
            INSERT INTO focus_sessions (
                id, user_id, task_id, start_time, end_time,
                duration_minutes, session_type, completed,
                interruptions, focus_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    session_id,
                    self.user_id,
                    session_data.get('task_id'),
                    session_data.get('start_time'),
                    session_data.get('end_time'),
                    session_data.get('duration_minutes', 0),
                    session_data.get('session_type', 'work'),
                    1 if session_data.get('completed', False) else 0,
                    session_data.get('interruptions', 0),
                    session_data.get('focus_score', 100.0),
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Saved session {session_id} to database")

            # Update daily progress log
            self._update_daily_progress(session_data)

            return {
                'success': True,
                'session_id': session_id
            }

        except Exception as e:
            logger.error(f"Failed to save session: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_session_history(
        self,
        days: int = 7,
        session_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get session history.

        Args:
            days: Number of days to retrieve
            session_type: Filter by session type (work, short_break, long_break)

        Returns:
            Session history
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
            SELECT * FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            """
            params = [self.user_id, start_date]

            if session_type:
                query += " AND session_type = ?"
                params.append(session_type)

            query += " ORDER BY start_time DESC"

            sessions = self.db.execute_query(query, tuple(params), fetch_all=True)

            return {
                'success': True,
                'sessions': sessions or [],
                'count': len(sessions) if sessions else 0
            }

        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return {
                'success': False,
                'error': str(e),
                'sessions': []
            }

    def get_today_sessions(self) -> Dict[str, Any]:
        """
        Get today's completed sessions.

        Returns:
            Today's sessions
        """
        try:
            today = datetime.now().date().isoformat()

            query = """
            SELECT * FROM focus_sessions
            WHERE user_id = ?
            AND date(start_time) = ?
            AND completed = 1
            ORDER BY start_time DESC
            """

            sessions = self.db.execute_query(
                query,
                (self.user_id, today),
                fetch_all=True
            )

            # Calculate statistics
            work_sessions = [s for s in sessions if s.get('session_type') == 'work']
            total_focus_time = sum(s.get('duration_minutes', 0) for s in work_sessions)
            avg_focus_score = sum(s.get('focus_score', 0) for s in work_sessions) / len(work_sessions) if work_sessions else 0

            return {
                'success': True,
                'sessions': sessions or [],
                'count': len(sessions) if sessions else 0,
                'work_sessions': len(work_sessions),
                'total_focus_time': total_focus_time,
                'average_focus_score': round(avg_focus_score, 1)
            }

        except Exception as e:
            logger.error(f"Failed to get today's sessions: {e}")
            return {
                'success': False,
                'error': str(e),
                'sessions': []
            }

    def get_weekly_summary(self) -> Dict[str, Any]:
        """
        Get weekly session summary.

        Returns:
            Weekly statistics
        """
        try:
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()

            query = """
            SELECT
                date(start_time) as date,
                COUNT(*) as session_count,
                SUM(CASE WHEN session_type = 'work' THEN 1 ELSE 0 END) as work_sessions,
                SUM(CASE WHEN session_type = 'work' THEN duration_minutes ELSE 0 END) as total_minutes,
                AVG(CASE WHEN session_type = 'work' THEN focus_score ELSE NULL END) as avg_focus_score
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ?
            AND completed = 1
            GROUP BY date(start_time)
            ORDER BY date DESC
            """

            daily_stats = self.db.execute_query(
                query,
                (self.user_id, week_ago),
                fetch_all=True
            )

            # Calculate totals
            total_sessions = sum(d.get('session_count', 0) for d in daily_stats) if daily_stats else 0
            total_work_sessions = sum(d.get('work_sessions', 0) for d in daily_stats) if daily_stats else 0
            total_minutes = sum(d.get('total_minutes', 0) for d in daily_stats) if daily_stats else 0

            return {
                'success': True,
                'daily_stats': daily_stats or [],
                'total_sessions': total_sessions,
                'total_work_sessions': total_work_sessions,
                'total_hours': round(total_minutes / 60, 1),
                'average_daily_sessions': round(total_sessions / 7, 1)
            }

        except Exception as e:
            logger.error(f"Failed to get weekly summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_task_sessions(self, task_id: str) -> Dict[str, Any]:
        """
        Get all sessions for a specific task.

        Args:
            task_id: Task ID

        Returns:
            Task sessions
        """
        try:
            query = """
            SELECT * FROM focus_sessions
            WHERE user_id = ? AND task_id = ?
            ORDER BY start_time DESC
            """

            sessions = self.db.execute_query(
                query,
                (self.user_id, task_id),
                fetch_all=True
            )

            # Calculate task statistics
            completed_sessions = [s for s in sessions if s.get('completed')] if sessions else []
            total_time = sum(s.get('duration_minutes', 0) for s in completed_sessions)

            return {
                'success': True,
                'sessions': sessions or [],
                'count': len(sessions) if sessions else 0,
                'completed_count': len(completed_sessions),
                'total_minutes': total_time
            }

        except Exception as e:
            logger.error(f"Failed to get task sessions: {e}")
            return {
                'success': False,
                'error': str(e),
                'sessions': []
            }

    def calculate_streak(self) -> Dict[str, Any]:
        """
        Calculate consecutive days with focus sessions.

        Returns:
            Streak info
        """
        try:
            # Get all dates with sessions (last 90 days)
            ninety_days_ago = (datetime.now() - timedelta(days=90)).isoformat()

            query = """
            SELECT DISTINCT date(start_time) as date
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ?
            AND completed = 1
            ORDER BY date DESC
            """

            session_dates = self.db.execute_query(
                query,
                (self.user_id, ninety_days_ago),
                fetch_all=True
            )

            if not session_dates:
                return {
                    'success': True,
                    'current_streak': 0,
                    'longest_streak': 0
                }

            # Parse dates
            dates = [datetime.fromisoformat(d['date']).date() for d in session_dates]

            # Calculate current streak
            current_streak = 0
            today = datetime.now().date()
            check_date = today

            for date in dates:
                if date == check_date:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                elif date < check_date:
                    # Gap found
                    break

            # Calculate longest streak
            longest_streak = 1
            current = 1

            for i in range(1, len(dates)):
                if (dates[i-1] - dates[i]).days == 1:
                    current += 1
                    longest_streak = max(longest_streak, current)
                else:
                    current = 1

            return {
                'success': True,
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'total_active_days': len(dates)
            }

        except Exception as e:
            logger.error(f"Failed to calculate streak: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_streak': 0,
                'longest_streak': 0
            }

    def get_productivity_score(self, date: Optional[str] = None) -> float:
        """
        Calculate productivity score for a given date (0-100).

        Args:
            date: Date to calculate (default: today)

        Returns:
            Productivity score
        """
        if not date:
            date = datetime.now().date().isoformat()

        try:
            query = """
            SELECT
                COUNT(*) as session_count,
                SUM(CASE WHEN session_type = 'work' THEN duration_minutes ELSE 0 END) as work_minutes,
                AVG(CASE WHEN session_type = 'work' THEN focus_score ELSE NULL END) as avg_focus_score
            FROM focus_sessions
            WHERE user_id = ?
            AND date(start_time) = ?
            AND completed = 1
            """

            result = self.db.execute_query(
                query,
                (self.user_id, date),
                fetch_one=True
            )

            if not result or result['session_count'] == 0:
                return 0.0

            # Score factors:
            # 1. Number of sessions (max 8 sessions = 40 points)
            # 2. Work time (max 4 hours = 40 points)
            # 3. Focus quality (avg focus score = 20 points)

            session_score = min(40, (result['session_count'] / 8) * 40)
            time_score = min(40, (result['work_minutes'] / 240) * 40)
            focus_score = (result['avg_focus_score'] or 0) * 0.2

            total_score = session_score + time_score + focus_score

            return round(min(100, total_score), 1)

        except Exception as e:
            logger.error(f"Failed to calculate productivity score: {e}")
            return 0.0

    def _update_daily_progress(self, session_data: Dict[str, Any]):
        """
        Update daily progress log with session data.

        Args:
            session_data: Session data
        """
        try:
            today = datetime.now().date().isoformat()

            # Check if progress log exists for today
            query = "SELECT id FROM progress_logs WHERE user_id = ? AND date = ?"
            existing = self.db.execute_query(query, (self.user_id, today), fetch_one=True)

            if existing:
                # Update existing log
                update_query = """
                UPDATE progress_logs
                SET
                    focus_sessions = focus_sessions + 1,
                    time_spent_minutes = time_spent_minutes + ?,
                    productivity_score = ?
                WHERE user_id = ? AND date = ?
                """

                productivity_score = self.get_productivity_score(today)

                self.db.execute_query(
                    update_query,
                    (
                        session_data.get('duration_minutes', 0),
                        productivity_score,
                        self.user_id,
                        today
                    )
                )
            else:
                # Create new log
                insert_query = """
                INSERT INTO progress_logs (
                    id, user_id, date, focus_sessions,
                    time_spent_minutes, productivity_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                productivity_score = self.get_productivity_score(today)

                self.db.execute_query(
                    insert_query,
                    (
                        str(uuid.uuid4()),
                        self.user_id,
                        today,
                        1,
                        session_data.get('duration_minutes', 0),
                        productivity_score,
                        datetime.now().isoformat()
                    )
                )

            logger.debug(f"Updated daily progress for {today}")

        except Exception as e:
            logger.error(f"Failed to update daily progress: {e}")


if __name__ == "__main__":
    print("Testing Session Manager...")

    manager = SessionManager(user_id="test_user")

    # Test save session
    test_session = {
        'session_id': str(uuid.uuid4()),
        'task_id': 'test_task_123',
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(),
        'duration_minutes': 25,
        'session_type': 'work',
        'completed': True,
        'interruptions': 1,
        'focus_score': 90.0
    }

    result = manager.save_session(test_session)
    print(f"Save result: {result}")

    # Test get today's sessions
    today = manager.get_today_sessions()
    print(f"Today's sessions: {today}")

    # Test streak calculation
    streak = manager.calculate_streak()
    print(f"Streak: {streak}")

    print("\nSession Manager validated!")
