"""
Analytics Manager - Phase 6 Sprint 4 (Final Component!)
Central integration manager coordinating all analytics systems.

Features:
- Unified analytics API
- Cross-system coordination
- Automatic achievement checking
- Progress synchronization
- Goal integration with tracking
- Comprehensive dashboard data

Author: Academic Command Center
Phase: 6 Sprint 4 - Final Component
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from .progress_tracker import ProgressTracker
from .performance_analytics import PerformanceAnalytics
from .goal_system import GoalSystem
from .study_analytics import StudyAnalytics
from .achievement_system import AchievementSystem

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AnalyticsManager:
    """
    Analytics Manager - Central coordinator for all analytics systems.

    Integrates:
    - Progress Tracker
    - Performance Analytics
    - Goal System
    - Study Analytics
    - Achievement System

    Provides:
    - Unified API
    - Cross-system synchronization
    - Automatic achievement detection
    - Dashboard data aggregation
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Analytics Manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize all analytics systems
        self.progress_tracker = ProgressTracker(user_id, self.db)
        self.performance_analytics = PerformanceAnalytics(user_id, self.db)
        self.goal_system = GoalSystem(user_id, self.db)
        self.study_analytics = StudyAnalytics(user_id, self.db)
        self.achievement_system = AchievementSystem(user_id, self.db)

        logger.info(f"Analytics Manager initialized for user {user_id}")

    def get_dashboard_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary.

        Args:
            days: Period to analyze

        Returns:
            Complete dashboard data
        """
        try:
            logger.info(f"Generating dashboard summary for {days} days...")

            # Get data from all systems
            performance = self.performance_analytics.calculate_performance_score(days)
            progress = self.progress_tracker.get_overall_progress(days)
            study_overview = self.study_analytics.get_study_overview(days)
            streak = self.study_analytics.track_study_streak()
            user_stats = self.achievement_system.get_user_stats()
            active_goals = self.goal_system.get_active_goals()
            goal_stats = self.goal_system.get_goal_statistics()

            # Aggregate key metrics
            summary = {
                'success': True,
                'period_days': days,
                'performance': {
                    'overall_score': performance.get('overall_score', 0) if performance.get('success') else 0,
                    'grade_level': performance.get('grade_level', 'unknown') if performance.get('success') else 'unknown',
                    'components': performance.get('components', {}) if performance.get('success') else {}
                },
                'progress': {
                    'assignments': progress.get('assignments', {}) if progress.get('success') else {},
                    'study_time': progress.get('study_time', {}) if progress.get('success') else {},
                    'tasks': progress.get('tasks', {}) if progress.get('success') else {}
                },
                'study': {
                    'total_hours': study_overview.get('total_study_time', {}).get('hours', 0) if study_overview.get('success') else 0,
                    'session_count': study_overview.get('session_count', 0) if study_overview.get('success') else 0,
                    'daily_average': study_overview.get('daily_average', {}).get('hours', 0) if study_overview.get('success') else 0
                },
                'streak': {
                    'current_streak': streak.get('current_streak', 0) if streak.get('success') else 0,
                    'longest_streak': streak.get('longest_streak', 0) if streak.get('success') else 0,
                    'streak_active': streak.get('streak_active', False) if streak.get('success') else False
                },
                'gamification': {
                    'level': user_stats.get('level', 1) if user_stats.get('success') else 1,
                    'total_points': user_stats.get('total_points', 0) if user_stats.get('success') else 0,
                    'rank': user_stats.get('rank', 'Novice') if user_stats.get('success') else 'Novice',
                    'achievements_unlocked': user_stats.get('achievements_unlocked', 0) if user_stats.get('success') else 0
                },
                'goals': {
                    'active_count': active_goals.get('count', 0) if active_goals.get('success') else 0,
                    'total': goal_stats.get('total', 0) if goal_stats.get('success') else 0,
                    'completion_rate': goal_stats.get('completion_rate', 0) if goal_stats.get('success') else 0
                }
            }

            logger.info("Dashboard summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate dashboard summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def record_study_session(
        self,
        session_id: str,
        subject: str,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Record a study session and update related systems.

        Args:
            session_id: Session ID
            subject: Subject name
            duration_minutes: Duration in minutes

        Returns:
            Update result with achievements
        """
        try:
            logger.info(f"Recording study session: {session_id} ({duration_minutes} min)")

            # Update study-related goals
            self._update_study_goals(duration_minutes)

            # Check for new achievements
            new_achievements = self.achievement_system.check_achievements()

            return {
                'success': True,
                'session_recorded': True,
                'new_achievements': new_achievements.get('newly_unlocked', []) if new_achievements.get('success') else []
            }

        except Exception as e:
            logger.error(f"Failed to record study session: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def record_assignment_completion(
        self,
        assignment_id: str,
        grade: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Record assignment completion and update systems.

        Args:
            assignment_id: Assignment ID
            grade: Optional grade

        Returns:
            Update result with achievements
        """
        try:
            logger.info(f"Recording assignment completion: {assignment_id}")

            # Update assignment-related goals
            self._update_assignment_goals()

            # Check for new achievements
            new_achievements = self.achievement_system.check_achievements()

            return {
                'success': True,
                'assignment_recorded': True,
                'new_achievements': new_achievements.get('newly_unlocked', []) if new_achievements.get('success') else []
            }

        except Exception as e:
            logger.error(f"Failed to record assignment completion: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def record_goal_completion(self, goal_id: str) -> Dict[str, Any]:
        """
        Record goal completion and check achievements.

        Args:
            goal_id: Goal ID

        Returns:
            Update result with achievements
        """
        try:
            logger.info(f"Recording goal completion: {goal_id}")

            # Check for new achievements
            new_achievements = self.achievement_system.check_achievements()

            return {
                'success': True,
                'goal_completed': True,
                'new_achievements': new_achievements.get('newly_unlocked', []) if new_achievements.get('success') else []
            }

        except Exception as e:
            logger.error(f"Failed to record goal completion: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.

        Args:
            days: Period to analyze

        Returns:
            Complete analytics report
        """
        try:
            logger.info(f"Generating comprehensive report for {days} days...")

            # Collect all analytics data
            report = {
                'success': True,
                'generated_at': datetime.now().isoformat(),
                'period_days': days,
                'progress_report': self.progress_tracker.generate_progress_report(days),
                'performance_score': self.performance_analytics.calculate_performance_score(days),
                'risk_assessment': self.performance_analytics.assess_risk(),
                'study_overview': self.study_analytics.get_study_overview(days),
                'study_patterns': self.study_analytics.analyze_study_patterns(days),
                'productivity_metrics': self.study_analytics.calculate_productivity_metrics(days),
                'streak_data': self.study_analytics.track_study_streak(),
                'focus_insights': self.study_analytics.get_focus_insights(days),
                'goal_statistics': self.goal_system.get_goal_statistics(),
                'active_goals': self.goal_system.get_active_goals(),
                'user_gamification_stats': self.achievement_system.get_user_stats(),
                'achievement_progress': self.achievement_system.get_all_achievements()
            }

            logger.info("Comprehensive report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_insights_and_recommendations(self, days: int = 30) -> Dict[str, Any]:
        """
        Get personalized insights and recommendations.

        Args:
            days: Period to analyze

        Returns:
            Insights and recommendations
        """
        try:
            # Get progress report with insights
            report = self.progress_tracker.generate_progress_report(days)

            # Get risk assessment
            risk = self.performance_analytics.assess_risk()

            # Combine insights
            all_insights = report.get('insights', []) if report.get('success') else []
            all_recommendations = report.get('recommendations', []) if report.get('success') else []

            # Add risk-based recommendations
            if risk.get('success'):
                risk_recommendations = risk.get('recommendations', [])
                all_recommendations.extend(risk_recommendations)

            # Get study-based recommendations
            focus_insights = self.study_analytics.get_focus_insights(days)
            if focus_insights.get('success'):
                focus_rec = focus_insights.get('recommendation', '')
                if focus_rec:
                    all_recommendations.append(focus_rec)

            return {
                'success': True,
                'insights': all_insights[:10],  # Top 10
                'recommendations': all_recommendations[:10],  # Top 10
                'risk_level': risk.get('risk_level', 'unknown') if risk.get('success') else 'unknown'
            }

        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_performance_prediction(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Get performance prediction.

        Args:
            days_ahead: Days to predict ahead

        Returns:
            Prediction data
        """
        try:
            prediction = self.performance_analytics.predict_performance('grade', days_ahead)
            return prediction

        except Exception as e:
            logger.error(f"Failed to get prediction: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def suggest_goals(self) -> Dict[str, Any]:
        """
        Suggest goals based on current performance.

        Returns:
            Goal suggestions
        """
        try:
            suggestions = []

            # Get current performance
            performance = self.performance_analytics.calculate_performance_score(30)

            if performance.get('success'):
                components = performance.get('components', {})

                # Suggest based on weaknesses
                if components.get('consistency', 100) < 70:
                    suggestions.append({
                        'template': 'Daily Study Habit',
                        'reason': 'Improve study consistency'
                    })

                if components.get('assignment_completion', 100) < 80:
                    suggestions.append({
                        'template': 'Assignment Completion',
                        'reason': 'Increase completion rate'
                    })

                if components.get('grade_average', 100) < 85:
                    suggestions.append({
                        'template': 'Grade Improvement',
                        'reason': 'Boost average grade'
                    })

            # Get templates
            templates = self.goal_system.get_templates()

            return {
                'success': True,
                'suggestions': suggestions,
                'all_templates': templates.get('templates', []) if templates.get('success') else []
            }

        except Exception as e:
            logger.error(f"Failed to suggest goals: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _update_study_goals(self, duration_minutes: int):
        """Update study-related goals."""

        try:
            # Get active study goals
            goals = self.goal_system.get_active_goals()

            if goals.get('success'):
                for goal in goals['goals']:
                    if goal['goal_type'] == 'study_habit' and goal['unit'] == 'hours':
                        # Increment hours
                        hours = duration_minutes / 60
                        current = goal['current_value']
                        self.goal_system.update_goal_progress(goal['id'], current + hours)

                    elif goal['goal_type'] == 'study_habit' and goal['unit'] == 'sessions':
                        # Increment sessions
                        current = goal['current_value']
                        self.goal_system.update_goal_progress(goal['id'], current + 1)

        except Exception as e:
            logger.error(f"Failed to update study goals: {e}")

    def _update_assignment_goals(self):
        """Update assignment-related goals."""

        try:
            # Get active assignment goals
            goals = self.goal_system.get_active_goals()

            if goals.get('success'):
                for goal in goals['goals']:
                    if goal['goal_type'] in ['completion', 'academic'] and goal['unit'] == 'assignments':
                        # Increment assignments
                        current = goal['current_value']
                        self.goal_system.update_goal_progress(goal['id'], current + 1)

        except Exception as e:
            logger.error(f"Failed to update assignment goals: {e}")


def create_analytics_manager(
    user_id: str,
    db_manager: Optional[DatabaseManager] = None
) -> AnalyticsManager:
    """
    Factory function to create Analytics Manager.

    Args:
        user_id: Current user ID
        db_manager: Database manager instance

    Returns:
        AnalyticsManager instance
    """
    return AnalyticsManager(user_id, db_manager)
