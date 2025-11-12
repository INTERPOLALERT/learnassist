"""
Academic Command Center - Essay Parser - Concept Extractor
Extracts key concepts using NLP (spaCy) and AI expansion.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ConceptExtractor:
    """
    Extracts and expands key concepts from essay descriptions.

    Two-stage process:
    1. NLP extraction (spaCy) - fast, local
    2. AI expansion - adds context and subtopics
    """

    def __init__(self, user_id: str, ai_router: Optional[AIRouter] = None):
        """
        Initialize concept extractor.

        Args:
            user_id: Current user ID
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter(user_id)

        # Load spaCy model (lazy loading)
        self.nlp = None

    def _load_spacy(self):
        """Lazy load spaCy model."""
        if self.nlp is None:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded")
            except Exception as e:
                logger.warning(f"Failed to load spaCy: {e}")
                self.nlp = False  # Mark as unavailable

    def extract(self, description: str) -> Dict[str, Any]:
        """
        Extract key concepts from essay description.

        Args:
            description: Essay description/task

        Returns:
            Dictionary with concepts and their details
        """
        if not description or len(description.strip()) < 10:
            return {'success': False, 'error': 'Description too short'}

        logger.info("Extracting concepts...")

        # Stage 1: NLP extraction
        nlp_concepts = self._extract_with_nlp(description)
        logger.info(f"NLP extracted {len(nlp_concepts)} concepts")

        # Stage 2: AI expansion
        if nlp_concepts:
            ai_result = self._expand_with_ai(description, nlp_concepts)
        else:
            # No NLP concepts, let AI find them
            ai_result = self._extract_with_ai_only(description)

        if ai_result['success']:
            return ai_result
        else:
            # Fallback to NLP-only
            return {
                'success': True,
                'concepts': [{'name': c, 'importance': 'Unknown', 'subtopics': []} for c in nlp_concepts],
                'fallback': True
            }

    def _extract_with_nlp(self, text: str) -> List[str]:
        """
        Extract concepts using spaCy NLP.

        Args:
            text: Description text

        Returns:
            List of concept strings
        """
        self._load_spacy()

        if not self.nlp or self.nlp is False:
            logger.warning("spaCy not available, skipping NLP extraction")
            return []

        try:
            doc = self.nlp(text)

            concepts: Set[str] = set()

            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'WORK_OF_ART', 'LAW', 'PRODUCT']:
                    concepts.add(ent.text)

            # Extract noun chunks (key phrases)
            for chunk in doc.noun_chunks:
                # Only include chunks with meaningful nouns
                if len(chunk.text.split()) <= 4 and chunk.root.pos_ == 'NOUN':
                    # Capitalize for consistency
                    concept = chunk.text.title()
                    concepts.add(concept)

            # Filter out very common words
            stop_concepts = {'the', 'a', 'an', 'this', 'that', 'these', 'those', 'it'}
            concepts = {c for c in concepts if c.lower() not in stop_concepts}

            return sorted(list(concepts))[:10]  # Top 10

        except Exception as e:
            logger.error(f"NLP extraction failed: {e}")
            return []

    def _expand_with_ai(
        self,
        description: str,
        nlp_concepts: List[str]
    ) -> Dict[str, Any]:
        """
        Expand NLP-extracted concepts with AI.

        Args:
            description: Essay description
            nlp_concepts: Concepts from NLP

        Returns:
            Expanded concept analysis
        """
        prompt = f"""Analyze key concepts for this essay:

Description: "{description}"

Initial concepts identified: {', '.join(nlp_concepts)}

For each major concept (3-7 concepts total), provide:
1. NAME: Concept name
2. IMPORTANCE: Why this is important for the essay
3. SUBTOPICS: List of related subtopics to research

Return ONLY valid JSON array (no markdown):
[
  {{
    "name": "Postmodernism",
    "importance": "Core theoretical framework being applied",
    "subtopics": ["Definition", "Key theorists", "Historical context"]
  }},
  ...
]
"""

        result = self.ai_router.execute_task({
            'task_type': 'parse_essay_instructions',
            'payload': {
                'prompt': prompt,
                'temperature': 0.4,
                'max_tokens': 1500
            }
        })

        if not result['success']:
            return {'success': False, 'error': result.get('error')}

        try:
            concepts = self._parse_ai_response(result['data'])

            # Validate
            if not isinstance(concepts, list) or len(concepts) == 0:
                raise ValueError("Invalid concepts format")

            return {
                'success': True,
                'concepts': concepts,
                'provider': result.get('provider'),
                'cached': result.get('cached', False)
            }

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {'success': False, 'error': str(e)}

    def _extract_with_ai_only(self, description: str) -> Dict[str, Any]:
        """
        Extract concepts using only AI (no NLP).

        Args:
            description: Essay description

        Returns:
            Concept analysis
        """
        prompt = f"""Extract key concepts from this essay description:

"{description}"

Identify 3-7 key concepts the student needs to understand.

For each concept, provide:
1. NAME: Concept name
2. IMPORTANCE: Why it's important for this essay
3. SUBTOPICS: Related subtopics to research

Return ONLY valid JSON array (no markdown):
[
  {{
    "name": "Concept Name",
    "importance": "Why it matters",
    "subtopics": ["subtopic1", "subtopic2", "subtopic3"]
  }},
  ...
]
"""

        result = self.ai_router.execute_task({
            'task_type': 'parse_essay_instructions',
            'payload': {
                'prompt': prompt,
                'temperature': 0.4,
                'max_tokens': 1500
            }
        })

        if not result['success']:
            return {'success': False, 'error': result.get('error')}

        try:
            concepts = self._parse_ai_response(result['data'])

            return {
                'success': True,
                'concepts': concepts,
                'provider': result.get('provider'),
                'cached': result.get('cached', False)
            }

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {'success': False, 'error': str(e)}

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI JSON response."""
        cleaned = response.strip()

        # Remove markdown code blocks
        if cleaned.startswith('```'):
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

        return json.loads(cleaned)


if __name__ == "__main__":
    print("Testing Concept Extractor...")

    extractor = ConceptExtractor(user_id="test_user")

    test_description = "Analyze the impact of postmodernism on contemporary music production, examining sampling techniques and genre-blending practices"

    # Test NLP extraction
    nlp_concepts = extractor._extract_with_nlp(test_description)
    print(f"\nNLP Concepts: {nlp_concepts}")

    print("\nConcept Extractor structure validated!")
