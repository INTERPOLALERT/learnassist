"""
Blackboard LMS Connector
Integration with Blackboard Learn REST API.

API Documentation: https://developer.blackboard.com/portal/displayApi

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


class BlackboardConnector:
    """
    Blackboard Learn REST API connector.

    Features:
    - OAuth 2.0 authentication
    - Course listing
    - Assignment fetching
    - Grade retrieval
    - Content downloading
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Blackboard connector.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        self.base_url = None
        self.access_token = None
        self.session = requests.Session()
        self._connected = False

    def connect(
        self,
        base_url: str,
        api_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Connect to Blackboard instance.

        Args:
            base_url: Blackboard base URL (e.g., https://blackboard.school.edu)
            api_token: OAuth access token or API key
            **kwargs: Additional params (client_id, client_secret, etc.)

        Returns:
            Connection result
        """
        try:
            # Clean base URL
            self.base_url = base_url.rstrip('/')

            # For Blackboard, typically use OAuth 2.0
            # This is a simplified implementation
            client_id = kwargs.get('client_id')
            client_secret = kwargs.get('client_secret')

            if client_id and client_secret:
                # OAuth flow
                token_result = self._get_oauth_token(client_id, client_secret)

                if not token_result.get('success'):
                    return token_result

                self.access_token = token_result['access_token']
            else:
                # Direct token
                self.access_token = api_token

            # Set session headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })

            # Test connection by fetching user info
            test_result = self.test_connection()

            if test_result.get('success'):
                self._connected = True
                logger.info("Connected to Blackboard successfully")
            else:
                self._connected = False

            return test_result

        except Exception as e:
            logger.error(f"Blackboard connection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def is_connected(self) -> bool:
        """Check if connected to Blackboard."""
        return self._connected

    def test_connection(self) -> Dict[str, Any]:
        """Test Blackboard connection."""
        try:
            # Try to fetch current user info
            url = f"{self.base_url}/learn/api/public/v1/users/me"

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                user_data = response.json()

                return {
                    'success': True,
                    'message': 'Connected to Blackboard',
                    'user': user_data.get('userName', 'Unknown')
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
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
            url = f"{self.base_url}/learn/api/public/v2/courses"

            response = self.session.get(url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                courses = data.get('results', [])

                # Normalize course data
                normalized = []
                for course in courses:
                    normalized.append({
                        'id': course.get('id'),
                        'name': course.get('name', 'Unnamed Course'),
                        'course_id': course.get('courseId'),
                        'description': course.get('description', ''),
                        'created': course.get('created')
                    })

                logger.info(f"Fetched {len(normalized)} courses from Blackboard")
                return normalized
            else:
                logger.error(f"Failed to get courses: HTTP {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return []

    def get_assignments(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get assignments for a course.

        Args:
            course_id: Blackboard course ID

        Returns:
            List of assignment dictionaries
        """
        try:
            # Blackboard uses "contents" API for assignments
            url = f"{self.base_url}/learn/api/public/v1/courses/{course_id}/contents"

            response = self.session.get(url, timeout=15)

            if response.status_code == 200:
                contents = response.json().get('results', [])

                # Filter for assignments
                assignments = []
                for content in contents:
                    if content.get('contentHandler', {}).get('id') == 'resource/x-bb-assignment':
                        assignments.append({
                            'id': content.get('id'),
                            'name': content.get('title', 'Unnamed Assignment'),
                            'description': content.get('description', ''),
                            'due_at': content.get('availability', {}).get('until'),
                            'course_id': course_id,
                            'course_name': None  # Would need separate call
                        })

                logger.info(f"Fetched {len(assignments)} assignments for course {course_id}")
                return assignments
            else:
                logger.error(f"Failed to get assignments: HTTP {response.status_code}")
                return []

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
                url = f"{self.base_url}/learn/api/public/v2/courses/{course_id}/gradebook/columns"

                response = self.session.get(url, timeout=15)

                if response.status_code == 200:
                    columns = response.json().get('results', [])

                    grades = []
                    for column in columns:
                        # Would need additional API calls to get actual grades
                        grades.append({
                            'course_id': course_id,
                            'assignment_id': column.get('id'),
                            'assignment_name': column.get('name'),
                            'score': None,  # Requires user-specific grade fetch
                            'max_points': column.get('score', {}).get('possible')
                        })

                    return grades
                else:
                    return []
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
            url = f"{self.base_url}/learn/api/public/v1/courses/{course_id}/contents"

            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                return []

            contents = response.json().get('results', [])

            downloaded_files = []

            for content in contents:
                # Check if content has attachments
                if content.get('hasAttachments'):
                    # Fetch attachments (would require additional API call)
                    # Simplified for now
                    pass

            logger.info(f"Downloaded {len(downloaded_files)} files from course {course_id}")
            return downloaded_files

        except Exception as e:
            logger.error(f"Error downloading materials: {e}")
            return []

    def _get_oauth_token(
        self,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """
        Get OAuth access token.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret

        Returns:
            Token result with access_token
        """
        try:
            url = f"{self.base_url}/learn/api/public/v1/oauth2/token"

            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }

            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()

                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'expires_in': token_data.get('expires_in')
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            logger.error(f"OAuth token fetch failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
