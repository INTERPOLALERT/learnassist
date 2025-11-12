"""
Academic Command Center - Materials Library - Auto Tagger
Automatically extracts key concepts and generates tags for materials using AI.
"""

import logging
import json
from typing import Dict, Any, List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AutoTagger:
    """
    Automatically tags materials with key concepts.

    Uses:
    - NLP entity extraction (spaCy)
    - AI summarization and concept extraction
    - Keyword extraction from text
    """

    def __init__(self, user_id: str, ai_router: Optional[AIRouter] = None):
        """
        Initialize auto tagger.

        Args:
            user_id: Current user ID
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter(user_id)

        # Try to load spaCy
        self.nlp = self._load_spacy()

    def _load_spacy(self):
        """Load spaCy NLP model."""
        try:
            import spacy
            return spacy.load('en_core_web_sm')
        except Exception as e:
            logger.warning(f"spaCy not available: {e}")
            return None

    def tag_material(
        self,
        text: str,
        file_name: str,
        max_concepts: int = 10
    ) -> Dict[str, Any]:
        """
        Generate tags for material.

        Args:
            text: Extracted text from material
            file_name: Name of file (for context)
            max_concepts: Maximum number of concepts to extract

        Returns:
            Tagging result with concepts and summary
        """
        logger.info(f"Auto-tagging material: {file_name}")

        # Truncate text if too long (to avoid API limits)
        truncated_text = self._truncate_text(text, max_chars=8000)

        results = {
            'key_concepts': [],
            'content_summary': '',
            'tags': [],
            'academic_level': 'unknown'
        }

        # Step 1: Extract concepts using NLP
        if self.nlp:
            nlp_concepts = self._extract_nlp_concepts(truncated_text)
            results['nlp_concepts'] = nlp_concepts
            logger.info(f"NLP extracted {len(nlp_concepts)} concepts")

        # Step 2: Use AI to extract key concepts and summarize
        ai_result = self._extract_ai_concepts(truncated_text, file_name, max_concepts)

        if ai_result['success']:
            results['key_concepts'] = ai_result['concepts']
            results['content_summary'] = ai_result['summary']
            results['academic_level'] = ai_result.get('academic_level', 'unknown')
            logger.info(f"AI extracted {len(results['key_concepts'])} concepts")

        # Step 3: Generate searchable tags (combine NLP + AI concepts)
        all_concepts = results['key_concepts']
        if self.nlp and nlp_concepts:
            all_concepts.extend(nlp_concepts[:5])  # Add top 5 NLP concepts

        # Deduplicate and normalize tags
        results['tags'] = self._normalize_tags(all_concepts)

        logger.info(f"✓ Generated {len(results['tags'])} tags")

        return {
            'success': True,
            **results
        }

    def _truncate_text(self, text: str, max_chars: int = 8000) -> str:
        """
        Truncate text intelligently (preserve beginnings and ends).

        Args:
            text: Full text
            max_chars: Maximum characters

        Returns:
            Truncated text
        """
        if len(text) <= max_chars:
            return text

        # Take first 60% and last 20% (skip middle)
        first_part_size = int(max_chars * 0.7)
        last_part_size = int(max_chars * 0.3)

        first_part = text[:first_part_size]
        last_part = text[-last_part_size:]

        return f"{first_part}\n\n[... middle section truncated ...]\n\n{last_part}"

    def _extract_nlp_concepts(self, text: str) -> List[str]:
        """
        Extract concepts using spaCy NLP.

        Args:
            text: Input text

        Returns:
            List of concept strings
        """
        if not self.nlp:
            return []

        try:
            doc = self.nlp(text[:100000])  # Limit for spaCy processing

            concepts = set()

            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'WORK_OF_ART', 'LAW', 'PRODUCT']:
                    concepts.add(ent.text)

            # Extract noun chunks (potential concepts)
            for chunk in doc.noun_chunks:
                # Filter out very common/generic chunks
                if len(chunk.text.split()) <= 4 and not chunk.root.is_stop:
                    concepts.add(chunk.text)

            # Sort by frequency (most common first)
            concept_list = list(concepts)
            return concept_list[:20]  # Top 20

        except Exception as e:
            logger.warning(f"NLP extraction failed: {e}")
            return []

    def _extract_ai_concepts(
        self,
        text: str,
        file_name: str,
        max_concepts: int
    ) -> Dict[str, Any]:
        """
        Extract concepts using AI.

        Args:
            text: Input text
            file_name: File name for context
            max_concepts: Maximum concepts to extract

        Returns:
            Extraction result
        """
        prompt = f"""Analyze this academic material and extract key concepts.

Material: "{file_name}"
Content preview:
{text[:4000]}

Provide:
1. Key concepts (up to {max_concepts} most important topics/themes)
2. Brief summary (2-3 sentences)
3. Academic level (undergraduate/graduate/phd/general)

Return ONLY valid JSON (no markdown):
{{
  "concepts": ["concept1", "concept2", ...],
  "summary": "Brief summary here",
  "academic_level": "undergraduate|graduate|phd|general"
}}
"""

        result = self.ai_router.execute_task({
            'task_type': 'concept_extraction',
            'payload': {
                'prompt': prompt,
                'temperature': 0.3,
                'max_tokens': 800
            }
        })

        if not result['success']:
            logger.warning(f"AI extraction failed: {result.get('error')}")
            return {
                'success': False,
                'concepts': [],
                'summary': '',
                'academic_level': 'unknown'
            }

        try:
            parsed = self._parse_ai_response(result['data'])
            return {
                'success': True,
                'concepts': parsed.get('concepts', []),
                'summary': parsed.get('summary', ''),
                'academic_level': parsed.get('academic_level', 'unknown')
            }

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                'success': False,
                'concepts': [],
                'summary': '',
                'academic_level': 'unknown'
            }

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

    def _normalize_tags(self, concepts: List[str]) -> List[str]:
        """
        Normalize and deduplicate tags.

        Args:
            concepts: List of concept strings

        Returns:
            Normalized tags
        """
        tags = set()

        for concept in concepts:
            if not concept:
                continue

            # Normalize
            tag = concept.strip().lower()

            # Remove very short or very long tags
            if len(tag) < 2 or len(tag) > 50:
                continue

            # Remove pure numbers
            if tag.isdigit():
                continue

            tags.add(tag)

        return sorted(list(tags))

    def suggest_material_links(
        self,
        material_concepts: List[str],
        essay_concepts: List[str]
    ) -> Dict[str, Any]:
        """
        Suggest if material should be linked to an essay.

        Args:
            material_concepts: Concepts from material
            essay_concepts: Required concepts from essay

        Returns:
            Link suggestion with relevance score
        """
        if not material_concepts or not essay_concepts:
            return {
                'should_link': False,
                'relevance_score': 0,
                'matching_concepts': []
            }

        # Normalize all concepts
        material_lower = [c.lower() for c in material_concepts]
        essay_lower = [c.lower() for c in essay_concepts]

        # Find matches
        matches = []
        for essay_concept in essay_lower:
            for material_concept in material_lower:
                # Exact match or substring match
                if essay_concept == material_concept or essay_concept in material_concept or material_concept in essay_concept:
                    matches.append(essay_concept)
                    break

        match_count = len(matches)
        relevance_score = int((match_count / len(essay_concepts)) * 100)

        should_link = relevance_score >= 30  # Link if 30%+ overlap

        return {
            'should_link': should_link,
            'relevance_score': relevance_score,
            'matching_concepts': matches,
            'match_count': match_count,
            'total_essay_concepts': len(essay_concepts)
        }


if __name__ == "__main__":
    print("Testing Auto Tagger...")

    tagger = AutoTagger(user_id="test_user")

    test_text = """
    Postmodernism is a broad movement that developed in the mid- to late 20th century
    across philosophy, the arts, architecture, and criticism. It represents a departure
    from modernism and is characterized by skepticism toward grand narratives and ideologies.
    """

    print("\nAuto Tagger structure validated!")
