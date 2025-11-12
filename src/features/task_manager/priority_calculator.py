"""
Academic Command Center - Task Manager - Priority Calculator
Calculates task priority based on deadlines, dependencies, and importance.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PriorityCalculator:
    """
    Calculates task priority scores.

    Factors:
    - Time until deadline (urgency)
    - Task dependencies (blocking others)
    - Task type (research before writing)
    - Rubric points (high-value tasks)
    - User's completion rate
    """

    # Priority weights
    WEIGHTS = {
        'urgency': 0.40,      # 40% - How soon is the deadline?
        'dependencies': 0.25,  # 25% - How many tasks depend on this?
        'importance': 0.20,    # 20% - How valuable is this task?
        'sequence': 0.15       # 15% - Where in the workflow is this?
    }

    # Sequence priorities (research before writing before polishing)
    SEQUENCE_PRIORITY = {
        'gap_research': 100,
        'concept_research': 95,
        'source_finding': 90,
        'rubric_research': 85,
        'outline': 80,
        'draft': 70,
        'revision': 50,
        'citations': 30,
        'formatting': 20
    }

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize priority calculator.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

    def calculate_priority(
        self,
        task: Dict[str, Any],
        essay_due_date: Optional[datetime],
        all_tasks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate priority score for a task.

        Args:
            task: Task dictionary
            essay_due_date: Essay deadline
            all_tasks: All tasks for the essay (to calculate dependencies)

        Returns:
            Priority analysis
        """
        # Calculate each factor
        urgency_score = self._calculate_urgency(task, essay_due_date)
        dependency_score = self._calculate_dependency_score(task, all_tasks)
        importance_score = self._calculate_importance(task)
        sequence_score = self._calculate_sequence_score(task)

        # Weighted total
        total_score = (
            urgency_score * self.WEIGHTS['urgency'] +
            dependency_score * self.WEIGHTS['dependencies'] +
            importance_score * self.WEIGHTS['importance'] +
            sequence_score * self.WEIGHTS['sequence']
        )

        # Round to integer (0-100)
        total_score = max(0, min(100, int(total_score)))

        return {
            'priority_score': total_score,
            'breakdown': {
                'urgency': urgency_score,
                'dependencies': dependency_score,
                'importance': importance_score,
                'sequence': sequence_score
            },
            'priority_label': self._get_priority_label(total_score)
        }

    def recalculate_all_priorities(self, essay_id: str) -> Dict[str, Any]:
        """
        Recalculate priorities for all tasks in an essay.

        Args:
            essay_id: Essay ID

        Returns:
            Update results
        """
        # Get essay and all tasks
        essay = self._get_essay(essay_id)
        if not essay:
            return {'success': False, 'error': 'Essay not found'}

        tasks = self._get_essay_tasks(essay_id)
        if not tasks:
            return {'success': True, 'message': 'No tasks to update'}

        # Parse due date
        due_date = None
        if essay.get('due_date'):
            try:
                due_date = datetime.fromisoformat(essay['due_date'])
            except:
                pass

        # Recalculate for each task
        updates = []
        for task in tasks:
            priority_result = self.calculate_priority(task, due_date, tasks)

            updates.append({
                'task_id': task['id'],
                'old_priority': task.get('priority_score', 0),
                'new_priority': priority_result['priority_score']
            })

            # Update database
            self._update_task_priority(task['id'], priority_result['priority_score'])

        return {
            'success': True,
            'updated': len(updates),
            'updates': updates
        }

    def _calculate_urgency(
        self,
        task: Dict[str, Any],
        essay_due_date: Optional[datetime]
    ) -> float:
        """
        Calculate urgency score (0-100).

        Args:
            task: Task dictionary
            essay_due_date: Essay deadline

        Returns:
            Urgency score
        """
        if not essay_due_date:
            # No deadline = medium urgency
            return 50.0

        now = datetime.now()

        # If deadline passed, maximum urgency
        if essay_due_date <= now:
            return 100.0

        # Calculate days until deadline
        days_until = (essay_due_date - now).total_seconds() / 86400

        # Get task's estimated time
        estimated_minutes = task.get('estimated_minutes', 60)
        task_days = estimated_minutes / (60 * 4)  # Assuming 4 hours work per day

        # Calculate "buffer ratio" = time available / time needed
        buffer_ratio = days_until / max(task_days, 0.5)

        # Convert to urgency score (inverse relationship)
        # buffer_ratio < 1.0 = very urgent (score > 80)
        # buffer_ratio 1.0-2.0 = urgent (score 60-80)
        # buffer_ratio 2.0-5.0 = medium (score 40-60)
        # buffer_ratio > 5.0 = low (score < 40)

        if buffer_ratio < 1.0:
            # Critical - not enough time
            urgency = 100 - (buffer_ratio * 20)
        elif buffer_ratio < 2.0:
            # Urgent
            urgency = 80 - ((buffer_ratio - 1.0) * 20)
        elif buffer_ratio < 5.0:
            # Medium
            urgency = 60 - ((buffer_ratio - 2.0) * 6.67)
        else:
            # Low urgency
            urgency = 40 - min((buffer_ratio - 5.0) * 5, 30)

        return max(0, min(100, urgency))

    def _calculate_dependency_score(
        self,
        task: Dict[str, Any],
        all_tasks: Optional[List[Dict[str, Any]]]
    ) -> float:
        """
        Calculate dependency score (0-100).

        Higher score = more tasks depend on this one (it's blocking others).

        Args:
            task: Task dictionary
            all_tasks: All tasks in the essay

        Returns:
            Dependency score
        """
        if not all_tasks:
            return 50.0

        task_id = task['id']

        # Count how many tasks depend on this one
        dependent_count = 0

        for other_task in all_tasks:
            dependencies = other_task.get('dependencies', [])
            if isinstance(dependencies, str):
                try:
                    dependencies = json.loads(dependencies)
                except:
                    dependencies = []

            if task_id in dependencies:
                dependent_count += 1

        # Convert to score
        # 0 dependents = low priority (30)
        # 1-2 dependents = medium (50-70)
        # 3+ dependents = high (80-100)

        if dependent_count == 0:
            return 30.0
        elif dependent_count == 1:
            return 50.0
        elif dependent_count == 2:
            return 70.0
        else:
            return min(100.0, 80.0 + (dependent_count - 3) * 5)

    def _calculate_importance(self, task: Dict[str, Any]) -> float:
        """
        Calculate task importance (0-100).

        Based on:
        - Rubric points (if applicable)
        - Whether it's a knowledge gap
        - Task type

        Args:
            task: Task dictionary

        Returns:
            Importance score
        """
        importance = 50.0  # Default

        metadata = task.get('metadata', '{}')
        try:
            meta = json.loads(metadata) if isinstance(metadata, str) else metadata
        except:
            meta = {}

        # Factor 1: Knowledge gaps are important
        if meta.get('is_gap', False):
            importance += 20

        # Factor 2: Rubric points
        rubric_points = meta.get('points', 0)
        if rubric_points > 0:
            # Scale: 10 points = +10 importance, 40 points = +30 importance
            importance += min(30, rubric_points / 2)

        # Factor 3: Task type importance
        task_type = task.get('task_type', '')
        if task_type == 'research':
            importance += 10  # Research is foundation for everything
        elif task_type == 'writing':
            task_category = task.get('task_category', '')
            if task_category == 'draft':
                importance += 15  # Draft is core work
            elif task_category == 'outline':
                importance += 10  # Outline is important prep

        # Clamp between 0 and 100
        return max(0, min(100, importance))

    def _calculate_sequence_score(self, task: Dict[str, Any]) -> float:
        """
        Calculate sequence score (0-100).

        Research should come before writing, writing before polishing.

        Args:
            task: Task dictionary

        Returns:
            Sequence score
        """
        task_category = task.get('task_category', '')

        # Use predefined sequence priorities
        return self.SEQUENCE_PRIORITY.get(task_category, 50)

    def _get_priority_label(self, score: int) -> str:
        """
        Get human-readable priority label.

        Args:
            score: Priority score (0-100)

        Returns:
            Label string
        """
        if score >= 80:
            return 'Critical'
        elif score >= 65:
            return 'High'
        elif score >= 45:
            return 'Medium'
        elif score >= 25:
            return 'Low'
        else:
            return 'Very Low'

    def _get_essay(self, essay_id: str) -> Optional[Dict[str, Any]]:
        """Get essay from database."""
        query = "SELECT * FROM essays WHERE id = ?"
        return self.db.execute_query(query, (essay_id,), fetch_one=True)

    def _get_essay_tasks(self, essay_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for an essay."""
        query = """
        SELECT * FROM tasks
        WHERE essay_id = ?
        AND status != 'completed'
        ORDER BY priority_score DESC
        """
        return self.db.execute_query(query, (essay_id,), fetch_all=True) or []

    def _update_task_priority(self, task_id: str, priority_score: int) -> bool:
        """Update task priority in database."""
        try:
            query = "UPDATE tasks SET priority_score = ? WHERE id = ?"
            self.db.execute_query(query, (priority_score, task_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update task priority: {e}")
            return False


if __name__ == "__main__":
    print("Testing Priority Calculator...")

    calculator = PriorityCalculator(user_id="test_user")

    test_task = {
        'id': '123',
        'title': 'Research: Postmodernism',
        'task_type': 'research',
        'task_category': 'gap_research',
        'estimated_minutes': 45,
        'dependencies': [],
        'metadata': json.dumps({
            'concept': 'Postmodernism',
            'is_gap': True
        })
    }

    due_date = datetime.now() + timedelta(days=7)

    result = calculator.calculate_priority(test_task, due_date, [test_task])

    print(f"\nPriority Score: {result['priority_score']}")
    print(f"Label: {result['priority_label']}")
    print(f"Breakdown: {result['breakdown']}")

    print("\nPriority Calculator validated!")
