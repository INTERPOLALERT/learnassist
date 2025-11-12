"""
Progress Tracker - Phase 6 Sprint 3
Track academic progress across subjects, assignments, and learning objectives.

Features:
- Subject progress tracking
- Assignment completion rates
- Grade trend analysis
- Learning objective mastery
- Progress reports and insights

Author: Academic Command Center
Phase: 6 Sprint 3
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class SubjectProgress:
    """Subject progress data."""
    subject_id: str
    subject_name: str
    total_assignments: int
    completed_assignments: int
    completion_rate: float  # 0-100
    average_grade: float  # 0-100
    current_grade: float  # 0-100
    trend: str  # improving, declining, stable
    last_updated: str


@dataclass
class ProgressReport:
    """Comprehensive progress report."""
    user_id: str
    period_start: str
    period_end: str
    overall_completion_rate: float
    overall_average_grade: float
    subjects: List[SubjectProgress]
    total_study_time_minutes: int
    total_focus_sessions: int
    assignments_completed: int
    assignments_pending: int
    grade_trend: str
    insights: List[str]
    recommendations: List[str]


@dataclass
class MilestoneProgress:
    """Learning milestone progress."""
    milestone_id: str
    title: str
    description: str
    target_date: str
    completion_percentage: float
    status: str  # not_started, in_progress, completed, overdue
    tasks_completed: int
    tasks_total: int


class ProgressTracker:
    """
    Academic Progress Tracker.

    Tracks and analyzes:
    - Subject-wise progress
    - Assignment completion
    - Grade trends
    - Learning objectives
    - Study patterns
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Progress Tracker.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Progress Tracker initialized for user {user_id}")

    def get_overall_progress(self, days: int = 30) -> Dict[str, Any]:
        """
        Get overall academic progress.

        Args:
            days: Number of days to analyze

        Returns:
            Overall progress data
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get assignment statistics
            assignment_query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                AVG(CASE WHEN grade IS NOT NULL THEN grade ELSE NULL END) as avg_grade
            FROM assignments
            WHERE user_id = ? AND created_at >= ?
            """

            assignment_stats = self.db.execute_query(
                assignment_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            # Get study time
            session_query = """
            SELECT
                COUNT(*) as session_count,
                SUM(duration_minutes) as total_minutes
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            """

            session_stats = self.db.execute_query(
                session_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            # Get task completion
            task_query = """
            SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_tasks
            FROM tasks
            WHERE user_id = ? AND created_at >= ?
            """

            task_stats = self.db.execute_query(
                task_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            # Calculate rates
            total_assignments = assignment_stats['total'] or 0
            completed_assignments = assignment_stats['completed'] or 0
            completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0

            total_tasks = task_stats['total_tasks'] or 0
            completed_tasks = task_stats['completed_tasks'] or 0
            task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            return {
                'success': True,
                'period_days': days,
                'assignments': {
                    'total': total_assignments,
                    'completed': completed_assignments,
                    'completion_rate': round(completion_rate, 1),
                    'average_grade': round(assignment_stats['avg_grade'] or 0, 1)
                },
                'study_time': {
                    'total_minutes': session_stats['total_minutes'] or 0,
                    'total_hours': round((session_stats['total_minutes'] or 0) / 60, 1),
                    'session_count': session_stats['session_count'] or 0,
                    'avg_session_minutes': round((session_stats['total_minutes'] or 0) / (session_stats['session_count'] or 1), 1)
                },
                'tasks': {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'completion_rate': round(task_completion_rate, 1)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get overall progress: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_subject_progress(self, subject_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get progress by subject.

        Args:
            subject_id: Optional specific subject ID

        Returns:
            Subject progress data
        """
        try:
            if subject_id:
                # Get specific subject
                query = """
                SELECT
                    s.id as subject_id,
                    s.name as subject_name,
                    COUNT(a.id) as total_assignments,
                    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed,
                    AVG(CASE WHEN a.grade IS NOT NULL THEN a.grade ELSE NULL END) as avg_grade
                FROM subjects s
                LEFT JOIN assignments a ON a.subject_id = s.id
                WHERE s.id = ? AND s.user_id = ?
                GROUP BY s.id, s.name
                """

                result = self.db.execute_query(
                    query,
                    (subject_id, self.user_id),
                    fetch_one=True
                )

                if not result:
                    return {
                        'success': False,
                        'error': 'Subject not found'
                    }

                total = result['total_assignments'] or 0
                completed = result['completed'] or 0
                completion_rate = (completed / total * 100) if total > 0 else 0

                return {
                    'success': True,
                    'subject': {
                        'id': result['subject_id'],
                        'name': result['subject_name'],
                        'total_assignments': total,
                        'completed_assignments': completed,
                        'completion_rate': round(completion_rate, 1),
                        'average_grade': round(result['avg_grade'] or 0, 1)
                    }
                }

            else:
                # Get all subjects
                query = """
                SELECT
                    s.id as subject_id,
                    s.name as subject_name,
                    s.color,
                    COUNT(a.id) as total_assignments,
                    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed,
                    AVG(CASE WHEN a.grade IS NOT NULL THEN a.grade ELSE NULL END) as avg_grade
                FROM subjects s
                LEFT JOIN assignments a ON a.subject_id = s.id
                WHERE s.user_id = ?
                GROUP BY s.id, s.name, s.color
                ORDER BY s.name
                """

                subjects = self.db.execute_query(
                    query,
                    (self.user_id,),
                    fetch_all=True
                )

                subject_data = []
                if subjects:
                    for subj in subjects:
                        total = subj['total_assignments'] or 0
                        completed = subj['completed'] or 0
                        completion_rate = (completed / total * 100) if total > 0 else 0

                        subject_data.append({
                            'id': subj['subject_id'],
                            'name': subj['subject_name'],
                            'color': subj['color'],
                            'total_assignments': total,
                            'completed_assignments': completed,
                            'completion_rate': round(completion_rate, 1),
                            'average_grade': round(subj['avg_grade'] or 0, 1)
                        })

                return {
                    'success': True,
                    'subjects': subject_data,
                    'count': len(subject_data)
                }

        except Exception as e:
            logger.error(f"Failed to get subject progress: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_grade_trends(self, subject_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Analyze grade trends over time.

        Args:
            subject_id: Optional subject filter
            days: Number of days to analyze

        Returns:
            Grade trend data
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Build query
            if subject_id:
                query = """
                SELECT
                    DATE(due_date) as date,
                    AVG(grade) as avg_grade,
                    COUNT(*) as count
                FROM assignments
                WHERE user_id = ?
                AND subject_id = ?
                AND grade IS NOT NULL
                AND due_date >= ?
                GROUP BY DATE(due_date)
                ORDER BY date ASC
                """
                params = (self.user_id, subject_id, start_date)
            else:
                query = """
                SELECT
                    DATE(due_date) as date,
                    AVG(grade) as avg_grade,
                    COUNT(*) as count
                FROM assignments
                WHERE user_id = ?
                AND grade IS NOT NULL
                AND due_date >= ?
                GROUP BY DATE(due_date)
                ORDER BY date ASC
                """
                params = (self.user_id, start_date)

            trends = self.db.execute_query(query, params, fetch_all=True)

            # Calculate trend direction
            if trends and len(trends) >= 2:
                first_half_avg = sum(t['avg_grade'] for t in trends[:len(trends)//2]) / (len(trends)//2)
                second_half_avg = sum(t['avg_grade'] for t in trends[len(trends)//2:]) / (len(trends) - len(trends)//2)

                if second_half_avg > first_half_avg + 5:
                    trend_direction = "improving"
                elif second_half_avg < first_half_avg - 5:
                    trend_direction = "declining"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "insufficient_data"

            # Format data points
            data_points = []
            if trends:
                for trend in trends:
                    data_points.append({
                        'date': trend['date'],
                        'average_grade': round(trend['avg_grade'], 1),
                        'assignment_count': trend['count']
                    })

            return {
                'success': True,
                'period_days': days,
                'trend_direction': trend_direction,
                'data_points': data_points,
                'total_points': len(data_points)
            }

        except Exception as e:
            logger.error(f"Failed to get grade trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_completion_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get assignment completion trends.

        Args:
            days: Number of days to analyze

        Returns:
            Completion trend data
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
            SELECT
                DATE(updated_at) as date,
                COUNT(*) as completed_count
            FROM assignments
            WHERE user_id = ?
            AND status = 'completed'
            AND updated_at >= ?
            GROUP BY DATE(updated_at)
            ORDER BY date ASC
            """

            trends = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            )

            data_points = []
            if trends:
                for trend in trends:
                    data_points.append({
                        'date': trend['date'],
                        'completed': trend['completed_count']
                    })

            return {
                'success': True,
                'period_days': days,
                'data_points': data_points,
                'total_completed': sum(p['completed'] for p in data_points)
            }

        except Exception as e:
            logger.error(f"Failed to get completion trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_progress_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive progress report.

        Args:
            days: Period to analyze

        Returns:
            Complete progress report
        """
        try:
            # Get overall progress
            overall = self.get_overall_progress(days)

            # Get subject progress
            subjects = self.get_subject_progress()

            # Get grade trends
            grade_trends = self.get_grade_trends(days=days)

            # Generate insights
            insights = self._generate_insights(
                overall,
                subjects.get('subjects', []),
                grade_trends
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                overall,
                subjects.get('subjects', []),
                grade_trends
            )

            return {
                'success': True,
                'period_days': days,
                'period_start': (datetime.now() - timedelta(days=days)).date().isoformat(),
                'period_end': datetime.now().date().isoformat(),
                'overall': overall,
                'subjects': subjects.get('subjects', []),
                'grade_trends': grade_trends,
                'insights': insights,
                'recommendations': recommendations
            }

        except Exception as e:
            logger.error(f"Failed to generate progress report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_insights(
        self,
        overall: Dict[str, Any],
        subjects: List[Dict[str, Any]],
        grade_trends: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from progress data."""
        insights = []

        if not overall.get('success'):
            return insights

        # Assignment insights
        completion_rate = overall.get('assignments', {}).get('completion_rate', 0)
        if completion_rate >= 80:
            insights.append(f"Excellent assignment completion rate: {completion_rate:.0f}%")
        elif completion_rate >= 60:
            insights.append(f"Good progress on assignments: {completion_rate:.0f}% completed")
        elif completion_rate > 0:
            insights.append(f"Assignment completion needs attention: only {completion_rate:.0f}% completed")

        # Grade insights
        avg_grade = overall.get('assignments', {}).get('average_grade', 0)
        if avg_grade >= 90:
            insights.append(f"Outstanding academic performance: {avg_grade:.0f}% average")
        elif avg_grade >= 80:
            insights.append(f"Strong academic performance: {avg_grade:.0f}% average")
        elif avg_grade >= 70:
            insights.append(f"Satisfactory performance: {avg_grade:.0f}% average")
        elif avg_grade > 0:
            insights.append(f"Performance below expectations: {avg_grade:.0f}% average")

        # Trend insights
        trend = grade_trends.get('trend_direction', '')
        if trend == 'improving':
            insights.append("Grades are trending upward - great improvement!")
        elif trend == 'declining':
            insights.append("Grades are declining - consider adjusting study strategies")
        elif trend == 'stable':
            insights.append("Grade performance is consistent")

        # Study time insights
        study_hours = overall.get('study_time', {}).get('total_hours', 0)
        session_count = overall.get('study_time', {}).get('session_count', 0)
        if study_hours >= 30:
            insights.append(f"Excellent study dedication: {study_hours:.1f} hours across {session_count} sessions")
        elif study_hours >= 15:
            insights.append(f"Good study time: {study_hours:.1f} hours in {session_count} sessions")
        elif study_hours > 0:
            insights.append(f"Study time could be increased: only {study_hours:.1f} hours logged")

        # Subject-specific insights
        if subjects:
            strongest = max(subjects, key=lambda s: s.get('average_grade', 0))
            if strongest.get('average_grade', 0) > 0:
                insights.append(f"Strongest subject: {strongest['name']} ({strongest['average_grade']:.0f}%)")

            weakest = min(subjects, key=lambda s: s.get('average_grade', 100))
            if weakest.get('average_grade', 0) > 0 and weakest != strongest:
                insights.append(f"Subject needing attention: {weakest['name']} ({weakest['average_grade']:.0f}%)")

        return insights

    def _generate_recommendations(
        self,
        overall: Dict[str, Any],
        subjects: List[Dict[str, Any]],
        grade_trends: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on progress."""
        recommendations = []

        if not overall.get('success'):
            return recommendations

        # Assignment recommendations
        completion_rate = overall.get('assignments', {}).get('completion_rate', 0)
        if completion_rate < 70:
            recommendations.append("Focus on completing pending assignments to improve your completion rate")

        # Grade recommendations
        avg_grade = overall.get('assignments', {}).get('average_grade', 0)
        if avg_grade < 75:
            recommendations.append("Consider additional study time or tutoring to improve grades")

        # Trend recommendations
        trend = grade_trends.get('trend_direction', '')
        if trend == 'declining':
            recommendations.append("Review recent assignments to identify areas where you're struggling")
            recommendations.append("Consider adjusting your study schedule or methods")

        # Study time recommendations
        study_hours = overall.get('study_time', {}).get('total_hours', 0)
        period_days = overall.get('period_days', 30)
        daily_avg = study_hours / period_days if period_days > 0 else 0

        if daily_avg < 1:
            recommendations.append("Aim for at least 1-2 hours of focused study per day")
        elif daily_avg > 6:
            recommendations.append("Consider taking breaks to avoid burnout - balance is important")

        # Subject recommendations
        if subjects:
            low_completion = [s for s in subjects if s.get('completion_rate', 0) < 60]
            if low_completion:
                for subj in low_completion[:2]:  # Top 2
                    recommendations.append(f"Prioritize completing {subj['name']} assignments")

            low_grade = [s for s in subjects if 0 < s.get('average_grade', 100) < 70]
            if low_grade:
                for subj in low_grade[:2]:  # Top 2
                    recommendations.append(f"Dedicate extra study time to {subj['name']}")

        # Task recommendations
        task_rate = overall.get('tasks', {}).get('completion_rate', 0)
        if task_rate < 60:
            recommendations.append("Break down large assignments into smaller, manageable tasks")

        return recommendations[:8]  # Limit to top 8


def create_progress_tracker(
    user_id: str,
    db_manager: Optional[DatabaseManager] = None
) -> ProgressTracker:
    """
    Factory function to create Progress Tracker.

    Args:
        user_id: Current user ID
        db_manager: Database manager instance

    Returns:
        ProgressTracker instance
    """
    return ProgressTracker(user_id, db_manager)
