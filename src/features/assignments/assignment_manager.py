"""
Assignment Manager - Phase 2 Sprint 1
Handles CRUD operations and business logic for assignments
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class AssignmentManager:
    """
    Manages assignment operations.

    Handles creation, reading, updating, and deleting assignments,
    as well as grade calculations and filtering.
    """

    def __init__(self, db_manager, user_id: str):
        """
        Initialize Assignment Manager.

        Args:
            db_manager: DatabaseManager instance
            user_id: Current user ID
        """
        self.db = db_manager
        self.user_id = user_id
        logger.info(f"Assignment Manager initialized for user {user_id}")

    def create_assignment(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new assignment.

        Args:
            data: Assignment data dictionary containing:
                - title (required)
                - description
                - assignment_type
                - due_date
                - subject_id
                - priority
                - status
                - grade
                - max_grade
                - notes
                - canvas_assignment_id

        Returns:
            Assignment ID if successful, None otherwise
        """
        try:
            assignment_id = str(uuid.uuid4())

            query = """
                INSERT INTO assignments (
                    id, user_id, subject_id, title, description, assignment_type,
                    due_date, status, priority, grade, max_grade, notes,
                    canvas_assignment_id, canvas_course_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                assignment_id,
                self.user_id,
                data.get('subject_id'),
                data.get('title', 'Untitled Assignment'),
                data.get('description', ''),
                data.get('assignment_type', 'homework'),
                data.get('due_date'),
                data.get('status', 'pending'),
                data.get('priority', 'medium'),
                data.get('grade'),
                data.get('max_grade', 100.0),
                data.get('notes', ''),
                data.get('canvas_assignment_id'),
                data.get('canvas_course_id'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )

            self.db.execute_query(query, params)
            logger.info(f"Created assignment: {assignment_id} - {data.get('title')}")

            return assignment_id

        except Exception as e:
            logger.error(f"Failed to create assignment: {e}")
            return None

    def get_assignment(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single assignment by ID.

        Args:
            assignment_id: Assignment ID

        Returns:
            Assignment dictionary or None
        """
        try:
            query = """
                SELECT a.*, s.name as subject_name, s.color as subject_color
                FROM assignments a
                LEFT JOIN subjects s ON a.subject_id = s.id
                WHERE a.id = ? AND a.user_id = ?
            """

            result = self.db.fetch_one(query, (assignment_id, self.user_id))

            if result:
                return self._row_to_dict(result)
            return None

        except Exception as e:
            logger.error(f"Failed to get assignment {assignment_id}: {e}")
            return None

    def get_assignments(self,
                       status: Optional[str] = None,
                       subject_id: Optional[str] = None,
                       priority: Optional[str] = None,
                       overdue_only: bool = False,
                       search_term: Optional[str] = None,
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get filtered list of assignments.

        Args:
            status: Filter by status (pending, in_progress, completed, submitted)
            subject_id: Filter by subject
            priority: Filter by priority (low, medium, high)
            overdue_only: Only show overdue assignments
            search_term: Search in title/description
            limit: Maximum number of results

        Returns:
            List of assignment dictionaries
        """
        try:
            query = """
                SELECT a.*, s.name as subject_name, s.color as subject_color
                FROM assignments a
                LEFT JOIN subjects s ON a.subject_id = s.id
                WHERE a.user_id = ?
            """

            params = [self.user_id]

            # Add filters
            if status:
                query += " AND a.status = ?"
                params.append(status)

            if subject_id:
                query += " AND a.subject_id = ?"
                params.append(subject_id)

            if priority:
                query += " AND a.priority = ?"
                params.append(priority)

            if overdue_only:
                query += " AND a.due_date < datetime('now') AND a.status NOT IN ('completed', 'submitted')"

            if search_term:
                query += " AND (a.title LIKE ? OR a.description LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])

            # Order by due date
            query += " ORDER BY CASE WHEN a.due_date IS NULL THEN 1 ELSE 0 END, a.due_date ASC"

            if limit:
                query += f" LIMIT {limit}"

            results = self.db.fetch_all(query, tuple(params))

            assignments = [self._row_to_dict(row) for row in results]

            # Add computed fields
            for assignment in assignments:
                self._add_computed_fields(assignment)

            logger.debug(f"Retrieved {len(assignments)} assignments")
            return assignments

        except Exception as e:
            logger.error(f"Failed to get assignments: {e}")
            return []

    def update_assignment(self, assignment_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing assignment.

        Args:
            assignment_id: Assignment ID
            data: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build dynamic update query
            fields = []
            params = []

            updateable_fields = [
                'title', 'description', 'assignment_type', 'due_date',
                'subject_id', 'status', 'priority', 'grade', 'max_grade',
                'notes', 'submitted_date', 'completion_percentage'
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
            params.extend([assignment_id, self.user_id])

            query = f"""
                UPDATE assignments
                SET {', '.join(fields)}
                WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(query, tuple(params))
            logger.info(f"Updated assignment: {assignment_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to update assignment {assignment_id}: {e}")
            return False

    def delete_assignment(self, assignment_id: str) -> bool:
        """
        Delete an assignment.

        Args:
            assignment_id: Assignment ID

        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM assignments WHERE id = ? AND user_id = ?"
            self.db.execute_query(query, (assignment_id, self.user_id))
            logger.info(f"Deleted assignment: {assignment_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete assignment {assignment_id}: {e}")
            return False

    def mark_completed(self, assignment_id: str, grade: Optional[float] = None) -> bool:
        """
        Mark an assignment as completed.

        Args:
            assignment_id: Assignment ID
            grade: Optional grade to record

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                'status': 'completed',
                'completion_percentage': 100.0,
                'submitted_date': datetime.now().isoformat()
            }

            if grade is not None:
                data['grade'] = grade

            return self.update_assignment(assignment_id, data)

        except Exception as e:
            logger.error(f"Failed to mark assignment completed: {e}")
            return False

    def calculate_grade_letter(self, grade: float, max_grade: float = 100.0) -> str:
        """
        Calculate letter grade from numeric grade.

        Args:
            grade: Numeric grade
            max_grade: Maximum possible grade

        Returns:
            Letter grade (A+, A, B+, etc.)
        """
        if grade is None or max_grade is None or max_grade == 0:
            return "N/A"

        percentage = (grade / max_grade) * 100

        if percentage >= 97:
            return "A+"
        elif percentage >= 93:
            return "A"
        elif percentage >= 90:
            return "A-"
        elif percentage >= 87:
            return "B+"
        elif percentage >= 83:
            return "B"
        elif percentage >= 80:
            return "B-"
        elif percentage >= 77:
            return "C+"
        elif percentage >= 73:
            return "C"
        elif percentage >= 70:
            return "C-"
        elif percentage >= 67:
            return "D+"
        elif percentage >= 63:
            return "D"
        elif percentage >= 60:
            return "D-"
        else:
            return "F"

    def calculate_gpa(self, assignments: Optional[List[Dict[str, Any]]] = None) -> float:
        """
        Calculate current GPA from graded assignments.

        Args:
            assignments: List of assignments (optional, will fetch if None)

        Returns:
            GPA on 4.0 scale
        """
        try:
            if assignments is None:
                assignments = self.get_assignments(status='completed')

            # Filter to only graded assignments
            graded = [a for a in assignments if a.get('grade') is not None and a.get('max_grade', 0) > 0]

            if not graded:
                return 0.0

            # Convert letter grades to GPA points
            grade_points = {
                'A+': 4.0, 'A': 4.0, 'A-': 3.7,
                'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                'C+': 2.3, 'C': 2.0, 'C-': 1.7,
                'D+': 1.3, 'D': 1.0, 'D-': 0.7,
                'F': 0.0
            }

            total_points = 0.0
            for assignment in graded:
                letter = self.calculate_grade_letter(assignment['grade'], assignment.get('max_grade', 100.0))
                total_points += grade_points.get(letter, 0.0)

            gpa = total_points / len(graded)
            return round(gpa, 2)

        except Exception as e:
            logger.error(f"Failed to calculate GPA: {e}")
            return 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get assignment statistics.

        Returns:
            Dictionary with stats (total, completed, overdue, avg_grade, gpa)
        """
        try:
            all_assignments = self.get_assignments()

            stats = {
                'total': len(all_assignments),
                'pending': len([a for a in all_assignments if a['status'] == 'pending']),
                'in_progress': len([a for a in all_assignments if a['status'] == 'in_progress']),
                'completed': len([a for a in all_assignments if a['status'] in ['completed', 'submitted']]),
                'overdue': len([a for a in all_assignments if a.get('is_overdue', False)]),
                'avg_grade': 0.0,
                'gpa': 0.0
            }

            # Calculate average grade
            graded = [a for a in all_assignments if a.get('grade') is not None and a.get('max_grade', 0) > 0]
            if graded:
                total_percentage = sum((a['grade'] / a.get('max_grade', 100.0)) * 100 for a in graded)
                stats['avg_grade'] = round(total_percentage / len(graded), 1)

            # Calculate GPA
            stats['gpa'] = self.calculate_gpa(all_assignments)

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        if not row:
            return {}

        return {
            'id': row[0],
            'user_id': row[1],
            'subject_id': row[2],
            'title': row[3],
            'description': row[4],
            'assignment_type': row[5],
            'created_at': row[6],
            'due_date': row[7],
            'submitted_date': row[8],
            'updated_at': row[9],
            'status': row[10],
            'priority': row[11],
            'completion_percentage': row[12],
            'grade': row[13],
            'max_grade': row[14],
            'grade_letter': row[15],
            'canvas_assignment_id': row[16],
            'canvas_course_id': row[17],
            'notes': row[18],
            'subject_name': row[19] if len(row) > 19 else None,
            'subject_color': row[20] if len(row) > 20 else '#3498db'
        }

    def _add_computed_fields(self, assignment: Dict[str, Any]) -> None:
        """Add computed fields to assignment dictionary."""
        # Days until due
        if assignment.get('due_date'):
            try:
                due_date = datetime.fromisoformat(assignment['due_date'].replace('Z', '+00:00'))
                now = datetime.now()
                delta = due_date - now

                assignment['days_until_due'] = delta.days
                assignment['hours_until_due'] = int(delta.total_seconds() / 3600)
                assignment['is_overdue'] = delta.total_seconds() < 0 and assignment['status'] not in ['completed', 'submitted']

                # Human-readable time remaining
                if assignment['is_overdue']:
                    assignment['time_remaining'] = "Overdue"
                elif delta.days == 0:
                    assignment['time_remaining'] = "Due today"
                elif delta.days == 1:
                    assignment['time_remaining'] = "Due tomorrow"
                elif delta.days < 7:
                    assignment['time_remaining'] = f"Due in {delta.days} days"
                else:
                    assignment['time_remaining'] = f"Due in {delta.days // 7} weeks"
            except:
                assignment['days_until_due'] = None
                assignment['is_overdue'] = False
                assignment['time_remaining'] = "No due date"
        else:
            assignment['days_until_due'] = None
            assignment['is_overdue'] = False
            assignment['time_remaining'] = "No due date"

        # Grade letter
        if assignment.get('grade') is not None and assignment.get('max_grade'):
            assignment['grade_letter'] = self.calculate_grade_letter(
                assignment['grade'],
                assignment['max_grade']
            )
        else:
            assignment['grade_letter'] = "N/A"

        # Priority color
        priority_colors = {
            'low': '#95a5a6',
            'medium': '#f39c12',
            'high': '#e74c3c'
        }
        assignment['priority_color'] = priority_colors.get(assignment.get('priority', 'medium'), '#f39c12')
