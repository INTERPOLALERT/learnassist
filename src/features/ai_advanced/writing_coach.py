"""
Writing Coach
AI-powered writing improvement and personalized feedback.

Features:
- Personalized writing feedback
- Style improvement suggestions
- Vocabulary enhancement
- Sentence structure analysis
- Tone adjustment
- Readability optimization

Author: Academic Command Center
Phase: 6 Sprint 2
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class WritingFeedback:
    """Personalized writing feedback."""
    category: str  # style, vocabulary, structure, tone
    severity: str  # suggestion, warning, error
    location: str  # paragraph or sentence number
    issue: str
    suggestion: str
    example: Optional[str]


@dataclass
class StyleAnalysis:
    """Writing style analysis."""
    formality_score: float  # 0-100 (0=very informal, 100=very formal)
    clarity_score: float  # 0-100
    engagement_score: float  # 0-100
    sentence_variety_score: float  # 0-100
    avg_sentence_length: float
    passive_voice_percentage: float
    transition_usage_score: float


@dataclass
class VocabularyAnalysis:
    """Vocabulary analysis."""
    sophistication_score: float  # 0-100
    repetition_issues: List[str]
    suggested_alternatives: Dict[str, List[str]]
    overused_words: List[str]
    academic_vocabulary_usage: float  # percentage


class WritingCoach:
    """
    AI-powered Writing Coach.

    Provides:
    - Personalized feedback on writing
    - Style improvement suggestions
    - Vocabulary enhancement
    - Sentence structure analysis
    - Tone and formality adjustment
    """

    def __init__(
        self,
        user_id: str,
        ai_router: Optional[AIRouter] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Writing Coach.

        Args:
            user_id: Current user ID
            ai_router: AI router instance
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter()
        self.db = db_manager or DatabaseManager()

        logger.info("Writing Coach initialized")

    def analyze_writing(
        self,
        text: str,
        target_style: str = "academic"
    ) -> Dict[str, Any]:
        """
        Comprehensive writing analysis and feedback.

        Args:
            text: Text to analyze
            target_style: Desired style (academic, professional, casual)

        Returns:
            Complete analysis with feedback
        """
        try:
            logger.info(f"Analyzing {len(text)} characters of {target_style} writing")

            # Analyze style
            style_analysis = self._analyze_style(text)

            # Analyze vocabulary
            vocab_analysis = self._analyze_vocabulary(text)

            # Generate personalized feedback
            feedback = self._generate_feedback(
                text,
                style_analysis,
                vocab_analysis,
                target_style
            )

            # Get improvement suggestions
            suggestions = self._get_improvement_suggestions(
                style_analysis,
                vocab_analysis,
                target_style
            )

            return {
                'success': True,
                'style': self._style_to_dict(style_analysis),
                'vocabulary': self._vocab_to_dict(vocab_analysis),
                'feedback': [self._feedback_to_dict(f) for f in feedback],
                'suggestions': suggestions,
                'overall_score': self._calculate_writing_score(
                    style_analysis,
                    vocab_analysis
                )
            }

        except Exception as e:
            logger.error(f"Writing analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def improve_sentence(self, sentence: str) -> Dict[str, Any]:
        """
        Suggest improvements for a specific sentence.

        Args:
            sentence: Sentence to improve

        Returns:
            Improved versions and explanations
        """
        try:
            prompt = f"""Improve this sentence for academic writing:

"{sentence}"

Provide 2-3 improved versions with explanations.

Return as JSON:
{{
    "improvements": [
        {{
            "version": "improved sentence",
            "explanation": "what was changed and why"
        }}
    ]
}}
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="writing",
                max_tokens=300
            )

            if result.get('success'):
                data = self._extract_json(result.get('text', '{}'))
                improvements = data.get('improvements', [])

                return {
                    'success': True,
                    'original': sentence,
                    'improvements': improvements
                }

            return {
                'success': True,
                'original': sentence,
                'improvements': []
            }

        except Exception as e:
            logger.error(f"Sentence improvement failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def suggest_alternatives(
        self,
        word: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Suggest alternative words.

        Args:
            word: Word to replace
            context: Sentence context

        Returns:
            Alternative words with explanations
        """
        try:
            prompt = f"""Suggest better academic alternatives for the word "{word}" in this context:

"{context}"

Provide 3-5 alternatives that:
- Are more sophisticated
- Fit the academic context
- Maintain the meaning

Return as JSON array: ["alternative1", "alternative2", ...]
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="writing",
                max_tokens=150
            )

            if result.get('success'):
                alternatives = self._extract_json_list(result.get('text', '[]'))

                return {
                    'success': True,
                    'word': word,
                    'alternatives': alternatives[:5]
                }

            return {
                'success': True,
                'word': word,
                'alternatives': []
            }

        except Exception as e:
            logger.error(f"Alternative suggestion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _analyze_style(self, text: str) -> StyleAnalysis:
        """Analyze writing style."""
        # Calculate sentence statistics
        sentences = self._split_sentences(text)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]

        avg_length = sum(sentence_lengths) / max(len(sentence_lengths), 1)

        # Calculate variety (standard deviation of lengths)
        if len(sentence_lengths) > 1:
            mean = avg_length
            variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
            std_dev = variance ** 0.5
            variety_score = min(100, (std_dev / mean) * 100 + 50)
        else:
            variety_score = 50.0

        # Detect passive voice
        passive_count = self._count_passive_voice(text)
        passive_percentage = (passive_count / max(len(sentences), 1)) * 100

        # Calculate transition usage
        transition_score = self._calculate_transition_score(text)

        # Formality score (heuristic)
        formality = self._calculate_formality(text)

        # Clarity score
        clarity = self._calculate_clarity(text, avg_length)

        # Engagement score
        engagement = 100 - min(100, passive_percentage * 2)

        return StyleAnalysis(
            formality_score=formality,
            clarity_score=clarity,
            engagement_score=engagement,
            sentence_variety_score=variety_score,
            avg_sentence_length=avg_length,
            passive_voice_percentage=passive_percentage,
            transition_usage_score=transition_score
        )

    def _analyze_vocabulary(self, text: str) -> VocabularyAnalysis:
        """Analyze vocabulary usage."""
        words = text.lower().split()
        word_freq = {}

        for word in words:
            word = re.sub(r'[^\w]', '', word)
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1

        # Find overused words (appear more than 3 times per 1000 words)
        total_words = len(words)
        threshold = max(3, total_words // 1000 * 3)
        overused = [
            word for word, count in word_freq.items()
            if count > threshold and word not in ['that', 'this', 'with', 'from']
        ]

        # Calculate sophistication (average word length)
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        sophistication = min(100, (avg_word_length - 3) * 20)

        # Detect repetition issues
        repetition_issues = []
        prev_word = None
        for word in words:
            if word == prev_word and len(word) > 4:
                repetition_issues.append(f"Repeated '{word}'")
            prev_word = word

        # Academic vocabulary (heuristic: words > 8 letters)
        academic_words = [w for w in words if len(w) > 8]
        academic_percentage = (len(academic_words) / max(len(words), 1)) * 100

        return VocabularyAnalysis(
            sophistication_score=sophistication,
            repetition_issues=repetition_issues[:10],
            suggested_alternatives={},  # Would be filled by AI
            overused_words=overused[:10],
            academic_vocabulary_usage=academic_percentage
        )

    def _generate_feedback(
        self,
        text: str,
        style: StyleAnalysis,
        vocab: VocabularyAnalysis,
        target_style: str
    ) -> List[WritingFeedback]:
        """Generate personalized feedback."""
        feedback = []

        # Style feedback
        if style.passive_voice_percentage > 20:
            feedback.append(WritingFeedback(
                category="style",
                severity="warning",
                location="Throughout",
                issue=f"Excessive passive voice ({style.passive_voice_percentage:.0f}%)",
                suggestion="Use more active voice for stronger, clearer writing",
                example="Change 'The experiment was conducted' to 'We conducted the experiment'"
            ))

        if style.avg_sentence_length > 25:
            feedback.append(WritingFeedback(
                category="structure",
                severity="suggestion",
                location="Throughout",
                issue=f"Long average sentence length ({style.avg_sentence_length:.1f} words)",
                suggestion="Break some sentences into shorter ones for better readability",
                example=None
            ))

        if style.sentence_variety_score < 50:
            feedback.append(WritingFeedback(
                category="style",
                severity="suggestion",
                location="Throughout",
                issue="Low sentence variety",
                suggestion="Vary sentence length and structure to maintain reader interest",
                example="Mix short, impactful sentences with longer, detailed ones"
            ))

        # Vocabulary feedback
        if vocab.overused_words:
            for word in vocab.overused_words[:3]:
                feedback.append(WritingFeedback(
                    category="vocabulary",
                    severity="suggestion",
                    location="Throughout",
                    issue=f"Overused word: '{word}'",
                    suggestion=f"Find alternative words for '{word}'",
                    example=None
                ))

        if vocab.sophistication_score < 40 and target_style == "academic":
            feedback.append(WritingFeedback(
                category="vocabulary",
                severity="warning",
                location="Throughout",
                issue="Vocabulary may be too simple for academic writing",
                suggestion="Use more sophisticated, discipline-specific terminology",
                example="Consider: 'utilize' instead of 'use', 'demonstrate' instead of 'show'"
            ))

        return feedback[:10]  # Limit to top 10

    def _get_improvement_suggestions(
        self,
        style: StyleAnalysis,
        vocab: VocabularyAnalysis,
        target_style: str
    ) -> List[str]:
        """Get actionable improvement suggestions."""
        suggestions = []

        # Style suggestions
        if style.clarity_score < 70:
            suggestions.append("Simplify complex sentences for better clarity")

        if style.engagement_score < 70:
            suggestions.append("Use more active voice to engage readers")

        if style.transition_usage_score < 60:
            suggestions.append("Add transition words to improve flow between ideas")

        # Vocabulary suggestions
        if vocab.sophistication_score < 50 and target_style == "academic":
            suggestions.append("Incorporate more advanced academic vocabulary")

        if vocab.overused_words:
            suggestions.append("Replace frequently repeated words with synonyms")

        if vocab.academic_vocabulary_usage < 10:
            suggestions.append("Use more technical and discipline-specific terms")

        # General suggestions
        if style.avg_sentence_length < 15:
            suggestions.append("Combine some short sentences for better flow")

        return suggestions

    def _calculate_writing_score(
        self,
        style: StyleAnalysis,
        vocab: VocabularyAnalysis
    ) -> float:
        """Calculate overall writing quality score."""
        scores = [
            style.formality_score,
            style.clarity_score,
            style.engagement_score,
            style.sentence_variety_score,
            vocab.sophistication_score
        ]

        return sum(scores) / len(scores)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_passive_voice(self, text: str) -> int:
        """Count passive voice instances (heuristic)."""
        passive_indicators = [
            r'\bis\s+\w+ed\b',
            r'\bwas\s+\w+ed\b',
            r'\bare\s+\w+ed\b',
            r'\bwere\s+\w+ed\b',
            r'\bbeen\s+\w+ed\b'
        ]

        count = 0
        text_lower = text.lower()

        for pattern in passive_indicators:
            count += len(re.findall(pattern, text_lower))

        return count

    def _calculate_transition_score(self, text: str) -> float:
        """Calculate transition word usage score."""
        transition_words = [
            'however', 'therefore', 'furthermore', 'moreover', 'additionally',
            'consequently', 'nevertheless', 'thus', 'hence', 'meanwhile',
            'in addition', 'for example', 'for instance', 'in contrast'
        ]

        count = sum(text.lower().count(word) for word in transition_words)
        paragraphs = len(text.split('\n\n'))

        transitions_per_para = count / max(paragraphs, 1)
        score = min(100, transitions_per_para * 30 + 40)

        return score

    def _calculate_formality(self, text: str) -> float:
        """Calculate formality score (heuristic)."""
        # Informal indicators
        informal_words = ['really', 'very', 'actually', 'basically', 'just', 'like']
        informal_count = sum(text.lower().count(word) for word in informal_words)

        # Formal indicators
        formal_words = ['however', 'furthermore', 'consequently', 'therefore']
        formal_count = sum(text.lower().count(word) for word in formal_words)

        total = len(text.split())
        informal_ratio = (informal_count / max(total, 1)) * 100
        formal_ratio = (formal_count / max(total, 1)) * 100

        formality = 50 + (formal_ratio * 10) - (informal_ratio * 10)

        return max(0, min(100, formality))

    def _calculate_clarity(self, text: str, avg_sentence_length: float) -> float:
        """Calculate clarity score."""
        # Penalize very long sentences
        if avg_sentence_length > 30:
            length_penalty = (avg_sentence_length - 30) * 2
        else:
            length_penalty = 0

        # Reward moderate sentence length (15-20 words)
        if 15 <= avg_sentence_length <= 20:
            clarity = 90
        elif 20 < avg_sentence_length <= 25:
            clarity = 75
        else:
            clarity = 60

        return max(0, clarity - length_penalty)

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from text."""
        try:
            import json
            start = text.find('{')
            if start != -1:
                end = text.rfind('}')
                if end != -1:
                    return json.loads(text[start:end+1])
            return json.loads(text)
        except:
            return {}

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

    def _style_to_dict(self, style: StyleAnalysis) -> Dict[str, Any]:
        """Convert StyleAnalysis to dictionary."""
        return {
            'formality_score': style.formality_score,
            'clarity_score': style.clarity_score,
            'engagement_score': style.engagement_score,
            'sentence_variety_score': style.sentence_variety_score,
            'avg_sentence_length': style.avg_sentence_length,
            'passive_voice_percentage': style.passive_voice_percentage,
            'transition_usage_score': style.transition_usage_score
        }

    def _vocab_to_dict(self, vocab: VocabularyAnalysis) -> Dict[str, Any]:
        """Convert VocabularyAnalysis to dictionary."""
        return {
            'sophistication_score': vocab.sophistication_score,
            'repetition_issues': vocab.repetition_issues,
            'suggested_alternatives': vocab.suggested_alternatives,
            'overused_words': vocab.overused_words,
            'academic_vocabulary_usage': vocab.academic_vocabulary_usage
        }

    def _feedback_to_dict(self, feedback: WritingFeedback) -> Dict[str, Any]:
        """Convert WritingFeedback to dictionary."""
        return {
            'category': feedback.category,
            'severity': feedback.severity,
            'location': feedback.location,
            'issue': feedback.issue,
            'suggestion': feedback.suggestion,
            'example': feedback.example
        }


def create_writing_coach(
    user_id: str,
    ai_router: Optional[AIRouter] = None,
    db_manager: Optional[DatabaseManager] = None
) -> WritingCoach:
    """
    Factory function to create Writing Coach.

    Args:
        user_id: Current user ID
        ai_router: AI router instance
        db_manager: Database manager instance

    Returns:
        WritingCoach instance
    """
    return WritingCoach(user_id, ai_router, db_manager)
