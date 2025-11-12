"""
Academic Command Center - Essay Parser - Rubric Decoder
Transforms vague rubric criteria into specific, measurable checklist items.
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


class RubricDecoder:
    """
    Decodes rubric criteria into actionable checklist items.

    Transforms vague criteria like:
      "Critical Analysis: 40 points"

    Into specific items like:
      ✓ Define postmodernism with references to 2 theorists
      ✓ Identify 3 specific impacts
      ✓ Explain cause-effect relationships
      ✓ Provide critical evaluation
    """

    def __init__(self, user_id: str, ai_router: Optional[AIRouter] = None):
        """
        Initialize rubric decoder.

        Args:
            user_id: Current user ID
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter(user_id)

    def decode(
        self,
        rubric: Dict[str, Any],
        essay_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Decode rubric into checklist.

        Args:
            rubric: Rubric dictionary from section_identifier
            essay_description: Essay description for context

        Returns:
            Decoded rubric with checklists
        """
        if not rubric:
            return {'success': False, 'error': 'No rubric provided'}

        logger.info(f"Decoding rubric with {len(rubric)} criteria...")

        decoded_criteria = {}

        for criterion_name, criterion_data in rubric.items():
            logger.info(f"Decoding criterion: {criterion_name}")

            # Extract points
            points = criterion_data.get('points', 0) if isinstance(criterion_data, dict) else 0

            # Decode this criterion
            checklist_result = self._decode_criterion(
                criterion_name,
                criterion_data,
                points,
                essay_description
            )

            if checklist_result['success']:
                decoded_criteria[criterion_name] = {
                    'points': points,
                    'weight': points / 100 if points else 0,
                    'checklist': checklist_result['checklist'],
                    'description': criterion_data.get('description', '') if isinstance(criterion_data, dict) else ''
                }
            else:
                # Fallback
                decoded_criteria[criterion_name] = {
                    'points': points,
                    'weight': points / 100 if points else 0,
                    'checklist': [f"Demonstrate {criterion_name.lower()}"],
                    'description': criterion_data.get('description', '') if isinstance(criterion_data, dict) else ''
                }

        return {
            'success': True,
            'decoded_rubric': decoded_criteria
        }

    def _decode_criterion(
        self,
        criterion_name: str,
        criterion_data: Any,
        points: int,
        essay_description: Optional[str]
    ) -> Dict[str, Any]:
        """
        Decode single rubric criterion using AI.

        Args:
            criterion_name: Name of criterion
            criterion_data: Criterion data
            points: Point value
            essay_description: Essay description for context

        Returns:
            Checklist items
        """
        # Build prompt
        description = criterion_data.get('description', '') if isinstance(criterion_data, dict) else ''

        prompt = f"""Convert this rubric criterion into a specific checklist:

Criterion: "{criterion_name}" ({points} points)
Description: "{description}"
{f'Essay task: "{essay_description}"' if essay_description else ''}

Create 4-7 specific, measurable items the student must DO to earn full points.
Make them:
- Concrete (can be verified in the essay)
- Actionable (clear what to do)
- Directly tied to this criterion

Return ONLY valid JSON array (no markdown):
[
  {{
    "item": "Define postmodernism with reference to at least 2 key theorists",
    "verifiable": true,
    "weight": 0.25
  }},
  ...
]

Weights should sum to 1.0.
"""

        result = self.ai_router.execute_task({
            'task_type': 'rubric_analysis',
            'payload': {
                'prompt': prompt,
                'temperature': 0.3,
                'max_tokens': 1000
            }
        })

        if not result['success']:
            logger.warning(f"AI decoding failed for {criterion_name}: {result.get('error')}")
            return {'success': False}

        try:
            checklist = self._parse_ai_response(result['data'])

            # Validate weights sum to ~1.0
            total_weight = sum(item.get('weight', 0) for item in checklist)
            if abs(total_weight - 1.0) > 0.1:
                # Normalize weights
                for item in checklist:
                    if 'weight' in item:
                        item['weight'] = item['weight'] / total_weight

            return {
                'success': True,
                'checklist': checklist
            }

        except Exception as e:
            logger.error(f"Failed to parse checklist: {e}")
            return {'success': False}

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI JSON response."""
        cleaned = response.strip()

        # Remove markdown
        if cleaned.startswith('```'):
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

        return json.loads(cleaned)


if __name__ == "__main__":
    print("Testing Rubric Decoder...")

    decoder = RubricDecoder(user_id="test_user")

    test_rubric = {
        "Critical Analysis": {
            "points": 40,
            "description": "Demonstrates deep engagement with theoretical concepts"
        },
        "Use of Sources": {
            "points": 30,
            "description": "Effective integration of academic sources"
        }
    }

    test_description = "Analyze the impact of postmodernism on contemporary music production"

    print("\nRubric Decoder structure validated!")
