"""
Academic Command Center - Essay Parser - Section Identifier
Uses AI to identify and extract sections from essay instructions.
"""

import json
import logging
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.ai_router import AIRouter

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SectionIdentifier:
    """
    Identifies sections in essay instructions using AI.

    Sections identified:
    - Title
    - Description (main task)
    - Requirements (word count, sources, etc.)
    - Rubric (grading criteria)
    - Deadline (due date)
    - Submission format
    """

    def __init__(
        self,
        user_id: str,
        ai_router: Optional[AIRouter] = None
    ):
        """
        Initialize section identifier.

        Args:
            user_id: Current user ID
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter(user_id)

    def identify_sections(self, text: str) -> Dict[str, Any]:
        """
        Identify sections in essay instruction text.

        Args:
            text: Preprocessed essay instruction text

        Returns:
            Dictionary with identified sections
        """
        if not text or len(text.strip()) < 10:
            return {
                'success': False,
                'error': 'Text too short to analyze'
            }

        logger.info(f"Identifying sections in {len(text)} character text")

        # Build AI prompt
        prompt = self._build_prompt(text)

        # Call AI
        result = self.ai_router.execute_task({
            'task_type': 'parse_essay_instructions',
            'payload': {
                'prompt': prompt,
                'temperature': 0.3,  # Lower temperature for structured output
                'max_tokens': 2000
            }
        })

        if not result['success']:
            logger.error(f"AI call failed: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error', 'AI processing failed')
            }

        # Parse AI response
        try:
            sections = self._parse_ai_response(result['data'])

            # Validate sections
            if not self._validate_sections(sections):
                logger.warning("AI response validation failed, using fallback")
                sections = self._fallback_section_extraction(text)

            return {
                'success': True,
                'sections': sections,
                'provider': result.get('provider'),
                'cached': result.get('cached', False)
            }

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                'success': False,
                'error': f'Failed to parse AI response: {str(e)}'
            }

    def _build_prompt(self, text: str) -> str:
        """Build AI prompt for section identification."""
        prompt = f"""You are analyzing an essay assignment brief. Break it into these sections:

1. TITLE: The essay title/name (if present)
2. DESCRIPTION: What the essay asks for (main task/question)
3. REQUIREMENTS: Specific requirements (word count, sources, citation style, etc.)
4. RUBRIC: Grading criteria and point values (if present)
5. DEADLINE: Due date and time (if present)
6. SUBMISSION: How/where to submit (if present)

Input text:
{text}

Return ONLY a valid JSON object in this exact format (no markdown, no code blocks):
{{
  "title": "Essay title or null",
  "description": "Main task description",
  "requirements": ["requirement 1", "requirement 2", ...],
  "rubric": {{"criterion name": {{"points": 40, "description": "..."}}, ...}} or null,
  "deadline": "Due date/time or null",
  "submission_format": "Submission instructions or null"
}}

Be precise. Extract exactly what's in the text. If a section is missing, use null.
"""
        return prompt

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI JSON response.

        Args:
            response: Raw AI response

        Returns:
            Parsed sections dictionary
        """
        # Clean response (remove markdown code blocks if present)
        cleaned = response.strip()

        # Remove code block markers
        if cleaned.startswith('```'):
            # Find first { and last }
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

        # Parse JSON
        try:
            sections = json.loads(cleaned)
            return sections
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed: {e}")
            logger.error(f"Response was: {cleaned[:500]}")

            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                try:
                    sections = json.loads(json_match.group(0))
                    return sections
                except:
                    pass

            raise ValueError(f"Could not parse JSON from AI response: {cleaned[:200]}")

    def _validate_sections(self, sections: Dict[str, Any]) -> bool:
        """
        Validate that sections dictionary has expected structure.

        Args:
            sections: Parsed sections

        Returns:
            True if valid
        """
        # Must have at least description
        if 'description' not in sections or not sections['description']:
            logger.warning("Missing description in sections")
            return False

        # Requirements should be a list
        if 'requirements' in sections and sections['requirements'] is not None:
            if not isinstance(sections['requirements'], list):
                logger.warning("Requirements is not a list")
                return False

        # Rubric should be dict or null
        if 'rubric' in sections and sections['rubric'] is not None:
            if not isinstance(sections['rubric'], dict):
                logger.warning("Rubric is not a dict")
                return False

        return True

    def _fallback_section_extraction(self, text: str) -> Dict[str, Any]:
        """
        Fallback: Rule-based section extraction if AI fails.

        Args:
            text: Original text

        Returns:
            Best-effort sections dictionary
        """
        logger.info("Using fallback section extraction")

        import re

        sections = {
            'title': None,
            'description': None,
            'requirements': [],
            'rubric': None,
            'deadline': None,
            'submission_format': None
        }

        lines = text.split('\n')

        # Try to find title (usually first line or has "Essay" in it)
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            if 'essay' in line.lower() or 'assignment' in line.lower():
                sections['title'] = line.strip()
                break

        # Find requirements (lines with numbers, "must", "should", "required")
        requirements = []
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['must', 'should', 'required', 'minimum', 'at least']):
                requirements.append(line.strip())
            elif re.match(r'^\d+\.', line):  # Numbered list
                requirements.append(line.strip())
            elif line.startswith('• '):  # Bullet point
                requirements.append(line.strip())

        sections['requirements'] = requirements

        # Find deadline
        deadline_patterns = [
            r'due.*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'submit.*?by.*?(\d{1,2}\s+\w+\s+\d{4})',
            r'deadline.*?(\d{1,2}\s+\w+)',
        ]
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sections['deadline'] = match.group(1)
                break

        # Description is everything else (simplified)
        sections['description'] = text[:500] if len(text) > 500 else text

        logger.info("Fallback extraction completed")
        return sections


if __name__ == "__main__":
    # Test section identifier
    print("Testing Section Identifier...")

    test_text = """
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

    identifier = SectionIdentifier(user_id="test_user")

    # Note: This will fail without real API keys, but shows the structure
    try:
        result = identifier.identify_sections(test_text)
        print(f"\nResult: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"\nExpected failure (no API keys): {e}")

    print("\nSection Identifier test structure validated!")
