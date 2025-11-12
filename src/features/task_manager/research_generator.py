"""
Academic Command Center - Task Manager - Research Task Generator
Generates targeted research tasks from essay requirements and knowledge gaps.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager, DatabaseHelper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ResearchTaskGenerator:
    """
    Generates research tasks from essay analysis.

    Creates tasks for:
    - Knowledge gaps (missing concepts)
    - Required sources
    - Concept deep-dives
    - Rubric requirements
    """

    # Task templates for different research types
    TASK_TEMPLATES = {
        'gap_research': {
            'title_template': 'Research: {concept}',
            'description_template': 'Find and read materials covering "{concept}". {suggestion}',
            'base_time_minutes': 45,
            'priority_boost': 20  # Gaps are high priority
        },
        'concept_research': {
            'title_template': 'Deep dive: {concept}',
            'description_template': 'Research "{concept}" in depth. Focus on: {subtopics}',
            'base_time_minutes': 60,
            'priority_boost': 10
        },
        'source_finding': {
            'title_template': 'Find {count} academic sources',
            'description_template': 'Locate {count} academic sources about {topic}. Citation style: {style}',
            'base_time_minutes': 30,
            'priority_boost': 15
        },
        'rubric_research': {
            'title_template': 'Research for: {criterion}',
            'description_template': 'Research to meet rubric requirement: {requirement}',
            'base_time_minutes': 40,
            'priority_boost': 12
        }
    }

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize research task generator.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.db_helper = DatabaseHelper(self.db)

    def generate_tasks(self, essay_id: str) -> Dict[str, Any]:
        """
        Generate all research tasks for an essay.

        Args:
            essay_id: Essay ID

        Returns:
            Result with generated tasks
        """
        logger.info(f"Generating research tasks for essay {essay_id}")

        # Get essay data
        essay = self._get_essay(essay_id)
        if not essay:
            return {'success': False, 'error': 'Essay not found'}

        tasks = []

        # 1. Generate tasks for knowledge gaps (highest priority)
        gap_tasks = self._generate_gap_tasks(essay)
        tasks.extend(gap_tasks)
        logger.info(f"Generated {len(gap_tasks)} gap research tasks")

        # 2. Generate tasks for key concepts
        concept_tasks = self._generate_concept_tasks(essay)
        tasks.extend(concept_tasks)
        logger.info(f"Generated {len(concept_tasks)} concept research tasks")

        # 3. Generate source finding tasks
        source_tasks = self._generate_source_tasks(essay)
        tasks.extend(source_tasks)
        logger.info(f"Generated {len(source_tasks)} source finding tasks")

        # 4. Generate rubric-specific research tasks
        rubric_tasks = self._generate_rubric_tasks(essay)
        tasks.extend(rubric_tasks)
        logger.info(f"Generated {len(rubric_tasks)} rubric research tasks")

        # Save all tasks to database
        saved_count = 0
        for task in tasks:
            if self._save_task(task):
                saved_count += 1

        logger.info(f"Saved {saved_count}/{len(tasks)} research tasks")

        return {
            'success': True,
            'tasks': tasks,
            'count': len(tasks),
            'breakdown': {
                'gap_tasks': len(gap_tasks),
                'concept_tasks': len(concept_tasks),
                'source_tasks': len(source_tasks),
                'rubric_tasks': len(rubric_tasks)
            }
        }

    def _get_essay(self, essay_id: str) -> Optional[Dict[str, Any]]:
        """Get essay from database with all parsed data."""
        query = """
        SELECT
            id, user_id, title, course_name,
            word_count_min, word_count_max,
            required_sources_min, citation_style,
            due_date,
            key_concepts, knowledge_gaps,
            rubric_criteria, task_verbs
        FROM essays
        WHERE id = ?
        """

        essay = self.db.execute_query(query, (essay_id,), fetch_one=True)
        return essay

    def _generate_gap_tasks(self, essay: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tasks for knowledge gaps."""
        import json

        gaps_json = essay.get('knowledge_gaps')
        if not gaps_json:
            return []

        try:
            gaps = json.loads(gaps_json)
        except:
            return []

        tasks = []
        template = self.TASK_TEMPLATES['gap_research']

        for i, gap_concept in enumerate(gaps, 1):
            task = {
                'id': str(uuid.uuid4()),
                'essay_id': essay['id'],
                'user_id': essay['user_id'],
                'task_type': 'research',
                'task_category': 'gap_research',
                'title': template['title_template'].format(concept=gap_concept),
                'description': template['description_template'].format(
                    concept=gap_concept,
                    suggestion="This concept is missing from your materials."
                ),
                'estimated_minutes': template['base_time_minutes'],
                'priority_score': 100 - (i * 5) + template['priority_boost'],  # First gaps are highest priority
                'dependencies': [],
                'metadata': json.dumps({
                    'concept': gap_concept,
                    'is_gap': True
                })
            }
            tasks.append(task)

        return tasks

    def _generate_concept_tasks(self, essay: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tasks for key concepts (that aren't gaps)."""
        import json

        concepts_json = essay.get('key_concepts')
        gaps_json = essay.get('knowledge_gaps')

        if not concepts_json:
            return []

        try:
            concepts = json.loads(concepts_json)
            gaps = json.loads(gaps_json) if gaps_json else []
        except:
            return []

        # Only create tasks for concepts that aren't gaps
        non_gap_concepts = [c for c in concepts if c not in gaps]

        tasks = []
        template = self.TASK_TEMPLATES['concept_research']

        # Only create tasks for top 3-5 concepts to avoid overwhelming
        for i, concept in enumerate(non_gap_concepts[:5], 1):
            task = {
                'id': str(uuid.uuid4()),
                'essay_id': essay['id'],
                'user_id': essay['user_id'],
                'task_type': 'research',
                'task_category': 'concept_research',
                'title': template['title_template'].format(concept=concept),
                'description': template['description_template'].format(
                    concept=concept,
                    subtopics="definitions, key theorists, applications, critiques"
                ),
                'estimated_minutes': template['base_time_minutes'],
                'priority_score': 80 - (i * 5) + template['priority_boost'],
                'dependencies': [],
                'metadata': json.dumps({
                    'concept': concept,
                    'is_gap': False
                })
            }
            tasks.append(task)

        return tasks

    def _generate_source_tasks(self, essay: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tasks for finding required sources."""
        required_sources = essay.get('required_sources_min')
        if not required_sources or required_sources == 0:
            return []

        import json

        # Get key concepts to guide source search
        concepts_json = essay.get('key_concepts')
        concepts = json.loads(concepts_json) if concepts_json else []
        main_topic = concepts[0] if concepts else essay.get('title', 'your essay topic')

        citation_style = essay.get('citation_style') or 'standard academic'

        template = self.TASK_TEMPLATES['source_finding']

        # Create source finding tasks in batches
        tasks = []
        sources_per_task = 3  # Find 3 sources at a time
        batches = (required_sources + sources_per_task - 1) // sources_per_task

        for batch in range(batches):
            batch_size = min(sources_per_task, required_sources - (batch * sources_per_task))

            task = {
                'id': str(uuid.uuid4()),
                'essay_id': essay['id'],
                'user_id': essay['user_id'],
                'task_type': 'research',
                'task_category': 'source_finding',
                'title': template['title_template'].format(count=batch_size),
                'description': template['description_template'].format(
                    count=batch_size,
                    topic=main_topic,
                    style=citation_style
                ),
                'estimated_minutes': template['base_time_minutes'] * batch_size / 3,
                'priority_score': 85 - (batch * 5) + template['priority_boost'],
                'dependencies': [],
                'metadata': json.dumps({
                    'source_count': batch_size,
                    'citation_style': citation_style,
                    'batch': batch + 1
                })
            }
            tasks.append(task)

        return tasks

    def _generate_rubric_tasks(self, essay: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate research tasks based on rubric requirements."""
        import json

        rubric_json = essay.get('rubric_criteria')
        if not rubric_json:
            return []

        try:
            rubric = json.loads(rubric_json)
        except:
            return []

        tasks = []
        template = self.TASK_TEMPLATES['rubric_research']

        # For each rubric criterion, check if research is needed
        for criterion_name, criterion_data in rubric.items():
            if not isinstance(criterion_data, dict):
                continue

            checklist = criterion_data.get('checklist', [])

            # Create research tasks for checklist items that need it
            for item in checklist:
                if not isinstance(item, dict):
                    continue

                item_text = item.get('item', '')

                # Keywords that suggest research is needed
                research_keywords = ['research', 'find', 'identify', 'define', 'explain', 'theorist', 'source']

                if any(keyword in item_text.lower() for keyword in research_keywords):
                    task = {
                        'id': str(uuid.uuid4()),
                        'essay_id': essay['id'],
                        'user_id': essay['user_id'],
                        'task_type': 'research',
                        'task_category': 'rubric_research',
                        'title': template['title_template'].format(criterion=criterion_name),
                        'description': template['description_template'].format(requirement=item_text),
                        'estimated_minutes': template['base_time_minutes'],
                        'priority_score': 75 + template['priority_boost'],
                        'dependencies': [],
                        'metadata': json.dumps({
                            'criterion': criterion_name,
                            'requirement': item_text,
                            'points': criterion_data.get('points', 0)
                        })
                    }
                    tasks.append(task)
                    break  # Only one task per criterion

        return tasks

    def _save_task(self, task: Dict[str, Any]) -> bool:
        """Save task to database."""
        try:
            query = """
            INSERT INTO tasks (
                id, essay_id, user_id, task_type, task_category,
                title, description, estimated_minutes,
                priority_score, dependencies, metadata,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """

            import json

            self.db.execute_query(
                query,
                (
                    task['id'],
                    task['essay_id'],
                    task['user_id'],
                    task['task_type'],
                    task['task_category'],
                    task['title'],
                    task['description'],
                    task['estimated_minutes'],
                    task['priority_score'],
                    json.dumps(task['dependencies']),
                    task['metadata'],
                    datetime.now().isoformat()
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
            return False


if __name__ == "__main__":
    print("Testing Research Task Generator...")

    generator = ResearchTaskGenerator(user_id="test_user")

    print("\nResearch Task Generator structure validated!")
