"""
Academic Command Center - Essay Parser - Task Verb Analyzer
Identifies and analyzes academic task verbs using Bloom's Taxonomy.
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


class VerbAnalyzer:
    """
    Analyzes task verbs in essay instructions.

    Identifies verbs like: analyze, evaluate, compare, discuss, etc.
    Uses Bloom's Taxonomy to classify cognitive level.
    """

    # Common academic task verbs by Bloom's level
    BLOOMS_TAXONOMY = {
        'remember': ['list', 'name', 'identify', 'define', 'state', 'describe', 'recall'],
        'understand': ['explain', 'summarize', 'interpret', 'discuss', 'paraphrase', 'classify'],
        'apply': ['use', 'demonstrate', 'apply', 'solve', 'show', 'illustrate'],
        'analyze': ['analyze', 'examine', 'compare', 'contrast', 'differentiate', 'investigate'],
        'evaluate': ['evaluate', 'assess', 'judge', 'critique', 'justify', 'argue', 'defend'],
        'create': ['create', 'design', 'develop', 'formulate', 'construct', 'propose']
    }

    def __init__(self, user_id: str, ai_router: Optional[AIRouter] = None):
        """
        Initialize verb analyzer.

        Args:
            user_id: Current user ID
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter(user_id)

    def analyze(self, description: str) -> Dict[str, Any]:
        """
        Analyze task verbs in essay description.

        Args:
            description: Essay task description

        Returns:
            Dictionary with verb analysis
        """
        if not description or len(description.strip()) < 5:
            return {'success': False, 'error': 'Description too short'}

        logger.info("Analyzing task verbs...")

        # First, try quick pattern matching
        detected_verbs = self._detect_verbs_pattern(description)

        # If found verbs, get AI analysis
        if detected_verbs:
            logger.info(f"Detected verbs: {detected_verbs}")
            ai_result = self._analyze_with_ai(description, detected_verbs)

            if ai_result['success']:
                return ai_result

        # Fallback: AI analysis without hints
        logger.info("No verbs detected, using AI analysis")
        return self._analyze_with_ai(description, [])

    def _detect_verbs_pattern(self, text: str) -> List[str]:
        """
        Detect task verbs using pattern matching.

        Args:
            text: Description text

        Returns:
            List of detected verbs
        """
        text_lower = text.lower()
        detected = []

        # Check each Bloom's level
        for level, verbs in self.BLOOMS_TAXONOMY.items():
            for verb in verbs:
                # Look for verb as whole word
                import re
                pattern = r'\b' + verb + r'\b'
                if re.search(pattern, text_lower):
                    if verb not in detected:
                        detected.append(verb)

        return detected

    def _analyze_with_ai(
        self,
        description: str,
        detected_verbs: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze task verbs using AI.

        Args:
            description: Essay description
            detected_verbs: Pre-detected verbs (if any)

        Returns:
            Analysis result
        """
        # Build prompt
        prompt = f"""Analyze the task verbs in this essay description:

"{description}"

{f"Detected verbs: {', '.join(detected_verbs)}" if detected_verbs else ""}

Identify:
1. PRIMARY_VERB: The main task verb (analyze, evaluate, compare, etc.)
2. DEFINITION: What this verb means in academic context
3. STUDENT_ACTIONS: List of specific actions the student must DO
4. BLOOMS_LEVEL: Cognitive level (remember, understand, apply, analyze, evaluate, create)
5. SECONDARY_VERBS: Any other task verbs present

Return ONLY valid JSON (no markdown):
{{
  "primary_verb": "analyze",
  "definition": "Break down the topic into components and examine relationships",
  "student_actions": [
    "Identify key elements",
    "Examine relationships",
    "Explain cause-effect",
    "Support with evidence"
  ],
  "blooms_level": "analyze",
  "secondary_verbs": ["examine", "discuss"]
}}
"""

        # Call AI
        result = self.ai_router.execute_task({
            'task_type': 'parse_essay_instructions',
            'payload': {
                'prompt': prompt,
                'temperature': 0.3,
                'max_tokens': 1000
            }
        })

        if not result['success']:
            logger.error(f"AI analysis failed: {result.get('error')}")
            return {'success': False, 'error': result.get('error')}

        # Parse response
        try:
            analysis = self._parse_ai_response(result['data'])

            # Validate
            if not self._validate_analysis(analysis):
                logger.warning("Invalid analysis, using fallback")
                return self._fallback_analysis(description, detected_verbs)

            return {
                'success': True,
                'analysis': analysis,
                'provider': result.get('provider'),
                'cached': result.get('cached', False)
            }

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._fallback_analysis(description, detected_verbs)

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI JSON response."""
        cleaned = response.strip()

        # Remove markdown code blocks
        if cleaned.startswith('```'):
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

        return json.loads(cleaned)

    def _validate_analysis(self, analysis: Dict[str, Any]) -> bool:
        """Validate analysis structure."""
        required_fields = ['primary_verb', 'definition', 'student_actions']

        for field in required_fields:
            if field not in analysis or not analysis[field]:
                logger.warning(f"Missing required field: {field}")
                return False

        if not isinstance(analysis['student_actions'], list):
            logger.warning("student_actions is not a list")
            return False

        return True

    def _fallback_analysis(
        self,
        description: str,
        detected_verbs: List[str]
    ) -> Dict[str, Any]:
        """
        Fallback analysis if AI fails.

        Args:
            description: Essay description
            detected_verbs: Detected verbs

        Returns:
            Basic analysis
        """
        logger.info("Using fallback verb analysis")

        if not detected_verbs:
            # No verbs detected, assume "discuss"
            primary_verb = "discuss"
        else:
            # Use first detected verb
            primary_verb = detected_verbs[0]

        # Get Bloom's level
        blooms_level = self._get_blooms_level(primary_verb)

        # Generic actions based on verb
        actions = self._get_generic_actions(primary_verb)

        return {
            'success': True,
            'analysis': {
                'primary_verb': primary_verb,
                'definition': f"Perform {primary_verb} operation on the topic",
                'student_actions': actions,
                'blooms_level': blooms_level,
                'secondary_verbs': detected_verbs[1:] if len(detected_verbs) > 1 else []
            },
            'fallback': True
        }

    def _get_blooms_level(self, verb: str) -> str:
        """Get Bloom's taxonomy level for verb."""
        for level, verbs in self.BLOOMS_TAXONOMY.items():
            if verb.lower() in verbs:
                return level
        return 'understand'  # Default

    def _get_generic_actions(self, verb: str) -> List[str]:
        """Get generic actions for verb."""
        action_map = {
            'analyze': [
                "Break down the topic into components",
                "Examine relationships between elements",
                "Identify patterns and connections",
                "Support analysis with evidence"
            ],
            'evaluate': [
                "Make judgments about the topic",
                "Assess strengths and weaknesses",
                "Justify your position with criteria",
                "Consider alternative perspectives"
            ],
            'compare': [
                "Identify similarities between topics",
                "Identify differences between topics",
                "Organize comparison systematically",
                "Draw conclusions from comparison"
            ],
            'discuss': [
                "Present multiple perspectives",
                "Examine different viewpoints",
                "Provide evidence for claims",
                "Reach a balanced conclusion"
            ],
            'explain': [
                "Clarify the topic clearly",
                "Provide reasons and evidence",
                "Use examples to illustrate",
                "Make connections explicit"
            ]
        }

        return action_map.get(verb.lower(), [
            f"Perform {verb} operation",
            "Provide evidence and examples",
            "Organize thoughts logically",
            "Reach a clear conclusion"
        ])


if __name__ == "__main__":
    print("Testing Verb Analyzer...")

    analyzer = VerbAnalyzer(user_id="test_user")

    test_description = "Analyze the impact of postmodernism on contemporary music production"

    # Test pattern detection
    verbs = analyzer._detect_verbs_pattern(test_description)
    print(f"\nDetected verbs: {verbs}")

    # Test fallback
    fallback = analyzer._fallback_analysis(test_description, verbs)
    print(f"\nFallback analysis: {json.dumps(fallback, indent=2)}")

    print("\nVerb Analyzer structure validated!")
