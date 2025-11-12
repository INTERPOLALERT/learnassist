"""
Academic Command Center - Citations - Citation Manager
Manages academic sources and citations.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SourceType:
    """Types of academic sources."""
    BOOK = "book"
    JOURNAL_ARTICLE = "journal_article"
    WEBSITE = "website"
    LECTURE = "lecture"
    OTHER = "other"


class CitationManager:
    """
    Manages academic sources and citations.

    Handles:
    - Source creation and storage
    - Citation retrieval
    - Source search
    - Citation counting
    - Usage tracking
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize citation manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Citation manager initialized for user {user_id}")

    def add_source(
        self,
        title: str,
        source_type: str,
        author: Optional[str] = None,
        year: Optional[int] = None,
        publication: Optional[str] = None,
        publisher: Optional[str] = None,
        pages: Optional[str] = None,
        url: Optional[str] = None,
        doi: Optional[str] = None,
        essay_id: Optional[str] = None,
        material_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new source.

        Args:
            title: Source title
            source_type: Type (book, journal_article, website, etc.)
            author: Author name(s)
            year: Publication year
            publication: Publication/journal name
            publisher: Publisher name
            pages: Page numbers
            url: URL
            doi: DOI
            essay_id: Optional essay link
            material_id: Optional material link
            notes: Personal notes

        Returns:
            Creation result with formatted citations
        """
        try:
            source_id = str(uuid.uuid4())

            # Import formatter here to avoid circular dependency
            from .citation_formatter import CitationFormatter
            formatter = CitationFormatter()

            # Generate formatted citations
            source_data = {
                'author': author,
                'year': year,
                'title': title,
                'publication': publication,
                'publisher': publisher,
                'pages': pages,
                'url': url,
                'doi': doi
            }

            citation_harvard = formatter.format_harvard(source_type, source_data)
            citation_apa = formatter.format_apa(source_type, source_data)
            citation_mla = formatter.format_mla(source_type, source_data)

            # Insert into database
            query = """
            INSERT INTO sources (
                id, user_id, essay_id, material_id, source_type,
                author, year, title, publication, publisher, pages,
                url, doi, citation_harvard, citation_apa, citation_mla,
                times_cited, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    source_id,
                    self.user_id,
                    essay_id,
                    material_id,
                    source_type,
                    author,
                    year,
                    title,
                    publication,
                    publisher,
                    pages,
                    url,
                    doi,
                    citation_harvard,
                    citation_apa,
                    citation_mla,
                    0,  # times_cited
                    notes,
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Added source: {source_id} - {title}")

            return {
                'success': True,
                'source_id': source_id,
                'citations': {
                    'harvard': citation_harvard,
                    'apa': citation_apa,
                    'mla': citation_mla
                }
            }

        except Exception as e:
            logger.error(f"Failed to add source: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_source(self, source_id: str) -> Dict[str, Any]:
        """
        Get a specific source by ID.

        Args:
            source_id: Source ID

        Returns:
            Source details
        """
        try:
            query = "SELECT * FROM sources WHERE id = ? AND user_id = ?"
            source = self.db.execute_query(
                query,
                (source_id, self.user_id),
                fetch_one=True
            )

            if not source:
                return {
                    'success': False,
                    'error': 'Source not found'
                }

            return {
                'success': True,
                'source': source
            }

        except Exception as e:
            logger.error(f"Failed to get source: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_all_sources(self, essay_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all sources for user, optionally filtered by essay.

        Args:
            essay_id: Optional essay ID to filter

        Returns:
            List of sources
        """
        try:
            if essay_id:
                query = """
                SELECT * FROM sources
                WHERE user_id = ? AND essay_id = ?
                ORDER BY created_at DESC
                """
                params = (self.user_id, essay_id)
            else:
                query = """
                SELECT * FROM sources
                WHERE user_id = ?
                ORDER BY created_at DESC
                """
                params = (self.user_id,)

            sources = self.db.execute_query(query, params, fetch_all=True)

            return {
                'success': True,
                'sources': sources or [],
                'count': len(sources) if sources else 0
            }

        except Exception as e:
            logger.error(f"Failed to get sources: {e}")
            return {
                'success': False,
                'error': str(e),
                'sources': []
            }

    def search_sources(self, search_term: str) -> Dict[str, Any]:
        """
        Search sources by title, author, or publication.

        Args:
            search_term: Search term

        Returns:
            Matching sources
        """
        try:
            query = """
            SELECT * FROM sources
            WHERE user_id = ?
            AND (
                title LIKE ?
                OR author LIKE ?
                OR publication LIKE ?
            )
            ORDER BY created_at DESC
            """

            search_pattern = f"%{search_term}%"
            sources = self.db.execute_query(
                query,
                (self.user_id, search_pattern, search_pattern, search_pattern),
                fetch_all=True
            )

            return {
                'success': True,
                'sources': sources or [],
                'count': len(sources) if sources else 0
            }

        except Exception as e:
            logger.error(f"Failed to search sources: {e}")
            return {
                'success': False,
                'error': str(e),
                'sources': []
            }

    def update_source(self, source_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update source details.

        Args:
            source_id: Source ID
            updates: Dictionary of fields to update

        Returns:
            Update result
        """
        try:
            # Build update query dynamically
            allowed_fields = [
                'author', 'year', 'title', 'publication', 'publisher',
                'pages', 'url', 'doi', 'notes', 'essay_id'
            ]

            update_fields = []
            update_values = []

            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)

            if not update_fields:
                return {
                    'success': False,
                    'error': 'No valid fields to update'
                }

            # Regenerate citations if relevant fields changed
            if any(f in updates for f in ['author', 'year', 'title', 'publication', 'publisher', 'pages', 'url', 'doi']):
                # Get current source
                source = self.get_source(source_id)
                if source['success']:
                    from .citation_formatter import CitationFormatter
                    formatter = CitationFormatter()

                    # Merge updates with existing data
                    source_data = {**source['source'], **updates}

                    citation_harvard = formatter.format_harvard(source_data['source_type'], source_data)
                    citation_apa = formatter.format_apa(source_data['source_type'], source_data)
                    citation_mla = formatter.format_mla(source_data['source_type'], source_data)

                    update_fields.extend(['citation_harvard', 'citation_apa', 'citation_mla'])
                    update_values.extend([citation_harvard, citation_apa, citation_mla])

            # Add WHERE clause values
            update_values.extend([source_id, self.user_id])

            query = f"""
            UPDATE sources
            SET {', '.join(update_fields)}
            WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(query, tuple(update_values))

            logger.info(f"Updated source: {source_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to update source: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_source(self, source_id: str) -> Dict[str, Any]:
        """
        Delete a source.

        Args:
            source_id: Source ID

        Returns:
            Delete result
        """
        try:
            query = "DELETE FROM sources WHERE id = ? AND user_id = ?"
            self.db.execute_query(query, (source_id, self.user_id))

            logger.info(f"Deleted source: {source_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to delete source: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def increment_citation_count(self, source_id: str) -> Dict[str, Any]:
        """
        Increment the times_cited counter for a source.

        Args:
            source_id: Source ID

        Returns:
            Update result
        """
        try:
            query = """
            UPDATE sources
            SET times_cited = times_cited + 1
            WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(query, (source_id, self.user_id))

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to increment citation count: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_citation_statistics(self) -> Dict[str, Any]:
        """
        Get citation statistics for user.

        Returns:
            Citation statistics
        """
        try:
            query = """
            SELECT
                COUNT(*) as total_sources,
                SUM(times_cited) as total_citations,
                AVG(times_cited) as avg_citations,
                COUNT(CASE WHEN source_type = ? THEN 1 END) as books,
                COUNT(CASE WHEN source_type = ? THEN 1 END) as journals,
                COUNT(CASE WHEN source_type = ? THEN 1 END) as websites,
                COUNT(CASE WHEN essay_id IS NOT NULL THEN 1 END) as linked_to_essays
            FROM sources
            WHERE user_id = ?
            """

            stats = self.db.execute_query(
                query,
                (
                    SourceType.BOOK,
                    SourceType.JOURNAL_ARTICLE,
                    SourceType.WEBSITE,
                    self.user_id
                ),
                fetch_one=True
            )

            if not stats or stats['total_sources'] == 0:
                return {
                    'success': True,
                    'total_sources': 0,
                    'total_citations': 0,
                    'avg_citations': 0,
                    'by_type': {}
                }

            return {
                'success': True,
                'total_sources': stats['total_sources'],
                'total_citations': stats['total_citations'] or 0,
                'avg_citations': round(stats['avg_citations'] or 0, 1),
                'by_type': {
                    'books': stats['books'],
                    'journals': stats['journals'],
                    'websites': stats['websites']
                },
                'linked_to_essays': stats['linked_to_essays']
            }

        except Exception as e:
            logger.error(f"Failed to get citation statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_bibliography(
        self,
        essay_id: Optional[str] = None,
        citation_style: str = 'harvard'
    ) -> Dict[str, Any]:
        """
        Generate a bibliography for an essay or all sources.

        Args:
            essay_id: Optional essay ID (None = all sources)
            citation_style: Citation style (harvard, apa, mla)

        Returns:
            Bibliography
        """
        try:
            sources_result = self.get_all_sources(essay_id)

            if not sources_result['success']:
                return sources_result

            sources = sources_result['sources']

            # Determine which citation field to use
            citation_field_map = {
                'harvard': 'citation_harvard',
                'apa': 'citation_apa',
                'mla': 'citation_mla'
            }

            citation_field = citation_field_map.get(citation_style, 'citation_harvard')

            # Sort alphabetically by author/title
            sorted_sources = sorted(
                sources,
                key=lambda s: (s.get('author') or s.get('title', '')).lower()
            )

            # Generate bibliography text
            bibliography_entries = []
            for source in sorted_sources:
                citation = source.get(citation_field)
                if citation:
                    bibliography_entries.append(citation)

            return {
                'success': True,
                'style': citation_style,
                'count': len(bibliography_entries),
                'bibliography': '\n\n'.join(bibliography_entries)
            }

        except Exception as e:
            logger.error(f"Failed to generate bibliography: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    print("Testing Citation Manager...")

    manager = CitationManager(user_id="test_user")

    # Test add source
    result = manager.add_source(
        title="Introduction to Algorithms",
        source_type=SourceType.BOOK,
        author="Cormen, T.H., Leiserson, C.E., Rivest, R.L. and Stein, C.",
        year=2009,
        publisher="MIT Press",
        notes="Classic algorithms textbook"
    )
    print(f"\nAdd source result: {result['success']}")
    if result['success']:
        source_id = result['source_id']
        print(f"Harvard: {result['citations']['harvard']}")

        # Test get source
        get_result = manager.get_source(source_id)
        print(f"\nGet source: {get_result['success']}")

        # Test statistics
        stats = manager.get_citation_statistics()
        print(f"\nStatistics: {stats}")

        # Test bibliography
        bib = manager.generate_bibliography(citation_style='harvard')
        print(f"\nBibliography entries: {bib['count']}")

    print("\nCitation Manager validated!")
