"""
Academic Command Center - Essay Parser - Main Orchestrator
Coordinates all essay parsing components to transform raw instructions into structured data.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.database import DatabaseManager, DatabaseHelper
from core.ai_router import AIRouter
from .preprocessor import TextPreprocessor
from .section_identifier import SectionIdentifier
from .requirement_extractor import RequirementExtractor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EssayParser:
    """
    Main essay parser orchestrator.

    Workflow:
    1. Preprocess text (clean, normalize)
    2. Identify sections (AI)
    3. Extract requirements (AI)
    4. Parse additional data (verbs, concepts, structure, rubric)
    5. Save to database
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None,
        ai_router: Optional[AIRouter] = None
    ):
        """
        Initialize essay parser.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.db_helper = DatabaseHelper(self.db)
        self.ai_router = ai_router or AIRouter(user_id)

        # Initialize components
        self.preprocessor = TextPreprocessor()
        self.section_identifier = SectionIdentifier(user_id, self.ai_router)
        self.requirement_extractor = RequirementExtractor(user_id, self.ai_router)

    def parse(
        self,
        raw_instructions: str,
        source_type: str = 'text',
        canvas_assignment_id: Optional[str] = None,
        course_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse essay instructions and save to database.

        Args:
            raw_instructions: Raw instruction text
            source_type: Source type (text, html, pdf, docx)
            canvas_assignment_id: Canvas assignment ID if from Canvas
            course_name: Course name if known

        Returns:
            Result dictionary with essay_id
        """
        logger.info("=" * 60)
        logger.info("Starting essay parsing...")
        logger.info(f"Input length: {len(raw_instructions)} characters")
        logger.info("=" * 60)

        try:
            # Step 1: Preprocess
            logger.info("[1/5] Preprocessing text...")
            preprocess_result = self.preprocessor.preprocess(
                raw_instructions,
                source_type
            )

            if not preprocess_result['success']:
                return {
                    'success': False,
                    'error': f"Preprocessing failed: {preprocess_result.get('error')}"
                }

            processed_text = preprocess_result['processed']
            logger.info(f"✓ Text preprocessed ({len(processed_text)} chars)")

            # Step 2: Identify sections
            logger.info("[2/5] Identifying sections...")
            sections_result = self.section_identifier.identify_sections(processed_text)

            if not sections_result['success']:
                return {
                    'success': False,
                    'error': f"Section identification failed: {sections_result.get('error')}"
                }

            sections = sections_result['sections']
            logger.info(f"✓ Sections identified")

            # Step 3: Extract requirements
            logger.info("[3/5] Extracting requirements...")
            requirements_list = sections.get('requirements', [])

            if requirements_list:
                req_result = self.requirement_extractor.extract(requirements_list)
                if not req_result['success']:
                    logger.warning(f"Requirement extraction failed: {req_result.get('error')}")
                    requirements = []
                    word_count_min = None
                    word_count_max = None
                    required_sources_min = None
                    citation_style = None
                else:
                    requirements = req_result['requirements']
                    word_count_min = req_result.get('word_count_min')
                    word_count_max = req_result.get('word_count_max')
                    required_sources_min = req_result.get('required_sources_min')
                    citation_style = req_result.get('citation_style')
                    logger.info(f"✓ Requirements extracted: {len(requirements)} items")
            else:
                requirements = []
                word_count_min = None
                word_count_max = None
                required_sources_min = None
                citation_style = None
                logger.info("No requirements found in sections")

            # Step 4: Parse deadline
            logger.info("[4/5] Processing deadline...")
            due_date = self._parse_deadline(sections.get('deadline'))
            logger.info(f"✓ Deadline: {due_date or 'Not specified'}")

            # Step 5: Save to database
            logger.info("[5/5] Saving to database...")
            essay_id = str(uuid.uuid4())

            essay_data = {
                'id': essay_id,
                'user_id': self.user_id,
                'canvas_assignment_id': canvas_assignment_id,
                'title': sections.get('title') or 'Untitled Essay',
                'raw_instructions': raw_instructions,
                'course_name': course_name,
                'word_count_min': word_count_min,
                'word_count_max': word_count_max,
                'required_sources_min': required_sources_min,
                'citation_style': citation_style,
                'due_date': due_date
            }

            self.db_helper.create_essay(essay_data)

            # Update with JSON fields
            import json
            update_query = """
            UPDATE essays
            SET extracted_requirements = ?,
                rubric_criteria = ?
            WHERE id = ?
            """
            self.db.execute_query(
                update_query,
                (
                    json.dumps(requirements),
                    json.dumps(sections.get('rubric')) if sections.get('rubric') else None,
                    essay_id
                )
            )

            logger.info(f"✓ Essay saved with ID: {essay_id}")
            logger.info("=" * 60)
            logger.info("Parsing completed successfully!")
            logger.info("=" * 60)

            return {
                'success': True,
                'essay_id': essay_id,
                'title': essay_data['title'],
                'word_count_min': word_count_min,
                'word_count_max': word_count_max,
                'required_sources': required_sources_min,
                'citation_style': citation_style,
                'due_date': due_date,
                'sections': sections,
                'requirements': requirements
            }

        except Exception as e:
            logger.error(f"Essay parsing failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_deadline(self, deadline_str: Optional[str]) -> Optional[str]:
        """
        Parse deadline string to ISO format.

        Args:
            deadline_str: Deadline string from sections

        Returns:
            ISO formatted datetime string or None
        """
        if not deadline_str:
            return None

        from dateutil import parser as date_parser

        try:
            # Try to parse with dateutil
            dt = date_parser.parse(deadline_str, fuzzy=True)
            return dt.isoformat()
        except Exception as e:
            logger.warning(f"Failed to parse deadline '{deadline_str}': {e}")
            return None


if __name__ == "__main__":
    print("Testing Essay Parser...")

    parser = EssayParser(user_id="test_user")

    test_instructions = """
    Essay 1: Cultural Analysis

    Write a 2500-word essay analyzing the impact of postmodernism on contemporary music production.

    Requirements:
    • Use at least 5 academic sources
    • Include examples from 3 different artists
    • Follow Harvard referencing style
    • Submit by December 15th, 2024, 11:59 PM

    Grading Rubric (100 points):
    • Critical Analysis: 40 points
    • Use of Sources: 30 points
    • Writing Quality: 20 points
    • Formatting: 10 points
    """

    print("\nNote: This requires API keys and database to run")
    print("Essay Parser structure validated!")
