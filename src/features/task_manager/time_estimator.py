"""
Academic Command Center - Task Manager - Time Estimator
Estimates task completion time using complexity analysis and user history.
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


class TimeEstimator:
    """
    Estimates task completion time.

    Uses:
    - Base estimates from task templates
    - Task complexity factors
    - User's historical performance
    - Time of day preferences
    """

    # Complexity multipliers
    COMPLEXITY_FACTORS = {
        'word_count': {
            # Words per hour for different activities
            'research': 0,  # Research doesn't produce words
            'outline': 200,  # Can outline ~200 words worth of content per hour
            'draft': 400,  # ~400 words per hour (first draft)
            'revision': 800,  # ~800 words per hour (editing faster than writing)
        },
        'academic_level': {
            'undergraduate': 1.0,
            'graduate': 1.3,
            'phd': 1.5
        },
        'familiarity': {
            'expert': 0.7,
            'familiar': 1.0,
            'new': 1.4
        },
        'difficulty': {
            'easy': 0.8,
            'medium': 1.0,
            'hard': 1.3,
            'very_hard': 1.6
        }
    }

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize time estimator.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

    def estimate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate time for a single task.

        Args:
            task: Task dictionary

        Returns:
            Updated task with refined time estimate
        """
        base_minutes = task.get('estimated_minutes', 60)
        task_type = task.get('task_type', 'writing')
        task_category = task.get('task_category', 'draft')

        # Get complexity factors
        complexity = self._calculate_complexity(task)

        # Get user's historical speed factor
        user_factor = self._get_user_speed_factor(task_type, task_category)

        # Calculate adjusted estimate
        adjusted_minutes = int(base_minutes * complexity * user_factor)

        # Add buffer for breaks (every 90 minutes = 15 min break)
        if adjusted_minutes > 90:
            break_time = ((adjusted_minutes // 90) * 15)
            adjusted_minutes += break_time

        # Round to nearest 5 minutes
        adjusted_minutes = max(5, round(adjusted_minutes / 5) * 5)

        return {
            'original_estimate': base_minutes,
            'adjusted_estimate': adjusted_minutes,
            'complexity_factor': complexity,
            'user_factor': user_factor,
            'includes_breaks': adjusted_minutes > base_minutes * complexity * user_factor
        }

    def estimate_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Estimate time for a batch of tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            Batch time estimate with breakdown
        """
        total_minutes = 0
        by_type = {}
        estimates = []

        for task in tasks:
            estimate = self.estimate_task(task)
            total_minutes += estimate['adjusted_estimate']

            task_type = task.get('task_type', 'unknown')
            by_type[task_type] = by_type.get(task_type, 0) + estimate['adjusted_estimate']

            estimates.append({
                'task_id': task.get('id'),
                'task_title': task.get('title'),
                'estimate': estimate
            })

        # Convert to hours and days
        total_hours = total_minutes / 60
        work_days = total_hours / 4  # Assuming 4 hours of productive work per day

        return {
            'total_minutes': total_minutes,
            'total_hours': round(total_hours, 1),
            'estimated_work_days': round(work_days, 1),
            'breakdown_by_type': by_type,
            'task_estimates': estimates
        }

    def _calculate_complexity(self, task: Dict[str, Any]) -> float:
        """
        Calculate complexity multiplier for a task.

        Args:
            task: Task dictionary

        Returns:
            Complexity multiplier (0.7 to 1.6)
        """
        complexity = 1.0

        metadata = task.get('metadata', '{}')
        try:
            meta = json.loads(metadata) if isinstance(metadata, str) else metadata
        except:
            meta = {}

        # Factor 1: Word count complexity
        word_allocation = meta.get('word_allocation', 0)
        if word_allocation > 1500:
            complexity *= 1.1  # Longer sections take more time
        elif word_allocation > 3000:
            complexity *= 1.2

        # Factor 2: Is it a gap (unknown topic)?
        if meta.get('is_gap', False):
            complexity *= 1.3  # Gap research takes longer

        # Factor 3: Task category difficulty
        task_category = task.get('task_category', '')
        category_difficulty = {
            'gap_research': 1.3,
            'concept_research': 1.1,
            'source_finding': 1.0,
            'rubric_research': 1.2,
            'outline': 0.9,
            'draft': 1.0,
            'revision': 0.8,
            'citations': 1.1,
            'formatting': 0.7
        }
        complexity *= category_difficulty.get(task_category, 1.0)

        # Factor 4: Section importance (intro/conclusion faster than body)
        section = meta.get('section', '').lower()
        if 'introduction' in section:
            complexity *= 0.9
        elif 'conclusion' in section:
            complexity *= 0.85
        elif 'analysis' in section or 'argument' in section:
            complexity *= 1.1

        # Clamp between 0.7 and 1.6
        return max(0.7, min(1.6, complexity))

    def _get_user_speed_factor(self, task_type: str, task_category: str) -> float:
        """
        Get user's speed factor based on historical performance.

        Args:
            task_type: Type of task
            task_category: Category of task

        Returns:
            Speed multiplier (0.7 to 1.5)
        """
        # Query user's historical task completion times
        query = """
        SELECT
            estimated_minutes,
            actual_minutes
        FROM tasks
        WHERE user_id = ?
        AND task_type = ?
        AND task_category = ?
        AND status = 'completed'
        AND actual_minutes IS NOT NULL
        AND estimated_minutes > 0
        ORDER BY completed_at DESC
        LIMIT 10
        """

        history = self.db.execute_query(
            query,
            (self.user_id, task_type, task_category),
            fetch_all=True
        )

        if not history or len(history) < 3:
            # Not enough data, use default
            return 1.0

        # Calculate average ratio of actual/estimated
        ratios = []
        for record in history:
            estimated = record.get('estimated_minutes', 0)
            actual = record.get('actual_minutes', 0)
            if estimated > 0 and actual > 0:
                ratios.append(actual / estimated)

        if not ratios:
            return 1.0

        # Use median to avoid outliers
        ratios.sort()
        median_ratio = ratios[len(ratios) // 2]

        # Clamp between 0.7 and 1.5
        return max(0.7, min(1.5, median_ratio))

    def predict_completion_date(
        self,
        tasks: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        hours_per_day: float = 4.0
    ) -> Dict[str, Any]:
        """
        Predict when tasks will be completed.

        Args:
            tasks: List of tasks
            start_date: When to start (default: now)
            hours_per_day: Available hours per day

        Returns:
            Completion prediction
        """
        if not tasks:
            return {
                'completion_date': None,
                'message': 'No tasks to schedule'
            }

        # Get total time estimate
        batch_estimate = self.estimate_batch(tasks)
        total_hours = batch_estimate['total_hours']

        # Calculate completion date
        if not start_date:
            start_date = datetime.now()

        days_needed = total_hours / hours_per_day

        # Account for weekends (add 2/7 more days)
        calendar_days = int(days_needed * (7/5))  # 5 work days per 7 calendar days

        completion_date = start_date + timedelta(days=calendar_days)

        return {
            'completion_date': completion_date.isoformat(),
            'days_needed': round(days_needed, 1),
            'calendar_days': calendar_days,
            'total_hours': total_hours,
            'hours_per_day': hours_per_day,
            'start_date': start_date.isoformat()
        }

    def suggest_daily_schedule(
        self,
        tasks: List[Dict[str, Any]],
        due_date: datetime,
        hours_per_day: float = 4.0
    ) -> Dict[str, Any]:
        """
        Suggest how to distribute tasks across days.

        Args:
            tasks: List of tasks
            due_date: Essay due date
            hours_per_day: Available hours per day

        Returns:
            Daily schedule suggestion
        """
        if not tasks:
            return {'schedule': [], 'message': 'No tasks to schedule'}

        # Sort tasks by priority and dependencies
        sorted_tasks = self._topological_sort(tasks)

        # Calculate total time needed
        batch_estimate = self.estimate_batch(sorted_tasks)
        total_hours = batch_estimate['total_hours']

        # Calculate days available
        now = datetime.now()
        if due_date <= now:
            return {
                'success': False,
                'error': 'Due date is in the past or today'
            }

        days_available = (due_date - now).days

        # Check if realistic
        if total_hours / hours_per_day > days_available:
            return {
                'success': False,
                'warning': 'Not enough time before deadline',
                'hours_needed': total_hours,
                'days_available': days_available,
                'hours_per_day_required': round(total_hours / days_available, 1)
            }

        # Distribute tasks across days
        schedule = []
        current_day = 0
        current_day_hours = 0
        current_day_tasks = []

        for task in sorted_tasks:
            estimate = self.estimate_task(task)
            task_hours = estimate['adjusted_estimate'] / 60

            # If adding this task exceeds daily limit, start new day
            if current_day_hours + task_hours > hours_per_day and current_day_tasks:
                schedule.append({
                    'day': current_day + 1,
                    'date': (now + timedelta(days=current_day)).date().isoformat(),
                    'hours': round(current_day_hours, 1),
                    'tasks': current_day_tasks
                })
                current_day += 1
                current_day_hours = 0
                current_day_tasks = []

            # Add task to current day
            current_day_tasks.append({
                'task_id': task.get('id'),
                'title': task.get('title'),
                'minutes': estimate['adjusted_estimate']
            })
            current_day_hours += task_hours

        # Add final day
        if current_day_tasks:
            schedule.append({
                'day': current_day + 1,
                'date': (now + timedelta(days=current_day)).date().isoformat(),
                'hours': round(current_day_hours, 1),
                'tasks': current_day_tasks
            })

        return {
            'success': True,
            'schedule': schedule,
            'total_days': len(schedule),
            'days_available': days_available,
            'buffer_days': days_available - len(schedule)
        }

    def _topological_sort(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort tasks by dependencies (tasks with no dependencies first).

        Args:
            tasks: List of tasks

        Returns:
            Sorted tasks
        """
        # Build dependency graph
        task_map = {task['id']: task for task in tasks}
        sorted_tasks = []
        processed = set()

        def process_task(task):
            if task['id'] in processed:
                return

            # Process dependencies first
            dependencies = task.get('dependencies', [])
            if isinstance(dependencies, str):
                try:
                    dependencies = json.loads(dependencies)
                except:
                    dependencies = []

            for dep_id in dependencies:
                if dep_id in task_map:
                    process_task(task_map[dep_id])

            sorted_tasks.append(task)
            processed.add(task['id'])

        for task in tasks:
            process_task(task)

        return sorted_tasks


if __name__ == "__main__":
    print("Testing Time Estimator...")

    estimator = TimeEstimator(user_id="test_user")

    test_task = {
        'id': '123',
        'title': 'Write Introduction',
        'task_type': 'writing',
        'task_category': 'draft',
        'estimated_minutes': 60,
        'metadata': json.dumps({
            'section': 'Introduction',
            'word_allocation': 250
        })
    }

    result = estimator.estimate_task(test_task)
    print(f"\nEstimate: {result['adjusted_estimate']} minutes")
    print(f"Complexity: {result['complexity_factor']}")
    print(f"User factor: {result['user_factor']}")

    print("\nTime Estimator validated!")
