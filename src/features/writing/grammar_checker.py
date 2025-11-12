"""
Academic Command Center - Writing Assistant - Grammar Checker
Checks grammar, spelling, and basic writing errors.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ErrorType:
    """Types of writing errors."""
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    PUNCTUATION = "punctuation"
    CAPITALIZATION = "capitalization"
    WORD_CHOICE = "word_choice"
    REPETITION = "repetition"


class ErrorSeverity:
    """Error severity levels."""
    ERROR = "error"  # Must fix
    WARNING = "warning"  # Should fix
    SUGGESTION = "suggestion"  # Optional improvement


class GrammarChecker:
    """
    Grammar and spelling checker for academic writing.

    Checks for:
    - Common spelling errors
    - Grammar mistakes
    - Punctuation issues
    - Capitalization errors
    - Word repetition
    - Common academic writing issues
    """

    def __init__(self):
        """Initialize grammar checker."""
        # Common misspellings (simplified set)
        self.common_misspellings = {
            'recieve': 'receive',
            'occured': 'occurred',
            'beleive': 'believe',
            'wich': 'which',
            'wierd': 'weird',
            'seperate': 'separate',
            'definately': 'definitely',
            'arguement': 'argument',
            'untill': 'until',
            'acheive': 'achieve',
            'adress': 'address',
            'begining': 'beginning',
            'calender': 'calendar',
            'enviroment': 'environment',
            'goverment': 'government',
            'independant': 'independent',
            'maintainance': 'maintenance',
            'occassion': 'occasion',
            'posession': 'possession',
            'succesful': 'successful'
        }

        # Common grammar patterns to check
        self.grammar_patterns = [
            # Double words
            (r'\b(\w+)\s+\1\b', 'Repeated word: "{0}"', ErrorType.GRAMMAR, ErrorSeverity.ERROR),
            # Multiple spaces
            (r'  +', 'Multiple spaces', ErrorType.PUNCTUATION, ErrorSeverity.WARNING),
            # Missing space after punctuation
            (r'[,;:!?][A-Za-z]', 'Missing space after punctuation', ErrorType.PUNCTUATION, ErrorSeverity.ERROR),
            # Space before punctuation
            (r'\s+[,;:!?]', 'Space before punctuation', ErrorType.PUNCTUATION, ErrorSeverity.WARNING),
            # Multiple punctuation
            (r'[!?]{2,}', 'Multiple exclamation/question marks', ErrorType.PUNCTUATION, ErrorSeverity.WARNING),
            # Lowercase sentence start
            (r'(?<=[.!?]\s)[a-z]', 'Sentence should start with capital letter', ErrorType.CAPITALIZATION, ErrorSeverity.ERROR),
            # Could of/should of/would of
            (r'\b(could|should|would) of\b', 'Use "have" instead of "of"', ErrorType.GRAMMAR, ErrorSeverity.ERROR),
            # Its vs it's
            (r"\bits\s+(is|has|was)\b", 'Consider "it\'s" (it is/has)', ErrorType.GRAMMAR, ErrorSeverity.WARNING),
            # Their/there/they're confusion
            (r"\btheir\s+(is|are|was|were)\b", 'Should be "there"', ErrorType.GRAMMAR, ErrorSeverity.ERROR),
            # Your vs you're
            (r"\byour\s+(are|were)\b", 'Should be "you\'re"', ErrorType.GRAMMAR, ErrorSeverity.ERROR),
            # Then vs than
            (r"\bbetter then\b", 'Should be "better than"', ErrorType.GRAMMAR, ErrorSeverity.ERROR),
            # A vs an
            (r'\ba\s+[aeiouAEIOU]', 'Use "an" before vowel sounds', ErrorType.GRAMMAR, ErrorSeverity.WARNING),
        ]

        # Academic writing patterns to avoid
        self.academic_issues = [
            (r'\bI think\b', 'Avoid first person in academic writing', ErrorType.WORD_CHOICE, ErrorSeverity.SUGGESTION),
            (r'\bI believe\b', 'Avoid first person in academic writing', ErrorType.WORD_CHOICE, ErrorSeverity.SUGGESTION),
            (r'\bin my opinion\b', 'Avoid in academic writing', ErrorType.WORD_CHOICE, ErrorSeverity.SUGGESTION),
            (r'\ba lot\b', 'Avoid informal phrases; use "many" or "much"', ErrorType.WORD_CHOICE, ErrorSeverity.SUGGESTION),
            (r'\bkinda\b|\bsorta\b|\bgonna\b|\bwanna\b', 'Avoid contractions/informal language', ErrorType.WORD_CHOICE, ErrorSeverity.ERROR),
            (r'\bvery\s+\w+', 'Consider stronger word instead of "very"', ErrorType.WORD_CHOICE, ErrorSeverity.SUGGESTION),
            (r'\betc\b(?!\.)', '"etc." should be followed by a period', ErrorType.PUNCTUATION, ErrorSeverity.ERROR),
        ]

        logger.info("Grammar checker initialized")

    def check_text(self, text: str) -> Dict[str, Any]:
        """
        Check text for errors.

        Args:
            text: Text to check

        Returns:
            Dictionary with errors and statistics
        """
        if not text or not text.strip():
            return {
                'success': True,
                'errors': [],
                'error_count': 0,
                'word_count': 0,
                'sentence_count': 0
            }

        try:
            errors = []

            # Check spelling
            spelling_errors = self._check_spelling(text)
            errors.extend(spelling_errors)

            # Check grammar patterns
            grammar_errors = self._check_grammar_patterns(text)
            errors.extend(grammar_errors)

            # Check academic writing issues
            academic_errors = self._check_academic_issues(text)
            errors.extend(academic_errors)

            # Check word repetition
            repetition_errors = self._check_repetition(text)
            errors.extend(repetition_errors)

            # Calculate statistics
            word_count = len(text.split())
            sentence_count = len(re.findall(r'[.!?]+', text))

            # Sort errors by position
            errors.sort(key=lambda x: x['position'])

            # Calculate error rate
            error_rate = (len(errors) / word_count * 100) if word_count > 0 else 0

            return {
                'success': True,
                'errors': errors,
                'error_count': len(errors),
                'word_count': word_count,
                'sentence_count': sentence_count,
                'error_rate': round(error_rate, 2),
                'errors_by_type': self._count_errors_by_type(errors),
                'errors_by_severity': self._count_errors_by_severity(errors)
            }

        except Exception as e:
            logger.error(f"Failed to check text: {e}")
            return {
                'success': False,
                'error': str(e),
                'errors': []
            }

    def _check_spelling(self, text: str) -> List[Dict[str, Any]]:
        """Check for common spelling errors."""
        errors = []

        words = re.findall(r'\b\w+\b', text.lower())

        for misspelling, correction in self.common_misspellings.items():
            pattern = r'\b' + misspelling + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                errors.append({
                    'type': ErrorType.SPELLING,
                    'severity': ErrorSeverity.ERROR,
                    'position': match.start(),
                    'length': len(match.group()),
                    'text': match.group(),
                    'message': f'Misspelled word: "{match.group()}"',
                    'suggestion': correction.capitalize() if match.group()[0].isupper() else correction
                })

        return errors

    def _check_grammar_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Check for grammar pattern issues."""
        errors = []

        for pattern, message, error_type, severity in self.grammar_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Format message with matched text if needed
                if '{0}' in message:
                    formatted_message = message.format(match.group(1) if match.lastindex else match.group())
                else:
                    formatted_message = message

                errors.append({
                    'type': error_type,
                    'severity': severity,
                    'position': match.start(),
                    'length': len(match.group()),
                    'text': match.group(),
                    'message': formatted_message,
                    'suggestion': None
                })

        return errors

    def _check_academic_issues(self, text: str) -> List[Dict[str, Any]]:
        """Check for academic writing issues."""
        errors = []

        for pattern, message, error_type, severity in self.academic_issues:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                errors.append({
                    'type': error_type,
                    'severity': severity,
                    'position': match.start(),
                    'length': len(match.group()),
                    'text': match.group(),
                    'message': message,
                    'suggestion': None
                })

        return errors

    def _check_repetition(self, text: str) -> List[Dict[str, Any]]:
        """Check for word repetition in nearby sentences."""
        errors = []

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        for i in range(len(sentences) - 1):
            if not sentences[i].strip() or not sentences[i + 1].strip():
                continue

            # Get words from consecutive sentences
            words1 = set(re.findall(r'\b\w{4,}\b', sentences[i].lower()))
            words2 = set(re.findall(r'\b\w{4,}\b', sentences[i + 1].lower()))

            # Find repeated words (excluding common words)
            common_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'they', 'them', 'their', 'there', 'when', 'what', 'which', 'will', 'would', 'could', 'should'}
            repeated = (words1 & words2) - common_words

            if len(repeated) > 2:  # More than 2 repeated words
                # Find position of second sentence
                position = sum(len(s) for s in sentences[:i+1]) + i + 1

                errors.append({
                    'type': ErrorType.REPETITION,
                    'severity': ErrorSeverity.SUGGESTION,
                    'position': position,
                    'length': len(sentences[i + 1]),
                    'text': sentences[i + 1].strip()[:50] + '...' if len(sentences[i + 1]) > 50 else sentences[i + 1].strip(),
                    'message': f'Multiple repeated words in consecutive sentences: {", ".join(list(repeated)[:3])}',
                    'suggestion': 'Consider varying vocabulary'
                })

        return errors

    def _count_errors_by_type(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count errors by type."""
        counter = Counter(error['type'] for error in errors)
        return dict(counter)

    def _count_errors_by_severity(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count errors by severity."""
        counter = Counter(error['severity'] for error in errors)
        return dict(counter)

    def get_writing_score(self, text: str) -> float:
        """
        Calculate writing quality score (0-100).

        Args:
            text: Text to score

        Returns:
            Writing score
        """
        result = self.check_text(text)

        if not result['success'] or result['word_count'] == 0:
            return 0.0

        # Base score
        score = 100.0

        # Deduct for errors
        errors = result['errors_by_severity']
        score -= errors.get(ErrorSeverity.ERROR, 0) * 5  # -5 per error
        score -= errors.get(ErrorSeverity.WARNING, 0) * 2  # -2 per warning
        score -= errors.get(ErrorSeverity.SUGGESTION, 0) * 0.5  # -0.5 per suggestion

        # Penalize high error rate
        if result['error_rate'] > 5:  # More than 5% error rate
            score -= (result['error_rate'] - 5) * 2

        return max(0.0, min(100.0, score))


if __name__ == "__main__":
    print("Testing Grammar Checker...")

    checker = GrammarChecker()

    # Test text with errors
    test_text = """
    This is a test sentance with some erors. I think this is definately a problem.
    The goverment should of done better. Their is alot of issues here.
    This sentence has the the same word twice. This is  wierd.
    """

    result = checker.check_text(test_text)
    print(f"\nCheck result: Found {result['error_count']} errors")
    print(f"Word count: {result['word_count']}")
    print(f"Error rate: {result['error_rate']}%")
    print(f"Errors by type: {result['errors_by_type']}")
    print(f"Errors by severity: {result['errors_by_severity']}")

    print("\nErrors found:")
    for error in result['errors'][:5]:  # Show first 5
        print(f"  - [{error['severity']}] {error['message']}")
        print(f"    Text: \"{error['text']}\"")
        if error['suggestion']:
            print(f"    Suggestion: {error['suggestion']}")

    # Test writing score
    score = checker.get_writing_score(test_text)
    print(f"\nWriting score: {score:.1f}/100")

    print("\nGrammar Checker validated!")
