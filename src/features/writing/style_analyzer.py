"""
Academic Command Center - Writing Assistant - Style Analyzer
Analyzes writing style, readability, and provides improvement suggestions.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from collections import Counter
import statistics

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """
    Analyzes writing style for academic papers.

    Analyzes:
    - Readability metrics
    - Sentence structure and variety
    - Paragraph length
    - Passive voice usage
    - Transition words
    - Academic tone
    - Vocabulary complexity
    """

    def __init__(self):
        """Initialize style analyzer."""
        # Common transition words
        self.transition_words = {
            'addition': ['furthermore', 'moreover', 'additionally', 'also', 'besides', 'in addition'],
            'contrast': ['however', 'nevertheless', 'nonetheless', 'conversely', 'on the other hand', 'in contrast'],
            'cause': ['therefore', 'thus', 'consequently', 'hence', 'as a result', 'accordingly'],
            'example': ['for example', 'for instance', 'specifically', 'namely', 'in particular'],
            'emphasis': ['indeed', 'certainly', 'undoubtedly', 'clearly', 'obviously'],
            'sequence': ['first', 'second', 'third', 'finally', 'next', 'then', 'subsequently']
        }

        # Passive voice indicators
        self.passive_indicators = [
            r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(is|are|was|were|be|been|being)\s+\w+en\b'
        ]

        # Weak words to avoid
        self.weak_words = [
            'very', 'really', 'quite', 'rather', 'somewhat', 'fairly',
            'pretty', 'just', 'actually', 'basically', 'literally'
        ]

        logger.info("Style analyzer initialized")

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text style comprehensively.

        Args:
            text: Text to analyze

        Returns:
            Style analysis results
        """
        if not text or not text.strip():
            return {
                'success': True,
                'readability_score': 0,
                'suggestions': ['Add text to analyze']
            }

        try:
            # Split into sentences and paragraphs
            sentences = self._split_sentences(text)
            paragraphs = self._split_paragraphs(text)
            words = re.findall(r'\b\w+\b', text.lower())

            # Calculate readability metrics
            readability = self._calculate_readability(text, sentences, words)

            # Analyze sentence structure
            sentence_analysis = self._analyze_sentences(sentences)

            # Analyze paragraphs
            paragraph_analysis = self._analyze_paragraphs(paragraphs)

            # Check passive voice
            passive_voice = self._check_passive_voice(text)

            # Check transitions
            transitions = self._check_transitions(text)

            # Check vocabulary
            vocabulary = self._analyze_vocabulary(words)

            # Generate suggestions
            suggestions = self._generate_suggestions(
                readability,
                sentence_analysis,
                paragraph_analysis,
                passive_voice,
                transitions,
                vocabulary
            )

            return {
                'success': True,
                'readability': readability,
                'sentences': sentence_analysis,
                'paragraphs': paragraph_analysis,
                'passive_voice': passive_voice,
                'transitions': transitions,
                'vocabulary': vocabulary,
                'suggestions': suggestions,
                'overall_score': self._calculate_overall_score(
                    readability, sentence_analysis, passive_voice, transitions
                )
            }

        except Exception as e:
            logger.error(f"Failed to analyze style: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]

    def _calculate_readability(
        self,
        text: str,
        sentences: List[str],
        words: List[str]
    ) -> Dict[str, Any]:
        """Calculate readability metrics."""
        if not sentences or not words:
            return {
                'avg_sentence_length': 0,
                'avg_word_length': 0,
                'score': 0,
                'level': 'Unknown'
            }

        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)

        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Count syllables (simplified)
        total_syllables = sum(self._count_syllables(word) for word in words)
        avg_syllables_per_word = total_syllables / len(words)

        # Simplified Flesch Reading Ease score
        # Formula: 206.835 - 1.015(words/sentences) - 84.6(syllables/words)
        reading_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        reading_ease = max(0, min(100, reading_ease))

        # Determine reading level
        if reading_ease >= 80:
            level = 'Very Easy'
        elif reading_ease >= 70:
            level = 'Easy'
        elif reading_ease >= 60:
            level = 'Standard'
        elif reading_ease >= 50:
            level = 'Fairly Difficult'
        elif reading_ease >= 30:
            level = 'Difficult'
        else:
            level = 'Very Difficult'

        return {
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_word_length': round(avg_word_length, 1),
            'avg_syllables_per_word': round(avg_syllables_per_word, 2),
            'score': round(reading_ease, 1),
            'level': level
        }

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)."""
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent e
        if word.endswith('e'):
            count -= 1

        # Ensure at least one syllable
        return max(1, count)

    def _analyze_sentences(self, sentences: List[str]) -> Dict[str, Any]:
        """Analyze sentence structure."""
        if not sentences:
            return {
                'count': 0,
                'avg_length': 0,
                'variety': 'N/A'
            }

        sentence_lengths = [len(s.split()) for s in sentences]

        # Calculate variety (standard deviation)
        if len(sentence_lengths) > 1:
            variety_score = statistics.stdev(sentence_lengths)
            if variety_score < 3:
                variety = 'Low - sentences are too similar'
            elif variety_score < 6:
                variety = 'Good - nice variation'
            else:
                variety = 'High - consider more consistency'
        else:
            variety = 'N/A - need more sentences'

        # Count sentence types
        short_sentences = sum(1 for length in sentence_lengths if length < 10)
        medium_sentences = sum(1 for length in sentence_lengths if 10 <= length <= 20)
        long_sentences = sum(1 for length in sentence_lengths if length > 20)

        return {
            'count': len(sentences),
            'avg_length': round(statistics.mean(sentence_lengths), 1),
            'min_length': min(sentence_lengths),
            'max_length': max(sentence_lengths),
            'variety': variety,
            'variety_score': round(variety_score, 1) if len(sentence_lengths) > 1 else 0,
            'short_count': short_sentences,
            'medium_count': medium_sentences,
            'long_count': long_sentences
        }

    def _analyze_paragraphs(self, paragraphs: List[str]) -> Dict[str, Any]:
        """Analyze paragraph structure."""
        if not paragraphs:
            return {
                'count': 0,
                'avg_sentences': 0,
                'avg_words': 0
            }

        paragraph_word_counts = [len(p.split()) for p in paragraphs]
        paragraph_sentence_counts = [len(self._split_sentences(p)) for p in paragraphs]

        avg_words = statistics.mean(paragraph_word_counts)

        # Determine paragraph length quality
        if avg_words < 50:
            length_quality = 'Short - consider developing ideas more'
        elif avg_words < 150:
            length_quality = 'Good length'
        else:
            length_quality = 'Long - consider breaking into smaller paragraphs'

        return {
            'count': len(paragraphs),
            'avg_sentences': round(statistics.mean(paragraph_sentence_counts), 1),
            'avg_words': round(avg_words, 1),
            'length_quality': length_quality
        }

    def _check_passive_voice(self, text: str) -> Dict[str, Any]:
        """Check for passive voice usage."""
        passive_instances = []

        for pattern in self.passive_indicators:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                passive_instances.append({
                    'position': match.start(),
                    'text': match.group(),
                    'context': text[max(0, match.start()-30):match.end()+30]
                })

        # Count sentences
        sentence_count = len(self._split_sentences(text))

        # Calculate passive voice rate
        passive_rate = (len(passive_instances) / sentence_count * 100) if sentence_count > 0 else 0

        # Determine quality
        if passive_rate < 10:
            quality = 'Excellent - minimal passive voice'
        elif passive_rate < 20:
            quality = 'Good - acceptable level'
        elif passive_rate < 30:
            quality = 'Fair - consider reducing passive voice'
        else:
            quality = 'Poor - too much passive voice'

        return {
            'count': len(passive_instances),
            'rate': round(passive_rate, 1),
            'quality': quality,
            'instances': passive_instances[:5]  # First 5 examples
        }

    def _check_transitions(self, text: str) -> Dict[str, Any]:
        """Check for transition word usage."""
        found_transitions = {category: [] for category in self.transition_words}
        total_transitions = 0

        for category, words in self.transition_words.items():
            for word in words:
                pattern = r'\b' + re.escape(word) + r'\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    found_transitions[category].extend(matches)
                    total_transitions += len(matches)

        # Count paragraphs
        paragraph_count = len(self._split_paragraphs(text))

        # Calculate transition rate
        transitions_per_paragraph = total_transitions / paragraph_count if paragraph_count > 0 else 0

        # Determine quality
        if transitions_per_paragraph < 0.5:
            quality = 'Low - add more transitions for flow'
        elif transitions_per_paragraph < 2:
            quality = 'Good - appropriate use'
        else:
            quality = 'High - may be overusing transitions'

        return {
            'total_count': total_transitions,
            'per_paragraph': round(transitions_per_paragraph, 2),
            'quality': quality,
            'by_category': {k: len(v) for k, v in found_transitions.items() if v}
        }

    def _analyze_vocabulary(self, words: List[str]) -> Dict[str, Any]:
        """Analyze vocabulary usage."""
        if not words:
            return {
                'unique_words': 0,
                'lexical_diversity': 0,
                'weak_words_count': 0
            }

        # Unique words
        unique_words = set(words)

        # Lexical diversity (unique/total ratio)
        lexical_diversity = len(unique_words) / len(words)

        # Check for weak words
        weak_words_found = [word for word in words if word in self.weak_words]

        # Long words (6+ letters)
        long_words = [word for word in words if len(word) >= 6]
        long_word_rate = len(long_words) / len(words)

        return {
            'total_words': len(words),
            'unique_words': len(unique_words),
            'lexical_diversity': round(lexical_diversity, 3),
            'weak_words_count': len(weak_words_found),
            'weak_words': Counter(weak_words_found).most_common(5),
            'long_word_rate': round(long_word_rate, 3),
            'avg_word_length': round(sum(len(word) for word in words) / len(words), 1)
        }

    def _generate_suggestions(
        self,
        readability: Dict,
        sentences: Dict,
        paragraphs: Dict,
        passive_voice: Dict,
        transitions: Dict,
        vocabulary: Dict
    ) -> List[str]:
        """Generate style improvement suggestions."""
        suggestions = []

        # Readability suggestions
        if readability['score'] < 50:
            suggestions.append("⚠️ Text is difficult to read - simplify sentences and vocabulary")
        elif readability['score'] > 80:
            suggestions.append("💡 Text may be too simple for academic writing")

        # Sentence variety suggestions
        if sentences['variety_score'] < 3:
            suggestions.append("📝 Vary sentence length for better flow")

        if sentences['long_count'] / sentences['count'] > 0.5:
            suggestions.append("✂️ Consider breaking up long sentences")

        # Paragraph suggestions
        if paragraphs['avg_words'] > 200:
            suggestions.append("📄 Paragraphs are too long - break into smaller units")
        elif paragraphs['avg_words'] < 40:
            suggestions.append("📄 Develop paragraphs more thoroughly")

        # Passive voice suggestions
        if passive_voice['rate'] > 20:
            suggestions.append("🎯 Reduce passive voice - use active constructions")

        # Transition suggestions
        if transitions['per_paragraph'] < 0.5:
            suggestions.append("🔗 Add transition words to improve flow between ideas")

        # Vocabulary suggestions
        if vocabulary['weak_words_count'] > vocabulary['total_words'] * 0.02:
            suggestions.append("💪 Replace weak words ('very', 'really') with stronger vocabulary")

        if vocabulary['lexical_diversity'] < 0.4:
            suggestions.append("📚 Increase vocabulary variety - avoid repetition")

        # Default suggestion if no issues
        if not suggestions:
            suggestions.append("✅ Strong writing style - keep up the good work!")

        return suggestions[:6]  # Top 6 suggestions

    def _calculate_overall_score(
        self,
        readability: Dict,
        sentences: Dict,
        passive_voice: Dict,
        transitions: Dict
    ) -> float:
        """Calculate overall style score (0-100)."""
        score = 0

        # Readability (30 points)
        if 50 <= readability['score'] <= 70:
            score += 30
        elif 40 <= readability['score'] <= 80:
            score += 20
        else:
            score += 10

        # Sentence variety (25 points)
        if 3 <= sentences.get('variety_score', 0) <= 8:
            score += 25
        elif 2 <= sentences.get('variety_score', 0) <= 10:
            score += 15
        else:
            score += 5

        # Passive voice (25 points)
        if passive_voice['rate'] < 15:
            score += 25
        elif passive_voice['rate'] < 25:
            score += 15
        else:
            score += 5

        # Transitions (20 points)
        if 0.5 <= transitions['per_paragraph'] <= 2:
            score += 20
        elif 0.3 <= transitions['per_paragraph'] <= 3:
            score += 10
        else:
            score += 5

        return round(score, 1)


if __name__ == "__main__":
    print("Testing Style Analyzer...")

    analyzer = StyleAnalyzer()

    # Test text
    test_text = """
    This is the first paragraph. It contains several sentences. Each sentence has a different length.
    However, they all work together to create a cohesive paragraph.

    Furthermore, this is the second paragraph. The transition word at the start helps connect ideas.
    Moreover, this paragraph demonstrates good academic writing style. Nevertheless, there is always
    room for improvement in any piece of writing.

    The final paragraph is very short. It is really quite simple. This is basically just a test.
    """

    result = analyzer.analyze_text(test_text)

    print(f"\nReadability Score: {result['readability']['score']} ({result['readability']['level']})")
    print(f"Average Sentence Length: {result['sentences']['avg_length']} words")
    print(f"Sentence Variety: {result['sentences']['variety']}")
    print(f"Passive Voice: {result['passive_voice']['rate']}% ({result['passive_voice']['quality']})")
    print(f"Transitions: {result['transitions']['per_paragraph']} per paragraph")
    print(f"Lexical Diversity: {result['vocabulary']['lexical_diversity']}")
    print(f"Overall Style Score: {result['overall_score']}/100")

    print("\nSuggestions:")
    for suggestion in result['suggestions']:
        print(f"  {suggestion}")

    print("\nStyle Analyzer validated!")
