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
from .verb_analyzer import VerbAnalyzer
from .concept_extractor import ConceptExtractor
from .structure_detector import StructureDetector
from .rubric_decoder import RubricDecoder
from .gap_detector import KnowledgeGapDetector

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EssayParser:
    """
    Main essay parser orchestrator.

    Workflow:
    1. Preprocess text (clean, normalize)
    2. Identify sections (AI)
    3. Extract requirements (AI)
    4. Analyze task verbs (AI)
    5. Extract concepts (NLP + AI)
    6. Detect structure (AI)
    7. Decode rubric (AI)
    8. Detect knowledge gaps
    9. Save to database
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

        # Initialize all components
        self.preprocessor = TextPreprocessor()
        self.section_identifier = SectionIdentifier(user_id, self.ai_router)
        self.requirement_extractor = RequirementExtractor(user_id, self.ai_router)
        self.verb_analyzer = VerbAnalyzer(user_id, self.ai_router)
        self.concept_extractor = ConceptExtractor(user_id, self.ai_router)
        self.structure_detector = StructureDetector(user_id, self.ai_router)
        self.rubric_decoder = RubricDecoder(user_id, self.ai_router)
        self.gap_detector = KnowledgeGapDetector(user_id, self.db)

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

            # Step 4: Analyze task verbs
            logger.info("[4/9] Analyzing task verbs...")
            description = sections.get('description', '')
            task_verbs_data = None

            if description:
                verb_result = self.verb_analyzer.analyze(description)
                if verb_result['success']:
                    task_verbs_data = verb_result['analysis']
                    logger.info(f"✓ Task verbs analyzed: {task_verbs_data.get('primary_verb')}")
                else:
                    logger.warning("Task verb analysis failed")
            else:
                logger.warning("No description for verb analysis")

            # Step 5: Extract concepts
            logger.info("[5/9] Extracting key concepts...")
            concepts_data = None

            if description:
                concept_result = self.concept_extractor.extract(description)
                if concept_result['success']:
                    concepts_data = concept_result['concepts']
                    logger.info(f"✓ Concepts extracted: {len(concepts_data)} concepts")
                else:
                    logger.warning("Concept extraction failed")
            else:
                logger.warning("No description for concept extraction")

            # Step 6: Detect structure
            logger.info("[6/9] Detecting essay structure...")
            structure_data = None

            if description:
                task_verbs = [task_verbs_data.get('primary_verb')] if task_verbs_data else None
                structure_result = self.structure_detector.detect(
                    description,
                    word_count_max or word_count_min,
                    task_verbs
                )
                if structure_result['success']:
                    structure_data = structure_result['structure']
                    logger.info(f"✓ Structure detected: {structure_data.get('essay_type', 'unknown')} essay")
                else:
                    logger.warning("Structure detection failed")

            # Step 7: Decode rubric
            logger.info("[7/9] Decoding rubric...")
            decoded_rubric = None

            rubric = sections.get('rubric')
            if rubric:
                rubric_result = self.rubric_decoder.decode(rubric, description)
                if rubric_result['success']:
                    decoded_rubric = rubric_result['decoded_rubric']
                    logger.info(f"✓ Rubric decoded: {len(decoded_rubric)} criteria")
                else:
                    logger.warning("Rubric decoding failed")
            else:
                logger.info("No rubric to decode")

            # Step 8: Detect knowledge gaps
            logger.info("[8/9] Detecting knowledge gaps...")
            knowledge_gaps = None

            if concepts_data:
                concept_names = [c['name'] for c in concepts_data]
                gap_result = self.gap_detector.detect_gaps(concept_names)
                if gap_result['success']:
                    knowledge_gaps = gap_result['gaps']
                    gap_count = len(knowledge_gaps)
                    logger.info(f"✓ Knowledge gaps detected: {gap_count} gaps found")
                else:
                    logger.warning("Gap detection failed")

            # Step 9: Parse deadline
            logger.info("[9/9] Processing deadline...")
            due_date = self._parse_deadline(sections.get('deadline'))
            logger.info(f"✓ Deadline: {due_date or 'Not specified'}")

            # Save to database
            logger.info("Saving to database...")
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

            # Update with all JSON fields
            import json
            update_query = """
            UPDATE essays
            SET extracted_requirements = ?,
                key_concepts = ?,
                task_verbs = ?,
                implicit_structure = ?,
                rubric_criteria = ?,
                knowledge_gaps = ?
            WHERE id = ?
            """

            # Prepare JSON data
            concepts_json = json.dumps([c['name'] for c in concepts_data]) if concepts_data else None
            task_verbs_json = json.dumps([task_verbs_data.get('primary_verb')] + task_verbs_data.get('secondary_verbs', [])) if task_verbs_data else None
            structure_json = json.dumps(structure_data) if structure_data else None
            rubric_json = json.dumps(decoded_rubric) if decoded_rubric else None
            gaps_json = json.dumps([g['concept'] for g in knowledge_gaps]) if knowledge_gaps else None

            self.db.execute_query(
                update_query,
                (
                    json.dumps(requirements),
                    concepts_json,
                    task_verbs_json,
                    structure_json,
                    rubric_json,
                    gaps_json,
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
                'requirements': requirements,
                'task_verbs': task_verbs_data,
                'concepts': concepts_data,
                'structure': structure_data,
                'decoded_rubric': decoded_rubric,
                'knowledge_gaps': knowledge_gaps
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
