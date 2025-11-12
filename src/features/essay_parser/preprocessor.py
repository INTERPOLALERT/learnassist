"""
Academic Command Center - Essay Parser - Text Preprocessor
Cleans and normalizes raw essay instruction text.
"""

import re
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import unicodedata

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TextPreprocessor:
    """
    Preprocesses raw essay instruction text.

    Features:
    - HTML tag stripping (preserves structure)
    - Whitespace normalization
    - OCR error correction
    - Unicode normalization
    - Bullet/numbering preservation
    """

    # Common OCR errors to fix
    OCR_CORRECTIONS = {
        # Number/Letter confusion
        r'\bO(?=\d)': '0',  # O followed by digit -> 0
        r'(?<=\d)O\b': '0',  # O preceded by digit -> 0
        r'\bl(?=\d)': '1',  # lowercase L before digit -> 1
        r'(?<=\d)l\b': '1',  # lowercase L after digit -> 1
        r'\bS0': 'SO',      # S-zero -> S-O
        r'0utput': 'Output',
        r'0ne': 'One',

        # Common word errors
        r'\btbe\b': 'the',
        r'\baod\b': 'and',
        r'\bwitb\b': 'with',
        r'\bfrom\s+tbe\b': 'from the',
        r'\bin\s+tbe\b': 'in the',

        # Spacing errors
        r'(\w)- (\w)': r'\1\2',  # Remove hyphen with space
        r'\s+,': ',',            # Space before comma
        r'\s+\.': '.',           # Space before period
        r'\(\s+': '(',           # Space after opening paren
        r'\s+\)': ')',           # Space before closing paren
    }

    def __init__(self):
        """Initialize preprocessor."""
        pass

    def preprocess(
        self,
        raw_text: str,
        source_type: str = 'text'  # text, html, pdf, docx
    ) -> Dict[str, Any]:
        """
        Preprocess raw instruction text.

        Args:
            raw_text: Raw instruction text
            source_type: Source of text (text, html, pdf, docx)

        Returns:
            Dictionary with processed text and metadata
        """
        if not raw_text or not raw_text.strip():
            return {
                'success': False,
                'error': 'Empty input text',
                'original': raw_text,
                'processed': ''
            }

        logger.info(f"Preprocessing {len(raw_text)} characters from {source_type}")

        original_text = raw_text
        processed_text = raw_text

        # Step 1: Strip HTML if present
        if source_type == 'html' or self._contains_html(raw_text):
            processed_text = self._strip_html(processed_text)
            logger.debug("HTML tags stripped")

        # Step 2: Normalize Unicode
        processed_text = self._normalize_unicode(processed_text)
        logger.debug("Unicode normalized")

        # Step 3: Fix OCR errors
        processed_text = self._fix_ocr_errors(processed_text)
        logger.debug("OCR errors corrected")

        # Step 4: Normalize whitespace
        processed_text = self._normalize_whitespace(processed_text)
        logger.debug("Whitespace normalized")

        # Step 5: Preserve structure markers
        processed_text = self._preserve_structure(processed_text)
        logger.debug("Structure preserved")

        # Calculate statistics
        stats = self._calculate_stats(original_text, processed_text)

        return {
            'success': True,
            'original': original_text,
            'processed': processed_text,
            'stats': stats,
            'source_type': source_type
        }

    def _contains_html(self, text: str) -> bool:
        """Check if text contains HTML tags."""
        html_pattern = r'<[^>]+>'
        return bool(re.search(html_pattern, text))

    def _strip_html(self, html_text: str) -> str:
        """
        Strip HTML tags while preserving structure.

        Args:
            html_text: HTML formatted text

        Returns:
            Plain text with preserved structure
        """
        try:
            soup = BeautifulSoup(html_text, 'html.parser')

            # Convert common HTML elements to text equivalents
            # Headers
            for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                header.insert_before('\n\n')
                header.insert_after('\n')

            # Paragraphs
            for p in soup.find_all('p'):
                p.insert_after('\n\n')

            # Line breaks
            for br in soup.find_all('br'):
                br.replace_with('\n')

            # Lists
            for ul in soup.find_all(['ul', 'ol']):
                ul.insert_before('\n')
                ul.insert_after('\n')

            for li in soup.find_all('li'):
                li.insert_before('• ')
                li.insert_after('\n')

            # Bold/italic (preserve emphasis markers)
            for strong in soup.find_all(['strong', 'b']):
                text = strong.get_text()
                strong.replace_with(f"**{text}**")

            for em in soup.find_all(['em', 'i']):
                text = em.get_text()
                em.replace_with(f"*{text}*")

            # Get text
            text = soup.get_text()

            return text

        except Exception as e:
            logger.warning(f"HTML parsing failed: {e}, returning stripped text")
            # Fallback: simple tag removal
            return re.sub(r'<[^>]+>', ' ', html_text)

    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters.

        Args:
            text: Text with potential Unicode issues

        Returns:
            Normalized text
        """
        # Normalize to NFC (Canonical Composition)
        text = unicodedata.normalize('NFC', text)

        # Replace common Unicode punctuation with ASCII
        replacements = {
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...',# Ellipsis
            '\xa0': ' ',    # Non-breaking space
            '\u00a0': ' ',  # Another non-breaking space
        }

        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)

        return text

    def _fix_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR errors.

        Args:
            text: Text with potential OCR errors

        Returns:
            Corrected text
        """
        for pattern, replacement in self.OCR_CORRECTIONS.items():
            text = re.sub(pattern, replacement, text)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace.

        Args:
            text: Text with irregular whitespace

        Returns:
            Normalized text
        """
        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Remove spaces at line ends
        text = re.sub(r' +\n', '\n', text)

        # Remove spaces at line starts (but preserve indentation structure)
        # Only remove if more than 4 spaces (likely accidental)
        text = re.sub(r'\n {5,}', '\n    ', text)

        # Collapse multiple spaces to single space
        text = re.sub(r' {2,}', ' ', text)

        # Collapse multiple newlines (but keep paragraph breaks)
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        # Trim leading/trailing whitespace
        text = text.strip()

        return text

    def _preserve_structure(self, text: str) -> str:
        """
        Preserve and enhance structural elements.

        Args:
            text: Text with structure markers

        Returns:
            Text with preserved structure
        """
        # Ensure numbered lists have consistent format
        # Match patterns like "1.", "1)", "(1)", "1 -", etc.
        text = re.sub(r'^(\d+)[.)]', r'\1.', text, flags=re.MULTILINE)

        # Ensure bullet points are consistent
        # Convert -, *, +, > to •
        text = re.sub(r'^[\-\*\+>]\s+', '• ', text, flags=re.MULTILINE)

        # Preserve section headers (all caps followed by colon or newline)
        # Add extra newline before section headers
        text = re.sub(
            r'\n([A-Z][A-Z\s]+:)',
            r'\n\n\1',
            text
        )

        return text

    def _calculate_stats(
        self,
        original: str,
        processed: str
    ) -> Dict[str, Any]:
        """
        Calculate preprocessing statistics.

        Args:
            original: Original text
            processed: Processed text

        Returns:
            Statistics dictionary
        """
        return {
            'original_length': len(original),
            'processed_length': len(processed),
            'characters_removed': len(original) - len(processed),
            'original_lines': original.count('\n') + 1,
            'processed_lines': processed.count('\n') + 1,
            'contains_bullets': '•' in processed,
            'contains_numbers': bool(re.search(r'^\d+\.', processed, re.MULTILINE)),
            'contains_sections': bool(re.search(r'^[A-Z][A-Z\s]+:', processed, re.MULTILINE))
        }

    def clean_for_ai(self, text: str) -> str:
        """
        Additional cleaning for AI processing.

        Args:
            text: Preprocessed text

        Returns:
            AI-ready text
        """
        # Remove excessive formatting
        cleaned = text

        # Remove markdown-style bold/italic
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)

        # Ensure single space after punctuation
        cleaned = re.sub(r'([.!?])\s+', r'\1 ', cleaned)

        # Remove any remaining control characters
        cleaned = ''.join(char for char in cleaned if unicodedata.category(char)[0] != 'C' or char in '\n\t')

        return cleaned.strip()


if __name__ == "__main__":
    # Test preprocessor
    print("Testing Text Preprocessor...")

    preprocessor = TextPreprocessor()

    # Test HTML stripping
    html_text = """
    <h1>Essay 1: Cultural Analysis</h1>
    <p>Write a <strong>2500-word</strong> essay analyzing the impact of postmodernism.</p>
    <ul>
        <li>Use at least 5 sources</li>
        <li>Follow Harvard referencing</li>
    </ul>
    """

    result = preprocessor.preprocess(html_text, source_type='html')
    print("\n--- HTML Test ---")
    print(f"Success: {result['success']}")
    print(f"Processed:\n{result['processed'][:200]}...")
    print(f"Stats: {result['stats']}")

    # Test OCR errors
    ocr_text = "Write a 25OO-word essay about tbe influence of postmodernism. Submit by Dec ember 15th."

    result = preprocessor.preprocess(ocr_text, source_type='pdf')
    print("\n--- OCR Test ---")
    print(f"Original: {ocr_text}")
    print(f"Processed: {result['processed']}")

    print("\nPreprocessor test completed!")
