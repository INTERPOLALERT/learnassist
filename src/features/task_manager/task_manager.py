"""
Academic Command Center - Task Manager - Main Orchestrator
Coordinates task generation, estimation, and prioritization.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager, DatabaseHelper
from .research_generator import ResearchTaskGenerator
from .writing_generator import WritingTaskGenerator
from .time_estimator import TimeEstimator
from .priority_calculator import PriorityCalculator

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TaskManager:
    """
    Main task manager orchestrator.

    Workflow:
    1. Generate research tasks (from essay parser output)
    2. Generate writing tasks (from essay structure)
    3. Estimate time for all tasks (using user history)
    4. Calculate priorities (based on deadlines and dependencies)
    5. Create daily schedule (reverse calendar from deadline)
    6. Save all tasks to database
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize task manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.db_helper = DatabaseHelper(self.db)

        # Initialize all components
        self.research_generator = ResearchTaskGenerator(user_id, self.db)
        self.writing_generator = WritingTaskGenerator(user_id, self.db)
        self.time_estimator = TimeEstimator(user_id, self.db)
        self.priority_calculator = PriorityCalculator(user_id, self.db)

    def generate_all_tasks(self, essay_id: str) -> Dict[str, Any]:
        """
        Generate complete task breakdown for an essay.

        Args:
            essay_id: Essay ID

        Returns:
            Result with all generated tasks
        """
        logger.info("=" * 60)
        logger.info(f"Generating tasks for essay {essay_id}")
        logger.info("=" * 60)

        try:
            # Get essay data
            essay = self._get_essay(essay_id)
            if not essay:
                return {'success': False, 'error': 'Essay not found'}

            logger.info(f"Essay: {essay.get('title', 'Untitled')}")

            # Step 1: Generate research tasks
            logger.info("\n[1/5] Generating research tasks...")
            research_result = self.research_generator.generate_tasks(essay_id)

            if not research_result['success']:
                logger.warning(f"Research task generation failed: {research_result.get('error')}")
                research_tasks = []
            else:
                research_tasks = research_result['tasks']
                logger.info(f"✓ Generated {len(research_tasks)} research tasks")

            # Step 2: Generate writing tasks
            logger.info("\n[2/5] Generating writing tasks...")
            writing_result = self.writing_generator.generate_tasks(essay_id)

            if not writing_result['success']:
                logger.warning(f"Writing task generation failed: {writing_result.get('error')}")
                writing_tasks = []
            else:
                writing_tasks = writing_result['tasks']
                logger.info(f"✓ Generated {len(writing_tasks)} writing tasks")

            # Combine all tasks
            all_tasks = research_tasks + writing_tasks
            logger.info(f"\nTotal tasks generated: {len(all_tasks)}")

            # Step 3: Refine time estimates
            logger.info("\n[3/5] Refining time estimates...")
            for task in all_tasks:
                estimate = self.time_estimator.estimate_task(task)
                task['estimated_minutes'] = estimate['adjusted_estimate']
                task['time_metadata'] = json.dumps(estimate)

            logger.info("✓ Time estimates refined")

            # Step 4: Calculate priorities
            logger.info("\n[4/5] Calculating priorities...")
            due_date = None
            if essay.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(essay['due_date'])
                except:
                    pass

            for task in all_tasks:
                priority = self.priority_calculator.calculate_priority(
                    task,
                    due_date,
                    all_tasks
                )
                task['priority_score'] = priority['priority_score']
                task['priority_metadata'] = json.dumps(priority)

            logger.info("✓ Priorities calculated")

            # Step 5: Update all tasks in database with new estimates and priorities
            logger.info("\n[5/5] Updating task metadata...")
            updated_count = 0
            for task in all_tasks:
                if self._update_task_metadata(task):
                    updated_count += 1

            logger.info(f"✓ Updated {updated_count}/{len(all_tasks)} tasks")

            # Generate summary statistics
            summary = self._generate_summary(all_tasks, essay)

            logger.info("\n" + "=" * 60)
            logger.info("Task generation completed successfully!")
            logger.info("=" * 60)

            return {
                'success': True,
                'essay_id': essay_id,
                'tasks': all_tasks,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"Task generation failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_daily_schedule(
        self,
        essay_id: str,
        hours_per_day: float = 4.0
    ) -> Dict[str, Any]:
        """
        Create daily schedule for essay tasks.

        Args:
            essay_id: Essay ID
            hours_per_day: Available work hours per day

        Returns:
            Daily schedule
        """
        essay = self._get_essay(essay_id)
        if not essay:
            return {'success': False, 'error': 'Essay not found'}

        # Get all incomplete tasks
        tasks = self._get_incomplete_tasks(essay_id)
        if not tasks:
            return {
                'success': True,
                'message': 'No incomplete tasks',
                'schedule': []
            }

        # Get due date
        due_date = None
        if essay.get('due_date'):
            try:
                due_date = datetime.fromisoformat(essay['due_date'])
            except:
                pass

        if not due_date:
            # No deadline - predict completion date
            prediction = self.time_estimator.predict_completion_date(
                tasks,
                hours_per_day=hours_per_day
            )
            return {
                'success': True,
                'no_deadline': True,
                'prediction': prediction
            }

        # Create schedule
        schedule_result = self.time_estimator.suggest_daily_schedule(
            tasks,
            due_date,
            hours_per_day
        )

        return {
            'success': True,
            'schedule': schedule_result
        }

    def get_next_tasks(
        self,
        essay_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get the next tasks to work on.

        Args:
            essay_id: Essay ID
            limit: Maximum number of tasks to return

        Returns:
            Next tasks ordered by priority
        """
        # Get all incomplete tasks
        query = """
        SELECT * FROM tasks
        WHERE essay_id = ?
        AND status = 'pending'
        ORDER BY priority_score DESC, created_at ASC
        LIMIT ?
        """

        tasks = self.db.execute_query(query, (essay_id, limit), fetch_all=True)

        if not tasks:
            return {
                'success': True,
                'message': 'No pending tasks',
                'tasks': []
            }

        # Check if dependencies are met
        available_tasks = []
        blocked_tasks = []

        for task in tasks:
            if self._check_dependencies_met(task):
                available_tasks.append(task)
            else:
                blocked_tasks.append(task)

        return {
            'success': True,
            'available_tasks': available_tasks,
            'blocked_tasks': blocked_tasks,
            'count': len(available_tasks)
        }

    def mark_task_completed(
        self,
        task_id: str,
        actual_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID
            actual_minutes: Actual time taken (for learning)

        Returns:
            Update result
        """
        try:
            query = """
            UPDATE tasks
            SET status = 'completed',
                completed_at = ?,
                actual_minutes = ?
            WHERE id = ?
            """

            self.db.execute_query(
                query,
                (datetime.now().isoformat(), actual_minutes, task_id)
            )

            # Recalculate priorities for remaining tasks
            task = self._get_task(task_id)
            if task:
                essay_id = task.get('essay_id')
                if essay_id:
                    self.priority_calculator.recalculate_all_priorities(essay_id)

            return {
                'success': True,
                'task_id': task_id,
                'message': 'Task marked as completed'
            }

        except Exception as e:
            logger.error(f"Failed to mark task completed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_essay(self, essay_id: str) -> Optional[Dict[str, Any]]:
        """Get essay from database."""
        query = "SELECT * FROM essays WHERE id = ?"
        return self.db.execute_query(query, (essay_id,), fetch_one=True)

    def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task from database."""
        query = "SELECT * FROM tasks WHERE id = ?"
        return self.db.execute_query(query, (task_id,), fetch_one=True)

    def _get_incomplete_tasks(self, essay_id: str) -> List[Dict[str, Any]]:
        """Get all incomplete tasks for an essay."""
        query = """
        SELECT * FROM tasks
        WHERE essay_id = ?
        AND status != 'completed'
        ORDER BY priority_score DESC
        """
        return self.db.execute_query(query, (essay_id,), fetch_all=True) or []

    def _update_task_metadata(self, task: Dict[str, Any]) -> bool:
        """Update task with refined estimates and priorities."""
        try:
            query = """
            UPDATE tasks
            SET estimated_minutes = ?,
                priority_score = ?
            WHERE id = ?
            """

            self.db.execute_query(
                query,
                (
                    task['estimated_minutes'],
                    task['priority_score'],
                    task['id']
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update task metadata: {e}")
            return False

    def _check_dependencies_met(self, task: Dict[str, Any]) -> bool:
        """Check if all task dependencies are completed."""
        dependencies = task.get('dependencies', [])
        if isinstance(dependencies, str):
            try:
                dependencies = json.loads(dependencies)
            except:
                dependencies = []

        if not dependencies:
            return True  # No dependencies

        # Check if all dependencies are completed
        for dep_id in dependencies:
            dep_task = self._get_task(dep_id)
            if not dep_task or dep_task.get('status') != 'completed':
                return False

        return True

    def _generate_summary(
        self,
        tasks: List[Dict[str, Any]],
        essay: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary statistics."""
        # Count by type
        research_count = sum(1 for t in tasks if t.get('task_type') == 'research')
        writing_count = sum(1 for t in tasks if t.get('task_type') == 'writing')

        # Count by priority
        critical_count = sum(1 for t in tasks if t.get('priority_score', 0) >= 80)
        high_count = sum(1 for t in tasks if 65 <= t.get('priority_score', 0) < 80)
        medium_count = sum(1 for t in tasks if 45 <= t.get('priority_score', 0) < 65)

        # Total time estimate
        total_minutes = sum(t.get('estimated_minutes', 0) for t in tasks)
        total_hours = total_minutes / 60
        work_days = total_hours / 4  # 4 hours per day

        # Check if realistic given deadline
        due_date_str = essay.get('due_date')
        realistic = True
        days_available = None

        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str)
                now = datetime.now()
                days_available = (due_date - now).days
                realistic = work_days <= days_available
            except:
                pass

        return {
            'total_tasks': len(tasks),
            'breakdown': {
                'research_tasks': research_count,
                'writing_tasks': writing_count
            },
            'by_priority': {
                'critical': critical_count,
                'high': high_count,
                'medium': medium_count
            },
            'time_estimate': {
                'total_minutes': total_minutes,
                'total_hours': round(total_hours, 1),
                'estimated_work_days': round(work_days, 1)
            },
            'deadline_analysis': {
                'days_available': days_available,
                'realistic': realistic,
                'hours_per_day_needed': round(total_hours / days_available, 1) if days_available else None
            }
        }


if __name__ == "__main__":
    print("Testing Task Manager...")

    manager = TaskManager(user_id="test_user")

    print("\nTask Manager structure validated!")
    print("\nUsage:")
    print("  manager.generate_all_tasks(essay_id)")
    print("  manager.get_next_tasks(essay_id)")
    print("  manager.get_daily_schedule(essay_id)")
    print("  manager.mark_task_completed(task_id, actual_minutes)")
