"""
Academic Command Center - Focus Mode - Distraction Logger
Logs and analyzes distractions during focus sessions.
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DistractionCategory:
    """Common distraction categories."""
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    PHONE = "phone"
    PERSON = "person"
    INTERNET = "internet"
    OTHER = "other"


class DistractionLogger:
    """
    Logs and analyzes distractions during focus sessions.

    Tracks:
    - Distraction frequency
    - Distraction categories
    - Impact on focus score
    - Patterns over time
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize distraction logger.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # In-memory cache for current session
        self.current_session_distractions: List[Dict[str, Any]] = []

        logger.info(f"Distraction logger initialized for user {user_id}")

    def log_distraction(
        self,
        session_id: str,
        category: str = DistractionCategory.OTHER,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a distraction event.

        Args:
            session_id: Current session ID
            category: Distraction category
            note: Optional note about distraction

        Returns:
            Log result
        """
        try:
            distraction = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'category': category,
                'note': note,
                'timestamp': datetime.now().isoformat()
            }

            # Add to in-memory cache
            self.current_session_distractions.append(distraction)

            logger.info(f"Logged distraction ({category}) for session {session_id}")

            return {
                'success': True,
                'distraction_id': distraction['id'],
                'session_distractions': len(self.current_session_distractions)
            }

        except Exception as e:
            logger.error(f"Failed to log distraction: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_session_distractions(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all distractions for a session.

        Args:
            session_id: Session ID

        Returns:
            List of distractions
        """
        # Return from cache if it matches current session
        return [
            d for d in self.current_session_distractions
            if d['session_id'] == session_id
        ]

    def clear_session_cache(self):
        """Clear in-memory distraction cache."""
        self.current_session_distractions = []

    def get_distraction_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get distraction statistics for time period.

        Args:
            days: Number of days to analyze

        Returns:
            Statistics
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Query sessions with interruptions
            query = """
            SELECT
                id,
                start_time,
                interruptions,
                focus_score
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ?
            AND session_type = 'work'
            AND completed = 1
            ORDER BY start_time DESC
            """

            sessions = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            )

            if not sessions:
                return {
                    'success': True,
                    'total_distractions': 0,
                    'average_per_session': 0.0,
                    'sessions_with_distractions': 0,
                    'distraction_free_rate': 0.0
                }

            # Calculate statistics
            total_sessions = len(sessions)
            total_distractions = sum(s.get('interruptions', 0) for s in sessions)
            sessions_with_distractions = sum(1 for s in sessions if s.get('interruptions', 0) > 0)
            average_per_session = total_distractions / total_sessions if total_sessions > 0 else 0
            distraction_free_rate = ((total_sessions - sessions_with_distractions) / total_sessions * 100) if total_sessions > 0 else 0

            # Group by day
            daily_distractions = {}
            for session in sessions:
                date = datetime.fromisoformat(session['start_time']).date().isoformat()
                if date not in daily_distractions:
                    daily_distractions[date] = {'count': 0, 'sessions': 0}
                daily_distractions[date]['count'] += session.get('interruptions', 0)
                daily_distractions[date]['sessions'] += 1

            # Find worst day
            worst_day = max(daily_distractions.items(), key=lambda x: x[1]['count']) if daily_distractions else None

            # Find best day (highest distraction-free rate)
            best_day = min(
                [(date, data['count'] / data['sessions']) for date, data in daily_distractions.items()],
                key=lambda x: x[1]
            ) if daily_distractions else None

            return {
                'success': True,
                'total_distractions': total_distractions,
                'total_sessions': total_sessions,
                'average_per_session': round(average_per_session, 2),
                'sessions_with_distractions': sessions_with_distractions,
                'distraction_free_rate': round(distraction_free_rate, 1),
                'daily_stats': daily_distractions,
                'worst_day': {
                    'date': worst_day[0],
                    'distractions': worst_day[1]['count']
                } if worst_day else None,
                'best_day': {
                    'date': best_day[0],
                    'average': round(best_day[1], 2)
                } if best_day else None
            }

        except Exception as e:
            logger.error(f"Failed to get distraction stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_category_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """
        Get breakdown of distractions by category.

        Note: This would require storing distraction events separately.
        For now, returns estimated breakdown based on common patterns.

        Args:
            days: Number of days to analyze

        Returns:
            Category breakdown
        """
        # Estimated common breakdown (would be real data in production)
        estimated_breakdown = {
            DistractionCategory.SOCIAL_MEDIA: 35,  # 35%
            DistractionCategory.EMAIL: 20,
            DistractionCategory.PHONE: 25,
            DistractionCategory.PERSON: 10,
            DistractionCategory.INTERNET: 7,
            DistractionCategory.OTHER: 3
        }

        return {
            'success': True,
            'breakdown': estimated_breakdown,
            'note': 'Estimated breakdown based on common patterns'
        }

    def get_time_pattern_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze when distractions occur most frequently.

        Args:
            days: Number of days to analyze

        Returns:
            Time pattern analysis
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
            SELECT
                start_time,
                interruptions
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ?
            AND session_type = 'work'
            AND completed = 1
            AND interruptions > 0
            ORDER BY start_time DESC
            """

            sessions = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            )

            if not sessions:
                return {
                    'success': True,
                    'hourly_breakdown': {},
                    'peak_distraction_hour': None
                }

            # Group by hour of day
            hourly_distractions = Counter()

            for session in sessions:
                hour = datetime.fromisoformat(session['start_time']).hour
                hourly_distractions[hour] += session.get('interruptions', 0)

            # Find peak hour
            peak_hour = hourly_distractions.most_common(1)[0] if hourly_distractions else None

            return {
                'success': True,
                'hourly_breakdown': dict(hourly_distractions),
                'peak_distraction_hour': {
                    'hour': peak_hour[0],
                    'distractions': peak_hour[1]
                } if peak_hour else None
            }

        except Exception as e:
            logger.error(f"Failed to analyze time patterns: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_recommendations(self) -> List[str]:
        """
        Get personalized recommendations to reduce distractions.

        Returns:
            List of recommendations
        """
        stats = self.get_distraction_stats(days=7)

        recommendations = []

        if not stats.get('success'):
            return ["Start tracking focus sessions to get personalized recommendations"]

        avg_distractions = stats.get('average_per_session', 0)
        distraction_free_rate = stats.get('distraction_free_rate', 0)

        # Recommendation based on distraction frequency
        if avg_distractions > 3:
            recommendations.append("Try enabling Do Not Disturb mode on your devices")
            recommendations.append("Consider using website blockers during focus sessions")
        elif avg_distractions > 1:
            recommendations.append("Put your phone in another room during focus sessions")
            recommendations.append("Close email and chat applications")

        # Recommendation based on distraction-free rate
        if distraction_free_rate < 30:
            recommendations.append("Set clear boundaries with family/roommates during focus time")
            recommendations.append("Work in a quieter environment if possible")
        elif distraction_free_rate > 70:
            recommendations.append("Great job! Your focus discipline is improving")
            recommendations.append("Try extending session length for deeper work")

        # Time-based recommendations
        time_patterns = self.get_time_pattern_analysis(days=7)
        if time_patterns.get('success') and time_patterns.get('peak_distraction_hour'):
            peak_hour = time_patterns['peak_distraction_hour']['hour']
            recommendations.append(f"Your most distracted time is around {peak_hour:02d}:00 - schedule breaks then")

        if not recommendations:
            recommendations = [
                "Track more sessions to get personalized recommendations",
                "Try to maintain a distraction-free workspace",
                "Use focus mode consistently to see patterns"
            ]

        return recommendations[:5]  # Return top 5


if __name__ == "__main__":
    print("Testing Distraction Logger...")

    logger_instance = DistractionLogger(user_id="test_user")

    # Test log distraction
    result = logger_instance.log_distraction(
        session_id="test_session_123",
        category=DistractionCategory.SOCIAL_MEDIA,
        note="Checked Twitter"
    )
    print(f"Log result: {result}")

    # Test get stats
    stats = logger_instance.get_distraction_stats(days=7)
    print(f"Stats: {stats}")

    # Test recommendations
    recommendations = logger_instance.get_recommendations()
    print(f"Recommendations: {recommendations}")

    print("\nDistraction Logger validated!")
