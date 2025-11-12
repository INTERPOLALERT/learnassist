"""
Academic Command Center - Canvas Integration - Canvas Sync
Manages Canvas LMS integration for grades and assignments.
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


class CanvasSyncManager:
    """
    Manages Canvas LMS integration.

    Handles:
    - Canvas API connection
    - Grade synchronization
    - Assignment submission status
    - Sync history tracking
    - Grade statistics
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize Canvas sync manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.canvas_api_key = None
        self.canvas_url = None

        logger.info(f"Canvas sync manager initialized for user {user_id}")

    def set_canvas_credentials(self, api_key: str, canvas_url: str) -> Dict[str, Any]:
        """
        Set Canvas API credentials.

        Args:
            api_key: Canvas API key
            canvas_url: Canvas instance URL

        Returns:
            Result dictionary
        """
        try:
            self.canvas_api_key = api_key
            self.canvas_url = canvas_url

            # Store in user_api_keys table
            query = """
            INSERT OR REPLACE INTO user_api_keys (
                id, user_id, provider, api_key_encrypted, api_key_iv,
                display_name, is_enabled, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            # For now, store as plain text (in production, should be encrypted)
            # The database schema expects encrypted BLOB, but we'll store text for simplicity
            api_id = str(uuid.uuid4())

            self.db.execute_query(
                query,
                (
                    api_id,
                    self.user_id,
                    'canvas',
                    api_key.encode(),  # Store as bytes
                    b'',  # Empty IV for now
                    'Canvas LMS',
                    1,  # enabled
                    datetime.now().isoformat()
                )
            )

            logger.info("Canvas credentials stored")

            return {
                'success': True,
                'message': 'Canvas credentials saved'
            }

        except Exception as e:
            logger.error(f"Failed to set Canvas credentials: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test Canvas API connection.

        Returns:
            Connection test result
        """
        try:
            if not self.canvas_api_key or not self.canvas_url:
                return {
                    'success': False,
                    'error': 'Canvas credentials not configured'
                }

            # In a real implementation, this would make an API call to Canvas
            # For now, simulate a successful connection
            logger.info("Testing Canvas connection (simulated)")

            return {
                'success': True,
                'message': 'Canvas connection successful',
                'user_name': 'Test Student',
                'courses_count': 5
            }

        except Exception as e:
            logger.error(f"Canvas connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def sync_grades(self, simulate: bool = True) -> Dict[str, Any]:
        """
        Sync grades from Canvas.

        Args:
            simulate: Whether to simulate sync (True) or use real API (False)

        Returns:
            Sync result
        """
        try:
            sync_id = str(uuid.uuid4())
            start_time = datetime.now()

            if simulate:
                # Simulate fetching grades
                logger.info("Simulating Canvas grade sync...")

                # Create sample grade data
                sample_grades = [
                    {
                        'assignment_name': 'Essay 1: Introduction to Philosophy',
                        'course_name': 'Philosophy 101',
                        'grade': 92.0,
                        'grade_letter': 'A',
                        'max_points': 100.0,
                        'submitted_at': '2024-01-15T10:30:00',
                        'graded_at': '2024-01-20T14:00:00'
                    },
                    {
                        'assignment_name': 'Midterm Exam',
                        'course_name': 'History 202',
                        'grade': 88.0,
                        'grade_letter': 'B+',
                        'max_points': 100.0,
                        'submitted_at': '2024-02-10T09:00:00',
                        'graded_at': '2024-02-15T16:30:00'
                    },
                    {
                        'assignment_name': 'Research Paper',
                        'course_name': 'English 301',
                        'grade': 95.0,
                        'grade_letter': 'A',
                        'max_points': 100.0,
                        'submitted_at': '2024-03-05T23:59:00',
                        'graded_at': '2024-03-12T10:00:00'
                    }
                ]

                # Update essays in database with grades
                for grade_data in sample_grades:
                    # Find matching essay by title
                    find_query = "SELECT id FROM essays WHERE user_id = ? AND title LIKE ? LIMIT 1"
                    essay = self.db.execute_query(
                        find_query,
                        (self.user_id, f"%{grade_data['assignment_name'][:20]}%"),
                        fetch_one=True
                    )

                    if essay:
                        # Update essay with grade
                        update_query = """
                        UPDATE essays
                        SET
                            grade_received = ?,
                            grade_letter = ?,
                            submitted_date = ?,
                            course_name = ?
                        WHERE id = ? AND user_id = ?
                        """

                        self.db.execute_query(
                            update_query,
                            (
                                grade_data['grade'],
                                grade_data['grade_letter'],
                                grade_data['submitted_at'],
                                grade_data['course_name'],
                                essay['id'],
                                self.user_id
                            )
                        )

                assignments_synced = len(sample_grades)
                errors_count = 0
            else:
                # Real Canvas API sync would go here
                logger.info("Real Canvas API sync not implemented yet")
                assignments_synced = 0
                errors_count = 0

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Log sync to database
            log_query = """
            INSERT INTO canvas_sync_log (
                id, user_id, sync_type, sync_status,
                assignments_synced, files_downloaded, rubrics_synced,
                errors_count, started_at, completed_at, duration_seconds,
                sync_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            sync_summary = f"Synced {assignments_synced} assignments"
            if errors_count > 0:
                sync_summary += f" with {errors_count} errors"

            self.db.execute_query(
                log_query,
                (
                    sync_id,
                    self.user_id,
                    'manual' if simulate else 'api',
                    'completed',
                    assignments_synced,
                    0,  # files_downloaded
                    0,  # rubrics_synced
                    errors_count,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    int(duration),
                    sync_summary
                )
            )

            logger.info(f"Canvas sync completed: {assignments_synced} assignments")

            return {
                'success': True,
                'sync_id': sync_id,
                'assignments_synced': assignments_synced,
                'duration_seconds': int(duration),
                'errors': errors_count
            }

        except Exception as e:
            logger.error(f"Canvas sync failed: {e}")

            # Log failed sync
            try:
                error_log_query = """
                INSERT INTO canvas_sync_log (
                    id, user_id, sync_type, sync_status,
                    errors_count, started_at, error_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                self.db.execute_query(
                    error_log_query,
                    (
                        str(uuid.uuid4()),
                        self.user_id,
                        'manual',
                        'failed',
                        1,
                        datetime.now().isoformat(),
                        str(e)
                    )
                )
            except:
                pass

            return {
                'success': False,
                'error': str(e)
            }

    def get_sync_history(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get Canvas sync history.

        Args:
            limit: Maximum number of records to return

        Returns:
            Sync history
        """
        try:
            query = """
            SELECT * FROM canvas_sync_log
            WHERE user_id = ?
            ORDER BY started_at DESC
            LIMIT ?
            """

            history = self.db.execute_query(
                query,
                (self.user_id, limit),
                fetch_all=True
            )

            return {
                'success': True,
                'history': history or [],
                'count': len(history) if history else 0
            }

        except Exception as e:
            logger.error(f"Failed to get sync history: {e}")
            return {
                'success': False,
                'error': str(e),
                'history': []
            }

    def get_grade_statistics(self) -> Dict[str, Any]:
        """
        Get grade statistics for synced assignments.

        Returns:
            Grade statistics
        """
        try:
            query = """
            SELECT
                COUNT(*) as total_graded,
                AVG(grade_received) as average_grade,
                MIN(grade_received) as lowest_grade,
                MAX(grade_received) as highest_grade,
                COUNT(CASE WHEN grade_letter LIKE 'A%' THEN 1 END) as a_grades,
                COUNT(CASE WHEN grade_letter LIKE 'B%' THEN 1 END) as b_grades,
                COUNT(CASE WHEN grade_letter LIKE 'C%' THEN 1 END) as c_grades,
                COUNT(CASE WHEN grade_letter LIKE 'D%' OR grade_letter LIKE 'F%' THEN 1 END) as below_c
            FROM essays
            WHERE user_id = ?
            AND grade_received IS NOT NULL
            """

            stats = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_one=True
            )

            if not stats or stats['total_graded'] == 0:
                return {
                    'success': True,
                    'total_graded': 0,
                    'average_grade': 0,
                    'grade_distribution': {}
                }

            return {
                'success': True,
                'total_graded': stats['total_graded'],
                'average_grade': round(stats['average_grade'], 2) if stats['average_grade'] else 0,
                'lowest_grade': stats['lowest_grade'],
                'highest_grade': stats['highest_grade'],
                'grade_distribution': {
                    'A': stats['a_grades'],
                    'B': stats['b_grades'],
                    'C': stats['c_grades'],
                    'Below C': stats['below_c']
                }
            }

        except Exception as e:
            logger.error(f"Failed to get grade statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_graded_assignments(self) -> Dict[str, Any]:
        """
        Get all graded assignments from Canvas.

        Returns:
            List of graded assignments
        """
        try:
            query = """
            SELECT
                id, title, course_name, grade_received,
                grade_letter, submitted_date, due_date
            FROM essays
            WHERE user_id = ?
            AND grade_received IS NOT NULL
            ORDER BY submitted_date DESC
            """

            assignments = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_all=True
            )

            return {
                'success': True,
                'assignments': assignments or [],
                'count': len(assignments) if assignments else 0
            }

        except Exception as e:
            logger.error(f"Failed to get graded assignments: {e}")
            return {
                'success': False,
                'error': str(e),
                'assignments': []
            }

    def get_pending_submissions(self) -> Dict[str, Any]:
        """
        Get assignments pending submission or grading.

        Returns:
            List of pending assignments
        """
        try:
            query = """
            SELECT
                id, title, course_name, due_date, status
            FROM essays
            WHERE user_id = ?
            AND (
                (status != 'submitted' AND due_date >= date('now'))
                OR (status = 'submitted' AND grade_received IS NULL)
            )
            ORDER BY due_date ASC
            """

            pending = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_all=True
            )

            return {
                'success': True,
                'pending': pending or [],
                'count': len(pending) if pending else 0
            }

        except Exception as e:
            logger.error(f"Failed to get pending submissions: {e}")
            return {
                'success': False,
                'error': str(e),
                'pending': []
            }


if __name__ == "__main__":
    print("Testing Canvas Sync Manager...")

    manager = CanvasSyncManager(user_id="test_user")

    # Test set credentials
    result = manager.set_canvas_credentials(
        api_key="test_api_key_12345",
        canvas_url="https://canvas.university.edu"
    )
    print(f"\nSet credentials: {result['success']}")

    # Test connection
    conn_test = manager.test_connection()
    print(f"Connection test: {conn_test['success']}")

    # Test sync (simulated)
    sync_result = manager.sync_grades(simulate=True)
    print(f"\nSync result: {sync_result}")

    # Test statistics
    stats = manager.get_grade_statistics()
    print(f"\nGrade statistics: {stats}")

    # Test sync history
    history = manager.get_sync_history(limit=5)
    print(f"\nSync history: {history['count']} records")

    print("\nCanvas Sync Manager validated!")
