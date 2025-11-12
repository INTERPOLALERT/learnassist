"""
Progress Reports View - Phase 6 Sprint 4
Detailed progress reports with subject breakdowns and trends.

Features:
- Comprehensive progress reports
- Subject-wise analysis
- Grade trend visualization
- Period selection
- Export capabilities
- Detailed insights

Author: Academic Command Center
Phase: 6 Sprint 4
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QComboBox, QTextEdit, QTabWidget, QProgressBar,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from typing import Optional
from datetime import datetime
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database import DatabaseManager
from features.analytics.progress_tracker import ProgressTracker
from features.analytics.performance_analytics import PerformanceAnalytics

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ProgressReportsView(QWidget):
    """
    Progress Reports View - Detailed academic progress analysis.
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Progress Reports View.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize analytics
        self.progress_tracker = ProgressTracker(user_id, self.db)
        self.performance_analytics = PerformanceAnalytics(user_id, self.db)

        self._init_ui()
        self._load_report()

    def _init_ui(self):
        """Initialize user interface."""

        layout = QVBoxLayout()

        # Title and period selector
        header_layout = QHBoxLayout()

        title_label = QLabel("Progress Reports")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Period selector
        period_label = QLabel("Period:")
        header_layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])
        self.period_combo.setCurrentIndex(1)  # Default 30 days
        self.period_combo.currentIndexChanged.connect(self._load_report)
        header_layout.addWidget(self.period_combo)

        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self._load_report)
        generate_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 8px 16px; }"
        )
        header_layout.addWidget(generate_btn)

        layout.addLayout(header_layout)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Overall Progress
        overall_tab = self._create_overall_tab()
        tabs.addTab(overall_tab, "Overall Progress")

        # Tab 2: Subject Analysis
        subject_tab = self._create_subject_tab()
        tabs.addTab(subject_tab, "By Subject")

        # Tab 3: Trends
        trends_tab = self._create_trends_tab()
        tabs.addTab(trends_tab, "Trends")

        # Tab 4: Insights
        insights_tab = self._create_insights_tab()
        tabs.addTab(insights_tab, "Insights")

        layout.addWidget(tabs)

        # Export button
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self._export_report)
        layout.addWidget(export_btn)

        self.setLayout(layout)

    def _create_overall_tab(self) -> QWidget:
        """Create overall progress tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Summary cards
        summary_layout = QHBoxLayout()

        self.completion_card = self._create_summary_card("Assignment Completion", "0%", "#4CAF50")
        self.grade_card = self._create_summary_card("Average Grade", "0%", "#2196F3")
        self.study_card = self._create_summary_card("Study Time", "0h", "#9C27B0")
        self.tasks_card = self._create_summary_card("Tasks Completed", "0", "#FF9800")

        summary_layout.addWidget(self.completion_card)
        summary_layout.addWidget(self.grade_card)
        summary_layout.addWidget(self.study_card)
        summary_layout.addWidget(self.tasks_card)

        layout.addLayout(summary_layout)

        # Detailed statistics
        stats_group = QGroupBox("Detailed Statistics")
        stats_layout = QVBoxLayout()

        self.assignments_label = QLabel("Assignments: 0 completed / 0 total")
        self.avg_grade_label = QLabel("Average Grade: 0%")
        self.study_hours_label = QLabel("Total Study Hours: 0h")
        self.sessions_label = QLabel("Focus Sessions: 0")
        self.tasks_label = QLabel("Tasks: 0 completed / 0 total")
        self.completion_rate_label = QLabel("Completion Rate: 0%")

        stats_layout.addWidget(self.assignments_label)
        stats_layout.addWidget(self.avg_grade_label)
        stats_layout.addWidget(self.study_hours_label)
        stats_layout.addWidget(self.sessions_label)
        stats_layout.addWidget(self.tasks_label)
        stats_layout.addWidget(self.completion_rate_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_subject_tab(self) -> QWidget:
        """Create subject analysis tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Subject table
        self.subject_table = QTableWidget()
        self.subject_table.setColumnCount(5)
        self.subject_table.setHorizontalHeaderLabels([
            "Subject", "Assignments", "Completed", "Completion %", "Avg Grade"
        ])
        self.subject_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.subject_table)

        widget.setLayout(layout)
        return widget

    def _create_trends_tab(self) -> QWidget:
        """Create trends analysis tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Grade trend
        grade_trend_group = QGroupBox("Grade Trend")
        grade_trend_layout = QVBoxLayout()

        self.grade_trend_label = QLabel("Trend Direction: -")
        self.grade_trend_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        grade_trend_layout.addWidget(self.grade_trend_label)

        self.trend_description = QLabel("No trend data available")
        grade_trend_layout.addWidget(self.trend_description)

        grade_trend_group.setLayout(grade_trend_layout)
        layout.addWidget(grade_trend_group)

        # Completion trend
        completion_trend_group = QGroupBox("Assignment Completion Trend")
        completion_trend_layout = QVBoxLayout()

        self.completion_trend_label = QLabel("Total Completed: 0")
        completion_trend_layout.addWidget(self.completion_trend_label)

        completion_trend_group.setLayout(completion_trend_layout)
        layout.addWidget(completion_trend_group)

        # Risk assessment
        risk_group = QGroupBox("Risk Assessment")
        risk_layout = QVBoxLayout()

        self.risk_level_label = QLabel("Risk Level: -")
        self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        risk_layout.addWidget(self.risk_level_label)

        self.risk_score_label = QLabel("Risk Score: 0/100")
        risk_layout.addWidget(self.risk_score_label)

        self.warning_signs_list = QTextEdit()
        self.warning_signs_list.setMaximumHeight(100)
        self.warning_signs_list.setReadOnly(True)
        risk_layout.addWidget(self.warning_signs_list)

        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_insights_tab(self) -> QWidget:
        """Create insights tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Insights
        insights_group = QGroupBox("Key Insights")
        insights_layout = QVBoxLayout()

        self.insights_text = QTextEdit()
        self.insights_text.setReadOnly(True)
        self.insights_text.setMinimumHeight(150)
        insights_layout.addWidget(self.insights_text)

        insights_group.setLayout(insights_layout)
        layout.addWidget(insights_group)

        # Recommendations
        recommendations_group = QGroupBox("Recommendations")
        recommendations_layout = QVBoxLayout()

        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMinimumHeight(150)
        recommendations_layout.addWidget(self.recommendations_text)

        recommendations_group.setLayout(recommendations_layout)
        layout.addWidget(recommendations_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_summary_card(self, title: str, value: str, color: str) -> QGroupBox:
        """Create a summary card widget."""

        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: gray;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def _load_report(self):
        """Load progress report data."""

        try:
            # Get selected period
            period_text = self.period_combo.currentText()
            days = self._get_days_from_period(period_text)

            logger.info(f"Loading progress report for {days} days...")

            # Get overall progress
            overall = self.progress_tracker.get_overall_progress(days)
            if overall.get('success'):
                self._update_overall_tab(overall)

            # Get subject progress
            subjects = self.progress_tracker.get_subject_progress()
            if subjects.get('success'):
                self._update_subject_tab(subjects)

            # Get grade trends
            grade_trends = self.progress_tracker.get_grade_trends(days=days)
            if grade_trends.get('success'):
                self._update_trends_tab(grade_trends, days)

            # Get risk assessment
            risk_data = self.performance_analytics.assess_risk()
            if risk_data.get('success'):
                self._update_risk_assessment(risk_data)

            # Get progress report with insights
            report = self.progress_tracker.generate_progress_report(days)
            if report.get('success'):
                self._update_insights_tab(report)

            logger.info("Progress report loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load progress report: {e}")

    def _update_overall_tab(self, data: dict):
        """Update overall progress tab."""

        assignments = data.get('assignments', {})
        study_time = data.get('study_time', {})
        tasks = data.get('tasks', {})

        # Update summary cards
        completion_value = self.completion_card.findChild(QLabel, "assignment_completion_value")
        if completion_value:
            completion_value.setText(f"{assignments.get('completion_rate', 0):.0f}%")

        grade_value = self.grade_card.findChild(QLabel, "average_grade_value")
        if grade_value:
            grade_value.setText(f"{assignments.get('average_grade', 0):.0f}%")

        study_value = self.study_card.findChild(QLabel, "study_time_value")
        if study_value:
            study_value.setText(f"{study_time.get('total_hours', 0):.1f}h")

        tasks_value = self.tasks_card.findChild(QLabel, "tasks_completed_value")
        if tasks_value:
            tasks_value.setText(f"{tasks.get('completed', 0)}")

        # Update detailed labels
        self.assignments_label.setText(
            f"Assignments: {assignments.get('completed', 0)} completed / {assignments.get('total', 0)} total"
        )
        self.avg_grade_label.setText(f"Average Grade: {assignments.get('average_grade', 0):.1f}%")
        self.study_hours_label.setText(f"Total Study Hours: {study_time.get('total_hours', 0):.1f}h")
        self.sessions_label.setText(f"Focus Sessions: {study_time.get('session_count', 0)}")
        self.tasks_label.setText(
            f"Tasks: {tasks.get('completed', 0)} completed / {tasks.get('total', 0)} total"
        )
        self.completion_rate_label.setText(f"Task Completion Rate: {tasks.get('completion_rate', 0):.1f}%")

    def _update_subject_tab(self, data: dict):
        """Update subject analysis tab."""

        subjects = data.get('subjects', [])

        self.subject_table.setRowCount(len(subjects))

        for row, subject in enumerate(subjects):
            # Subject name
            self.subject_table.setItem(row, 0, QTableWidgetItem(subject['name']))

            # Total assignments
            self.subject_table.setItem(row, 1, QTableWidgetItem(str(subject['total_assignments'])))

            # Completed
            self.subject_table.setItem(row, 2, QTableWidgetItem(str(subject['completed_assignments'])))

            # Completion percentage
            completion_item = QTableWidgetItem(f"{subject['completion_rate']:.1f}%")
            if subject['completion_rate'] >= 80:
                completion_item.setForeground(QColor("#4CAF50"))
            elif subject['completion_rate'] >= 60:
                completion_item.setForeground(QColor("#FF9800"))
            else:
                completion_item.setForeground(QColor("#f44336"))
            self.subject_table.setItem(row, 3, completion_item)

            # Average grade
            grade_item = QTableWidgetItem(f"{subject['average_grade']:.1f}%")
            if subject['average_grade'] >= 90:
                grade_item.setForeground(QColor("#4CAF50"))
            elif subject['average_grade'] >= 80:
                grade_item.setForeground(QColor("#2196F3"))
            elif subject['average_grade'] >= 70:
                grade_item.setForeground(QColor("#FF9800"))
            else:
                grade_item.setForeground(QColor("#f44336"))
            self.subject_table.setItem(row, 4, grade_item)

    def _update_trends_tab(self, grade_trends: dict, days: int):
        """Update trends tab."""

        # Grade trend
        trend_direction = grade_trends.get('trend_direction', 'insufficient_data')
        self.grade_trend_label.setText(f"Trend Direction: {trend_direction.replace('_', ' ').title()}")

        # Color code based on trend
        if trend_direction == 'improving':
            self.grade_trend_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50;")
            self.trend_description.setText("Your grades are trending upward. Keep up the great work!")
        elif trend_direction == 'declining':
            self.grade_trend_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f44336;")
            self.trend_description.setText("Your grades are declining. Consider reviewing study strategies.")
        elif trend_direction == 'stable':
            self.grade_trend_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2196F3;")
            self.trend_description.setText("Your grade performance is consistent.")
        else:
            self.grade_trend_label.setStyleSheet("font-weight: bold; font-size: 14px; color: gray;")
            self.trend_description.setText("Not enough data for trend analysis yet.")

        # Completion trend
        completion_trends = self.progress_tracker.get_completion_trends(days)
        if completion_trends.get('success'):
            total_completed = completion_trends.get('total_completed', 0)
            self.completion_trend_label.setText(f"Total Completed: {total_completed} assignments")

    def _update_risk_assessment(self, data: dict):
        """Update risk assessment."""

        risk_level = data.get('risk_level', 'low')
        risk_score = data.get('risk_score', 0)
        warning_signs = data.get('warning_signs', [])

        self.risk_level_label.setText(f"Risk Level: {risk_level.upper()}")

        # Color code based on risk
        if risk_level == 'critical':
            self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #d32f2f;")
        elif risk_level == 'high':
            self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f44336;")
        elif risk_level == 'medium':
            self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FF9800;")
        else:
            self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50;")

        self.risk_score_label.setText(f"Risk Score: {risk_score}/100")

        # Warning signs
        if warning_signs:
            signs_text = "\n".join([f"  {sign}" for sign in warning_signs])
            self.warning_signs_list.setText(signs_text)
        else:
            self.warning_signs_list.setText("No warning signs detected")

    def _update_insights_tab(self, report: dict):
        """Update insights tab."""

        insights = report.get('insights', [])
        recommendations = report.get('recommendations', [])

        # Insights
        if insights:
            insights_text = "\n\n".join([f"=¡ {insight}" for insight in insights])
            self.insights_text.setText(insights_text)
        else:
            self.insights_text.setText("No insights available yet. Keep tracking your progress!")

        # Recommendations
        if recommendations:
            recommendations_text = "\n\n".join([f"=ª {rec}" for rec in recommendations])
            self.recommendations_text.setText(recommendations_text)
        else:
            self.recommendations_text.setText("No specific recommendations at this time. Keep up the good work!")

    def _get_days_from_period(self, period_text: str) -> int:
        """Get days from period selection."""

        if "7 Days" in period_text:
            return 7
        elif "30 Days" in period_text:
            return 30
        elif "90 Days" in period_text:
            return 90
        else:  # All Time
            return 365

    def _export_report(self):
        """Export progress report."""

        try:
            logger.info("Exporting progress report...")

            # Get current period
            period_text = self.period_combo.currentText()
            days = self._get_days_from_period(period_text)

            # Generate report
            report = self.progress_tracker.generate_progress_report(days)

            if report.get('success'):
                # Create report text
                report_text = self._format_report_for_export(report, period_text)

                # Save to file (simple text file for now)
                filename = f"progress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w') as f:
                    f.write(report_text)

                logger.info(f"Report exported to {filename}")

                # Show success message
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Progress report exported to:\n{filename}"
                )

        except Exception as e:
            logger.error(f"Failed to export report: {e}")

    def _format_report_for_export(self, report: dict, period: str) -> str:
        """Format report data for export."""

        lines = []
        lines.append("=" * 60)
        lines.append("ACADEMIC PROGRESS REPORT")
        lines.append("=" * 60)
        lines.append(f"Period: {period}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Overall stats
        overall = report.get('overall', {})
        if overall.get('success'):
            lines.append("OVERALL STATISTICS")
            lines.append("-" * 60)

            assignments = overall.get('assignments', {})
            lines.append(f"Assignments: {assignments.get('completed', 0)}/{assignments.get('total', 0)} ({assignments.get('completion_rate', 0):.1f}%)")
            lines.append(f"Average Grade: {assignments.get('average_grade', 0):.1f}%")

            study_time = overall.get('study_time', {})
            lines.append(f"Total Study Time: {study_time.get('total_hours', 0):.1f} hours")
            lines.append(f"Focus Sessions: {study_time.get('session_count', 0)}")
            lines.append("")

        # Insights
        insights = report.get('insights', [])
        if insights:
            lines.append("KEY INSIGHTS")
            lines.append("-" * 60)
            for insight in insights:
                lines.append(f"" {insight}")
            lines.append("")

        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 60)
            for rec in recommendations:
                lines.append(f"" {rec}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("End of Report")
        lines.append("=" * 60)

        return "\n".join(lines)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ProgressReportsView(user_id="test_user")
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())
