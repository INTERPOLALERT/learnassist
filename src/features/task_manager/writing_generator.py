"""
Academic Command Center - Task Manager - Writing Task Generator
Generates structured writing tasks from essay structure and requirements.
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager, DatabaseHelper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class WritingTaskGenerator:
    """
    Generates writing tasks from essay structure.

    Creates tasks for:
    - Each essay section (intro, body, conclusion)
    - Outlining
    - Draft writing
    - Revision passes
    - Citation/formatting
    """

    # Task templates for different writing stages
    TASK_TEMPLATES = {
        'outline': {
            'title_template': 'Create outline for {section}',
            'description_template': 'Outline the key points for {section}. Target: {words} words. Purpose: {purpose}',
            'time_per_100_words': 5,  # minutes
            'priority_boost': 15
        },
        'draft': {
            'title_template': 'Write first draft: {section}',
            'description_template': 'Write the first draft of {section}. Target: {words} words. {guidance}',
            'time_per_100_words': 15,  # minutes
            'priority_boost': 10
        },
        'revision': {
            'title_template': 'Revise: {section}',
            'description_template': 'Review and revise {section} for clarity, flow, and argument strength.',
            'time_per_100_words': 8,  # minutes
            'priority_boost': 5
        },
        'citations': {
            'title_template': 'Add citations and references',
            'description_template': 'Format all citations in {style} style. Add bibliography/reference list.',
            'base_time_minutes': 30,
            'priority_boost': 8
        },
        'formatting': {
            'title_template': 'Final formatting and proofreading',
            'description_template': 'Check formatting requirements, proofread for errors, verify word count.',
            'base_time_minutes': 20,
            'priority_boost': 3
        }
    }

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize writing task generator.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.db_helper = DatabaseHelper(self.db)

    def generate_tasks(self, essay_id: str) -> Dict[str, Any]:
        """
        Generate all writing tasks for an essay.

        Args:
            essay_id: Essay ID

        Returns:
            Result with generated tasks
        """
        logger.info(f"Generating writing tasks for essay {essay_id}")

        # Get essay data
        essay = self._get_essay(essay_id)
        if not essay:
            return {'success': False, 'error': 'Essay not found'}

        tasks = []

        # 1. Generate outline tasks for each section
        outline_tasks = self._generate_outline_tasks(essay)
        tasks.extend(outline_tasks)
        logger.info(f"Generated {len(outline_tasks)} outline tasks")

        # 2. Generate draft writing tasks for each section
        draft_tasks = self._generate_draft_tasks(essay, outline_tasks)
        tasks.extend(draft_tasks)
        logger.info(f"Generated {len(draft_tasks)} draft writing tasks")

        # 3. Generate revision tasks
        revision_tasks = self._generate_revision_tasks(essay, draft_tasks)
        tasks.extend(revision_tasks)
        logger.info(f"Generated {len(revision_tasks)} revision tasks")

        # 4. Generate citation/formatting tasks
        final_tasks = self._generate_final_tasks(essay, revision_tasks)
        tasks.extend(final_tasks)
        logger.info(f"Generated {len(final_tasks)} final tasks")

        # Save all tasks to database
        saved_count = 0
        for task in tasks:
            if self._save_task(task):
                saved_count += 1

        logger.info(f"Saved {saved_count}/{len(tasks)} writing tasks")

        return {
            'success': True,
            'tasks': tasks,
            'count': len(tasks),
            'breakdown': {
                'outline_tasks': len(outline_tasks),
                'draft_tasks': len(draft_tasks),
                'revision_tasks': len(revision_tasks),
                'final_tasks': len(final_tasks)
            }
        }

    def _get_essay(self, essay_id: str) -> Optional[Dict[str, Any]]:
        """Get essay from database with all parsed data."""
        query = """
        SELECT
            id, user_id, title, course_name,
            word_count_min, word_count_max,
            citation_style, due_date,
            implicit_structure, task_verbs
        FROM essays
        WHERE id = ?
        """

        essay = self.db.execute_query(query, (essay_id,), fetch_one=True)
        return essay

    def _generate_outline_tasks(self, essay: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate outline tasks for each essay section."""
        structure_json = essay.get('implicit_structure')
        if not structure_json:
            # Fallback: create generic outline task
            return self._generate_generic_outline_task(essay)

        try:
            structure = json.loads(structure_json)
        except:
            return self._generate_generic_outline_task(essay)

        sections = structure.get('sections', [])
        if not sections:
            return self._generate_generic_outline_task(essay)

        tasks = []
        template = self.TASK_TEMPLATES['outline']

        for i, section in enumerate(sections, 1):
            section_name = section.get('name', f'Section {i}')
            word_allocation = section.get('word_allocation', 0)
            purpose = section.get('purpose', 'Write this section')

            estimated_minutes = max(
                15,  # Minimum 15 minutes
                int((word_allocation / 100) * template['time_per_100_words'])
            )

            task = {
                'id': str(uuid.uuid4()),
                'essay_id': essay['id'],
                'user_id': essay['user_id'],
                'task_type': 'writing',
                'task_category': 'outline',
                'title': template['title_template'].format(section=section_name),
                'description': template['description_template'].format(
                    section=section_name,
                    words=word_allocation,
                    purpose=purpose
                ),
                'estimated_minutes': estimated_minutes,
                'priority_score': 90 - (i * 3) + template['priority_boost'],
                'dependencies': [],
                'metadata': json.dumps({
                    'section': section_name,
                    'word_allocation': word_allocation,
                    'section_index': i
                })
            }
            tasks.append(task)

        return tasks

    def _generate_generic_outline_task(self, essay: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a single generic outline task when structure is unknown."""
        word_count = essay.get('word_count_max') or essay.get('word_count_min') or 2000
        template = self.TASK_TEMPLATES['outline']

        task = {
            'id': str(uuid.uuid4()),
            'essay_id': essay['id'],
            'user_id': essay['user_id'],
            'task_type': 'writing',
            'task_category': 'outline',
            'title': 'Create essay outline',
            'description': f'Create a detailed outline for your {word_count}-word essay.',
            'estimated_minutes': 30,
            'priority_score': 90 + template['priority_boost'],
            'dependencies': [],
            'metadata': json.dumps({
                'section': 'Full Essay',
                'word_allocation': word_count
            })
        }
        return [task]

    def _generate_draft_tasks(
        self,
        essay: Dict[str, Any],
        outline_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate draft writing tasks for each section."""
        structure_json = essay.get('implicit_structure')
        if not structure_json:
            return self._generate_generic_draft_task(essay, outline_tasks)

        try:
            structure = json.loads(structure_json)
        except:
            return self._generate_generic_draft_task(essay, outline_tasks)

        sections = structure.get('sections', [])
        if not sections:
            return self._generate_generic_draft_task(essay, outline_tasks)

        tasks = []
        template = self.TASK_TEMPLATES['draft']

        # Get task verbs for guidance
        task_verbs_json = essay.get('task_verbs')
        primary_verb = None
        if task_verbs_json:
            try:
                task_verbs = json.loads(task_verbs_json)
                primary_verb = task_verbs[0] if task_verbs else None
            except:
                pass

        for i, section in enumerate(sections, 1):
            section_name = section.get('name', f'Section {i}')
            word_allocation = section.get('word_allocation', 0)
            purpose = section.get('purpose', '')

            # Create guidance based on task verb
            guidance = self._create_writing_guidance(primary_verb, section_name, purpose)

            estimated_minutes = max(
                30,  # Minimum 30 minutes per section
                int((word_allocation / 100) * template['time_per_100_words'])
            )

            # Draft tasks depend on outline tasks
            outline_task_id = outline_tasks[i-1]['id'] if i <= len(outline_tasks) else None
            dependencies = [outline_task_id] if outline_task_id else []

            task = {
                'id': str(uuid.uuid4()),
                'essay_id': essay['id'],
                'user_id': essay['user_id'],
                'task_type': 'writing',
                'task_category': 'draft',
                'title': template['title_template'].format(section=section_name),
                'description': template['description_template'].format(
                    section=section_name,
                    words=word_allocation,
                    guidance=guidance
                ),
                'estimated_minutes': estimated_minutes,
                'priority_score': 85 - (i * 3) + template['priority_boost'],
                'dependencies': dependencies,
                'metadata': json.dumps({
                    'section': section_name,
                    'word_allocation': word_allocation,
                    'section_index': i
                })
            }
            tasks.append(task)

        return tasks

    def _generate_generic_draft_task(
        self,
        essay: Dict[str, Any],
        outline_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate a single generic draft task when structure is unknown."""
        word_count = essay.get('word_count_max') or essay.get('word_count_min') or 2000
        template = self.TASK_TEMPLATES['draft']

        outline_task_id = outline_tasks[0]['id'] if outline_tasks else None

        task = {
            'id': str(uuid.uuid4()),
            'essay_id': essay['id'],
            'user_id': essay['user_id'],
            'task_type': 'writing',
            'task_category': 'draft',
            'title': 'Write first draft',
            'description': f'Write the first draft of your essay. Target: {word_count} words.',
            'estimated_minutes': int((word_count / 100) * template['time_per_100_words']),
            'priority_score': 85 + template['priority_boost'],
            'dependencies': [outline_task_id] if outline_task_id else [],
            'metadata': json.dumps({
                'section': 'Full Essay',
                'word_allocation': word_count
            })
        }
        return [task]

    def _generate_revision_tasks(
        self,
        essay: Dict[str, Any],
        draft_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate revision tasks for each section."""
        structure_json = essay.get('implicit_structure')

        tasks = []
        template = self.TASK_TEMPLATES['revision']

        # Create one revision task per draft task
        for i, draft_task in enumerate(draft_tasks, 1):
            metadata = json.loads(draft_task['metadata'])
            section_name = metadata.get('section', f'Section {i}')
            word_allocation = metadata.get('word_allocation', 0)

            estimated_minutes = max(
                20,  # Minimum 20 minutes
                int((word_allocation / 100) * template['time_per_100_words'])
            )

            task = {
                'id': str(uuid.uuid4()),
                'essay_id': essay['id'],
                'user_id': essay['user_id'],
                'task_type': 'writing',
                'task_category': 'revision',
                'title': template['title_template'].format(section=section_name),
                'description': template['description_template'].format(section=section_name),
                'estimated_minutes': estimated_minutes,
                'priority_score': 70 - (i * 2) + template['priority_boost'],
                'dependencies': [draft_task['id']],
                'metadata': json.dumps({
                    'section': section_name,
                    'word_allocation': word_allocation,
                    'section_index': i
                })
            }
            tasks.append(task)

        return tasks

    def _generate_final_tasks(
        self,
        essay: Dict[str, Any],
        revision_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate final citation and formatting tasks."""
        tasks = []

        # All revision tasks must be done first
        all_revision_ids = [task['id'] for task in revision_tasks]

        # 1. Citations task
        citation_style = essay.get('citation_style') or 'standard'
        citation_template = self.TASK_TEMPLATES['citations']

        citation_task = {
            'id': str(uuid.uuid4()),
            'essay_id': essay['id'],
            'user_id': essay['user_id'],
            'task_type': 'writing',
            'task_category': 'citations',
            'title': citation_template['title_template'],
            'description': citation_template['description_template'].format(style=citation_style),
            'estimated_minutes': citation_template['base_time_minutes'],
            'priority_score': 60 + citation_template['priority_boost'],
            'dependencies': all_revision_ids,
            'metadata': json.dumps({
                'citation_style': citation_style
            })
        }
        tasks.append(citation_task)

        # 2. Final formatting task
        formatting_template = self.TASK_TEMPLATES['formatting']

        word_count = essay.get('word_count_max') or essay.get('word_count_min')
        description = formatting_template['description_template']
        if word_count:
            description += f' Target word count: {word_count} words.'

        formatting_task = {
            'id': str(uuid.uuid4()),
            'essay_id': essay['id'],
            'user_id': essay['user_id'],
            'task_type': 'writing',
            'task_category': 'formatting',
            'title': formatting_template['title_template'],
            'description': description,
            'estimated_minutes': formatting_template['base_time_minutes'],
            'priority_score': 50 + formatting_template['priority_boost'],
            'dependencies': [citation_task['id']],
            'metadata': json.dumps({
                'final_check': True
            })
        }
        tasks.append(formatting_task)

        return tasks

    def _create_writing_guidance(
        self,
        task_verb: Optional[str],
        section_name: str,
        purpose: str
    ) -> str:
        """Create writing guidance based on task verb."""
        verb_guidance = {
            'analyze': 'Break down the topic, examine relationships, and draw conclusions.',
            'evaluate': 'Make judgments, assess value/quality, and justify your position.',
            'compare': 'Identify similarities and differences systematically.',
            'argue': 'Present evidence, build logical case, address counterarguments.',
            'explain': 'Clarify concepts, provide examples, show cause-effect.',
            'describe': 'Provide detailed observations and characteristics.',
            'discuss': 'Explore multiple perspectives and implications.'
        }

        guidance = verb_guidance.get(task_verb, 'Write clearly and support with evidence.')

        if purpose:
            guidance += f' {purpose}'

        return guidance

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
    print("Testing Writing Task Generator...")

    generator = WritingTaskGenerator(user_id="test_user")

    print("\nWriting Task Generator structure validated!")
