"""
LMS Integration Manager
Unified interface for multiple Learning Management Systems.

Supports:
- Canvas (via canvasapi - existing Phase 4 integration)
- Blackboard (via REST API)
- Moodle (via Web Services API)

Author: Academic Command Center
Phase: 6 Sprint 1
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LMSPlatform(Enum):
    """Supported LMS platforms."""
    CANVAS = "canvas"
    BLACKBOARD = "blackboard"
    MOODLE = "moodle"


class LMSIntegrationManager:
    """
    Central manager for LMS integrations.

    Features:
    - Multi-platform support (Canvas, Blackboard, Moodle)
    - Unified interface for common operations
    - Assignment syncing
    - Grade fetching
    - Material downloading
    - Course listing
    """

    def __init__(
        self,
        user_id: str,
        platform: LMSPlatform,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize LMS integration manager.

        Args:
            user_id: Current user ID
            platform: LMS platform to use
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.platform = platform
        self.db = db_manager or DatabaseManager()

        # Lazy load platform-specific connector
        self._connector = None

        logger.info(f"LMS integration manager initialized for {platform.value}")

    def connect(
        self,
        base_url: str,
        api_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Connect to LMS platform.

        Args:
            base_url: LMS base URL (e.g., https://canvas.school.edu)
            api_token: API access token
            **kwargs: Platform-specific connection params

        Returns:
            Connection result with success status
        """
        try:
            # Get platform-specific connector
            connector = self._get_connector()

            # Attempt connection
            result = connector.connect(base_url, api_token, **kwargs)

            if result.get('success'):
                # Store credentials in database (encrypted)
                self._store_credentials(base_url, api_token, **kwargs)

                logger.info(f"Connected to {self.platform.value} successfully")

            return result

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_courses(self) -> Dict[str, Any]:
        """
        Get list of courses from LMS.

        Returns:
            Courses list with metadata
        """
        try:
            connector = self._get_connector()

            if not connector.is_connected():
                return {
                    'success': False,
                    'error': 'Not connected to LMS',
                    'courses': []
                }

            courses = connector.get_courses()

            return {
                'success': True,
                'courses': courses,
                'count': len(courses)
            }

        except Exception as e:
            logger.error(f"Failed to get courses: {e}")
            return {
                'success': False,
                'error': str(e),
                'courses': []
            }

    def get_assignments(
        self,
        course_id: str
    ) -> Dict[str, Any]:
        """
        Get assignments for a course.

        Args:
            course_id: Course ID

        Returns:
            Assignments list
        """
        try:
            connector = self._get_connector()

            if not connector.is_connected():
                return {
                    'success': False,
                    'error': 'Not connected to LMS',
                    'assignments': []
                }

            assignments = connector.get_assignments(course_id)

            return {
                'success': True,
                'assignments': assignments,
                'count': len(assignments)
            }

        except Exception as e:
            logger.error(f"Failed to get assignments: {e}")
            return {
                'success': False,
                'error': str(e),
                'assignments': []
            }

    def get_grades(
        self,
        course_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get grades from LMS.

        Args:
            course_id: Optional course ID filter

        Returns:
            Grades data
        """
        try:
            connector = self._get_connector()

            if not connector.is_connected():
                return {
                    'success': False,
                    'error': 'Not connected to LMS',
                    'grades': []
                }

            grades = connector.get_grades(course_id)

            return {
                'success': True,
                'grades': grades,
                'count': len(grades)
            }

        except Exception as e:
            logger.error(f"Failed to get grades: {e}")
            return {
                'success': False,
                'error': str(e),
                'grades': []
            }

    def sync_assignments_to_essays(
        self,
        course_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync LMS assignments to local essays.

        Args:
            course_id: Optional course ID filter

        Returns:
            Sync result with statistics
        """
        try:
            # Get assignments
            assignments_result = self.get_assignments(course_id) if course_id else self._get_all_assignments()

            if not assignments_result.get('success'):
                return assignments_result

            assignments = assignments_result.get('assignments', [])

            synced = 0
            skipped = 0
            errors = []

            for assignment in assignments:
                try:
                    # Check if essay already exists
                    existing = self._find_existing_essay(assignment.get('id'))

                    if existing:
                        # Update existing essay
                        self._update_essay_from_assignment(existing['id'], assignment)
                        synced += 1
                    else:
                        # Create new essay
                        self._create_essay_from_assignment(assignment)
                        synced += 1

                except Exception as e:
                    errors.append({
                        'assignment_id': assignment.get('id'),
                        'error': str(e)
                    })
                    skipped += 1

            return {
                'success': True,
                'synced': synced,
                'skipped': skipped,
                'errors': errors,
                'total': len(assignments)
            }

        except Exception as e:
            logger.error(f"Assignment sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def download_materials(
        self,
        course_id: str,
        destination_dir: str
    ) -> Dict[str, Any]:
        """
        Download course materials.

        Args:
            course_id: Course ID
            destination_dir: Local directory to save files

        Returns:
            Download result with file list
        """
        try:
            connector = self._get_connector()

            if not connector.is_connected():
                return {
                    'success': False,
                    'error': 'Not connected to LMS',
                    'files': []
                }

            files = connector.download_materials(course_id, destination_dir)

            return {
                'success': True,
                'files': files,
                'count': len(files)
            }

        except Exception as e:
            logger.error(f"Material download failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'files': []
            }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test LMS connection.

        Returns:
            Test result with connection status
        """
        try:
            connector = self._get_connector()

            if not connector.is_connected():
                return {
                    'success': False,
                    'message': 'Not connected'
                }

            # Try to fetch user info
            result = connector.test_connection()

            return result

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_connector(self):
        """Get platform-specific connector (lazy loading)."""
        if self._connector is None:
            if self.platform == LMSPlatform.CANVAS:
                from .canvas_connector import CanvasConnector
                self._connector = CanvasConnector(self.user_id, self.db)
            elif self.platform == LMSPlatform.BLACKBOARD:
                from .blackboard_connector import BlackboardConnector
                self._connector = BlackboardConnector(self.user_id, self.db)
            elif self.platform == LMSPlatform.MOODLE:
                from .moodle_connector import MoodleConnector
                self._connector = MoodleConnector(self.user_id, self.db)
            else:
                raise ValueError(f"Unsupported platform: {self.platform}")

        return self._connector

    def _get_all_assignments(self) -> Dict[str, Any]:
        """Get assignments from all courses."""
        try:
            courses_result = self.get_courses()

            if not courses_result.get('success'):
                return courses_result

            all_assignments = []

            for course in courses_result.get('courses', []):
                assignments_result = self.get_assignments(course['id'])

                if assignments_result.get('success'):
                    all_assignments.extend(assignments_result.get('assignments', []))

            return {
                'success': True,
                'assignments': all_assignments
            }

        except Exception as e:
            logger.error(f"Failed to get all assignments: {e}")
            return {
                'success': False,
                'error': str(e),
                'assignments': []
            }

    def _find_existing_essay(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Find existing essay by LMS assignment ID."""
        query = """
        SELECT id, title, raw_instructions
        FROM essays
        WHERE user_id = ? AND canvas_assignment_id = ?
        """

        result = self.db.execute_query(
            query,
            (self.user_id, assignment_id),
            fetch_one=True
        )

        return result

    def _create_essay_from_assignment(self, assignment: Dict[str, Any]) -> str:
        """Create new essay from LMS assignment."""
        import uuid

        essay_id = str(uuid.uuid4())

        query = """
        INSERT INTO essays (
            id, user_id, canvas_assignment_id,
            title, raw_instructions, course_name,
            due_date, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(query, (
            essay_id,
            self.user_id,
            assignment.get('id'),
            assignment.get('name', 'Untitled Assignment'),
            assignment.get('description', ''),
            assignment.get('course_name', ''),
            assignment.get('due_at'),
            'not_started',
            datetime.now()
        ))

        logger.info(f"Created essay {essay_id} from assignment {assignment.get('id')}")

        return essay_id

    def _update_essay_from_assignment(
        self,
        essay_id: str,
        assignment: Dict[str, Any]
    ) -> None:
        """Update existing essay from LMS assignment."""
        query = """
        UPDATE essays
        SET title = ?,
            raw_instructions = ?,
            due_date = ?,
            updated_at = ?
        WHERE id = ?
        """

        self.db.execute_query(query, (
            assignment.get('name', 'Untitled Assignment'),
            assignment.get('description', ''),
            assignment.get('due_at'),
            datetime.now(),
            essay_id
        ))

        logger.info(f"Updated essay {essay_id} from assignment {assignment.get('id')}")

    def _store_credentials(
        self,
        base_url: str,
        api_token: str,
        **kwargs
    ) -> None:
        """Store LMS credentials in database (encrypted)."""
        # This should use the encryption service to store credentials securely
        # For now, we'll log that credentials would be stored
        logger.info(f"Storing {self.platform.value} credentials for user {self.user_id}")

        # TODO: Implement secure credential storage using EncryptionService
        # from core.encryption import EncryptionService
        # enc = EncryptionService()
        # encrypted_token = enc.encrypt(api_token)
        # Store in database...


def create_integration_manager(
    user_id: str,
    platform: str,
    db_manager: Optional[DatabaseManager] = None
) -> LMSIntegrationManager:
    """
    Factory function to create LMS integration manager.

    Args:
        user_id: Current user ID
        platform: Platform name (canvas, blackboard, moodle)
        db_manager: Database manager instance

    Returns:
        LMSIntegrationManager instance
    """
    # Convert string to enum
    if isinstance(platform, str):
        platform = LMSPlatform(platform.lower())

    return LMSIntegrationManager(user_id, platform, db_manager)
