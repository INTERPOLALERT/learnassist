"""
Note Manager - Phase 4 Sprint 1
Handles CRUD operations and business logic for notes
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid
import json

logger = logging.getLogger(__name__)


class NoteManager:
    """
    Manages note operations.

    Handles creation, reading, updating, and deleting notes,
    as well as tagging, search, and organization.
    """

    def __init__(self, db_manager, user_id: str):
        """
        Initialize Note Manager.

        Args:
            db_manager: DatabaseManager instance
            user_id: Current user ID
        """
        self.db = db_manager
        self.user_id = user_id
        logger.info(f"Note Manager initialized for user {user_id}")

        # Ensure notes table exists
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure notes and note_tags tables exist."""
        try:
            # Create notes table
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    folder TEXT DEFAULT 'General',
                    subject_id TEXT,
                    assignment_id TEXT,
                    is_pinned BOOLEAN DEFAULT 0,
                    is_favorite BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id),
                    FOREIGN KEY (assignment_id) REFERENCES assignments(id)
                )
            """)

            # Create note_tags table
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS note_tags (
                    id TEXT PRIMARY KEY,
                    note_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
                )
            """)

            # Create index for faster tag searches
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_note_tags_tag
                ON note_tags(tag)
            """)

            logger.debug("Notes tables verified/created")

        except Exception as e:
            logger.error(f"Failed to ensure notes tables: {e}")

    def create_note(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new note.

        Args:
            data: Note data dictionary containing:
                - title (required)
                - content
                - folder
                - subject_id
                - assignment_id
                - tags (list of strings)
                - is_pinned
                - is_favorite

        Returns:
            Note ID if successful, None otherwise
        """
        try:
            note_id = str(uuid.uuid4())

            query = """
                INSERT INTO notes (
                    id, user_id, title, content, folder, subject_id,
                    assignment_id, is_pinned, is_favorite, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                note_id,
                self.user_id,
                data.get('title', 'Untitled Note'),
                data.get('content', ''),
                data.get('folder', 'General'),
                data.get('subject_id'),
                data.get('assignment_id'),
                data.get('is_pinned', False),
                data.get('is_favorite', False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )

            self.db.execute_query(query, params)

            # Add tags if provided
            if 'tags' in data and data['tags']:
                self._add_tags(note_id, data['tags'])

            logger.info(f"Created note: {note_id} - {data.get('title')}")
            return note_id

        except Exception as e:
            logger.error(f"Failed to create note: {e}")
            return None

    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note dictionary or None
        """
        try:
            query = """
                SELECT n.*, s.name as subject_name, s.color as subject_color,
                       a.title as assignment_title
                FROM notes n
                LEFT JOIN subjects s ON n.subject_id = s.id
                LEFT JOIN assignments a ON n.assignment_id = a.id
                WHERE n.id = ? AND n.user_id = ?
            """

            result = self.db.fetch_one(query, (note_id, self.user_id))

            if result:
                note = self._row_to_dict(result)
                # Add tags
                note['tags'] = self._get_tags(note_id)
                return note
            return None

        except Exception as e:
            logger.error(f"Failed to get note {note_id}: {e}")
            return None

    def get_notes(self,
                  folder: Optional[str] = None,
                  subject_id: Optional[str] = None,
                  assignment_id: Optional[str] = None,
                  tag: Optional[str] = None,
                  search_term: Optional[str] = None,
                  pinned_only: bool = False,
                  favorites_only: bool = False,
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get filtered list of notes.

        Args:
            folder: Filter by folder
            subject_id: Filter by subject
            assignment_id: Filter by assignment
            tag: Filter by tag
            search_term: Search in title/content
            pinned_only: Only show pinned notes
            favorites_only: Only show favorite notes
            limit: Maximum number of results

        Returns:
            List of note dictionaries
        """
        try:
            query = """
                SELECT DISTINCT n.*, s.name as subject_name, s.color as subject_color,
                       a.title as assignment_title
                FROM notes n
                LEFT JOIN subjects s ON n.subject_id = s.id
                LEFT JOIN assignments a ON n.assignment_id = a.id
                LEFT JOIN note_tags nt ON n.id = nt.note_id
                WHERE n.user_id = ?
            """

            params = [self.user_id]

            # Add filters
            if folder:
                query += " AND n.folder = ?"
                params.append(folder)

            if subject_id:
                query += " AND n.subject_id = ?"
                params.append(subject_id)

            if assignment_id:
                query += " AND n.assignment_id = ?"
                params.append(assignment_id)

            if tag:
                query += " AND nt.tag = ?"
                params.append(tag)

            if search_term:
                query += " AND (n.title LIKE ? OR n.content LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])

            if pinned_only:
                query += " AND n.is_pinned = 1"

            if favorites_only:
                query += " AND n.is_favorite = 1"

            # Order by pinned first, then updated date
            query += " ORDER BY n.is_pinned DESC, n.updated_at DESC"

            if limit:
                query += f" LIMIT {limit}"

            results = self.db.fetch_all(query, tuple(params))

            notes = []
            for row in results:
                note = self._row_to_dict(row)
                # Add tags
                note['tags'] = self._get_tags(note['id'])
                notes.append(note)

            logger.debug(f"Retrieved {len(notes)} notes")
            return notes

        except Exception as e:
            logger.error(f"Failed to get notes: {e}")
            return []

    def update_note(self, note_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing note.

        Args:
            note_id: Note ID
            data: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build dynamic update query
            fields = []
            params = []

            updateable_fields = [
                'title', 'content', 'folder', 'subject_id', 'assignment_id',
                'is_pinned', 'is_favorite'
            ]

            for field in updateable_fields:
                if field in data:
                    fields.append(f"{field} = ?")
                    params.append(data[field])

            if not fields:
                logger.warning("No fields to update")
                return False

            # Always update updated_at
            fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())

            # Add WHERE clause params
            params.extend([note_id, self.user_id])

            query = f"""
                UPDATE notes
                SET {', '.join(fields)}
                WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(query, tuple(params))

            # Update tags if provided
            if 'tags' in data:
                self._update_tags(note_id, data['tags'])

            logger.info(f"Updated note: {note_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update note {note_id}: {e}")
            return False

    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note.

        Args:
            note_id: Note ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete tags first (cascade should handle this, but explicit is better)
            self.db.execute_query("DELETE FROM note_tags WHERE note_id = ?", (note_id,))

            # Delete note
            query = "DELETE FROM notes WHERE id = ? AND user_id = ?"
            self.db.execute_query(query, (note_id, self.user_id))

            logger.info(f"Deleted note: {note_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete note {note_id}: {e}")
            return False

    def get_folders(self) -> List[str]:
        """
        Get list of all folders.

        Returns:
            List of folder names
        """
        try:
            query = """
                SELECT DISTINCT folder
                FROM notes
                WHERE user_id = ?
                ORDER BY folder
            """

            results = self.db.fetch_all(query, (self.user_id,))
            folders = [row[0] for row in results if row[0]]

            # Always include General if not present
            if 'General' not in folders:
                folders.insert(0, 'General')

            return folders

        except Exception as e:
            logger.error(f"Failed to get folders: {e}")
            return ['General']

    def get_all_tags(self) -> List[str]:
        """
        Get list of all unique tags.

        Returns:
            List of tag names
        """
        try:
            query = """
                SELECT DISTINCT tag
                FROM note_tags nt
                JOIN notes n ON nt.note_id = n.id
                WHERE n.user_id = ?
                ORDER BY tag
            """

            results = self.db.fetch_all(query, (self.user_id,))
            tags = [row[0] for row in results if row[0]]

            return tags

        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get note statistics.

        Returns:
            Dictionary with stats (total, folders, tags, favorites)
        """
        try:
            all_notes = self.get_notes()

            stats = {
                'total': len(all_notes),
                'pinned': len([n for n in all_notes if n.get('is_pinned')]),
                'favorites': len([n for n in all_notes if n.get('is_favorite')]),
                'folders': len(self.get_folders()),
                'total_tags': len(self.get_all_tags()),
                'with_subject': len([n for n in all_notes if n.get('subject_id')]),
                'with_assignment': len([n for n in all_notes if n.get('assignment_id')])
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def _get_tags(self, note_id: str) -> List[str]:
        """Get tags for a note."""
        try:
            query = "SELECT tag FROM note_tags WHERE note_id = ? ORDER BY tag"
            results = self.db.fetch_all(query, (note_id,))
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Failed to get tags for note {note_id}: {e}")
            return []

    def _add_tags(self, note_id: str, tags: List[str]) -> None:
        """Add tags to a note."""
        try:
            for tag in tags:
                if tag.strip():
                    tag_id = str(uuid.uuid4())
                    query = """
                        INSERT INTO note_tags (id, note_id, tag, created_at)
                        VALUES (?, ?, ?, ?)
                    """
                    self.db.execute_query(
                        query,
                        (tag_id, note_id, tag.strip(), datetime.now().isoformat())
                    )
        except Exception as e:
            logger.error(f"Failed to add tags: {e}")

    def _update_tags(self, note_id: str, tags: List[str]) -> None:
        """Update tags for a note (replace all)."""
        try:
            # Delete existing tags
            self.db.execute_query("DELETE FROM note_tags WHERE note_id = ?", (note_id,))

            # Add new tags
            self._add_tags(note_id, tags)

        except Exception as e:
            logger.error(f"Failed to update tags: {e}")

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        if not row:
            return {}

        return {
            'id': row[0],
            'user_id': row[1],
            'title': row[2],
            'content': row[3],
            'folder': row[4],
            'subject_id': row[5],
            'assignment_id': row[6],
            'is_pinned': bool(row[7]),
            'is_favorite': bool(row[8]),
            'created_at': row[9],
            'updated_at': row[10],
            'subject_name': row[11] if len(row) > 11 else None,
            'subject_color': row[12] if len(row) > 12 else '#3498db',
            'assignment_title': row[13] if len(row) > 13 else None
        }
