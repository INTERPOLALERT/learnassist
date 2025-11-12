"""
Study Analytics - Phase 6 Sprint 3
Comprehensive study pattern analysis and productivity metrics.

Features:
- Study time tracking and analysis
- Productivity metrics
- Focus session insights
- Study pattern detection
- Peak performance times
- Study streak tracking

Author: Academic Command Center
Phase: 6 Sprint 3
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class StudySession:
    """Study session data."""
    session_id: str
    subject: str
    duration_minutes: int
    start_time: str
    end_time: str
    productivity_score: float
    focus_level: str


@dataclass
class StudyPattern:
    """Study pattern analysis."""
    total_study_time_minutes: int
    average_session_minutes: float
    session_count: int
    most_productive_hour: int
    most_productive_day: str
    study_consistency: float
    peak_focus_times: List[int]


@dataclass
class ProductivityMetrics:
    """Productivity measurements."""
    overall_productivity: float
    time_efficiency: float
    focus_quality: float
    consistency_score: float
    output_per_hour: float


@dataclass
class StudyStreak:
    """Study streak data."""
    current_streak: int
    longest_streak: int
    last_study_date: str
    streak_active: bool


class StudyAnalytics:
    """
    Study Analytics Engine.

    Provides:
    - Time tracking analysis
    - Productivity metrics
    - Study pattern detection
    - Focus insights
    - Streak tracking
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Study Analytics.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Study Analytics initialized for user {user_id}")

    def get_study_overview(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive study overview.

        Args:
            days: Period to analyze

        Returns:
            Study overview data
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get session statistics
            query = """
            SELECT
                COUNT(*) as session_count,
                SUM(duration_minutes) as total_minutes,
                AVG(duration_minutes) as avg_minutes,
                MIN(duration_minutes) as min_minutes,
                MAX(duration_minutes) as max_minutes
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            """

            stats = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_one=True
            )

            session_count = stats['session_count'] or 0
            total_minutes = stats['total_minutes'] or 0
            avg_minutes = stats['avg_minutes'] or 0

            # Calculate daily statistics
            daily_avg = total_minutes / days
            weekly_total = (total_minutes / days) * 7

            # Get subject distribution
            subject_query = """
            SELECT subject, SUM(duration_minutes) as minutes
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            GROUP BY subject
            ORDER BY minutes DESC
            LIMIT 5
            """

            subjects = self.db.execute_query(
                subject_query,
                (self.user_id, start_date),
                fetch_all=True
            ) or []

            subject_distribution = []
            for subj in subjects:
                subject_distribution.append({
                    'subject': subj['subject'],
                    'minutes': subj['minutes'],
                    'hours': round(subj['minutes'] / 60, 1),
                    'percentage': round((subj['minutes'] / total_minutes * 100) if total_minutes > 0 else 0, 1)
                })

            return {
                'success': True,
                'period_days': days,
                'total_study_time': {
                    'minutes': total_minutes,
                    'hours': round(total_minutes / 60, 1)
                },
                'session_count': session_count,
                'average_session': {
                    'minutes': round(avg_minutes, 1),
                    'hours': round(avg_minutes / 60, 2)
                },
                'daily_average': {
                    'minutes': round(daily_avg, 1),
                    'hours': round(daily_avg / 60, 1)
                },
                'weekly_average': {
                    'minutes': round(weekly_total, 1),
                    'hours': round(weekly_total / 60, 1)
                },
                'session_range': {
                    'min_minutes': stats['min_minutes'] or 0,
                    'max_minutes': stats['max_minutes'] or 0
                },
                'subject_distribution': subject_distribution
            }

        except Exception as e:
            logger.error(f"Failed to get study overview: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def analyze_study_patterns(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze study patterns and habits.

        Args:
            days: Period to analyze

        Returns:
            Pattern analysis
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get all sessions with timestamps
            query = """
            SELECT
                start_time,
                duration_minutes,
                subject
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            ORDER BY start_time ASC
            """

            sessions = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            ) or []

            if not sessions:
                return {
                    'success': True,
                    'message': 'No study sessions in period'
                }

            # Analyze by hour of day
            hour_distribution = defaultdict(int)
            day_distribution = defaultdict(int)
            daily_sessions = defaultdict(int)

            for session in sessions:
                try:
                    dt = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                    hour_distribution[dt.hour] += session['duration_minutes']
                    day_distribution[dt.strftime('%A')] += session['duration_minutes']
                    daily_sessions[dt.date().isoformat()] += 1
                except:
                    continue

            # Find most productive hour
            most_productive_hour = max(hour_distribution, key=hour_distribution.get) if hour_distribution else 9

            # Find most productive day
            most_productive_day = max(day_distribution, key=day_distribution.get) if day_distribution else 'Monday'

            # Calculate consistency (days with sessions / total days)
            days_with_sessions = len(daily_sessions)
            consistency = (days_with_sessions / days) * 100

            # Find peak focus times (hours with most study time)
            sorted_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)
            peak_focus_times = [hour for hour, _ in sorted_hours[:3]]

            # Convert to 12-hour format for display
            def format_hour(h):
                if h == 0:
                    return "12 AM"
                elif h < 12:
                    return f"{h} AM"
                elif h == 12:
                    return "12 PM"
                else:
                    return f"{h-12} PM"

            # Format hour distribution for chart
            hour_chart = []
            for hour in range(24):
                minutes = hour_distribution.get(hour, 0)
                if minutes > 0:
                    hour_chart.append({
                        'hour': hour,
                        'hour_label': format_hour(hour),
                        'minutes': minutes,
                        'hours': round(minutes / 60, 1)
                    })

            # Format day distribution
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_chart = []
            for day in days_order:
                minutes = day_distribution.get(day, 0)
                day_chart.append({
                    'day': day,
                    'minutes': minutes,
                    'hours': round(minutes / 60, 1)
                })

            return {
                'success': True,
                'period_days': days,
                'most_productive_hour': most_productive_hour,
                'most_productive_hour_label': format_hour(most_productive_hour),
                'most_productive_day': most_productive_day,
                'study_consistency': round(consistency, 1),
                'days_with_sessions': days_with_sessions,
                'peak_focus_times': [format_hour(h) for h in peak_focus_times],
                'hourly_distribution': hour_chart,
                'daily_distribution': day_chart
            }

        except Exception as e:
            logger.error(f"Failed to analyze study patterns: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_productivity_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate productivity metrics.

        Args:
            days: Period to analyze

        Returns:
            Productivity metrics
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get study time and grades
            query = """
            SELECT
                SUM(fs.duration_minutes) as total_minutes,
                COUNT(DISTINCT fs.id) as session_count,
                AVG(a.grade) as avg_grade,
                COUNT(DISTINCT a.id) as assignment_count
            FROM focus_sessions fs
            LEFT JOIN assignments a ON a.user_id = fs.user_id
                AND a.status = 'completed'
                AND DATE(a.updated_at) >= DATE(fs.start_time)
            WHERE fs.user_id = ? AND fs.start_time >= ?
            """

            data = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_one=True
            )

            total_minutes = data['total_minutes'] or 0
            session_count = data['session_count'] or 0
            avg_grade = data['avg_grade'] or 0
            assignment_count = data['assignment_count'] or 0

            if total_minutes == 0:
                return {
                    'success': True,
                    'message': 'No study time recorded'
                }

            # Calculate metrics
            total_hours = total_minutes / 60

            # Time efficiency (assignments per hour)
            time_efficiency = assignment_count / total_hours if total_hours > 0 else 0

            # Focus quality (based on session length consistency)
            avg_session = total_minutes / session_count if session_count > 0 else 0
            if 25 <= avg_session <= 50:  # Pomodoro range
                focus_quality = 95
            elif 15 <= avg_session <= 90:
                focus_quality = 80
            else:
                focus_quality = 60

            # Output per hour (grade points per hour)
            output_per_hour = avg_grade / total_hours if total_hours > 0 else 0

            # Consistency score
            consistency_query = """
            SELECT COUNT(DISTINCT DATE(start_time)) as study_days
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            """

            consistency_data = self.db.execute_query(
                consistency_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            study_days = consistency_data['study_days'] or 0
            consistency_score = (study_days / days) * 100

            # Overall productivity (weighted average)
            overall_productivity = (
                time_efficiency * 10 +  # Assignments/hour * 10
                (focus_quality / 100) * 30 +  # Focus quality (0-30)
                consistency_score * 0.4 +  # Consistency (0-40)
                min(30, avg_grade / 3)  # Grade contribution (0-30)
            )

            return {
                'success': True,
                'period_days': days,
                'overall_productivity': round(overall_productivity, 1),
                'time_efficiency': round(time_efficiency, 2),
                'focus_quality': round(focus_quality, 1),
                'consistency_score': round(consistency_score, 1),
                'output_per_hour': round(output_per_hour, 2),
                'metrics_breakdown': {
                    'total_study_hours': round(total_hours, 1),
                    'session_count': session_count,
                    'assignments_completed': assignment_count,
                    'average_grade': round(avg_grade, 1),
                    'study_days': study_days
                }
            }

        except Exception as e:
            logger.error(f"Failed to calculate productivity: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def track_study_streak(self) -> Dict[str, Any]:
        """
        Track study streak.

        Returns:
            Streak data
        """
        try:
            # Get all study dates
            query = """
            SELECT DISTINCT DATE(start_time) as study_date
            FROM focus_sessions
            WHERE user_id = ?
            ORDER BY study_date DESC
            """

            dates = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_all=True
            ) or []

            if not dates:
                return {
                    'success': True,
                    'current_streak': 0,
                    'longest_streak': 0,
                    'streak_active': False,
                    'message': 'No study sessions recorded'
                }

            # Calculate current streak
            current_streak = 0
            today = datetime.now().date()
            expected_date = today

            for date_row in dates:
                study_date = datetime.strptime(date_row['study_date'], '%Y-%m-%d').date()

                if study_date == expected_date:
                    current_streak += 1
                    expected_date = study_date - timedelta(days=1)
                elif study_date < expected_date:
                    break

            # Calculate longest streak
            longest_streak = 0
            temp_streak = 1

            for i in range(len(dates) - 1):
                date1 = datetime.strptime(dates[i]['study_date'], '%Y-%m-%d').date()
                date2 = datetime.strptime(dates[i+1]['study_date'], '%Y-%m-%d').date()

                if (date1 - date2).days == 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1

            longest_streak = max(longest_streak, current_streak)

            # Check if streak is active (studied today or yesterday)
            last_study_date = datetime.strptime(dates[0]['study_date'], '%Y-%m-%d').date()
            days_since_last = (today - last_study_date).days
            streak_active = days_since_last <= 1

            return {
                'success': True,
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'last_study_date': dates[0]['study_date'],
                'days_since_last_session': days_since_last,
                'streak_active': streak_active,
                'milestone': self._get_streak_milestone(current_streak)
            }

        except Exception as e:
            logger.error(f"Failed to track study streak: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_focus_insights(self, days: int = 30) -> Dict[str, Any]:
        """
        Get focus session insights.

        Args:
            days: Period to analyze

        Returns:
            Focus insights
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get session duration distribution
            query = """
            SELECT duration_minutes
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            """

            sessions = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            ) or []

            if not sessions:
                return {
                    'success': True,
                    'message': 'No focus sessions in period'
                }

            durations = [s['duration_minutes'] for s in sessions]

            # Categorize session lengths
            short_sessions = len([d for d in durations if d < 20])
            ideal_sessions = len([d for d in durations if 20 <= d <= 50])  # Pomodoro range
            long_sessions = len([d for d in durations if d > 50])

            total_sessions = len(durations)

            # Calculate insights
            avg_duration = sum(durations) / len(durations)

            # Determine focus level
            ideal_percentage = (ideal_sessions / total_sessions * 100) if total_sessions > 0 else 0

            if ideal_percentage >= 70:
                focus_level = "excellent"
                focus_feedback = "Your focus sessions are well-optimized for productivity"
            elif ideal_percentage >= 50:
                focus_level = "good"
                focus_feedback = "Most sessions are in a productive range"
            elif short_sessions > ideal_sessions + long_sessions:
                focus_level = "needs_improvement"
                focus_feedback = "Consider longer focus sessions for better retention"
            else:
                focus_level = "fair"
                focus_feedback = "Mix of session lengths - aim for 20-50 minute sessions"

            return {
                'success': True,
                'period_days': days,
                'total_sessions': total_sessions,
                'average_duration_minutes': round(avg_duration, 1),
                'session_distribution': {
                    'short': short_sessions,
                    'short_percentage': round((short_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
                    'ideal': ideal_sessions,
                    'ideal_percentage': round(ideal_percentage, 1),
                    'long': long_sessions,
                    'long_percentage': round((long_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1)
                },
                'focus_level': focus_level,
                'feedback': focus_feedback,
                'recommendation': self._get_focus_recommendation(short_sessions, ideal_sessions, long_sessions)
            }

        except Exception as e:
            logger.error(f"Failed to get focus insights: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_streak_milestone(self, streak: int) -> Optional[str]:
        """Get streak milestone message."""
        if streak >= 100:
            return "Legendary! 100+ day streak!"
        elif streak >= 50:
            return "Amazing! 50+ day streak!"
        elif streak >= 30:
            return "Impressive! 30+ day streak!"
        elif streak >= 14:
            return "Great! 2+ week streak!"
        elif streak >= 7:
            return "Good job! 1+ week streak!"
        elif streak >= 3:
            return "Building momentum! 3+ days!"
        elif streak > 0:
            return "Keep it up!"
        return None

    def _get_focus_recommendation(self, short: int, ideal: int, long: int) -> str:
        """Get focus session recommendation."""
        if short > ideal and short > long:
            return "Try extending sessions to 25-50 minutes using the Pomodoro technique"
        elif long > ideal and long > short:
            return "Consider breaking long sessions into 25-50 minute chunks with breaks"
        elif ideal > short + long:
            return "Excellent session lengths! Keep maintaining this rhythm"
        else:
            return "Aim for more sessions in the 20-50 minute range for optimal focus"


def create_study_analytics(
    user_id: str,
    db_manager: Optional[DatabaseManager] = None
) -> StudyAnalytics:
    """
    Factory function to create Study Analytics.

    Args:
        user_id: Current user ID
        db_manager: Database manager instance

    Returns:
        StudyAnalytics instance
    """
    return StudyAnalytics(user_id, db_manager)
