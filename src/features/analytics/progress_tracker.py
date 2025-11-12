"""
Academic Command Center - Analytics - Progress Tracker
Tracks academic goals, milestones, and progress metrics.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GoalType:
    """Types of academic goals."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEMESTER = "semester"
    CUSTOM = "custom"


class GoalStatus:
    """Goal completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressTracker:
    """
    Tracks academic goals and progress metrics.

    Monitors:
    - Focus session goals
    - Task completion goals
    - Essay writing goals
    - Study time goals
    - Custom milestones
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize progress tracker.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Progress tracker initialized for user {user_id}")

    def create_goal(
        self,
        title: str,
        goal_type: str = GoalType.DAILY,
        target_value: int = 1,
        metric: str = "sessions",
        deadline: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new goal.

        Args:
            title: Goal title
            goal_type: Goal type (daily, weekly, monthly, semester, custom)
            target_value: Target value to achieve
            metric: What to track (sessions, tasks, minutes, essays)
            deadline: Optional deadline (ISO format)
            description: Optional description

        Returns:
            Creation result
        """
        try:
            goal_id = str(uuid.uuid4())

            # Calculate deadline if not provided
            if not deadline:
                now = datetime.now()
                if goal_type == GoalType.DAILY:
                    deadline = (now + timedelta(days=1)).date().isoformat()
                elif goal_type == GoalType.WEEKLY:
                    deadline = (now + timedelta(weeks=1)).isoformat()
                elif goal_type == GoalType.MONTHLY:
                    deadline = (now + timedelta(days=30)).isoformat()
                elif goal_type == GoalType.SEMESTER:
                    deadline = (now + timedelta(days=120)).isoformat()
                else:  # CUSTOM
                    deadline = (now + timedelta(days=7)).isoformat()

            query = """
            INSERT INTO goals (
                id, user_id, title, goal_type, target_value,
                current_value, metric, deadline, description,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    goal_id,
                    self.user_id,
                    title,
                    goal_type,
                    target_value,
                    0,  # current_value starts at 0
                    metric,
                    deadline,
                    description,
                    GoalStatus.NOT_STARTED,
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Created goal: {goal_id} - {title}")

            return {
                'success': True,
                'goal_id': goal_id,
                'deadline': deadline
            }

        except Exception as e:
            logger.error(f"Failed to create goal: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def update_goal_progress(self, goal_id: str, increment: int = 1) -> Dict[str, Any]:
        """
        Update progress on a goal.

        Args:
            goal_id: Goal ID
            increment: Amount to increment current value

        Returns:
            Update result
        """
        try:
            # Get current goal
            query = "SELECT * FROM goals WHERE id = ? AND user_id = ?"
            goal = self.db.execute_query(query, (goal_id, self.user_id), fetch_one=True)

            if not goal:
                return {
                    'success': False,
                    'error': 'Goal not found'
                }

            new_value = goal['current_value'] + increment

            # Determine new status
            if new_value >= goal['target_value']:
                new_status = GoalStatus.COMPLETED
            elif new_value > 0:
                new_status = GoalStatus.IN_PROGRESS
            else:
                new_status = GoalStatus.NOT_STARTED

            # Update goal
            update_query = """
            UPDATE goals
            SET current_value = ?,
                status = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(
                update_query,
                (
                    new_value,
                    new_status,
                    datetime.now().isoformat(),
                    goal_id,
                    self.user_id
                )
            )

            completion_percentage = (new_value / goal['target_value'] * 100) if goal['target_value'] > 0 else 0

            logger.info(f"Updated goal {goal_id}: {new_value}/{goal['target_value']}")

            return {
                'success': True,
                'current_value': new_value,
                'target_value': goal['target_value'],
                'percentage': round(completion_percentage, 1),
                'status': new_status,
                'completed': new_status == GoalStatus.COMPLETED
            }

        except Exception as e:
            logger.error(f"Failed to update goal progress: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_active_goals(self) -> Dict[str, Any]:
        """
        Get all active goals for user.

        Returns:
            Active goals list
        """
        try:
            query = """
            SELECT * FROM goals
            WHERE user_id = ?
            AND status IN (?, ?)
            AND (deadline >= date('now') OR deadline IS NULL)
            ORDER BY deadline ASC, created_at DESC
            """

            goals = self.db.execute_query(
                query,
                (self.user_id, GoalStatus.NOT_STARTED, GoalStatus.IN_PROGRESS),
                fetch_all=True
            )

            # Calculate percentages
            if goals:
                for goal in goals:
                    goal['percentage'] = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
                    goal['percentage'] = round(goal['percentage'], 1)

            return {
                'success': True,
                'goals': goals or [],
                'count': len(goals) if goals else 0
            }

        except Exception as e:
            logger.error(f"Failed to get active goals: {e}")
            return {
                'success': False,
                'error': str(e),
                'goals': []
            }

    def get_completed_goals(self, days: int = 30) -> Dict[str, Any]:
        """
        Get recently completed goals.

        Args:
            days: Number of days to look back

        Returns:
            Completed goals list
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
            SELECT * FROM goals
            WHERE user_id = ?
            AND status = ?
            AND updated_at >= ?
            ORDER BY updated_at DESC
            """

            goals = self.db.execute_query(
                query,
                (self.user_id, GoalStatus.COMPLETED, start_date),
                fetch_all=True
            )

            return {
                'success': True,
                'goals': goals or [],
                'count': len(goals) if goals else 0
            }

        except Exception as e:
            logger.error(f"Failed to get completed goals: {e}")
            return {
                'success': False,
                'error': str(e),
                'goals': []
            }

    def get_goal_statistics(self) -> Dict[str, Any]:
        """
        Get overall goal statistics.

        Returns:
            Goal statistics
        """
        try:
            query = """
            SELECT
                COUNT(*) as total_goals,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as not_started
            FROM goals
            WHERE user_id = ?
            AND (deadline >= date('now') OR deadline IS NULL OR status = ?)
            """

            stats = self.db.execute_query(
                query,
                (
                    GoalStatus.COMPLETED,
                    GoalStatus.IN_PROGRESS,
                    GoalStatus.NOT_STARTED,
                    self.user_id,
                    GoalStatus.COMPLETED
                ),
                fetch_one=True
            )

            if not stats or stats['total_goals'] == 0:
                return {
                    'success': True,
                    'total_goals': 0,
                    'completed': 0,
                    'in_progress': 0,
                    'not_started': 0,
                    'completion_rate': 0.0
                }

            completion_rate = (stats['completed'] / stats['total_goals'] * 100) if stats['total_goals'] > 0 else 0

            return {
                'success': True,
                'total_goals': stats['total_goals'],
                'completed': stats['completed'],
                'in_progress': stats['in_progress'],
                'not_started': stats['not_started'],
                'completion_rate': round(completion_rate, 1)
            }

        except Exception as e:
            logger.error(f"Failed to get goal statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def check_and_update_goal_statuses(self) -> Dict[str, Any]:
        """
        Check all goals and mark expired ones as failed.

        Returns:
            Update result
        """
        try:
            query = """
            UPDATE goals
            SET status = ?,
                updated_at = ?
            WHERE user_id = ?
            AND status IN (?, ?)
            AND deadline < date('now')
            """

            self.db.execute_query(
                query,
                (
                    GoalStatus.FAILED,
                    datetime.now().isoformat(),
                    self.user_id,
                    GoalStatus.NOT_STARTED,
                    GoalStatus.IN_PROGRESS
                )
            )

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to check goal statuses: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_goal(self, goal_id: str) -> Dict[str, Any]:
        """
        Delete a goal.

        Args:
            goal_id: Goal ID

        Returns:
            Delete result
        """
        try:
            query = "DELETE FROM goals WHERE id = ? AND user_id = ?"
            self.db.execute_query(query, (goal_id, self.user_id))

            logger.info(f"Deleted goal: {goal_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to delete goal: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    print("Testing Progress Tracker...")

    tracker = ProgressTracker(user_id="test_user")

    # Test create goal
    result = tracker.create_goal(
        title="Complete 4 Focus Sessions",
        goal_type=GoalType.DAILY,
        target_value=4,
        metric="sessions"
    )
    print(f"Create goal: {result}")

    if result['success']:
        goal_id = result['goal_id']

        # Test update progress
        for i in range(3):
            update = tracker.update_goal_progress(goal_id)
            print(f"Progress update {i+1}: {update}")

        # Test get active goals
        active = tracker.get_active_goals()
        print(f"Active goals: {active}")

        # Test statistics
        stats = tracker.get_goal_statistics()
        print(f"Statistics: {stats}")

    print("\nProgress Tracker validated!")
