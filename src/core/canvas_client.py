"""
Academic Command Center - Canvas LMS Client
Handles all Canvas API interactions for syncing assignments, files, and grades.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from canvasapi import Canvas
from canvasapi.exceptions import CanvasException

from .database import DatabaseManager
from .api_manager import APIKeyManager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CanvasClient:
    """
    Canvas LMS API client for Academic Command Center.

    Features:
    - Sync assignments from Canvas
    - Download course materials
    - Fetch rubrics and grading criteria
    - Track submission status
    - Retrieve tutor feedback
    """

    def __init__(
        self,
        user_id: str,
        canvas_url: str = "https://canvas.instructure.com",
        db_manager: Optional[DatabaseManager] = None,
        api_manager: Optional[APIKeyManager] = None
    ):
        """
        Initialize Canvas client.

        Args:
            user_id: Current user ID
            canvas_url: Canvas institution URL
            db_manager: Database manager instance
            api_manager: API key manager instance
        """
        self.user_id = user_id
        self.canvas_url = canvas_url
        self.db = db_manager or DatabaseManager()
        self.api_manager = api_manager or APIKeyManager(user_id, self.db)

        # Get Canvas token
        self.canvas_token = self.api_manager.get_key('canvas')
        if not self.canvas_token:
            logger.warning("No Canvas token configured")
            self.canvas = None
        else:
            try:
                self.canvas = Canvas(self.canvas_url, self.canvas_token)
                logger.info(f"Canvas client initialized for {self.canvas_url}")
            except Exception as e:
                logger.error(f"Failed to initialize Canvas client: {e}")
                self.canvas = None

    def test_connection(self) -> Dict[str, Any]:
        """
        Test Canvas API connection.

        Returns:
            Connection test result
        """
        if not self.canvas:
            return {
                'success': False,
                'error': 'Canvas client not initialized (no token?)'
            }

        try:
            user = self.canvas.get_current_user()
            return {
                'success': True,
                'user_name': user.name,
                'user_id': user.id
            }
        except CanvasException as e:
            logger.error(f"Canvas connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def sync_all(self, sync_type: str = 'full') -> Dict[str, Any]:
        """
        Sync all Canvas data.

        Args:
            sync_type: 'full' or 'incremental'

        Returns:
            Sync results
        """
        if not self.canvas:
            return {
                'success': False,
                'error': 'Canvas not configured'
            }

        # Create sync log entry
        sync_id = str(uuid.uuid4())
        sync_started = datetime.now()

        query = """
        INSERT INTO canvas_sync_log (
            id, user_id, sync_type, sync_status, started_at
        ) VALUES (?, ?, ?, 'in_progress', ?)
        """
        self.db.execute_query(query, (sync_id, self.user_id, sync_type, sync_started))

        stats = {
            'assignments_synced': 0,
            'files_downloaded': 0,
            'rubrics_synced': 0,
            'errors': []
        }

        try:
            # Get active courses
            courses = self.canvas.get_courses(enrollment_state='active')

            for course in courses:
                logger.info(f"Syncing course: {course.name}")

                # Sync assignments
                try:
                    assignments = course.get_assignments()
                    for assignment in assignments:
                        self._sync_assignment(course, assignment)
                        stats['assignments_synced'] += 1
                except Exception as e:
                    error_msg = f"Failed to sync assignments for {course.name}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

                # Sync course files
                try:
                    files = course.get_files()
                    for file in files:
                        self._download_course_file(course, file)
                        stats['files_downloaded'] += 1
                except Exception as e:
                    error_msg = f"Failed to sync files for {course.name}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            # Update sync log
            sync_completed = datetime.now()
            duration = (sync_completed - sync_started).total_seconds()

            query = """
            UPDATE canvas_sync_log
            SET sync_status = 'completed',
                assignments_synced = ?,
                files_downloaded = ?,
                rubrics_synced = ?,
                errors_count = ?,
                error_details = ?,
                completed_at = ?,
                duration_seconds = ?
            WHERE id = ?
            """
            self.db.execute_query(
                query,
                (
                    stats['assignments_synced'],
                    stats['files_downloaded'],
                    stats['rubrics_synced'],
                    len(stats['errors']),
                    str(stats['errors']) if stats['errors'] else None,
                    sync_completed,
                    int(duration),
                    sync_id
                )
            )

            logger.info(f"Canvas sync completed: {stats}")
            return {
                'success': True,
                **stats
            }

        except Exception as e:
            logger.error(f"Canvas sync failed: {e}")

            # Update sync log as failed
            query = """
            UPDATE canvas_sync_log
            SET sync_status = 'failed',
                error_details = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            self.db.execute_query(query, (str(e), sync_id))

            return {
                'success': False,
                'error': str(e),
                **stats
            }

    def _sync_assignment(self, course, assignment) -> None:
        """Sync single assignment to database."""
        # Check if already exists
        query = "SELECT id FROM essays WHERE canvas_assignment_id = ? AND user_id = ?"
        existing = self.db.execute_query(
            query,
            (str(assignment.id), self.user_id),
            fetch_one=True
        )

        # Extract data
        essay_data = {
            'canvas_assignment_id': str(assignment.id),
            'title': assignment.name,
            'raw_instructions': getattr(assignment, 'description', '') or '',
            'course_name': course.name,
            'course_code': getattr(course, 'course_code', ''),
            'due_date': getattr(assignment, 'due_at', None),
            'status': 'not_started'
        }

        if existing:
            # Update existing
            query = """
            UPDATE essays
            SET title = ?,
                raw_instructions = ?,
                due_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE canvas_assignment_id = ? AND user_id = ?
            """
            self.db.execute_query(
                query,
                (
                    essay_data['title'],
                    essay_data['raw_instructions'],
                    essay_data['due_date'],
                    essay_data['canvas_assignment_id'],
                    self.user_id
                )
            )
            logger.debug(f"Updated assignment: {assignment.name}")
        else:
            # Create new
            essay_id = str(uuid.uuid4())
            query = """
            INSERT INTO essays (
                id, user_id, canvas_assignment_id,
                title, raw_instructions, course_name, course_code,
                due_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(
                query,
                (
                    essay_id,
                    self.user_id,
                    essay_data['canvas_assignment_id'],
                    essay_data['title'],
                    essay_data['raw_instructions'],
                    essay_data['course_name'],
                    essay_data['course_code'],
                    essay_data['due_date'],
                    essay_data['status']
                )
            )
            logger.debug(f"Created new assignment: {assignment.name}")

        # Sync rubric if available
        if hasattr(assignment, 'rubric') and assignment.rubric:
            self._sync_rubric(essay_id if not existing else existing['id'], assignment.rubric)

    def _sync_rubric(self, essay_id: str, rubric_data: List) -> None:
        """Extract and save rubric criteria."""
        rubric_criteria = {}

        for criterion in rubric_data:
            criterion_name = criterion.get('description', 'Unknown')
            points = criterion.get('points', 0)

            # Extract rating levels
            levels = {}
            if 'ratings' in criterion:
                for rating in criterion['ratings']:
                    level_name = rating.get('description', '').lower()
                    level_points = rating.get('points', 0)
                    levels[level_name] = {
                        'description': rating.get('long_description', ''),
                        'points': level_points
                    }

            rubric_criteria[criterion_name] = {
                'weight': points / 100 if points else 0,
                'points': points,
                'levels': levels
            }

        # Save to essay record
        query = """
        UPDATE essays
        SET rubric_criteria = ?
        WHERE id = ?
        """
        self.db.execute_query(query, (str(rubric_criteria), essay_id))
        logger.debug(f"Synced rubric for essay {essay_id}")

    def _download_course_file(self, course, file) -> None:
        """Download and save course file to materials library."""
        # Check if already downloaded
        query = "SELECT id FROM materials WHERE file_hash = ? AND user_id = ?"
        file_hash = str(file.id)  # Use Canvas file ID as hash

        existing = self.db.execute_query(query, (file_hash, self.user_id), fetch_one=True)
        if existing:
            logger.debug(f"File already exists: {file.filename}")
            return

        # Download file
        import os
        import requests

        download_dir = r"C:\Users\Gamer\Getitdone\temp\canvas_files"
        os.makedirs(download_dir, exist_ok=True)

        file_path = os.path.join(download_dir, file.filename)

        try:
            # Download from Canvas
            file_url = file.url
            response = requests.get(file_url, allow_redirects=True)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Add to materials library
            material_id = str(uuid.uuid4())
            query = """
            INSERT INTO materials (
                id, user_id, file_name, file_type, file_path,
                file_hash, course_name, upload_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """

            file_ext = os.path.splitext(file.filename)[1].lower().replace('.', '')

            self.db.execute_query(
                query,
                (
                    material_id,
                    self.user_id,
                    file.filename,
                    file_ext,
                    file_path,
                    file_hash,
                    course.name
                )
            )

            logger.debug(f"Downloaded file: {file.filename}")

        except Exception as e:
            logger.error(f"Failed to download file {file.filename}: {e}")

    def get_submission_status(self, canvas_assignment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get submission status for an assignment.

        Args:
            canvas_assignment_id: Canvas assignment ID

        Returns:
            Submission data or None
        """
        if not self.canvas:
            return None

        try:
            # Get assignment
            assignment = self.canvas.get_assignment(canvas_assignment_id)

            # Get user's submission
            user = self.canvas.get_current_user()
            submission = assignment.get_submission(user.id)

            return {
                'submitted': submission.submitted_at is not None,
                'submitted_at': submission.submitted_at,
                'grade': getattr(submission, 'grade', None),
                'score': getattr(submission, 'score', None),
                'workflow_state': submission.workflow_state,
                'late': getattr(submission, 'late', False)
            }

        except Exception as e:
            logger.error(f"Failed to get submission status: {e}")
            return None

    def submit_assignment(
        self,
        canvas_assignment_id: str,
        file_path: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit assignment to Canvas.

        Args:
            canvas_assignment_id: Canvas assignment ID
            file_path: Path to file to submit
            comment: Optional submission comment

        Returns:
            Submission result
        """
        if not self.canvas:
            return {
                'success': False,
                'error': 'Canvas not configured'
            }

        try:
            assignment = self.canvas.get_assignment(canvas_assignment_id)

            # Upload file
            with open(file_path, 'rb') as f:
                submission = assignment.submit(
                    submission={
                        'submission_type': 'online_upload'
                    },
                    file=f,
                    comment={'text_comment': comment} if comment else None
                )

            logger.info(f"Assignment submitted: {canvas_assignment_id}")
            return {
                'success': True,
                'submission_id': submission.id,
                'submitted_at': submission.submitted_at
            }

        except Exception as e:
            logger.error(f"Assignment submission failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # Test Canvas Client
    print("Testing Canvas Client...")

    client = CanvasClient(user_id="test_user_123")

    # Test connection
    result = client.test_connection()
    print(f"Connection test: {result}")

    print("\nCanvas Client test completed!")
