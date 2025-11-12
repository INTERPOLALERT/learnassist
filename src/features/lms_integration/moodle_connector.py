"""
Moodle LMS Connector
Integration with Moodle Web Services API.

API Documentation: https://docs.moodle.org/dev/Web_services

Author: Academic Command Center
Phase: 6 Sprint 1
"""

import logging
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MoodleConnector:
    """
    Moodle Web Services API connector.

    Features:
    - Web Services authentication
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
        Initialize Moodle connector.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        self.base_url = None
        self.api_token = None
        self.webservice_url = None
        self._connected = False

    def connect(
        self,
        base_url: str,
        api_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Connect to Moodle instance.

        Args:
            base_url: Moodle base URL (e.g., https://moodle.school.edu)
            api_token: Web Services token
            **kwargs: Additional params

        Returns:
            Connection result
        """
        try:
            # Clean base URL
            self.base_url = base_url.rstrip('/')
            self.api_token = api_token

            # Moodle Web Services endpoint
            self.webservice_url = f"{self.base_url}/webservice/rest/server.php"

            # Test connection
            test_result = self.test_connection()

            if test_result.get('success'):
                self._connected = True
                logger.info("Connected to Moodle successfully")
            else:
                self._connected = False

            return test_result

        except Exception as e:
            logger.error(f"Moodle connection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def is_connected(self) -> bool:
        """Check if connected to Moodle."""
        return self._connected

    def test_connection(self) -> Dict[str, Any]:
        """Test Moodle connection."""
        try:
            # Call core_webservice_get_site_info to test connection
            result = self._call_function('core_webservice_get_site_info', {})

            if result.get('success'):
                site_info = result.get('data', {})

                return {
                    'success': True,
                    'message': 'Connected to Moodle',
                    'user': site_info.get('username', 'Unknown'),
                    'site_name': site_info.get('sitename', 'Moodle')
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_courses(self) -> List[Dict[str, Any]]:
        """
        Get list of enrolled courses.

        Returns:
            List of course dictionaries
        """
        try:
            # Use core_enrol_get_users_courses to get enrolled courses
            result = self._call_function('core_enrol_get_users_courses', {
                'userid': self._get_current_user_id()
            })

            if not result.get('success'):
                logger.error(f"Failed to get courses: {result.get('error')}")
                return []

            courses = result.get('data', [])

            # Normalize course data
            normalized = []
            for course in courses:
                normalized.append({
                    'id': str(course.get('id')),
                    'name': course.get('fullname', 'Unnamed Course'),
                    'short_name': course.get('shortname', ''),
                    'description': course.get('summary', ''),
                    'start_date': course.get('startdate'),
                    'end_date': course.get('enddate')
                })

            logger.info(f"Fetched {len(normalized)} courses from Moodle")
            return normalized

        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return []

    def get_assignments(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get assignments for a course.

        Args:
            course_id: Moodle course ID

        Returns:
            List of assignment dictionaries
        """
        try:
            # Use mod_assign_get_assignments
            result = self._call_function('mod_assign_get_assignments', {
                'courseids[]': int(course_id)
            })

            if not result.get('success'):
                logger.error(f"Failed to get assignments: {result.get('error')}")
                return []

            data = result.get('data', {})
            course_data = data.get('courses', [])

            assignments = []

            for course in course_data:
                for assignment in course.get('assignments', []):
                    assignments.append({
                        'id': str(assignment.get('id')),
                        'name': assignment.get('name', 'Unnamed Assignment'),
                        'description': assignment.get('intro', ''),
                        'due_at': assignment.get('duedate'),
                        'course_id': course_id,
                        'course_name': course.get('fullname'),
                        'allow_submissions_from': assignment.get('allowsubmissionsfromdate'),
                        'cutoff_date': assignment.get('cutoffdate')
                    })

            logger.info(f"Fetched {len(assignments)} assignments for course {course_id}")
            return assignments

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
            user_id = self._get_current_user_id()

            if course_id:
                # Get grades for specific course
                result = self._call_function('gradereport_user_get_grade_items', {
                    'courseid': int(course_id),
                    'userid': user_id
                })

                if not result.get('success'):
                    return []

                data = result.get('data', {})
                grade_items = data.get('usergrades', [{}])[0].get('gradeitems', [])

                grades = []
                for item in grade_items:
                    grades.append({
                        'course_id': course_id,
                        'assignment_id': str(item.get('id')),
                        'assignment_name': item.get('itemname'),
                        'score': item.get('graderaw'),
                        'max_points': item.get('grademax'),
                        'percentage': item.get('percentageformatted'),
                        'feedback': item.get('feedback')
                    })

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
            # Get course contents
            result = self._call_function('core_course_get_contents', {
                'courseid': int(course_id)
            })

            if not result.get('success'):
                return []

            sections = result.get('data', [])

            downloaded_files = []
            os.makedirs(destination_dir, exist_ok=True)

            for section in sections:
                for module in section.get('modules', []):
                    # Check if module has content files
                    for content_file in module.get('contents', []):
                        file_url = content_file.get('fileurl')

                        if file_url:
                            # Download file
                            file_path = self._download_file(
                                file_url,
                                destination_dir,
                                content_file.get('filename', 'file')
                            )

                            if file_path:
                                downloaded_files.append(file_path)

            logger.info(f"Downloaded {len(downloaded_files)} files from course {course_id}")
            return downloaded_files

        except Exception as e:
            logger.error(f"Error downloading materials: {e}")
            return []

    def _call_function(
        self,
        function_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call Moodle Web Services function.

        Args:
            function_name: Web Services function name
            params: Function parameters

        Returns:
            API response
        """
        try:
            # Build request parameters
            request_params = {
                'wstoken': self.api_token,
                'wsfunction': function_name,
                'moodlewsrestformat': 'json'
            }

            # Add function-specific parameters
            request_params.update(params)

            # Make request
            response = requests.get(
                self.webservice_url,
                params=request_params,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()

                # Check for Moodle error
                if isinstance(data, dict) and 'exception' in data:
                    return {
                        'success': False,
                        'error': data.get('message', 'Moodle API error')
                    }

                return {
                    'success': True,
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            logger.error(f"Moodle API call failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_current_user_id(self) -> int:
        """Get current user's Moodle ID."""
        try:
            result = self._call_function('core_webservice_get_site_info', {})

            if result.get('success'):
                return result.get('data', {}).get('userid', 0)
            else:
                return 0

        except Exception as e:
            logger.error(f"Failed to get user ID: {e}")
            return 0

    def _download_file(
        self,
        file_url: str,
        destination_dir: str,
        filename: str
    ) -> Optional[str]:
        """
        Download a file from Moodle.

        Args:
            file_url: File URL (with token)
            destination_dir: Local directory
            filename: Filename

        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            # Add token to URL
            url_with_token = f"{file_url}&token={self.api_token}"

            # Download file
            response = requests.get(url_with_token, timeout=30)

            if response.status_code == 200:
                file_path = os.path.join(destination_dir, filename)

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Downloaded file: {filename}")
                return file_path
            else:
                logger.error(f"Failed to download file {filename}: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error downloading file {filename}: {e}")
            return None
