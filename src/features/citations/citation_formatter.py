"""
Academic Command Center - Citations - Citation Formatter
Formats citations in Harvard, APA, and MLA styles.
"""

import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CitationFormatter:
    """
    Formats academic citations in multiple styles.

    Supports:
    - Harvard style
    - APA (American Psychological Association) style
    - MLA (Modern Language Association) style

    For different source types:
    - Books
    - Journal articles
    - Websites
    - Lectures
    - Other sources
    """

    def __init__(self):
        """Initialize citation formatter."""
        logger.info("Citation formatter initialized")

    def format_harvard(self, source_type: str, data: Dict[str, Any]) -> str:
        """
        Format citation in Harvard style.

        Harvard format examples:
        - Book: Author(s) (Year) Title. Edition. Place: Publisher.
        - Journal: Author(s) (Year) 'Article title', Journal Name, volume(issue), pp.pages.
        - Website: Author(s) (Year) Page title. Available at: URL (Accessed: date).

        Args:
            source_type: Type of source
            data: Source data dictionary

        Returns:
            Formatted Harvard citation
        """
        try:
            author = data.get('author', 'Anon.')
            year = data.get('year', 'n.d.')
            title = data.get('title', 'Untitled')

            if source_type == 'book':
                publisher = data.get('publisher', 'Unknown Publisher')
                citation = f"{author} ({year}) {title}. {publisher}."

            elif source_type == 'journal_article':
                publication = data.get('publication', 'Unknown Journal')
                pages = data.get('pages', '')
                pages_str = f", pp.{pages}" if pages else ""
                doi = data.get('doi', '')
                doi_str = f" doi:{doi}" if doi else ""

                citation = f"{author} ({year}) '{title}', {publication}{pages_str}{doi_str}."

            elif source_type == 'website':
                url = data.get('url', '')
                url_str = f" Available at: {url}" if url else ""
                citation = f"{author} ({year}) {title}.{url_str} (Accessed: {self._get_access_date()})."

            elif source_type == 'lecture':
                publication = data.get('publication', 'Lecture')
                citation = f"{author} ({year}) {title}. {publication}."

            else:  # other
                publication = data.get('publication', '')
                pub_str = f" {publication}." if publication else "."
                citation = f"{author} ({year}) {title}{pub_str}"

            return citation

        except Exception as e:
            logger.error(f"Failed to format Harvard citation: {e}")
            return f"Error formatting citation: {str(e)}"

    def format_apa(self, source_type: str, data: Dict[str, Any]) -> str:
        """
        Format citation in APA style.

        APA 7th edition format examples:
        - Book: Author, A. A. (Year). Title of work. Publisher.
        - Journal: Author, A. A. (Year). Title of article. Journal Name, volume(issue), pages. https://doi.org/xxx
        - Website: Author, A. A. (Year, Month Day). Title of page. Site Name. URL

        Args:
            source_type: Type of source
            data: Source data dictionary

        Returns:
            Formatted APA citation
        """
        try:
            author = data.get('author', 'Author, A.')
            year = data.get('year', 'n.d.')
            title = data.get('title', 'Untitled')

            if source_type == 'book':
                publisher = data.get('publisher', 'Unknown Publisher')
                citation = f"{author} ({year}). {title}. {publisher}."

            elif source_type == 'journal_article':
                publication = data.get('publication', 'Unknown Journal')
                pages = data.get('pages', '')
                pages_str = f", {pages}" if pages else ""
                doi = data.get('doi', '')
                doi_str = f" https://doi.org/{doi}" if doi else ""

                # For APA, title is not italicized in journals
                citation = f"{author} ({year}). {title}. {publication}{pages_str}.{doi_str}"

            elif source_type == 'website':
                url = data.get('url', '')
                citation = f"{author} ({year}). {title}. Retrieved from {url}" if url else f"{author} ({year}). {title}."

            elif source_type == 'lecture':
                publication = data.get('publication', 'Lecture')
                citation = f"{author} ({year}). {title} [{publication}]."

            else:  # other
                publication = data.get('publication', '')
                pub_str = f" {publication}." if publication else "."
                citation = f"{author} ({year}). {title}{pub_str}"

            return citation

        except Exception as e:
            logger.error(f"Failed to format APA citation: {e}")
            return f"Error formatting citation: {str(e)}"

    def format_mla(self, source_type: str, data: Dict[str, Any]) -> str:
        """
        Format citation in MLA style.

        MLA 9th edition format examples:
        - Book: Author. Title. Publisher, Year.
        - Journal: Author. "Article Title." Journal Name, vol. X, no. X, Year, pp. X-X.
        - Website: Author. "Page Title." Website Name, Date, URL.

        Args:
            source_type: Type of source
            data: Source data dictionary

        Returns:
            Formatted MLA citation
        """
        try:
            author = data.get('author', 'Anonymous')
            year = data.get('year', 'n.d.')
            title = data.get('title', 'Untitled')

            if source_type == 'book':
                publisher = data.get('publisher', 'Unknown Publisher')
                citation = f"{author}. {title}. {publisher}, {year}."

            elif source_type == 'journal_article':
                publication = data.get('publication', 'Unknown Journal')
                pages = data.get('pages', '')
                pages_str = f", pp. {pages}" if pages else ""

                citation = f'{author}. "{title}." {publication}, {year}{pages_str}.'

            elif source_type == 'website':
                url = data.get('url', '')
                url_str = f", {url}" if url else ""
                citation = f'{author}. "{title}." {year}{url_str}. Accessed {self._get_access_date()}.'

            elif source_type == 'lecture':
                publication = data.get('publication', 'Lecture')
                citation = f'{author}. "{title}." {publication}, {year}.'

            else:  # other
                citation = f"{author}. {title}. {year}."

            return citation

        except Exception as e:
            logger.error(f"Failed to format MLA citation: {e}")
            return f"Error formatting citation: {str(e)}"

    def _get_access_date(self) -> str:
        """
        Get current date for access date in citations.

        Returns:
            Formatted date string
        """
        from datetime import datetime
        return datetime.now().strftime("%d %B %Y")

    def format_in_text_citation(
        self,
        author: str,
        year: Optional[int],
        page: Optional[str] = None,
        style: str = 'harvard'
    ) -> str:
        """
        Format an in-text citation.

        Args:
            author: Author name
            year: Publication year
            page: Optional page number
            style: Citation style (harvard, apa, mla)

        Returns:
            Formatted in-text citation
        """
        try:
            # Extract last name if full name provided
            if ',' in author:
                last_name = author.split(',')[0].strip()
            else:
                # Take last word as last name
                last_name = author.split()[-1] if author.split() else author

            year_str = str(year) if year else 'n.d.'

            if style == 'harvard' or style == 'apa':
                # Format: (Author, Year, p.X)
                if page:
                    return f"({last_name}, {year_str}, p.{page})"
                else:
                    return f"({last_name}, {year_str})"

            elif style == 'mla':
                # Format: (Author X)
                if page:
                    return f"({last_name} {page})"
                else:
                    return f"({last_name})"

            else:
                return f"({last_name}, {year_str})"

        except Exception as e:
            logger.error(f"Failed to format in-text citation: {e}")
            return f"({author}, {year})"

    def validate_citation_data(self, source_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that citation data is complete.

        Args:
            source_type: Type of source
            data: Source data dictionary

        Returns:
            Validation result with missing fields
        """
        required_fields = {
            'book': ['author', 'year', 'title', 'publisher'],
            'journal_article': ['author', 'year', 'title', 'publication'],
            'website': ['author', 'year', 'title', 'url'],
            'lecture': ['author', 'year', 'title'],
            'other': ['title']
        }

        missing_fields = []
        required = required_fields.get(source_type, ['title'])

        for field in required:
            if not data.get(field):
                missing_fields.append(field)

        warnings = []

        # Check for common issues
        if data.get('author') == 'Anon.' or data.get('author') == 'Anonymous':
            warnings.append("Author is anonymous - consider finding original author")

        if data.get('year') == 'n.d.':
            warnings.append("No publication date - verify if date can be found")

        if source_type == 'website' and not data.get('url'):
            warnings.append("Website citation should include URL")

        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'warnings': warnings
        }


if __name__ == "__main__":
    print("Testing Citation Formatter...")

    formatter = CitationFormatter()

    # Test book citation
    book_data = {
        'author': 'Smith, J.',
        'year': 2020,
        'title': 'Introduction to Python Programming',
        'publisher': 'Tech Press'
    }

    print("\nBook Citation:")
    print(f"Harvard: {formatter.format_harvard('book', book_data)}")
    print(f"APA: {formatter.format_apa('book', book_data)}")
    print(f"MLA: {formatter.format_mla('book', book_data)}")

    # Test journal article
    journal_data = {
        'author': 'Jones, A. and Brown, B.',
        'year': 2021,
        'title': 'Machine Learning Applications',
        'publication': 'Journal of AI Research',
        'pages': '123-145',
        'doi': '10.1234/jair.2021.5678'
    }

    print("\nJournal Article:")
    print(f"Harvard: {formatter.format_harvard('journal_article', journal_data)}")
    print(f"APA: {formatter.format_apa('journal_article', journal_data)}")
    print(f"MLA: {formatter.format_mla('journal_article', journal_data)}")

    # Test in-text citation
    print("\nIn-text Citations:")
    print(f"Harvard: {formatter.format_in_text_citation('Smith, J.', 2020, '45', 'harvard')}")
    print(f"APA: {formatter.format_in_text_citation('Smith, J.', 2020, '45', 'apa')}")
    print(f"MLA: {formatter.format_in_text_citation('Smith, J.', 2020, '45', 'mla')}")

    # Test validation
    print("\nValidation:")
    validation = formatter.validate_citation_data('book', book_data)
    print(f"Valid: {validation['valid']}")
    print(f"Missing: {validation['missing_fields']}")
    print(f"Warnings: {validation['warnings']}")

    print("\nCitation Formatter validated!")
