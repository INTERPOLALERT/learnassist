"""
Academic Command Center - Essay Parser - Requirement Extractor
Extracts structured requirements from essay instructions using AI.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RequirementExtractor:
    """Extract structured requirements from essay instructions."""

    REQUIREMENT_TYPES = [
        'word_count', 'source_count', 'citation_style',
        'example_count', 'format', 'other'
    ]

    CONSTRAINT_TYPES = ['minimum', 'maximum', 'exact', 'flexible']

    def __init__(self, user_id: str, ai_router: Optional[AIRouter] = None):
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter(user_id)

    def extract(self, requirements_list: List[str]) -> Dict[str, Any]:
        """Extract structured requirements from text list."""
        if not requirements_list:
            return {'success': True, 'requirements': []}

        prompt = f"""Extract structured data from these essay requirements:

{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements_list))}

For each requirement, identify:
1. TYPE: word_count, source_count, citation_style, example_count, format, or other
2. VALUE: The specific number/value
3. CONSTRAINT: minimum, maximum, exact, or flexible
4. DESCRIPTION: Original text

Return ONLY valid JSON array (no markdown):
[
  {{"type": "word_count", "value": 2500, "constraint": "exact", "description": "2500 words"}},
  ...
]
"""

        result = self.ai_router.execute_task({
            'task_type': 'parse_essay_instructions',
            'payload': {'prompt': prompt, 'temperature': 0.2, 'max_tokens': 1500}
        })

        if not result['success']:
            return {'success': False, 'error': result.get('error')}

        try:
            requirements = json.loads(self._clean_json_response(result['data']))

            # Validate and enhance
            requirements = self._validate_requirements(requirements)

            return {
                'success': True,
                'requirements': requirements,
                'word_count_min': self._extract_word_count(requirements, 'min'),
                'word_count_max': self._extract_word_count(requirements, 'max'),
                'required_sources_min': self._extract_source_count(requirements, 'min'),
                'citation_style': self._extract_citation_style(requirements)
            }
        except Exception as e:
            logger.error(f"Failed to parse requirements: {e}")
            return {'success': False, 'error': str(e)}

    def _clean_json_response(self, response: str) -> str:
        """Clean AI response to extract JSON."""
        cleaned = response.strip()
        if cleaned.startswith('```'):
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]
        return cleaned

    def _validate_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """Validate and normalize requirements."""
        validated = []
        for req in requirements:
            if 'type' in req and 'value' in req:
                validated.append({
                    'type': req['type'],
                    'value': req['value'],
                    'constraint': req.get('constraint', 'exact'),
                    'description': req.get('description', str(req['value']))
                })
        return validated

    def _extract_word_count(self, requirements: List[Dict], which: str) -> Optional[int]:
        """Extract word count from requirements."""
        for req in requirements:
            if req['type'] == 'word_count':
                value = req['value']
                constraint = req.get('constraint', 'exact')

                if which == 'min':
                    if constraint in ['minimum', 'exact']:
                        return int(value)
                elif which == 'max':
                    if constraint in ['maximum', 'exact']:
                        return int(value)
        return None

    def _extract_source_count(self, requirements: List[Dict], which: str) -> Optional[int]:
        """Extract source count."""
        for req in requirements:
            if req['type'] == 'source_count':
                if which == 'min':
                    return int(req['value'])
        return None

    def _extract_citation_style(self, requirements: List[Dict]) -> Optional[str]:
        """Extract citation style."""
        for req in requirements:
            if req['type'] == 'citation_style':
                return str(req['value'])
        return None


if __name__ == "__main__":
    print("Requirement Extractor structure validated!")
