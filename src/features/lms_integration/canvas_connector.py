"""
Canvas LMS Connector
Wrapper for existing Phase 4 Canvas integration.

Uses the canvasapi library for Canvas LMS integration.

Author: Academic Command Center
Phase: 6 Sprint 1 (wraps Phase 4 integration)
"""

import logging
from typing import Dict, Any, Optional, List
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from canvasapi import Canvas
    CANVAS_AVAILABLE = True
except ImportError:
    CANVAS_AVAILABLE = False


class CanvasConnector:
    """
    Canvas LMS connector (wraps Phase 4 integration).

    Features:
    - Course listing
    - Assignment fetching
    - Grade retrieval
    - File downloading
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Canvas connector.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        if not CANVAS_AVAILABLE:
            raise ImportError("canvasapi library required. Install with: pip install canvasapi")

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        self.canvas = None
        self._connected = False

    def connect(
        self,
        base_url: str,
        api_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Connect to Canvas instance.

        Args:
            base_url: Canvas base URL
            api_token: Canvas API token
            **kwargs: Additional params

        Returns:
            Connection result
        """
        try:
            # Create Canvas instance
            self.canvas = Canvas(base_url, api_token)

            # Test connection
            test_result = self.test_connection()

            if test_result.get('success'):
                self._connected = True
                logger.info("Connected to Canvas successfully")
            else:
                self._connected = False

            return test_result

        except Exception as e:
            logger.error(f"Canvas connection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def is_connected(self) -> bool:
        """Check if connected to Canvas."""
        return self._connected and self.canvas is not None

    def test_connection(self) -> Dict[str, Any]:
        """Test Canvas connection."""
        try:
            # Try to get current user
            user = self.canvas.get_current_user()

            return {
                'success': True,
                'message': 'Connected to Canvas',
                'user': user.name
            }

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_courses(self) -> List[Dict[str, Any]]:
        """
        Get list of courses.

        Returns:
            List of course dictionaries
        """
        try:
            courses = self.canvas.get_courses()

            normalized = []
            for course in courses:
                try:
                    normalized.append({
                        'id': str(course.id),
                        'name': course.name,
                        'course_code': getattr(course, 'course_code', ''),
                        'start_at': getattr(course, 'start_at', None),
                        'end_at': getattr(course, 'end_at', None)
                    })
                except Exception as e:
                    logger.warning(f"Error processing course: {e}")
                    continue

            logger.info(f"Fetched {len(normalized)} courses from Canvas")
            return normalized

        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return []

    def get_assignments(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get assignments for a course.

        Args:
            course_id: Canvas course ID

        Returns:
            List of assignment dictionaries
        """
        try:
            course = self.canvas.get_course(course_id)
            assignments = course.get_assignments()

            normalized = []
            for assignment in assignments:
                try:
                    normalized.append({
                        'id': str(assignment.id),
                        'name': assignment.name,
                        'description': getattr(assignment, 'description', ''),
                        'due_at': getattr(assignment, 'due_at', None),
                        'course_id': course_id,
                        'course_name': course.name,
                        'points_possible': getattr(assignment, 'points_possible', None)
                    })
                except Exception as e:
                    logger.warning(f"Error processing assignment: {e}")
                    continue

            logger.info(f"Fetched {len(normalized)} assignments for course {course_id}")
            return normalized

        except Exception as e:
            logger.error(f"Error fetching assignments: {e}")
            return []

    def get_grades(self, course_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get grades.

        Args:
            course_id: Optional course filter

        Returns:
            List of grade dictionaries
        """
        try:
            if course_id:
                # Get grades for specific course
                course = self.canvas.get_course(course_id)
                enrollments = course.get_enrollments(user_id='self')

                grades = []
                for enrollment in enrollments:
                    try:
                        grades.append({
                            'course_id': course_id,
                            'course_name': course.name,
                            'current_score': getattr(enrollment, 'grades', {}).get('current_score'),
                            'final_score': getattr(enrollment, 'grades', {}).get('final_score'),
                            'current_grade': getattr(enrollment, 'grades', {}).get('current_grade')
                        })
                    except Exception as e:
                        logger.warning(f"Error processing enrollment: {e}")
                        continue

                return grades
            else:
                # Get grades for all courses
                courses = self.get_courses()
                all_grades = []

                for course in courses:
                    course_grades = self.get_grades(course['id'])
                    all_grades.extend(course_grades)

                return all_grades

        except Exception as e:
            logger.error(f"Error fetching grades: {e}")
            return []

    def download_materials(
        self,
        course_id: str,
        destination_dir: str
    ) -> List[str]:
        """
        Download course materials.

        Args:
            course_id: Course ID
            destination_dir: Local directory

        Returns:
            List of downloaded file paths
        """
        try:
            course = self.canvas.get_course(course_id)
            files = course.get_files()

            downloaded_files = []
            os.makedirs(destination_dir, exist_ok=True)

            for file in files:
                try:
                    file_path = os.path.join(destination_dir, file.filename)

                    # Download file
                    file.download(file_path)

                    downloaded_files.append(file_path)
                    logger.info(f"Downloaded: {file.filename}")

                except Exception as e:
                    logger.warning(f"Error downloading file {file.filename}: {e}")
                    continue

            logger.info(f"Downloaded {len(downloaded_files)} files from course {course_id}")
            return downloaded_files

        except Exception as e:
            logger.error(f"Error downloading materials: {e}")
            return []
