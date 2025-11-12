"""
Academic Command Center - Version Control - Diff Viewer
Provides detailed text comparison and change visualization.
"""

import logging
import difflib
from typing import Dict, Any, List, Tuple, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ChangeType:
    """Change type constants."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class DiffViewer:
    """
    Provides text comparison and diff visualization.

    Features:
    - Line-by-line comparison
    - Word-level differences
    - Change statistics
    - Side-by-side diff
    - Unified diff format
    - Change highlighting
    """

    def __init__(self):
        """Initialize diff viewer."""
        logger.info("Diff viewer initialized")

    def compare_texts(
        self,
        text1: str,
        text2: str,
        context_lines: int = 3
    ) -> Dict[str, Any]:
        """
        Compare two texts and generate detailed diff.

        Args:
            text1: Original text
            text2: Modified text
            context_lines: Number of context lines around changes

        Returns:
            Detailed comparison results
        """
        try:
            # Split into lines
            lines1 = text1.split('\n')
            lines2 = text2.split('\n')

            # Generate unified diff
            unified_diff = list(difflib.unified_diff(
                lines1,
                lines2,
                lineterm='',
                n=context_lines
            ))

            # Generate side-by-side comparison
            side_by_side = self._generate_side_by_side(lines1, lines2)

            # Calculate statistics
            stats = self._calculate_diff_stats(lines1, lines2)

            # Get change summary
            changes = self._extract_changes(lines1, lines2)

            return {
                'success': True,
                'unified_diff': unified_diff,
                'side_by_side': side_by_side,
                'statistics': stats,
                'changes': changes
            }

        except Exception as e:
            logger.error(f"Failed to compare texts: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_side_by_side(
        self,
        lines1: List[str],
        lines2: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate side-by-side comparison.

        Args:
            lines1: Original lines
            lines2: Modified lines

        Returns:
            List of line pairs with change types
        """
        differ = difflib.SequenceMatcher(None, lines1, lines2)
        result = []

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'equal':
                # Unchanged lines
                for i in range(i1, i2):
                    result.append({
                        'type': ChangeType.UNCHANGED,
                        'line_number_old': i + 1,
                        'line_number_new': j1 + (i - i1) + 1,
                        'content_old': lines1[i],
                        'content_new': lines2[j1 + (i - i1)]
                    })

            elif tag == 'delete':
                # Removed lines
                for i in range(i1, i2):
                    result.append({
                        'type': ChangeType.REMOVED,
                        'line_number_old': i + 1,
                        'line_number_new': None,
                        'content_old': lines1[i],
                        'content_new': ''
                    })

            elif tag == 'insert':
                # Added lines
                for j in range(j1, j2):
                    result.append({
                        'type': ChangeType.ADDED,
                        'line_number_old': None,
                        'line_number_new': j + 1,
                        'content_old': '',
                        'content_new': lines2[j]
                    })

            elif tag == 'replace':
                # Modified lines (both removed and added)
                max_lines = max(i2 - i1, j2 - j1)

                for k in range(max_lines):
                    old_line = lines1[i1 + k] if (i1 + k) < i2 else ''
                    new_line = lines2[j1 + k] if (j1 + k) < j2 else ''

                    old_line_num = (i1 + k + 1) if (i1 + k) < i2 else None
                    new_line_num = (j1 + k + 1) if (j1 + k) < j2 else None

                    # Determine change type
                    if old_line and new_line:
                        change_type = ChangeType.MODIFIED
                    elif old_line:
                        change_type = ChangeType.REMOVED
                    else:
                        change_type = ChangeType.ADDED

                    result.append({
                        'type': change_type,
                        'line_number_old': old_line_num,
                        'line_number_new': new_line_num,
                        'content_old': old_line,
                        'content_new': new_line,
                        'word_diff': self._word_level_diff(old_line, new_line) if change_type == ChangeType.MODIFIED else None
                    })

        return result

    def _word_level_diff(self, line1: str, line2: str) -> Dict[str, List[Tuple[str, str]]]:
        """
        Generate word-level differences for modified lines.

        Args:
            line1: Original line
            line2: Modified line

        Returns:
            Word-level changes
        """
        words1 = line1.split()
        words2 = line2.split()

        differ = difflib.SequenceMatcher(None, words1, words2)
        added_words = []
        removed_words = []

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'delete':
                removed_words.extend([(word, 'removed') for word in words1[i1:i2]])
            elif tag == 'insert':
                added_words.extend([(word, 'added') for word in words2[j1:j2]])
            elif tag == 'replace':
                removed_words.extend([(word, 'removed') for word in words1[i1:i2]])
                added_words.extend([(word, 'added') for word in words2[j1:j2]])

        return {
            'added': added_words,
            'removed': removed_words
        }

    def _calculate_diff_stats(
        self,
        lines1: List[str],
        lines2: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate statistics about the differences.

        Args:
            lines1: Original lines
            lines2: Modified lines

        Returns:
            Statistics dictionary
        """
        differ = difflib.SequenceMatcher(None, lines1, lines2)

        lines_added = 0
        lines_removed = 0
        lines_modified = 0
        lines_unchanged = 0

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'equal':
                lines_unchanged += (i2 - i1)
            elif tag == 'delete':
                lines_removed += (i2 - i1)
            elif tag == 'insert':
                lines_added += (j2 - j1)
            elif tag == 'replace':
                lines_modified += max(i2 - i1, j2 - j1)

        # Word count changes
        words1 = ' '.join(lines1).split()
        words2 = ' '.join(lines2).split()
        words_added = len(words2) - len(words1)

        # Character count changes
        chars1 = len(''.join(lines1))
        chars2 = len(''.join(lines2))
        chars_added = chars2 - chars1

        # Similarity ratio
        similarity = differ.ratio()

        return {
            'lines': {
                'total_old': len(lines1),
                'total_new': len(lines2),
                'added': lines_added,
                'removed': lines_removed,
                'modified': lines_modified,
                'unchanged': lines_unchanged
            },
            'words': {
                'total_old': len(words1),
                'total_new': len(words2),
                'diff': words_added
            },
            'characters': {
                'total_old': chars1,
                'total_new': chars2,
                'diff': chars_added
            },
            'similarity_percent': round(similarity * 100, 1)
        }

    def _extract_changes(
        self,
        lines1: List[str],
        lines2: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract individual changes as a list.

        Args:
            lines1: Original lines
            lines2: Modified lines

        Returns:
            List of changes
        """
        differ = difflib.SequenceMatcher(None, lines1, lines2)
        changes = []

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'delete':
                changes.append({
                    'type': ChangeType.REMOVED,
                    'line_start': i1 + 1,
                    'line_end': i2,
                    'content': '\n'.join(lines1[i1:i2]),
                    'line_count': i2 - i1
                })

            elif tag == 'insert':
                changes.append({
                    'type': ChangeType.ADDED,
                    'line_start': j1 + 1,
                    'line_end': j2,
                    'content': '\n'.join(lines2[j1:j2]),
                    'line_count': j2 - j1
                })

            elif tag == 'replace':
                changes.append({
                    'type': ChangeType.MODIFIED,
                    'line_start_old': i1 + 1,
                    'line_end_old': i2,
                    'line_start_new': j1 + 1,
                    'line_end_new': j2,
                    'content_old': '\n'.join(lines1[i1:i2]),
                    'content_new': '\n'.join(lines2[j1:j2]),
                    'line_count': max(i2 - i1, j2 - j1)
                })

        return changes

    def generate_html_diff(
        self,
        text1: str,
        text2: str,
        title1: str = "Original",
        title2: str = "Modified"
    ) -> str:
        """
        Generate HTML-formatted side-by-side diff.

        Args:
            text1: Original text
            text2: Modified text
            title1: Title for original text
            title2: Title for modified text

        Returns:
            HTML string
        """
        try:
            lines1 = text1.split('\n')
            lines2 = text2.split('\n')

            differ = difflib.HtmlDiff()
            html_diff = differ.make_file(
                lines1,
                lines2,
                fromdesc=title1,
                todesc=title2,
                context=True,
                numlines=3
            )

            return html_diff

        except Exception as e:
            logger.error(f"Failed to generate HTML diff: {e}")
            return f"<html><body>Error generating diff: {e}</body></html>"

    def get_change_summary(self, stats: Dict[str, Any]) -> str:
        """
        Generate human-readable change summary.

        Args:
            stats: Statistics from _calculate_diff_stats

        Returns:
            Summary string
        """
        lines_stats = stats['lines']
        words_stats = stats['words']
        similarity = stats['similarity_percent']

        parts = []

        if lines_stats['added'] > 0:
            parts.append(f"+{lines_stats['added']} lines")
        if lines_stats['removed'] > 0:
            parts.append(f"-{lines_stats['removed']} lines")
        if lines_stats['modified'] > 0:
            parts.append(f"~{lines_stats['modified']} modified")

        if words_stats['diff'] != 0:
            sign = '+' if words_stats['diff'] > 0 else ''
            parts.append(f"{sign}{words_stats['diff']} words")

        if not parts:
            return "No changes detected"

        summary = ', '.join(parts)
        summary += f" ({similarity}% similar)"

        return summary


if __name__ == "__main__":
    print("Testing Diff Viewer...")

    viewer = DiffViewer()

    # Test texts
    text1 = """This is the first paragraph of the essay.
It contains several sentences.
Some of these sentences will be modified.

This is the second paragraph.
It will remain mostly unchanged."""

    text2 = """This is the first paragraph of the essay.
It contains multiple sentences now.
Some of these sentences have been updated.
And this is a new line!

This is the second paragraph.
It will remain mostly unchanged."""

    # Test compare texts
    result = viewer.compare_texts(text1, text2)

    if result['success']:
        print("\n=== Comparison Statistics ===")
        stats = result['statistics']
        print(f"Lines added: {stats['lines']['added']}")
        print(f"Lines removed: {stats['lines']['removed']}")
        print(f"Lines modified: {stats['lines']['modified']}")
        print(f"Words diff: {stats['words']['diff']}")
        print(f"Similarity: {stats['similarity_percent']}%")

        print("\n=== Change Summary ===")
        summary = viewer.get_change_summary(stats)
        print(summary)

        print("\n=== Changes Detected ===")
        for i, change in enumerate(result['changes'], 1):
            print(f"{i}. {change['type']}: {change.get('line_count', 0)} lines")

        print("\n=== Side-by-Side Preview (first 5 lines) ===")
        for line_data in result['side_by_side'][:5]:
            change_type = line_data['type']
            if change_type == ChangeType.ADDED:
                print(f"  [+] {line_data['content_new']}")
            elif change_type == ChangeType.REMOVED:
                print(f"  [-] {line_data['content_old']}")
            elif change_type == ChangeType.MODIFIED:
                print(f"  [~] {line_data['content_new']}")

    print("\nDiff Viewer validated!")
