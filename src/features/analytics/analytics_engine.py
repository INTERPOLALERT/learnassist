"""
Academic Command Center - Analytics - Analytics Engine
Processes data and generates insights about productivity and performance.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Processes academic data and generates insights.

    Analyzes:
    - Focus session patterns
    - Task completion trends
    - Essay writing progress
    - Productivity scores
    - Study time distribution
    - Performance trends
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize analytics engine.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Analytics engine initialized for user {user_id}")

    def get_productivity_overview(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive productivity overview.

        Args:
            days: Number of days to analyze

        Returns:
            Productivity overview
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get focus sessions data
            focus_query = """
            SELECT
                COUNT(*) as total_sessions,
                SUM(CASE WHEN session_type = 'work' THEN 1 ELSE 0 END) as work_sessions,
                SUM(CASE WHEN session_type = 'work' THEN duration_minutes ELSE 0 END) as total_minutes,
                AVG(CASE WHEN session_type = 'work' THEN focus_score ELSE NULL END) as avg_focus_score,
                SUM(interruptions) as total_interruptions
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ?
            AND completed = 1
            """

            focus_data = self.db.execute_query(
                focus_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            # Get tasks data
            tasks_query = """
            SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks
            FROM tasks
            WHERE user_id = ?
            AND created_at >= ?
            """

            tasks_data = self.db.execute_query(
                tasks_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            # Get essays data
            essays_query = """
            SELECT
                COUNT(*) as total_essays,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_essays,
                AVG(word_count) as avg_word_count
            FROM essays
            WHERE user_id = ?
            AND created_at >= ?
            """

            essays_data = self.db.execute_query(
                essays_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            # Calculate metrics
            work_sessions = focus_data['work_sessions'] or 0
            total_hours = (focus_data['total_minutes'] or 0) / 60
            avg_focus = focus_data['avg_focus_score'] or 0
            task_completion_rate = (tasks_data['completed_tasks'] / tasks_data['total_tasks'] * 100) if tasks_data['total_tasks'] > 0 else 0

            return {
                'success': True,
                'period_days': days,
                'focus': {
                    'work_sessions': work_sessions,
                    'total_hours': round(total_hours, 1),
                    'avg_focus_score': round(avg_focus, 1),
                    'total_interruptions': focus_data['total_interruptions'] or 0,
                    'avg_session_length': round((focus_data['total_minutes'] or 0) / work_sessions, 1) if work_sessions > 0 else 0
                },
                'tasks': {
                    'total': tasks_data['total_tasks'] or 0,
                    'completed': tasks_data['completed_tasks'] or 0,
                    'in_progress': tasks_data['in_progress_tasks'] or 0,
                    'completion_rate': round(task_completion_rate, 1)
                },
                'essays': {
                    'total': essays_data['total_essays'] or 0,
                    'completed': essays_data['completed_essays'] or 0,
                    'avg_word_count': round(essays_data['avg_word_count'] or 0)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get productivity overview: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_daily_trends(self, days: int = 14) -> Dict[str, Any]:
        """
        Get daily productivity trends.

        Args:
            days: Number of days to analyze

        Returns:
            Daily trends data
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).date().isoformat()

            query = """
            SELECT
                date,
                focus_sessions,
                time_spent_minutes,
                productivity_score,
                tasks_completed
            FROM progress_logs
            WHERE user_id = ?
            AND date >= ?
            ORDER BY date ASC
            """

            daily_data = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            )

            if not daily_data:
                return {
                    'success': True,
                    'daily_data': [],
                    'trend': 'no_data'
                }

            # Calculate trend (comparing first half vs second half)
            mid_point = len(daily_data) // 2
            if mid_point > 0:
                first_half_avg = sum(d['productivity_score'] for d in daily_data[:mid_point]) / mid_point
                second_half_avg = sum(d['productivity_score'] for d in daily_data[mid_point:]) / (len(daily_data) - mid_point)

                if second_half_avg > first_half_avg * 1.1:
                    trend = 'improving'
                elif second_half_avg < first_half_avg * 0.9:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'

            return {
                'success': True,
                'daily_data': daily_data,
                'trend': trend,
                'days_analyzed': len(daily_data)
            }

        except Exception as e:
            logger.error(f"Failed to get daily trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_time_distribution(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze time distribution across different activities.

        Args:
            days: Number of days to analyze

        Returns:
            Time distribution data
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get focus time by hour of day
            hourly_query = """
            SELECT
                CAST(strftime('%H', start_time) AS INTEGER) as hour,
                COUNT(*) as session_count,
                SUM(duration_minutes) as total_minutes
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ?
            AND completed = 1
            GROUP BY hour
            ORDER BY hour
            """

            hourly_data = self.db.execute_query(
                hourly_query,
                (self.user_id, start_date),
                fetch_all=True
            )

            # Get time by day of week
            weekly_query = """
            SELECT
                CAST(strftime('%w', start_time) AS INTEGER) as day_of_week,
                COUNT(*) as session_count,
                SUM(duration_minutes) as total_minutes
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ?
            AND completed = 1
            GROUP BY day_of_week
            ORDER BY day_of_week
            """

            weekly_data = self.db.execute_query(
                weekly_query,
                (self.user_id, start_date),
                fetch_all=True
            )

            # Find peak hours
            if hourly_data:
                peak_hour = max(hourly_data, key=lambda x: x['total_minutes'])
            else:
                peak_hour = None

            # Find most productive day
            if weekly_data:
                peak_day = max(weekly_data, key=lambda x: x['total_minutes'])
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                peak_day['day_name'] = day_names[peak_day['day_of_week']]
            else:
                peak_day = None

            return {
                'success': True,
                'hourly_distribution': hourly_data or [],
                'weekly_distribution': weekly_data or [],
                'peak_hour': peak_hour,
                'peak_day': peak_day
            }

        except Exception as e:
            logger.error(f"Failed to get time distribution: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_performance_insights(self) -> Dict[str, Any]:
        """
        Generate personalized performance insights.

        Returns:
            Performance insights and recommendations
        """
        try:
            # Get recent performance data
            overview_30 = self.get_productivity_overview(days=30)
            overview_7 = self.get_productivity_overview(days=7)
            trends = self.get_daily_trends(days=14)
            time_dist = self.get_time_distribution(days=30)

            insights = []
            recommendations = []

            if not overview_30['success']:
                return {
                    'success': True,
                    'insights': ['Start tracking your sessions to get personalized insights!'],
                    'recommendations': []
                }

            # Insight 1: Focus session consistency
            sessions_30 = overview_30['focus']['work_sessions']
            sessions_7 = overview_7['focus']['work_sessions']

            if sessions_30 > 0:
                avg_daily_sessions = sessions_30 / 30
                if avg_daily_sessions >= 3:
                    insights.append(f"Excellent consistency! You average {avg_daily_sessions:.1f} focus sessions per day")
                elif avg_daily_sessions >= 1.5:
                    insights.append(f"Good progress with {avg_daily_sessions:.1f} daily sessions on average")
                else:
                    insights.append(f"Your session frequency is {avg_daily_sessions:.1f} per day - room for improvement")
                    recommendations.append("Try to complete at least 2-3 focus sessions per day")

            # Insight 2: Focus quality
            avg_focus = overview_30['focus']['avg_focus_score']
            if avg_focus > 0:
                if avg_focus >= 85:
                    insights.append(f"Outstanding focus quality! {avg_focus:.0f}% average score")
                elif avg_focus >= 70:
                    insights.append(f"Good focus quality at {avg_focus:.0f}%")
                else:
                    insights.append(f"Focus score is {avg_focus:.0f}% - distractions are impacting quality")
                    recommendations.append("Try enabling Do Not Disturb mode during focus sessions")

            # Insight 3: Task completion
            task_rate = overview_30['tasks']['completion_rate']
            if task_rate > 0:
                if task_rate >= 70:
                    insights.append(f"Strong task completion rate of {task_rate:.0f}%")
                else:
                    insights.append(f"Task completion at {task_rate:.0f}% - consider breaking tasks into smaller pieces")
                    recommendations.append("Break large tasks into smaller, manageable subtasks")

            # Insight 4: Productivity trend
            if trends['success'] and trends['trend'] != 'no_data':
                if trends['trend'] == 'improving':
                    insights.append("Your productivity is trending upward! Keep it up!")
                elif trends['trend'] == 'declining':
                    insights.append("Productivity has declined recently - let's get back on track")
                    recommendations.append("Review your goals and adjust your study schedule")

            # Insight 5: Time optimization
            if time_dist['success'] and time_dist['peak_hour']:
                peak_hour = time_dist['peak_hour']['hour']
                insights.append(f"Your most productive time is around {peak_hour:02d}:00")
                recommendations.append(f"Schedule important tasks during your peak hours ({peak_hour:02d}:00)")

            # Insight 6: Weekly pattern
            if time_dist['success'] and time_dist['peak_day']:
                peak_day_name = time_dist['peak_day']['day_name']
                insights.append(f"{peak_day_name} is your most productive day")

            # Default insights if no data
            if not insights:
                insights = [
                    "Start tracking sessions to unlock personalized insights",
                    "Complete tasks to see your productivity patterns",
                    "Maintain consistency for at least 7 days for meaningful analysis"
                ]
                recommendations = [
                    "Set a daily goal of 2-3 focus sessions",
                    "Track your progress regularly",
                    "Build a consistent study routine"
                ]

            return {
                'success': True,
                'insights': insights[:6],  # Top 6 insights
                'recommendations': recommendations[:5]  # Top 5 recommendations
            }

        except Exception as e:
            logger.error(f"Failed to generate performance insights: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_comparison_metrics(self, period1_days: int = 7, period2_days: int = 14) -> Dict[str, Any]:
        """
        Compare two time periods to show improvement or decline.

        Args:
            period1_days: Recent period (e.g., last 7 days)
            period2_days: Earlier period (e.g., previous 7 days)

        Returns:
            Comparison metrics
        """
        try:
            # Recent period
            recent = self.get_productivity_overview(days=period1_days)

            # Earlier period (from period2_days ago to period1_days ago)
            start_date = (datetime.now() - timedelta(days=period2_days)).isoformat()
            end_date = (datetime.now() - timedelta(days=period1_days)).isoformat()

            focus_query = """
            SELECT
                COUNT(*) as work_sessions,
                SUM(duration_minutes) as total_minutes,
                AVG(focus_score) as avg_focus_score
            FROM focus_sessions
            WHERE user_id = ?
            AND start_time >= ? AND start_time < ?
            AND session_type = 'work'
            AND completed = 1
            """

            earlier_focus = self.db.execute_query(
                focus_query,
                (self.user_id, start_date, end_date),
                fetch_one=True
            )

            # Calculate changes
            recent_sessions = recent['focus']['work_sessions']
            earlier_sessions = earlier_focus['work_sessions'] or 0

            recent_hours = recent['focus']['total_hours']
            earlier_hours = (earlier_focus['total_minutes'] or 0) / 60

            recent_focus_score = recent['focus']['avg_focus_score']
            earlier_focus_score = earlier_focus['avg_focus_score'] or 0

            def calculate_change(current, previous):
                if previous == 0:
                    return 0 if current == 0 else 100
                return ((current - previous) / previous) * 100

            return {
                'success': True,
                'recent_period_days': period1_days,
                'earlier_period_days': period2_days - period1_days,
                'comparisons': {
                    'sessions': {
                        'recent': recent_sessions,
                        'earlier': earlier_sessions,
                        'change_percent': round(calculate_change(recent_sessions, earlier_sessions), 1)
                    },
                    'hours': {
                        'recent': round(recent_hours, 1),
                        'earlier': round(earlier_hours, 1),
                        'change_percent': round(calculate_change(recent_hours, earlier_hours), 1)
                    },
                    'focus_score': {
                        'recent': round(recent_focus_score, 1),
                        'earlier': round(earlier_focus_score, 1),
                        'change_percent': round(calculate_change(recent_focus_score, earlier_focus_score), 1)
                    }
                }
            }

        except Exception as e:
            logger.error(f"Failed to get comparison metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    print("Testing Analytics Engine...")

    engine = AnalyticsEngine(user_id="test_user")

    # Test productivity overview
    overview = engine.get_productivity_overview(days=30)
    print(f"Productivity overview: {overview}")

    # Test daily trends
    trends = engine.get_daily_trends(days=14)
    print(f"Daily trends: {trends}")

    # Test insights
    insights = engine.get_performance_insights()
    print(f"Performance insights: {insights}")

    # Test comparison
    comparison = engine.get_comparison_metrics()
    print(f"Comparison: {comparison}")

    print("\nAnalytics Engine validated!")
