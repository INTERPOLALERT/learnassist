"""
Academic Command Center - Essay Parser - Structure Detector
Infers expected essay structure using AI, even when not explicitly stated.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StructureDetector:
    """
    Detects implicit essay structure.

    Even if instructions don't explicitly say "write intro, body, conclusion",
    this component infers the expected structure based on:
    - Essay type (analytical, argumentative, comparative, etc.)
    - Academic level
    - Word count
    - Task verbs
    """

    # Default structures for common essay types
    DEFAULT_STRUCTURES = {
        'analytical': [
            {'section': 'Introduction', 'percentage': 10},
            {'section': 'Literature Review', 'percentage': 15},
            {'section': 'Analysis', 'percentage': 55},
            {'section': 'Conclusion', 'percentage': 20}
        ],
        'argumentative': [
            {'section': 'Introduction', 'percentage': 10},
            {'section': 'Argument', 'percentage': 60},
            {'section': 'Counter-argument', 'percentage': 20},
            {'section': 'Conclusion', 'percentage': 10}
        ],
        'comparative': [
            {'section': 'Introduction', 'percentage': 10},
            {'section': 'Comparison Part 1', 'percentage': 35},
            {'section': 'Comparison Part 2', 'percentage': 35},
            {'section': 'Conclusion', 'percentage': 20}
        ]
    }

    def __init__(self, user_id: str, ai_router: Optional[AIRouter] = None):
        """
        Initialize structure detector.

        Args:
            user_id: Current user ID
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter(user_id)

    def detect(
        self,
        description: str,
        word_count: Optional[int] = None,
        task_verbs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect expected essay structure.

        Args:
            description: Essay description
            word_count: Target word count
            task_verbs: Task verbs (e.g., ["analyze", "compare"])

        Returns:
            Structure analysis
        """
        if not description:
            return {'success': False, 'error': 'No description provided'}

        logger.info("Detecting essay structure...")

        # Build prompt
        prompt = self._build_prompt(description, word_count, task_verbs)

        # Call AI
        result = self.ai_router.execute_task({
            'task_type': 'parse_essay_instructions',
            'payload': {
                'prompt': prompt,
                'temperature': 0.3,
                'max_tokens': 1500
            }
        })

        if not result['success']:
            logger.warning(f"AI detection failed, using fallback: {result.get('error')}")
            return self._fallback_structure(description, word_count, task_verbs)

        try:
            structure = self._parse_ai_response(result['data'])

            # Validate and enhance
            structure = self._validate_structure(structure, word_count)

            return {
                'success': True,
                'structure': structure,
                'provider': result.get('provider'),
                'cached': result.get('cached', False)
            }

        except Exception as e:
            logger.error(f"Failed to parse structure: {e}")
            return self._fallback_structure(description, word_count, task_verbs)

    def _build_prompt(
        self,
        description: str,
        word_count: Optional[int],
        task_verbs: Optional[List[str]]
    ) -> str:
        """Build AI prompt for structure detection."""
        word_count_str = f"{word_count} words" if word_count else "typical essay length"
        verbs_str = f"Task verbs: {', '.join(task_verbs)}" if task_verbs else ""

        prompt = f"""Determine the expected essay structure for this assignment:

Description: "{description}"
Word count: {word_count_str}
{verbs_str}

Provide a detailed structure breakdown:
1. List expected sections (intro, body parts, conclusion)
2. Allocate word count per section
3. Describe the purpose of each section

Return ONLY valid JSON (no markdown):
{{
  "essay_type": "analytical|argumentative|comparative|expository",
  "sections": [
    {{
      "name": "Introduction",
      "word_allocation": 250,
      "percentage": 10,
      "purpose": "Introduce topic, provide context, state thesis"
    }},
    ...
  ]
}}
"""
        return prompt

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI JSON response."""
        cleaned = response.strip()

        # Remove markdown
        if cleaned.startswith('```'):
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

        return json.loads(cleaned)

    def _validate_structure(
        self,
        structure: Dict[str, Any],
        word_count: Optional[int]
    ) -> Dict[str, Any]:
        """
        Validate and normalize structure.

        Args:
            structure: Parsed structure
            word_count: Target word count

        Returns:
            Validated structure
        """
        if 'sections' not in structure:
            raise ValueError("Missing sections in structure")

        sections = structure['sections']

        # Calculate total percentage
        total_pct = sum(s.get('percentage', 0) for s in sections)

        # If percentages don't add to ~100, normalize
        if abs(total_pct - 100) > 5:
            logger.warning(f"Percentages don't add to 100 ({total_pct}), normalizing")
            for section in sections:
                if 'percentage' in section:
                    section['percentage'] = (section['percentage'] / total_pct) * 100

        # Recalculate word allocations if word count provided
        if word_count:
            for section in sections:
                if 'percentage' in section:
                    section['word_allocation'] = int((section['percentage'] / 100) * word_count)

        return structure

    def _fallback_structure(
        self,
        description: str,
        word_count: Optional[int],
        task_verbs: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Fallback structure detection.

        Args:
            description: Essay description
            word_count: Word count
            task_verbs: Task verbs

        Returns:
            Basic structure
        """
        logger.info("Using fallback structure detection")

        # Guess essay type from description
        desc_lower = description.lower()

        if any(v in desc_lower for v in ['compare', 'contrast']):
            essay_type = 'comparative'
        elif any(v in desc_lower for v in ['argue', 'persuade', 'convince']):
            essay_type = 'argumentative'
        elif any(v in desc_lower for v in ['analyze', 'examine', 'investigate']):
            essay_type = 'analytical'
        else:
            essay_type = 'expository'

        # Get default structure
        template = self.DEFAULT_STRUCTURES.get(
            essay_type,
            self.DEFAULT_STRUCTURES['analytical']
        )

        # Apply word counts
        sections = []
        wc = word_count or 2000  # Default

        for section in template:
            sections.append({
                'name': section['section'],
                'word_allocation': int((section['percentage'] / 100) * wc),
                'percentage': section['percentage'],
                'purpose': f"Section for {section['section'].lower()}"
            })

        return {
            'success': True,
            'structure': {
                'essay_type': essay_type,
                'sections': sections
            },
            'fallback': True
        }


if __name__ == "__main__":
    print("Testing Structure Detector...")

    detector = StructureDetector(user_id="test_user")

    # Test fallback
    result = detector._fallback_structure(
        "Analyze the impact of postmodernism",
        2500,
        ["analyze"]
    )

    print(f"\nFallback structure:")
    print(json.dumps(result, indent=2))

    print("\nStructure Detector validated!")
