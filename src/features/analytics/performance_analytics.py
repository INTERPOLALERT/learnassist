"""
Performance Analytics Engine - Phase 6 Sprint 3
Statistical analysis, predictions, and advanced performance insights.

Features:
- Performance scoring
- Trend predictions
- Risk assessment
- Comparative analytics
- Study efficiency metrics
- Success probability calculations

Author: Academic Command Center
Phase: 6 Sprint 3
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceScore:
    """Performance scoring data."""
    overall_score: float  # 0-100
    assignment_score: float  # 0-100
    grade_score: float  # 0-100
    consistency_score: float  # 0-100
    efficiency_score: float  # 0-100
    trend_score: float  # 0-100
    percentile: float  # Where user ranks (0-100)
    grade_level: str  # excellent, good, fair, needs_improvement


@dataclass
class PredictionData:
    """Performance prediction data."""
    metric: str
    current_value: float
    predicted_value: float
    confidence: float  # 0-100
    timeframe_days: int
    trend: str  # improving, declining, stable
    factors: List[str]


@dataclass
class RiskAssessment:
    """Academic risk assessment."""
    risk_level: str  # low, medium, high, critical
    risk_score: float  # 0-100
    at_risk_subjects: List[str]
    warning_signs: List[str]
    recommendations: List[str]


@dataclass
class StudyEfficiency:
    """Study efficiency metrics."""
    time_to_grade_ratio: float
    productivity_score: float  # 0-100
    focus_quality: float  # 0-100
    optimal_study_hours: float
    efficiency_trend: str


class PerformanceAnalytics:
    """
    Performance Analytics Engine.

    Provides:
    - Statistical performance analysis
    - Predictive modeling
    - Risk assessment
    - Efficiency metrics
    - Comparative analytics
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Performance Analytics Engine.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Performance Analytics initialized for user {user_id}")

    def calculate_performance_score(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate comprehensive performance score.

        Args:
            days: Period to analyze

        Returns:
            Performance scoring data
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get assignment metrics
            assignment_query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                AVG(CASE WHEN grade IS NOT NULL THEN grade ELSE NULL END) as avg_grade
            FROM assignments
            WHERE user_id = ? AND created_at >= ?
            """

            assignment_data = self.db.execute_query(
                assignment_query,
                (self.user_id, start_date),
                fetch_one=True
            )

            # Calculate component scores
            assignment_score = self._calculate_assignment_score(assignment_data)
            grade_score = assignment_data['avg_grade'] or 0
            consistency_score = self._calculate_consistency_score(days)
            efficiency_score = self._calculate_efficiency_score(days)
            trend_score = self._calculate_trend_score(days)

            # Overall score (weighted average)
            overall_score = (
                assignment_score * 0.25 +
                grade_score * 0.30 +
                consistency_score * 0.15 +
                efficiency_score * 0.15 +
                trend_score * 0.15
            )

            # Determine grade level
            if overall_score >= 90:
                grade_level = "excellent"
            elif overall_score >= 80:
                grade_level = "good"
            elif overall_score >= 70:
                grade_level = "fair"
            else:
                grade_level = "needs_improvement"

            # Calculate percentile (simplified)
            percentile = self._estimate_percentile(overall_score)

            return {
                'success': True,
                'overall_score': round(overall_score, 1),
                'components': {
                    'assignment_completion': round(assignment_score, 1),
                    'grade_average': round(grade_score, 1),
                    'consistency': round(consistency_score, 1),
                    'efficiency': round(efficiency_score, 1),
                    'trend': round(trend_score, 1)
                },
                'grade_level': grade_level,
                'percentile': round(percentile, 1),
                'period_days': days
            }

        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def predict_performance(self, metric: str = "grade", days_ahead: int = 30) -> Dict[str, Any]:
        """
        Predict future performance.

        Args:
            metric: Metric to predict (grade, completion_rate, study_time)
            days_ahead: Days to predict ahead

        Returns:
            Prediction data
        """
        try:
            # Get historical data (last 30 days)
            start_date = (datetime.now() - timedelta(days=30)).isoformat()

            if metric == "grade":
                # Get grade trend
                query = """
                SELECT AVG(grade) as avg_grade, DATE(due_date) as date
                FROM assignments
                WHERE user_id = ? AND grade IS NOT NULL AND due_date >= ?
                GROUP BY DATE(due_date)
                ORDER BY date ASC
                """

                historical = self.db.execute_query(
                    query,
                    (self.user_id, start_date),
                    fetch_all=True
                )

                if not historical or len(historical) < 2:
                    return {
                        'success': False,
                        'error': 'Insufficient historical data'
                    }

                # Simple linear prediction
                values = [h['avg_grade'] for h in historical]
                current_value = values[-1]

                # Calculate trend
                first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
                second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
                trend_slope = (second_half_avg - first_half_avg) / (len(values)//2)

                # Predict forward
                predicted_value = current_value + (trend_slope * (days_ahead / len(values)))
                predicted_value = max(0, min(100, predicted_value))  # Clamp to 0-100

                # Determine trend direction
                if trend_slope > 0.5:
                    trend = "improving"
                elif trend_slope < -0.5:
                    trend = "declining"
                else:
                    trend = "stable"

                # Calculate confidence based on data consistency
                variance = sum((v - sum(values)/len(values))**2 for v in values) / len(values)
                confidence = max(0, min(100, 100 - (variance / 10)))

                # Identify factors
                factors = self._identify_performance_factors(days_ahead)

                return {
                    'success': True,
                    'metric': metric,
                    'current_value': round(current_value, 1),
                    'predicted_value': round(predicted_value, 1),
                    'confidence': round(confidence, 1),
                    'timeframe_days': days_ahead,
                    'trend': trend,
                    'factors': factors
                }

            else:
                return {
                    'success': False,
                    'error': f'Prediction not implemented for metric: {metric}'
                }

        except Exception as e:
            logger.error(f"Failed to predict performance: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def assess_risk(self) -> Dict[str, Any]:
        """
        Assess academic risk level.

        Returns:
            Risk assessment data
        """
        try:
            risk_score = 0
            warning_signs = []
            at_risk_subjects = []

            # Check grade performance
            grade_query = """
            SELECT AVG(grade) as avg_grade
            FROM assignments
            WHERE user_id = ? AND grade IS NOT NULL
            AND created_at >= date('now', '-30 days')
            """

            grade_data = self.db.execute_query(
                grade_query,
                (self.user_id,),
                fetch_one=True
            )

            avg_grade = grade_data['avg_grade'] or 0
            if avg_grade < 70:
                risk_score += 30
                warning_signs.append("Average grade below 70%")
            elif avg_grade < 80:
                risk_score += 15
                warning_signs.append("Average grade below 80%")

            # Check completion rate
            completion_query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM assignments
            WHERE user_id = ? AND created_at >= date('now', '-30 days')
            """

            completion_data = self.db.execute_query(
                completion_query,
                (self.user_id,),
                fetch_one=True
            )

            total = completion_data['total'] or 0
            completed = completion_data['completed'] or 0
            completion_rate = (completed / total * 100) if total > 0 else 0

            if completion_rate < 50:
                risk_score += 30
                warning_signs.append("Assignment completion rate below 50%")
            elif completion_rate < 70:
                risk_score += 15
                warning_signs.append("Assignment completion rate below 70%")

            # Check overdue assignments
            overdue_query = """
            SELECT COUNT(*) as overdue
            FROM assignments
            WHERE user_id = ? AND status != 'completed'
            AND due_date < date('now')
            """

            overdue_data = self.db.execute_query(
                overdue_query,
                (self.user_id,),
                fetch_one=True
            )

            overdue_count = overdue_data['overdue'] or 0
            if overdue_count >= 5:
                risk_score += 20
                warning_signs.append(f"{overdue_count} overdue assignments")
            elif overdue_count >= 3:
                risk_score += 10
                warning_signs.append(f"{overdue_count} overdue assignments")

            # Check study time
            study_query = """
            SELECT SUM(duration_minutes) as total_minutes
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= date('now', '-7 days')
            """

            study_data = self.db.execute_query(
                study_query,
                (self.user_id,),
                fetch_one=True
            )

            study_minutes = study_data['total_minutes'] or 0
            if study_minutes < 300:  # Less than 5 hours per week
                risk_score += 20
                warning_signs.append("Low study time (< 5 hours/week)")

            # Check declining trend
            trend_query = """
            SELECT AVG(grade) as avg_grade, DATE(due_date) as date
            FROM assignments
            WHERE user_id = ? AND grade IS NOT NULL
            AND due_date >= date('now', '-30 days')
            GROUP BY DATE(due_date)
            ORDER BY date ASC
            """

            trend_data = self.db.execute_query(
                trend_query,
                (self.user_id,),
                fetch_all=True
            )

            if trend_data and len(trend_data) >= 4:
                first_half = trend_data[:len(trend_data)//2]
                second_half = trend_data[len(trend_data)//2:]

                first_avg = sum(t['avg_grade'] for t in first_half) / len(first_half)
                second_avg = sum(t['avg_grade'] for t in second_half) / len(second_half)

                if second_avg < first_avg - 5:
                    risk_score += 15
                    warning_signs.append("Grade trend declining")

            # Identify at-risk subjects
            subject_query = """
            SELECT s.name, AVG(a.grade) as avg_grade
            FROM subjects s
            LEFT JOIN assignments a ON a.subject_id = s.id
            WHERE s.user_id = ? AND a.grade IS NOT NULL
            GROUP BY s.id, s.name
            HAVING AVG(a.grade) < 75
            """

            subjects = self.db.execute_query(
                subject_query,
                (self.user_id,),
                fetch_all=True
            )

            if subjects:
                at_risk_subjects = [s['name'] for s in subjects]

            # Determine risk level
            if risk_score >= 60:
                risk_level = "critical"
            elif risk_score >= 40:
                risk_level = "high"
            elif risk_score >= 20:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Generate recommendations
            recommendations = self._generate_risk_recommendations(
                risk_level,
                warning_signs,
                at_risk_subjects
            )

            return {
                'success': True,
                'risk_level': risk_level,
                'risk_score': min(100, risk_score),
                'warning_signs': warning_signs,
                'at_risk_subjects': at_risk_subjects,
                'recommendations': recommendations
            }

        except Exception as e:
            logger.error(f"Failed to assess risk: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def analyze_study_efficiency(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze study time efficiency.

        Args:
            days: Period to analyze

        Returns:
            Study efficiency metrics
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get study time and grades
            query = """
            SELECT
                SUM(fs.duration_minutes) as total_minutes,
                COUNT(DISTINCT fs.id) as session_count,
                AVG(a.grade) as avg_grade
            FROM focus_sessions fs
            LEFT JOIN assignments a ON a.user_id = fs.user_id
                AND DATE(a.due_date) >= DATE(fs.start_time)
            WHERE fs.user_id = ? AND fs.start_time >= ?
            """

            data = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_one=True
            )

            total_minutes = data['total_minutes'] or 0
            session_count = data['session_count'] or 0
            avg_grade = data['avg_grade'] or 0

            # Calculate efficiency metrics
            if total_minutes > 0:
                time_to_grade_ratio = avg_grade / (total_minutes / 60) if total_minutes > 0 else 0

                # Productivity score (based on grade per hour)
                productivity_score = min(100, time_to_grade_ratio * 5)

                # Focus quality (based on session consistency)
                avg_session_minutes = total_minutes / session_count if session_count > 0 else 0
                if 25 <= avg_session_minutes <= 90:  # Optimal range
                    focus_quality = 90
                elif 15 <= avg_session_minutes <= 120:
                    focus_quality = 70
                else:
                    focus_quality = 50

                # Optimal study hours (based on performance)
                daily_hours = (total_minutes / 60) / days
                if avg_grade >= 85 and daily_hours >= 1.5:
                    optimal_study_hours = daily_hours
                    efficiency_trend = "optimal"
                elif avg_grade < 75:
                    optimal_study_hours = daily_hours * 1.3  # Recommend 30% more
                    efficiency_trend = "needs_increase"
                elif daily_hours > 5:
                    optimal_study_hours = daily_hours * 0.9  # Slightly less
                    efficiency_trend = "optimal_with_breaks"
                else:
                    optimal_study_hours = daily_hours
                    efficiency_trend = "stable"

                return {
                    'success': True,
                    'total_study_hours': round(total_minutes / 60, 1),
                    'session_count': session_count,
                    'avg_session_minutes': round(avg_session_minutes, 1),
                    'time_to_grade_ratio': round(time_to_grade_ratio, 2),
                    'productivity_score': round(productivity_score, 1),
                    'focus_quality': round(focus_quality, 1),
                    'optimal_study_hours_per_day': round(optimal_study_hours, 1),
                    'efficiency_trend': efficiency_trend,
                    'period_days': days
                }
            else:
                return {
                    'success': True,
                    'total_study_hours': 0,
                    'message': 'No study sessions recorded in period'
                }

        except Exception as e:
            logger.error(f"Failed to analyze study efficiency: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_comparative_analytics(self) -> Dict[str, Any]:
        """
        Get comparative analytics (user vs. typical performance).

        Returns:
            Comparative data
        """
        try:
            # Get user's performance
            user_query = """
            SELECT
                AVG(grade) as avg_grade,
                COUNT(*) as assignment_count
            FROM assignments
            WHERE user_id = ? AND grade IS NOT NULL
            AND created_at >= date('now', '-30 days')
            """

            user_data = self.db.execute_query(
                user_query,
                (self.user_id,),
                fetch_one=True
            )

            user_avg = user_data['avg_grade'] or 0
            user_count = user_data['assignment_count'] or 0

            # Simulated benchmark data (in production, this would query all users)
            benchmark_avg = 78.5  # Average performance
            benchmark_count = 15  # Average assignments per month

            # Calculate comparisons
            grade_diff = user_avg - benchmark_avg
            assignment_diff = user_count - benchmark_count

            if user_avg > 0:
                grade_percentile = min(100, max(0, 50 + (grade_diff * 2)))
            else:
                grade_percentile = 0

            return {
                'success': True,
                'user_performance': {
                    'average_grade': round(user_avg, 1),
                    'assignment_count': user_count
                },
                'benchmark': {
                    'average_grade': benchmark_avg,
                    'assignment_count': benchmark_count
                },
                'comparison': {
                    'grade_difference': round(grade_diff, 1),
                    'assignment_difference': assignment_diff,
                    'grade_percentile': round(grade_percentile, 1),
                    'performance_relative': 'above_average' if grade_diff > 0 else 'below_average' if grade_diff < 0 else 'average'
                }
            }

        except Exception as e:
            logger.error(f"Failed to get comparative analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_assignment_score(self, data: Dict[str, Any]) -> float:
        """Calculate assignment completion score."""
        total = data['total'] or 0
        completed = data['completed'] or 0

        if total == 0:
            return 0.0

        completion_rate = (completed / total) * 100
        return completion_rate

    def _calculate_consistency_score(self, days: int) -> float:
        """Calculate consistency score based on regular activity."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Count days with activity
            query = """
            SELECT COUNT(DISTINCT DATE(start_time)) as active_days
            FROM focus_sessions
            WHERE user_id = ? AND start_time >= ?
            """

            result = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_one=True
            )

            active_days = result['active_days'] or 0
            consistency_score = (active_days / days) * 100

            return min(100, consistency_score)

        except Exception as e:
            logger.error(f"Failed to calculate consistency: {e}")
            return 50.0

    def _calculate_efficiency_score(self, days: int) -> float:
        """Calculate study efficiency score."""
        efficiency_data = self.analyze_study_efficiency(days)

        if efficiency_data.get('success'):
            return efficiency_data.get('productivity_score', 50.0)

        return 50.0

    def _calculate_trend_score(self, days: int) -> float:
        """Calculate trend score (higher for improving trends)."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
            SELECT AVG(grade) as avg_grade, DATE(due_date) as date
            FROM assignments
            WHERE user_id = ? AND grade IS NOT NULL AND due_date >= ?
            GROUP BY DATE(due_date)
            ORDER BY date ASC
            """

            trends = self.db.execute_query(
                query,
                (self.user_id, start_date),
                fetch_all=True
            )

            if not trends or len(trends) < 2:
                return 70.0  # Neutral score

            values = [t['avg_grade'] for t in trends]
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

            diff = second_half_avg - first_half_avg

            if diff > 5:
                return 95.0  # Strongly improving
            elif diff > 2:
                return 85.0  # Improving
            elif diff > -2:
                return 75.0  # Stable
            elif diff > -5:
                return 60.0  # Slight decline
            else:
                return 40.0  # Declining

        except Exception as e:
            logger.error(f"Failed to calculate trend score: {e}")
            return 70.0

    def _estimate_percentile(self, score: float) -> float:
        """Estimate percentile based on score."""
        # Simple estimation (in production, would compare to all users)
        if score >= 95:
            return 99
        elif score >= 90:
            return 95
        elif score >= 85:
            return 85
        elif score >= 80:
            return 75
        elif score >= 75:
            return 60
        elif score >= 70:
            return 45
        elif score >= 65:
            return 30
        else:
            return 15

    def _identify_performance_factors(self, days: int) -> List[str]:
        """Identify factors affecting performance."""
        factors = []

        # Check study time trend
        study_query = """
        SELECT SUM(duration_minutes) as total_minutes
        FROM focus_sessions
        WHERE user_id = ? AND start_time >= date('now', '-7 days')
        """

        study_data = self.db.execute_query(
            study_query,
            (self.user_id,),
            fetch_one=True
        )

        study_hours = (study_data['total_minutes'] or 0) / 60
        if study_hours >= 20:
            factors.append("Consistent high study time")
        elif study_hours <= 5:
            factors.append("Low study time")

        # Check assignment completion
        completion_query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM assignments
        WHERE user_id = ? AND created_at >= date('now', '-30 days')
        """

        completion_data = self.db.execute_query(
            completion_query,
            (self.user_id,),
            fetch_one=True
        )

        total = completion_data['total'] or 0
        completed = completion_data['completed'] or 0
        rate = (completed / total * 100) if total > 0 else 0

        if rate >= 90:
            factors.append("Excellent assignment completion")
        elif rate <= 60:
            factors.append("Low assignment completion affecting grades")

        return factors

    def _generate_risk_recommendations(
        self,
        risk_level: str,
        warning_signs: List[str],
        at_risk_subjects: List[str]
    ) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []

        if risk_level in ["high", "critical"]:
            recommendations.append("Consider meeting with an academic advisor")
            recommendations.append("Create a structured study schedule")

        if "Average grade below" in str(warning_signs):
            recommendations.append("Focus on understanding concepts before memorization")
            recommendations.append("Seek tutoring or study groups for difficult subjects")

        if "Assignment completion rate" in str(warning_signs):
            recommendations.append("Break assignments into smaller, manageable tasks")
            recommendations.append("Set daily completion goals")

        if "overdue assignments" in str(warning_signs):
            recommendations.append("Prioritize completing overdue assignments immediately")
            recommendations.append("Use calendar reminders for upcoming deadlines")

        if "Low study time" in str(warning_signs):
            recommendations.append("Increase study time to at least 1-2 hours daily")
            recommendations.append("Use Pomodoro technique for focused sessions")

        if at_risk_subjects:
            recommendations.append(f"Dedicate extra time to: {', '.join(at_risk_subjects[:3])}")

        return recommendations[:8]


def create_performance_analytics(
    user_id: str,
    db_manager: Optional[DatabaseManager] = None
) -> PerformanceAnalytics:
    """
    Factory function to create Performance Analytics Engine.

    Args:
        user_id: Current user ID
        db_manager: Database manager instance

    Returns:
        PerformanceAnalytics instance
    """
    return PerformanceAnalytics(user_id, db_manager)
