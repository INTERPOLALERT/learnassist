"""
Calendar Manager - Phase 5 Sprint 1
Aggregates events from assignments, sessions, and goals
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from calendar import monthrange

logger = logging.getLogger(__name__)


class CalendarManager:
    """
    Manages calendar events from multiple sources.

    Aggregates assignments, study sessions, and goals into unified calendar events.
    """

    def __init__(self, db_manager, user_id: str):
        """
        Initialize Calendar Manager.

        Args:
            db_manager: DatabaseManager instance
            user_id: Current user ID
        """
        self.db = db_manager
        self.user_id = user_id
        logger.info(f"Calendar Manager initialized for user {user_id}")

    def get_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get all calendar events in date range.

        Args:
            start_date: Start of range
            end_date: End of range

        Returns:
            List of event dictionaries with keys:
                - id: Event ID
                - title: Event title
                - date: Event datetime
                - type: Event type (assignment, session, goal)
                - color: Display color
                - metadata: Type-specific data
        """
        events = []

        # Get assignments
        events.extend(self._get_assignment_events(start_date, end_date))

        # Get study sessions
        events.extend(self._get_session_events(start_date, end_date))

        # Get goal deadlines
        events.extend(self._get_goal_events(start_date, end_date))

        # Sort by date
        events.sort(key=lambda e: e['date'])

        return events

    def get_events_for_date(self, date: datetime) -> List[Dict[str, Any]]:
        """
        Get all events for a specific date.

        Args:
            date: Date to get events for

        Returns:
            List of events
        """
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return self.get_events(start, end)

    def get_events_for_month(self, year: int, month: int) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get all events for a month, grouped by day.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            Dictionary mapping day (1-31) to list of events
        """
        start_date = datetime(year, month, 1)
        days_in_month = monthrange(year, month)[1]
        end_date = datetime(year, month, days_in_month, 23, 59, 59)

        events = self.get_events(start_date, end_date)

        # Group by day
        events_by_day = {}
        for event in events:
            day = event['date'].day
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

        return events_by_day

    def get_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get calendar statistics for date range.

        Args:
            start_date: Start of range
            end_date: End of range

        Returns:
            Dictionary with statistics
        """
        events = self.get_events(start_date, end_date)

        stats = {
            'total_events': len(events),
            'assignments': len([e for e in events if e['type'] == 'assignment']),
            'sessions': len([e for e in events if e['type'] == 'session']),
            'goals': len([e for e in events if e['type'] == 'goal']),
            'overdue_assignments': 0,
            'completed_assignments': 0
        }

        # Count assignment statuses
        for event in events:
            if event['type'] == 'assignment':
                if event['metadata'].get('is_overdue'):
                    stats['overdue_assignments'] += 1
                if event['metadata'].get('status') in ['completed', 'submitted']:
                    stats['completed_assignments'] += 1

        return stats

    def _get_assignment_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get assignment due date events."""
        try:
            query = """
                SELECT a.id, a.title, a.due_date, a.status, a.priority,
                       s.name as subject_name, s.color as subject_color
                FROM assignments a
                LEFT JOIN subjects s ON a.subject_id = s.id
                WHERE a.user_id = ?
                  AND a.due_date IS NOT NULL
                  AND datetime(a.due_date) >= datetime(?)
                  AND datetime(a.due_date) <= datetime(?)
                ORDER BY a.due_date
            """

            results = self.db.fetch_all(
                query,
                (self.user_id, start_date.isoformat(), end_date.isoformat())
            )

            events = []
            for row in results:
                due_date = datetime.fromisoformat(row[2].replace('Z', '+00:00'))
                status = row[3]
                priority = row[4]

                # Determine color based on status and priority
                if status in ['completed', 'submitted']:
                    color = '#27ae60'  # Green
                elif due_date < datetime.now():
                    color = '#e74c3c'  # Red (overdue)
                elif priority == 'high':
                    color = '#e74c3c'  # Red
                elif priority == 'medium':
                    color = '#f39c12'  # Orange
                else:
                    color = '#3498db'  # Blue

                # Use subject color if available
                if row[6]:
                    color = row[6]

                events.append({
                    'id': f"assignment_{row[0]}",
                    'title': row[1],
                    'date': due_date,
                    'type': 'assignment',
                    'color': color,
                    'metadata': {
                        'assignment_id': row[0],
                        'status': status,
                        'priority': priority,
                        'subject_name': row[5],
                        'is_overdue': due_date < datetime.now() and status not in ['completed', 'submitted']
                    }
                })

            return events

        except Exception as e:
            logger.error(f"Failed to get assignment events: {e}")
            return []

    def _get_session_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get study session events."""
        try:
            query = """
                SELECT f.id, f.start_time, f.duration, f.subject,
                       s.name as subject_name, s.color as subject_color
                FROM focus_sessions f
                LEFT JOIN subjects s ON f.subject = s.id
                WHERE f.user_id = ?
                  AND datetime(f.start_time) >= datetime(?)
                  AND datetime(f.start_time) <= datetime(?)
                ORDER BY f.start_time
            """

            results = self.db.fetch_all(
                query,
                (self.user_id, start_date.isoformat(), end_date.isoformat())
            )

            events = []
            for row in results:
                start_time = datetime.fromisoformat(row[1].replace('Z', '+00:00'))
                duration = row[2] or 0
                subject_name = row[4] or "Study Session"
                color = row[5] or '#9b59b6'  # Purple default

                # Format title with duration
                hours = duration // 60
                minutes = duration % 60
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m"
                else:
                    duration_str = f"{minutes}m"

                events.append({
                    'id': f"session_{row[0]}",
                    'title': f"{subject_name} ({duration_str})",
                    'date': start_time,
                    'type': 'session',
                    'color': color,
                    'metadata': {
                        'session_id': row[0],
                        'duration': duration,
                        'subject_name': subject_name
                    }
                })

            return events

        except Exception as e:
            logger.error(f"Failed to get session events: {e}")
            return []

    def _get_goal_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get goal deadline events."""
        try:
            query = """
                SELECT id, title, target_date, status, category
                FROM goals
                WHERE user_id = ?
                  AND target_date IS NOT NULL
                  AND date(target_date) >= date(?)
                  AND date(target_date) <= date(?)
                ORDER BY target_date
            """

            results = self.db.fetch_all(
                query,
                (self.user_id, start_date.date().isoformat(), end_date.date().isoformat())
            )

            events = []
            for row in results:
                try:
                    # Parse target_date (might be date or datetime string)
                    target_str = row[2]
                    if 'T' in target_str or ' ' in target_str:
                        # DateTime format
                        target_date = datetime.fromisoformat(target_str.replace('Z', '+00:00'))
                    else:
                        # Date only format
                        target_date = datetime.fromisoformat(target_str + 'T00:00:00')
                except:
                    continue

                status = row[3]
                category = row[4]

                # Determine color based on status
                if status == 'completed':
                    color = '#27ae60'  # Green
                elif target_date < datetime.now():
                    color = '#e74c3c'  # Red (overdue)
                else:
                    color = '#f39c12'  # Orange

                events.append({
                    'id': f"goal_{row[0]}",
                    'title': f"🎯 {row[1]}",
                    'date': target_date,
                    'type': 'goal',
                    'color': color,
                    'metadata': {
                        'goal_id': row[0],
                        'status': status,
                        'category': category
                    }
                })

            return events

        except Exception as e:
            logger.error(f"Failed to get goal events: {e}")
            return []
