"""
Content Summarizer
AI-powered content summarization and key point extraction.

Features:
- Article summarization
- Key point extraction
- Note generation
- Abstract creation
- TL;DR generation
- Bullet point summaries

Author: Academic Command Center
Phase: 6 Sprint 2
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class Summary:
    """Content summary."""
    summary_type: str  # brief, detailed, abstract, tldr, bullets
    summary_text: str
    word_count: int
    key_points: List[str]
    main_themes: List[str]
    confidence_score: float  # 0-100


@dataclass
class KeyPoint:
    """Extracted key point."""
    point: str
    importance: str  # high, medium, low
    category: str  # main_idea, supporting_detail, conclusion
    source_location: Optional[str]


class ContentSummarizer:
    """
    AI-powered Content Summarizer.

    Provides:
    - Article and document summarization
    - Key point extraction
    - Note generation
    - Abstract creation
    - TL;DR summaries
    """

    def __init__(
        self,
        user_id: str,
        ai_router: Optional[AIRouter] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Content Summarizer.

        Args:
            user_id: Current user ID
            ai_router: AI router instance
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter()
        self.db = db_manager or DatabaseManager()

        logger.info("Content Summarizer initialized")

    def summarize(
        self,
        content: str,
        summary_type: str = "brief",
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Summarize content.

        Args:
            content: Text to summarize
            summary_type: Type (brief, detailed, abstract, tldr, bullets)
            max_length: Maximum summary length in words

        Returns:
            Summary with key points
        """
        try:
            logger.info(f"Summarizing {len(content)} characters as {summary_type}")

            # Generate summary based on type
            if summary_type == "tldr":
                summary_text = self._generate_tldr(content)
            elif summary_type == "bullets":
                summary_text = self._generate_bullets(content)
            elif summary_type == "abstract":
                summary_text = self._generate_abstract(content)
            elif summary_type == "detailed":
                summary_text = self._generate_detailed_summary(content)
            else:  # brief
                summary_text = self._generate_brief_summary(content, max_length)

            # Extract key points
            key_points = self._extract_key_points(content)

            # Identify themes
            themes = self._identify_themes(content)

            # Calculate confidence
            confidence = self._calculate_confidence(content, summary_text)

            summary = Summary(
                summary_type=summary_type,
                summary_text=summary_text,
                word_count=len(summary_text.split()),
                key_points=[kp.point for kp in key_points],
                main_themes=themes,
                confidence_score=confidence
            )

            return {
                'success': True,
                'summary': summary_text,
                'word_count': len(summary_text.split()),
                'key_points': [self._keypoint_to_dict(kp) for kp in key_points],
                'themes': themes,
                'confidence': confidence,
                'type': summary_type
            }

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_notes(
        self,
        content: str,
        note_style: str = "outline"
    ) -> Dict[str, Any]:
        """
        Generate study notes from content.

        Args:
            content: Source material
            note_style: Style (outline, bullet, cornell)

        Returns:
            Formatted notes
        """
        try:
            logger.info(f"Generating {note_style} notes")

            if note_style == "cornell":
                notes = self._generate_cornell_notes(content)
            elif note_style == "bullet":
                notes = self._generate_bullet_notes(content)
            else:  # outline
                notes = self._generate_outline_notes(content)

            return {
                'success': True,
                'notes': notes,
                'style': note_style
            }

        except Exception as e:
            logger.error(f"Note generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_brief_summary(
        self,
        content: str,
        max_length: Optional[int]
    ) -> str:
        """Generate brief summary."""
        try:
            length_instruction = f"in about {max_length} words" if max_length else "in 2-3 sentences"

            prompt = f"""Summarize this content {length_instruction}:

{content[:3000]}

Provide a concise summary that captures the main points.
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="summarization",
                max_tokens=max_length * 2 if max_length else 200
            )

            if result.get('success'):
                return result.get('text', '').strip()

            return self._fallback_summary(content, 3)

        except Exception as e:
            logger.error(f"Brief summary generation failed: {e}")
            return self._fallback_summary(content, 3)

    def _generate_detailed_summary(self, content: str) -> str:
        """Generate detailed summary."""
        try:
            prompt = f"""Provide a detailed summary of this content:

{content[:4000]}

Include:
- Main arguments/points
- Supporting evidence
- Key findings
- Conclusions

Length: 1-2 paragraphs
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="summarization",
                max_tokens=500
            )

            if result.get('success'):
                return result.get('text', '').strip()

            return self._fallback_summary(content, 10)

        except Exception as e:
            logger.error(f"Detailed summary failed: {e}")
            return self._fallback_summary(content, 10)

    def _generate_tldr(self, content: str) -> str:
        """Generate TL;DR (Too Long; Didn't Read) summary."""
        try:
            prompt = f"""Provide a TL;DR (Too Long; Didn't Read) summary:

{content[:2000]}

One sentence that captures the absolute essential point.
Start with "TL;DR: "
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="summarization",
                max_tokens=100
            )

            if result.get('success'):
                summary = result.get('text', '').strip()
                if not summary.startswith('TL;DR'):
                    summary = f"TL;DR: {summary}"
                return summary

            return f"TL;DR: {self._fallback_summary(content, 1)}"

        except Exception as e:
            logger.error(f"TL;DR generation failed: {e}")
            return f"TL;DR: {self._fallback_summary(content, 1)}"

    def _generate_bullets(self, content: str) -> str:
        """Generate bullet point summary."""
        try:
            prompt = f"""Summarize this content as bullet points (5-7 points):

{content[:3000]}

Use this format:
• Point 1
• Point 2
etc.
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="summarization",
                max_tokens=300
            )

            if result.get('success'):
                return result.get('text', '').strip()

            # Fallback
            sentences = content.split('.')[:5]
            bullets = "\n".join([f"• {s.strip()}" for s in sentences if s.strip()])
            return bullets

        except Exception as e:
            logger.error(f"Bullet summary failed: {e}")
            sentences = content.split('.')[:5]
            return "\n".join([f"• {s.strip()}" for s in sentences if s.strip()])

    def _generate_abstract(self, content: str) -> str:
        """Generate academic-style abstract."""
        try:
            prompt = f"""Write an academic abstract for this content:

{content[:4000]}

Abstract should include:
- Background/context
- Purpose/objectives
- Methods (if applicable)
- Key findings/arguments
- Conclusions

Length: 150-250 words
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="summarization",
                max_tokens=400
            )

            if result.get('success'):
                return result.get('text', '').strip()

            return self._fallback_summary(content, 200)

        except Exception as e:
            logger.error(f"Abstract generation failed: {e}")
            return self._fallback_summary(content, 200)

    def _extract_key_points(self, content: str) -> List[KeyPoint]:
        """Extract key points from content."""
        try:
            prompt = f"""Extract 5-7 key points from this content:

{content[:3000]}

For each point, indicate:
- The point itself
- Importance (high/medium/low)
- Category (main_idea/supporting_detail/conclusion)

Return as JSON array:
[
    {{
        "point": "key point text",
        "importance": "high",
        "category": "main_idea"
    }}
]
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=500
            )

            if result.get('success'):
                points_data = self._extract_json_list(result.get('text', '[]'))

                key_points = []
                for data in points_data[:7]:
                    point = KeyPoint(
                        point=data.get('point', ''),
                        importance=data.get('importance', 'medium'),
                        category=data.get('category', 'main_idea'),
                        source_location=None
                    )
                    key_points.append(point)

                return key_points

            return self._fallback_key_points(content)

        except Exception as e:
            logger.error(f"Key point extraction failed: {e}")
            return self._fallback_key_points(content)

    def _identify_themes(self, content: str) -> List[str]:
        """Identify main themes."""
        try:
            prompt = f"""Identify 3-5 main themes in this content:

{content[:2000]}

Return as JSON array: ["theme1", "theme2", ...]
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=150
            )

            if result.get('success'):
                return self._extract_json_list(result.get('text', '[]'))[:5]

            return []

        except Exception as e:
            logger.error(f"Theme identification failed: {e}")
            return []

    def _generate_cornell_notes(self, content: str) -> str:
        """Generate Cornell-style notes."""
        try:
            prompt = f"""Create Cornell-style notes for this content:

{content[:3000]}

Format:
CUE COLUMN (Questions/Keywords):
- Key question 1
- Key question 2

NOTES COLUMN (Main points):
- Detailed note 1
- Detailed note 2

SUMMARY:
Brief summary paragraph
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="notes",
                max_tokens=500
            )

            if result.get('success'):
                return result.get('text', '').strip()

            return self._fallback_notes(content)

        except Exception as e:
            logger.error(f"Cornell notes failed: {e}")
            return self._fallback_notes(content)

    def _generate_bullet_notes(self, content: str) -> str:
        """Generate bullet-point notes."""
        try:
            prompt = f"""Create bullet-point study notes:

{content[:3000]}

Organize with:
- Main topics as headers
- Sub-points indented
- Key terms bolded (use **)
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="notes",
                max_tokens=400
            )

            if result.get('success'):
                return result.get('text', '').strip()

            return self._fallback_notes(content)

        except Exception as e:
            logger.error(f"Bullet notes failed: {e}")
            return self._fallback_notes(content)

    def _generate_outline_notes(self, content: str) -> str:
        """Generate outline-style notes."""
        try:
            prompt = f"""Create an outline of this content:

{content[:3000]}

Format:
I. Main Topic 1
   A. Subtopic
      1. Detail
      2. Detail
   B. Subtopic
II. Main Topic 2
etc.
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="notes",
                max_tokens=400
            )

            if result.get('success'):
                return result.get('text', '').strip()

            return self._fallback_notes(content)

        except Exception as e:
            logger.error(f"Outline notes failed: {e}")
            return self._fallback_notes(content)

    def _calculate_confidence(self, content: str, summary: str) -> float:
        """Calculate summary confidence score."""
        # Simple heuristic: ratio of summary to content length
        content_words = len(content.split())
        summary_words = len(summary.split())

        if content_words == 0:
            return 0.0

        compression_ratio = summary_words / content_words

        # Ideal compression: 5-15%
        if 0.05 <= compression_ratio <= 0.15:
            confidence = 90.0
        elif 0.01 <= compression_ratio <= 0.20:
            confidence = 75.0
        else:
            confidence = 60.0

        return confidence

    def _fallback_summary(self, content: str, sentence_count: int) -> str:
        """Fallback summary using first N sentences."""
        sentences = content.split('.')[:sentence_count]
        return '. '.join(s.strip() for s in sentences if s.strip()) + '.'

    def _fallback_key_points(self, content: str) -> List[KeyPoint]:
        """Fallback key points from paragraphs."""
        paragraphs = content.split('\n\n')[:5]

        points = []
        for para in paragraphs:
            if len(para) > 50:
                points.append(KeyPoint(
                    point=para[:150] + "...",
                    importance="medium",
                    category="main_idea",
                    source_location=None
                ))

        return points

    def _fallback_notes(self, content: str) -> str:
        """Fallback basic notes."""
        paragraphs = content.split('\n\n')[:5]
        notes = "\n\n".join([f"• {p[:200]}" for p in paragraphs if p.strip()])
        return notes

    def _extract_json_list(self, text: str) -> List:
        """Extract JSON array from text."""
        try:
            import json
            start = text.find('[')
            if start != -1:
                end = text.rfind(']')
                if end != -1:
                    return json.loads(text[start:end+1])
            return json.loads(text)
        except:
            return []

    def _keypoint_to_dict(self, point: KeyPoint) -> Dict[str, Any]:
        """Convert KeyPoint to dictionary."""
        return {
            'point': point.point,
            'importance': point.importance,
            'category': point.category,
            'source_location': point.source_location
        }


def create_content_summarizer(
    user_id: str,
    ai_router: Optional[AIRouter] = None,
    db_manager: Optional[DatabaseManager] = None
) -> ContentSummarizer:
    """
    Factory function to create Content Summarizer.

    Args:
        user_id: Current user ID
        ai_router: AI router instance
        db_manager: Database manager instance

    Returns:
        ContentSummarizer instance
    """
    return ContentSummarizer(user_id, ai_router, db_manager)
