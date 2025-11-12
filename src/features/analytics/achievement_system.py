"""
Achievement System - Phase 6 Sprint 3
Gamification system with badges, achievements, and rewards.

Features:
- Badge system
- Achievement tracking
- Milestone rewards
- Progress-based unlocks
- Leaderboard support
- Motivational notifications

Author: Academic Command Center
Phase: 6 Sprint 3
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class Achievement:
    """Achievement data structure."""
    id: str
    name: str
    description: str
    category: str  # study, grades, streak, goals, special
    tier: str  # bronze, silver, gold, platinum
    points: int
    icon: str
    requirement_type: str
    requirement_value: int
    unlocked: bool
    unlock_date: Optional[str]
    progress: int
    progress_percentage: float


@dataclass
class Badge:
    """Badge data structure."""
    id: str
    name: str
    description: str
    icon: str
    earned_date: str
    category: str


@dataclass
class UserProgress:
    """User gamification progress."""
    total_points: int
    level: int
    badges_earned: int
    achievements_unlocked: int
    rank: str


# Pre-defined achievements
ACHIEVEMENT_DEFINITIONS = [
    # Study Time Achievements
    {
        'name': 'First Steps',
        'description': 'Complete your first study session',
        'category': 'study',
        'tier': 'bronze',
        'points': 10,
        'icon': '=Ú',
        'requirement_type': 'study_sessions',
        'requirement_value': 1
    },
    {
        'name': 'Dedicated Learner',
        'description': 'Complete 25 study sessions',
        'category': 'study',
        'tier': 'silver',
        'points': 50,
        'icon': '=Ö',
        'requirement_type': 'study_sessions',
        'requirement_value': 25
    },
    {
        'name': 'Study Master',
        'description': 'Complete 100 study sessions',
        'category': 'study',
        'tier': 'gold',
        'points': 200,
        'icon': '<',
        'requirement_type': 'study_sessions',
        'requirement_value': 100
    },
    {
        'name': 'Marathon Runner',
        'description': 'Study for 50 total hours',
        'category': 'study',
        'tier': 'gold',
        'points': 150,
        'icon': 'ñ',
        'requirement_type': 'study_hours',
        'requirement_value': 50
    },
    # Streak Achievements
    {
        'name': 'Consistency Starter',
        'description': 'Maintain a 3-day study streak',
        'category': 'streak',
        'tier': 'bronze',
        'points': 20,
        'icon': '=%',
        'requirement_type': 'streak_days',
        'requirement_value': 3
    },
    {
        'name': 'Week Warrior',
        'description': 'Maintain a 7-day study streak',
        'category': 'streak',
        'tier': 'silver',
        'points': 50,
        'icon': '=%',
        'requirement_type': 'streak_days',
        'requirement_value': 7
    },
    {
        'name': 'Unstoppable',
        'description': 'Maintain a 30-day study streak',
        'category': 'streak',
        'tier': 'gold',
        'points': 200,
        'icon': '=%',
        'requirement_type': 'streak_days',
        'requirement_value': 30
    },
    {
        'name': 'Legend',
        'description': 'Maintain a 100-day study streak',
        'category': 'streak',
        'tier': 'platinum',
        'points': 500,
        'icon': '=Q',
        'requirement_type': 'streak_days',
        'requirement_value': 100
    },
    # Grade Achievements
    {
        'name': 'A Student',
        'description': 'Achieve 90% average on 5 assignments',
        'category': 'grades',
        'tier': 'silver',
        'points': 100,
        'icon': 'P',
        'requirement_type': 'high_grades',
        'requirement_value': 5
    },
    {
        'name': 'Perfect Score',
        'description': 'Get 100% on an assignment',
        'category': 'grades',
        'tier': 'gold',
        'points': 150,
        'icon': '=¯',
        'requirement_type': 'perfect_assignment',
        'requirement_value': 1
    },
    # Goal Achievements
    {
        'name': 'Goal Setter',
        'description': 'Create your first goal',
        'category': 'goals',
        'tier': 'bronze',
        'points': 10,
        'icon': '<¯',
        'requirement_type': 'goals_created',
        'requirement_value': 1
    },
    {
        'name': 'Achiever',
        'description': 'Complete 5 goals',
        'category': 'goals',
        'tier': 'silver',
        'points': 75,
        'icon': '',
        'requirement_type': 'goals_completed',
        'requirement_value': 5
    },
    {
        'name': 'Goal Crusher',
        'description': 'Complete 20 goals',
        'category': 'goals',
        'tier': 'gold',
        'points': 250,
        'icon': '<Æ',
        'requirement_type': 'goals_completed',
        'requirement_value': 20
    },
    # Assignment Achievements
    {
        'name': 'Task Master',
        'description': 'Complete 10 assignments',
        'category': 'assignments',
        'tier': 'bronze',
        'points': 30,
        'icon': '=Ý',
        'requirement_type': 'assignments_completed',
        'requirement_value': 10
    },
    {
        'name': 'Productivity Pro',
        'description': 'Complete 50 assignments',
        'category': 'assignments',
        'tier': 'silver',
        'points': 100,
        'icon': '=Ë',
        'requirement_type': 'assignments_completed',
        'requirement_value': 50
    },
    # Special Achievements
    {
        'name': 'Early Bird',
        'description': 'Complete 5 study sessions before 8 AM',
        'category': 'special',
        'tier': 'silver',
        'points': 75,
        'icon': '<',
        'requirement_type': 'early_sessions',
        'requirement_value': 5
    },
    {
        'name': 'Night Owl',
        'description': 'Complete 5 study sessions after 10 PM',
        'category': 'special',
        'tier': 'silver',
        'points': 75,
        'icon': '>',
        'requirement_type': 'late_sessions',
        'requirement_value': 5
    }
]


class AchievementSystem:
    """
    Achievement and Gamification System.

    Provides:
    - Achievement tracking
    - Badge awarding
    - Progress monitoring
    - Level progression
    - Point system
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Achievement System.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Achievement System initialized for user {user_id}")

    def check_achievements(self) -> Dict[str, Any]:
        """
        Check for newly unlocked achievements.

        Returns:
            Newly unlocked achievements
        """
        try:
            newly_unlocked = []

            for achievement_def in ACHIEVEMENT_DEFINITIONS:
                # Check if already unlocked
                check_query = """
                SELECT id FROM achievements
                WHERE user_id = ? AND name = ?
                """

                existing = self.db.execute_query(
                    check_query,
                    (self.user_id, achievement_def['name']),
                    fetch_one=True
                )

                if existing:
                    continue  # Already unlocked

                # Check if requirement is met
                requirement_met, progress = self._check_requirement(
                    achievement_def['requirement_type'],
                    achievement_def['requirement_value']
                )

                if requirement_met:
                    # Unlock achievement
                    unlock_result = self._unlock_achievement(achievement_def)
                    if unlock_result['success']:
                        newly_unlocked.append({
                            'name': achievement_def['name'],
                            'description': achievement_def['description'],
                            'tier': achievement_def['tier'],
                            'points': achievement_def['points'],
                            'icon': achievement_def['icon']
                        })

            return {
                'success': True,
                'newly_unlocked': newly_unlocked,
                'count': len(newly_unlocked)
            }

        except Exception as e:
            logger.error(f"Failed to check achievements: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_all_achievements(self) -> Dict[str, Any]:
        """
        Get all achievements with progress.

        Returns:
            Achievement list with progress
        """
        try:
            achievements = []

            for achievement_def in ACHIEVEMENT_DEFINITIONS:
                # Check if unlocked
                check_query = """
                SELECT unlocked_at FROM achievements
                WHERE user_id = ? AND name = ?
                """

                result = self.db.execute_query(
                    check_query,
                    (self.user_id, achievement_def['name']),
                    fetch_one=True
                )

                unlocked = result is not None
                unlock_date = result['unlocked_at'] if result else None

                # Get current progress
                requirement_met, progress = self._check_requirement(
                    achievement_def['requirement_type'],
                    achievement_def['requirement_value']
                )

                progress_percentage = min(100, (progress / achievement_def['requirement_value']) * 100)

                achievements.append({
                    'name': achievement_def['name'],
                    'description': achievement_def['description'],
                    'category': achievement_def['category'],
                    'tier': achievement_def['tier'],
                    'points': achievement_def['points'],
                    'icon': achievement_def['icon'],
                    'requirement_value': achievement_def['requirement_value'],
                    'unlocked': unlocked,
                    'unlock_date': unlock_date,
                    'progress': progress,
                    'progress_percentage': round(progress_percentage, 1)
                })

            # Sort: unlocked first, then by points
            achievements.sort(key=lambda x: (not x['unlocked'], -x['points']))

            return {
                'success': True,
                'achievements': achievements,
                'total': len(achievements),
                'unlocked': len([a for a in achievements if a['unlocked']])
            }

        except Exception as e:
            logger.error(f"Failed to get achievements: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user gamification statistics.

        Returns:
            User stats
        """
        try:
            # Get total points
            points_query = """
            SELECT COALESCE(SUM(points), 0) as total_points
            FROM achievements
            WHERE user_id = ?
            """

            points_result = self.db.execute_query(
                points_query,
                (self.user_id,),
                fetch_one=True
            )

            total_points = points_result['total_points'] or 0

            # Calculate level (every 100 points = 1 level)
            level = (total_points // 100) + 1

            # Get achievements count
            achievements_query = """
            SELECT COUNT(*) as count
            FROM achievements
            WHERE user_id = ?
            """

            achievements_result = self.db.execute_query(
                achievements_query,
                (self.user_id,),
                fetch_one=True
            )

            achievements_unlocked = achievements_result['count'] or 0

            # Determine rank
            rank = self._calculate_rank(total_points, achievements_unlocked)

            # Get recent achievements
            recent_query = """
            SELECT name, points, unlocked_at
            FROM achievements
            WHERE user_id = ?
            ORDER BY unlocked_at DESC
            LIMIT 5
            """

            recent_achievements = self.db.execute_query(
                recent_query,
                (self.user_id,),
                fetch_all=True
            ) or []

            # Calculate progress to next level
            points_to_next_level = (level * 100) - total_points
            level_progress = ((total_points % 100) / 100) * 100

            return {
                'success': True,
                'total_points': total_points,
                'level': level,
                'level_progress': round(level_progress, 1),
                'points_to_next_level': points_to_next_level,
                'achievements_unlocked': achievements_unlocked,
                'total_achievements': len(ACHIEVEMENT_DEFINITIONS),
                'completion_percentage': round((achievements_unlocked / len(ACHIEVEMENT_DEFINITIONS)) * 100, 1),
                'rank': rank,
                'recent_achievements': recent_achievements
            }

        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_achievements_by_category(self, category: str) -> Dict[str, Any]:
        """
        Get achievements filtered by category.

        Args:
            category: Category filter

        Returns:
            Filtered achievements
        """
        try:
            all_achievements = self.get_all_achievements()

            if not all_achievements['success']:
                return all_achievements

            filtered = [
                a for a in all_achievements['achievements']
                if a['category'] == category
            ]

            return {
                'success': True,
                'category': category,
                'achievements': filtered,
                'total': len(filtered),
                'unlocked': len([a for a in filtered if a['unlocked']])
            }

        except Exception as e:
            logger.error(f"Failed to get achievements by category: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _check_requirement(
        self,
        requirement_type: str,
        requirement_value: int
    ) -> tuple[bool, int]:
        """
        Check if requirement is met.

        Returns:
            (requirement_met, current_progress)
        """
        try:
            if requirement_type == 'study_sessions':
                query = """
                SELECT COUNT(*) as count
                FROM focus_sessions
                WHERE user_id = ?
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            elif requirement_type == 'study_hours':
                query = """
                SELECT SUM(duration_minutes) as total_minutes
                FROM focus_sessions
                WHERE user_id = ?
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                total_minutes = result['total_minutes'] or 0
                progress = total_minutes // 60  # Convert to hours

            elif requirement_type == 'streak_days':
                # Import study analytics to get streak
                from .study_analytics import StudyAnalytics
                analytics = StudyAnalytics(self.user_id, self.db)
                streak_data = analytics.track_study_streak()
                progress = streak_data.get('current_streak', 0)

            elif requirement_type == 'high_grades':
                query = """
                SELECT COUNT(*) as count
                FROM assignments
                WHERE user_id = ? AND grade >= 90
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            elif requirement_type == 'perfect_assignment':
                query = """
                SELECT COUNT(*) as count
                FROM assignments
                WHERE user_id = ? AND grade = 100
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            elif requirement_type == 'goals_created':
                query = """
                SELECT COUNT(*) as count
                FROM goals
                WHERE user_id = ?
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            elif requirement_type == 'goals_completed':
                query = """
                SELECT COUNT(*) as count
                FROM goals
                WHERE user_id = ? AND status = 'completed'
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            elif requirement_type == 'assignments_completed':
                query = """
                SELECT COUNT(*) as count
                FROM assignments
                WHERE user_id = ? AND status = 'completed'
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            elif requirement_type == 'early_sessions':
                query = """
                SELECT COUNT(*) as count
                FROM focus_sessions
                WHERE user_id = ?
                AND CAST(strftime('%H', start_time) AS INTEGER) < 8
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            elif requirement_type == 'late_sessions':
                query = """
                SELECT COUNT(*) as count
                FROM focus_sessions
                WHERE user_id = ?
                AND CAST(strftime('%H', start_time) AS INTEGER) >= 22
                """
                result = self.db.execute_query(query, (self.user_id,), fetch_one=True)
                progress = result['count'] or 0

            else:
                progress = 0

            return (progress >= requirement_value, progress)

        except Exception as e:
            logger.error(f"Failed to check requirement: {e}")
            return (False, 0)

    def _unlock_achievement(self, achievement_def: Dict[str, Any]) -> Dict[str, Any]:
        """Unlock an achievement."""
        try:
            achievement_id = str(uuid.uuid4())

            query = """
            INSERT INTO achievements (
                id, user_id, name, description, category, tier,
                points, icon, unlocked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    achievement_id,
                    self.user_id,
                    achievement_def['name'],
                    achievement_def['description'],
                    achievement_def['category'],
                    achievement_def['tier'],
                    achievement_def['points'],
                    achievement_def['icon'],
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Unlocked achievement: {achievement_def['name']} for user {self.user_id}")

            return {
                'success': True,
                'achievement_id': achievement_id
            }

        except Exception as e:
            logger.error(f"Failed to unlock achievement: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_rank(self, total_points: int, achievements_unlocked: int) -> str:
        """Calculate user rank based on points and achievements."""
        if total_points >= 2000 or achievements_unlocked >= 15:
            return "Master"
        elif total_points >= 1000 or achievements_unlocked >= 10:
            return "Expert"
        elif total_points >= 500 or achievements_unlocked >= 7:
            return "Advanced"
        elif total_points >= 200 or achievements_unlocked >= 4:
            return "Intermediate"
        elif total_points >= 50 or achievements_unlocked >= 2:
            return "Beginner"
        else:
            return "Novice"


def create_achievement_system(
    user_id: str,
    db_manager: Optional[DatabaseManager] = None
) -> AchievementSystem:
    """
    Factory function to create Achievement System.

    Args:
        user_id: Current user ID
        db_manager: Database manager instance

    Returns:
        AchievementSystem instance
    """
    return AchievementSystem(user_id, db_manager)
