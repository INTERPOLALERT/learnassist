"""
Goal Setting System - Phase 6 Sprint 3
SMART goal creation, tracking, and milestone management.

Features:
- SMART goal creation (Specific, Measurable, Achievable, Relevant, Time-bound)
- Milestone tracking
- Progress monitoring
- Goal templates
- Achievement notifications
- Goal analytics

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
class Goal:
    """Goal data structure."""
    id: str
    user_id: str
    title: str
    description: str
    goal_type: str  # academic, study_habit, grade, completion, custom
    category: str  # short_term, long_term, habit
    target_value: float
    current_value: float
    unit: str  # hours, assignments, percentage, sessions
    start_date: str
    target_date: str
    status: str  # not_started, in_progress, completed, abandoned
    is_smart: bool
    milestones: List[Dict[str, Any]]
    progress_percentage: float


@dataclass
class Milestone:
    """Milestone data structure."""
    id: str
    goal_id: str
    title: str
    description: str
    target_value: float
    target_date: str
    completed: bool
    completed_date: Optional[str]


@dataclass
class GoalTemplate:
    """Pre-defined goal template."""
    name: str
    description: str
    goal_type: str
    suggested_target: float
    unit: str
    duration_days: int


class GoalSystem:
    """
    Goal Setting and Tracking System.

    Provides:
    - SMART goal creation
    - Milestone management
    - Progress tracking
    - Goal templates
    - Achievement detection
    """

    # Goal templates
    TEMPLATES = [
        GoalTemplate(
            name="Daily Study Habit",
            description="Study for X hours every day",
            goal_type="study_habit",
            suggested_target=2.0,
            unit="hours",
            duration_days=30
        ),
        GoalTemplate(
            name="Assignment Completion",
            description="Complete X% of assignments on time",
            goal_type="completion",
            suggested_target=90.0,
            unit="percentage",
            duration_days=30
        ),
        GoalTemplate(
            name="Grade Improvement",
            description="Achieve X% average grade",
            goal_type="grade",
            suggested_target=85.0,
            unit="percentage",
            duration_days=90
        ),
        GoalTemplate(
            name="Focus Sessions",
            description="Complete X focus sessions per week",
            goal_type="study_habit",
            suggested_target=15.0,
            unit="sessions",
            duration_days=7
        ),
        GoalTemplate(
            name="Subject Mastery",
            description="Achieve X% in specific subject",
            goal_type="academic",
            suggested_target=90.0,
            unit="percentage",
            duration_days=60
        )
    ]

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Goal System.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Goal System initialized for user {user_id}")

    def create_goal(
        self,
        title: str,
        description: str,
        goal_type: str,
        target_value: float,
        unit: str,
        target_date: str,
        category: str = "short_term",
        milestones: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new SMART goal.

        Args:
            title: Goal title (Specific)
            description: Detailed description
            goal_type: Type of goal
            target_value: Target value (Measurable)
            unit: Unit of measurement
            target_date: Deadline (Time-bound)
            category: Goal category
            milestones: Optional milestone list

        Returns:
            Goal creation result
        """
        try:
            goal_id = str(uuid.uuid4())
            start_date = datetime.now().isoformat()

            # Validate SMART criteria
            is_smart = self._validate_smart_goal(
                title,
                description,
                target_value,
                target_date
            )

            # Create goal
            query = """
            INSERT INTO goals (
                id, user_id, title, description, goal_type, category,
                target_value, current_value, unit, start_date, target_date,
                status, is_smart, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    goal_id,
                    self.user_id,
                    title,
                    description,
                    goal_type,
                    category,
                    target_value,
                    0.0,  # current_value starts at 0
                    unit,
                    start_date,
                    target_date,
                    "not_started",
                    1 if is_smart else 0,
                    datetime.now().isoformat()
                )
            )

            # Create milestones if provided
            created_milestones = []
            if milestones:
                for milestone in milestones:
                    milestone_result = self.create_milestone(
                        goal_id,
                        milestone['title'],
                        milestone.get('description', ''),
                        milestone['target_value'],
                        milestone['target_date']
                    )
                    if milestone_result['success']:
                        created_milestones.append(milestone_result['milestone_id'])

            logger.info(f"Created goal: {goal_id} - {title}")

            return {
                'success': True,
                'goal_id': goal_id,
                'is_smart': is_smart,
                'milestones_created': len(created_milestones)
            }

        except Exception as e:
            logger.error(f"Failed to create goal: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_from_template(
        self,
        template_name: str,
        target_value: Optional[float] = None,
        custom_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create goal from template.

        Args:
            template_name: Template name
            target_value: Custom target (uses suggested if None)
            custom_duration: Custom duration in days

        Returns:
            Goal creation result
        """
        try:
            # Find template
            template = None
            for t in self.TEMPLATES:
                if t.name == template_name:
                    template = t
                    break

            if not template:
                return {
                    'success': False,
                    'error': f'Template not found: {template_name}'
                }

            # Use template values or custom
            target = target_value if target_value is not None else template.suggested_target
            duration = custom_duration if custom_duration is not None else template.duration_days
            target_date = (datetime.now() + timedelta(days=duration)).isoformat()

            # Create goal
            return self.create_goal(
                title=template.name,
                description=template.description,
                goal_type=template.goal_type,
                target_value=target,
                unit=template.unit,
                target_date=target_date,
                category="short_term" if duration <= 30 else "long_term"
            )

        except Exception as e:
            logger.error(f"Failed to create from template: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_milestone(
        self,
        goal_id: str,
        title: str,
        description: str,
        target_value: float,
        target_date: str
    ) -> Dict[str, Any]:
        """
        Create milestone for a goal.

        Args:
            goal_id: Parent goal ID
            title: Milestone title
            description: Description
            target_value: Target value
            target_date: Target date

        Returns:
            Milestone creation result
        """
        try:
            milestone_id = str(uuid.uuid4())

            query = """
            INSERT INTO milestones (
                id, goal_id, title, description, target_value,
                target_date, completed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    milestone_id,
                    goal_id,
                    title,
                    description,
                    target_value,
                    target_date,
                    0,
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Created milestone: {milestone_id} for goal {goal_id}")

            return {
                'success': True,
                'milestone_id': milestone_id
            }

        except Exception as e:
            logger.error(f"Failed to create milestone: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def update_goal_progress(
        self,
        goal_id: str,
        current_value: float
    ) -> Dict[str, Any]:
        """
        Update goal progress.

        Args:
            goal_id: Goal ID
            current_value: New current value

        Returns:
            Update result
        """
        try:
            # Get goal
            goal = self.get_goal(goal_id)
            if not goal.get('success'):
                return goal

            goal_data = goal['goal']

            # Calculate progress
            target = goal_data['target_value']
            progress_percentage = (current_value / target * 100) if target > 0 else 0

            # Determine new status
            if progress_percentage >= 100:
                new_status = "completed"
            elif current_value > 0:
                new_status = "in_progress"
            else:
                new_status = "not_started"

            # Update goal
            query = """
            UPDATE goals
            SET current_value = ?,
                status = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(
                query,
                (
                    current_value,
                    new_status,
                    datetime.now().isoformat(),
                    goal_id,
                    self.user_id
                )
            )

            # Check and update milestones
            self._update_milestones(goal_id, current_value)

            logger.info(f"Updated goal {goal_id}: {current_value}/{target}")

            return {
                'success': True,
                'current_value': current_value,
                'target_value': target,
                'progress_percentage': round(progress_percentage, 1),
                'status': new_status,
                'completed': new_status == "completed"
            }

        except Exception as e:
            logger.error(f"Failed to update goal progress: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_goal(self, goal_id: str) -> Dict[str, Any]:
        """
        Get goal by ID.

        Args:
            goal_id: Goal ID

        Returns:
            Goal data
        """
        try:
            query = "SELECT * FROM goals WHERE id = ? AND user_id = ?"
            goal = self.db.execute_query(
                query,
                (goal_id, self.user_id),
                fetch_one=True
            )

            if not goal:
                return {
                    'success': False,
                    'error': 'Goal not found'
                }

            # Get milestones
            milestone_query = "SELECT * FROM milestones WHERE goal_id = ?"
            milestones = self.db.execute_query(
                milestone_query,
                (goal_id,),
                fetch_all=True
            ) or []

            # Calculate progress
            progress_percentage = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0

            goal['progress_percentage'] = round(progress_percentage, 1)
            goal['milestones'] = milestones

            return {
                'success': True,
                'goal': goal
            }

        except Exception as e:
            logger.error(f"Failed to get goal: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_active_goals(self) -> Dict[str, Any]:
        """
        Get all active goals.

        Returns:
            Active goals list
        """
        try:
            query = """
            SELECT * FROM goals
            WHERE user_id = ?
            AND status IN ('not_started', 'in_progress')
            AND date(target_date) >= date('now')
            ORDER BY target_date ASC
            """

            goals = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_all=True
            ) or []

            # Add progress percentages
            for goal in goals:
                progress = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
                goal['progress_percentage'] = round(progress, 1)

            return {
                'success': True,
                'goals': goals,
                'count': len(goals)
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
            AND status = 'completed'
            AND updated_at >= ?
            ORDER BY updated_at DESC
            """

            goals = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            ) or []

            return {
                'success': True,
                'goals': goals,
                'count': len(goals)
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
        Get goal statistics.

        Returns:
            Goal statistics
        """
        try:
            query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) as not_started,
                AVG(current_value / NULLIF(target_value, 0) * 100) as avg_progress
            FROM goals
            WHERE user_id = ?
            """

            stats = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_one=True
            )

            if not stats or stats['total'] == 0:
                return {
                    'success': True,
                    'total': 0,
                    'completed': 0,
                    'in_progress': 0,
                    'not_started': 0,
                    'completion_rate': 0.0,
                    'average_progress': 0.0
                }

            completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0

            return {
                'success': True,
                'total': stats['total'],
                'completed': stats['completed'],
                'in_progress': stats['in_progress'],
                'not_started': stats['not_started'],
                'completion_rate': round(completion_rate, 1),
                'average_progress': round(stats['avg_progress'] or 0, 1)
            }

        except Exception as e:
            logger.error(f"Failed to get goal statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_templates(self) -> Dict[str, Any]:
        """
        Get available goal templates.

        Returns:
            Template list
        """
        return {
            'success': True,
            'templates': [
                {
                    'name': t.name,
                    'description': t.description,
                    'goal_type': t.goal_type,
                    'suggested_target': t.suggested_target,
                    'unit': t.unit,
                    'duration_days': t.duration_days
                }
                for t in self.TEMPLATES
            ]
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
            # Delete milestones first
            self.db.execute_query(
                "DELETE FROM milestones WHERE goal_id = ?",
                (goal_id,)
            )

            # Delete goal
            self.db.execute_query(
                "DELETE FROM goals WHERE id = ? AND user_id = ?",
                (goal_id, self.user_id)
            )

            logger.info(f"Deleted goal: {goal_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to delete goal: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_smart_goal(
        self,
        title: str,
        description: str,
        target_value: float,
        target_date: str
    ) -> bool:
        """
        Validate if goal meets SMART criteria.

        Returns:
            True if SMART
        """
        # Specific: Has title and description
        specific = len(title) >= 5 and len(description) >= 10

        # Measurable: Has numeric target
        measurable = target_value > 0

        # Achievable: Target is reasonable (subjective, so always True)
        achievable = True

        # Relevant: Has valid goal type (checked during creation)
        relevant = True

        # Time-bound: Has target date in future
        try:
            target_dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            time_bound = target_dt > datetime.now()
        except:
            time_bound = False

        return specific and measurable and achievable and relevant and time_bound

    def _update_milestones(self, goal_id: str, current_value: float) -> None:
        """Update milestone completion based on current value."""
        try:
            # Get uncompleted milestones
            query = """
            SELECT * FROM milestones
            WHERE goal_id = ? AND completed = 0
            ORDER BY target_value ASC
            """

            milestones = self.db.execute_query(
                query,
                (goal_id,),
                fetch_all=True
            ) or []

            # Mark completed milestones
            for milestone in milestones:
                if current_value >= milestone['target_value']:
                    update_query = """
                    UPDATE milestones
                    SET completed = 1,
                        completed_date = ?
                    WHERE id = ?
                    """

                    self.db.execute_query(
                        update_query,
                        (datetime.now().isoformat(), milestone['id'])
                    )

                    logger.info(f"Milestone completed: {milestone['id']}")

        except Exception as e:
            logger.error(f"Failed to update milestones: {e}")


def create_goal_system(
    user_id: str,
    db_manager: Optional[DatabaseManager] = None
) -> GoalSystem:
    """
    Factory function to create Goal System.

    Args:
        user_id: Current user ID
        db_manager: Database manager instance

    Returns:
        GoalSystem instance
    """
    return GoalSystem(user_id, db_manager)
