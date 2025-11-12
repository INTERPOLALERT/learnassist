"""
Analytics Dashboard View - Phase 6 Sprint 4
Central analytics hub displaying performance metrics and insights.

Features:
- Performance score overview
- Study time statistics
- Grade trends visualization
- Active goals display
- Recent achievements
- Progress insights

Author: Academic Command Center
Phase: 6 Sprint 4
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QProgressBar, QScrollArea,
    QGridLayout, QFrame, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from typing import Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database import DatabaseManager
from features.analytics.progress_tracker import ProgressTracker
from features.analytics.performance_analytics import PerformanceAnalytics
from features.analytics.goal_system import GoalSystem
from features.analytics.study_analytics import StudyAnalytics
from features.analytics.achievement_system import AchievementSystem

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AnalyticsDashboardView(QWidget):
    """
    Analytics Dashboard - Central hub for all analytics.
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Analytics Dashboard.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize analytics systems
        self.progress_tracker = ProgressTracker(user_id, self.db)
        self.performance_analytics = PerformanceAnalytics(user_id, self.db)
        self.goal_system = GoalSystem(user_id, self.db)
        self.study_analytics = StudyAnalytics(user_id, self.db)
        self.achievement_system = AchievementSystem(user_id, self.db)

        self._init_ui()
        self._load_data()

        # Auto-refresh every 5 minutes
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(300000)  # 5 minutes

    def _init_ui(self):
        """Initialize user interface."""

        main_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Analytics Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Top metrics row
        metrics_row = self._create_metrics_row()
        scroll_layout.addLayout(metrics_row)

        # Performance section
        performance_section = self._create_performance_section()
        scroll_layout.addWidget(performance_section)

        # Two-column layout
        columns_layout = QHBoxLayout()

        # Left column
        left_column = QVBoxLayout()

        # Study overview
        study_section = self._create_study_section()
        left_column.addWidget(study_section)

        # Active goals
        goals_section = self._create_goals_section()
        left_column.addWidget(goals_section)

        columns_layout.addLayout(left_column, 1)

        # Right column
        right_column = QVBoxLayout()

        # Recent achievements
        achievements_section = self._create_achievements_section()
        right_column.addWidget(achievements_section)

        # Insights and recommendations
        insights_section = self._create_insights_section()
        right_column.addWidget(insights_section)

        columns_layout.addLayout(right_column, 1)

        scroll_layout.addLayout(columns_layout)

        # Refresh button
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self._load_data)
        refresh_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 10px; }"
        )
        scroll_layout.addWidget(refresh_btn)

        scroll_layout.addStretch()

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)

        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def _create_metrics_row(self) -> QHBoxLayout:
        """Create top metrics row with key statistics."""

        layout = QHBoxLayout()

        # Metric cards
        self.performance_card = self._create_metric_card("Performance", "0", "#4CAF50")
        self.level_card = self._create_metric_card("Level", "0", "#2196F3")
        self.streak_card = self._create_metric_card("Streak", "0 days", "#FF9800")
        self.study_time_card = self._create_metric_card("Study Time", "0h", "#9C27B0")

        layout.addWidget(self.performance_card)
        layout.addWidget(self.level_card)
        layout.addWidget(self.streak_card)
        layout.addWidget(self.study_time_card)

        return layout

    def _create_metric_card(self, title: str, value: str, color: str) -> QGroupBox:
        """Create a metric card widget."""

        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {color};
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: gray;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName(f"{title.lower()}_value")
        value_font = QFont()
        value_font.setPointSize(20)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def _create_performance_section(self) -> QGroupBox:
        """Create performance overview section."""

        section = QGroupBox("Performance Overview")
        layout = QVBoxLayout()

        # Performance score bar
        self.performance_label = QLabel("Overall Score: 0/100")
        layout.addWidget(self.performance_label)

        self.performance_bar = QProgressBar()
        self.performance_bar.setMaximum(100)
        self.performance_bar.setValue(0)
        self.performance_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.performance_bar)

        # Component scores
        components_layout = QGridLayout()

        self.assignment_score_label = QLabel("Assignments: -")
        self.grade_score_label = QLabel("Grades: -")
        self.consistency_score_label = QLabel("Consistency: -")
        self.efficiency_score_label = QLabel("Efficiency: -")

        components_layout.addWidget(self.assignment_score_label, 0, 0)
        components_layout.addWidget(self.grade_score_label, 0, 1)
        components_layout.addWidget(self.consistency_score_label, 1, 0)
        components_layout.addWidget(self.efficiency_score_label, 1, 1)

        layout.addLayout(components_layout)

        # Grade level
        self.grade_level_label = QLabel("Grade Level: -")
        grade_level_font = QFont()
        grade_level_font.setBold(True)
        self.grade_level_label.setFont(grade_level_font)
        layout.addWidget(self.grade_level_label)

        section.setLayout(layout)
        return section

    def _create_study_section(self) -> QGroupBox:
        """Create study statistics section."""

        section = QGroupBox("Study Statistics (Last 30 Days)")
        layout = QVBoxLayout()

        self.total_study_label = QLabel("Total Study Time: 0h")
        self.session_count_label = QLabel("Focus Sessions: 0")
        self.daily_avg_label = QLabel("Daily Average: 0h")
        self.productivity_label = QLabel("Productivity Score: 0/100")

        layout.addWidget(self.total_study_label)
        layout.addWidget(self.session_count_label)
        layout.addWidget(self.daily_avg_label)
        layout.addWidget(self.productivity_label)

        # Most productive time
        self.productive_time_label = QLabel("Most Productive: -")
        self.productive_time_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.productive_time_label)

        section.setLayout(layout)
        return section

    def _create_goals_section(self) -> QGroupBox:
        """Create active goals section."""

        section = QGroupBox("Active Goals")
        layout = QVBoxLayout()

        self.goals_list = QListWidget()
        self.goals_list.setMaximumHeight(200)
        layout.addWidget(self.goals_list)

        view_all_btn = QPushButton("View All Goals")
        view_all_btn.clicked.connect(self._view_all_goals)
        layout.addWidget(view_all_btn)

        section.setLayout(layout)
        return section

    def _create_achievements_section(self) -> QGroupBox:
        """Create recent achievements section."""

        section = QGroupBox("Recent Achievements")
        layout = QVBoxLayout()

        # Stats
        self.achievement_stats_label = QLabel("0/0 Achievements Unlocked")
        layout.addWidget(self.achievement_stats_label)

        # Recent achievements list
        self.achievements_list = QListWidget()
        self.achievements_list.setMaximumHeight(180)
        layout.addWidget(self.achievements_list)

        view_all_btn = QPushButton("View All Achievements")
        view_all_btn.clicked.connect(self._view_all_achievements)
        layout.addWidget(view_all_btn)

        section.setLayout(layout)
        return section

    def _create_insights_section(self) -> QGroupBox:
        """Create insights and recommendations section."""

        section = QGroupBox("Insights & Recommendations")
        layout = QVBoxLayout()

        self.insights_list = QListWidget()
        self.insights_list.setMaximumHeight(200)
        layout.addWidget(self.insights_list)

        section.setLayout(layout)
        return section

    def _load_data(self):
        """Load all analytics data."""

        try:
            logger.info("Loading analytics dashboard data...")

            # Get performance score
            performance_data = self.performance_analytics.calculate_performance_score(30)
            if performance_data.get('success'):
                score = performance_data['overall_score']
                grade_level = performance_data['grade_level']
                components = performance_data['components']

                self.performance_bar.setValue(int(score))
                self.performance_label.setText(f"Overall Score: {score:.1f}/100")
                self.grade_level_label.setText(f"Grade Level: {grade_level.replace('_', ' ').title()}")

                # Update metric card
                perf_value_label = self.performance_card.findChild(QLabel, "performance_value")
                if perf_value_label:
                    perf_value_label.setText(f"{score:.0f}")

                # Component scores
                self.assignment_score_label.setText(f"Assignments: {components['assignment_completion']:.0f}/100")
                self.grade_score_label.setText(f"Grades: {components['grade_average']:.0f}/100")
                self.consistency_score_label.setText(f"Consistency: {components['consistency']:.0f}/100")
                self.efficiency_score_label.setText(f"Efficiency: {components['efficiency']:.0f}/100")

            # Get user stats (level)
            user_stats = self.achievement_system.get_user_stats()
            if user_stats.get('success'):
                level = user_stats['level']
                level_value_label = self.level_card.findChild(QLabel, "level_value")
                if level_value_label:
                    level_value_label.setText(str(level))

            # Get study streak
            streak_data = self.study_analytics.track_study_streak()
            if streak_data.get('success'):
                streak = streak_data['current_streak']
                streak_value_label = self.streak_card.findChild(QLabel, "streak_value")
                if streak_value_label:
                    streak_value_label.setText(f"{streak} days")

            # Get study overview
            study_overview = self.study_analytics.get_study_overview(30)
            if study_overview.get('success'):
                total_hours = study_overview['total_study_time']['hours']
                session_count = study_overview['session_count']
                daily_avg = study_overview['daily_average']['hours']

                # Update metric card
                study_value_label = self.study_time_card.findChild(QLabel, "study time_value")
                if study_value_label:
                    study_value_label.setText(f"{total_hours:.1f}h")

                self.total_study_label.setText(f"Total Study Time: {total_hours:.1f}h")
                self.session_count_label.setText(f"Focus Sessions: {session_count}")
                self.daily_avg_label.setText(f"Daily Average: {daily_avg:.1f}h")

            # Get productivity metrics
            productivity = self.study_analytics.calculate_productivity_metrics(30)
            if productivity.get('success') and 'overall_productivity' in productivity:
                prod_score = productivity['overall_productivity']
                self.productivity_label.setText(f"Productivity Score: {prod_score:.0f}/100")

            # Get study patterns
            patterns = self.study_analytics.analyze_study_patterns(30)
            if patterns.get('success') and 'most_productive_hour_label' in patterns:
                productive_time = patterns['most_productive_hour_label']
                productive_day = patterns['most_productive_day']
                self.productive_time_label.setText(f"Most Productive: {productive_day} at {productive_time}")

            # Get active goals
            self._load_active_goals()

            # Get recent achievements
            self._load_recent_achievements()

            # Get insights
            self._load_insights()

            logger.info("Analytics dashboard data loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")

    def _load_active_goals(self):
        """Load active goals."""

        try:
            self.goals_list.clear()

            goals_data = self.goal_system.get_active_goals()
            if goals_data.get('success'):
                goals = goals_data['goals'][:5]  # Top 5

                for goal in goals:
                    item_text = f"{goal['title']} - {goal['progress_percentage']:.0f}%"
                    item = QListWidgetItem(item_text)

                    # Color based on progress
                    if goal['progress_percentage'] >= 75:
                        item.setForeground(QColor("#4CAF50"))
                    elif goal['progress_percentage'] >= 50:
                        item.setForeground(QColor("#FF9800"))
                    else:
                        item.setForeground(QColor("#f44336"))

                    self.goals_list.addItem(item)

                if not goals:
                    self.goals_list.addItem("No active goals")

        except Exception as e:
            logger.error(f"Failed to load goals: {e}")

    def _load_recent_achievements(self):
        """Load recent achievements."""

        try:
            self.achievements_list.clear()

            user_stats = self.achievement_system.get_user_stats()
            if user_stats.get('success'):
                unlocked = user_stats['achievements_unlocked']
                total = user_stats['total_achievements']
                self.achievement_stats_label.setText(f"{unlocked}/{total} Achievements Unlocked")

                recent = user_stats.get('recent_achievements', [])[:5]

                for achievement in recent:
                    item_text = f"{achievement['name']} (+{achievement['points']} pts)"
                    item = QListWidgetItem(item_text)
                    item.setForeground(QColor("#FFD700"))  # Gold color
                    self.achievements_list.addItem(item)

                if not recent:
                    self.achievements_list.addItem("No achievements yet")

        except Exception as e:
            logger.error(f"Failed to load achievements: {e}")

    def _load_insights(self):
        """Load insights and recommendations."""

        try:
            self.insights_list.clear()

            # Get progress report
            report = self.progress_tracker.generate_progress_report(30)
            if report.get('success'):
                insights = report.get('insights', [])
                recommendations = report.get('recommendations', [])

                # Add insights
                for insight in insights[:3]:
                    item = QListWidgetItem(f"=¡ {insight}")
                    self.insights_list.addItem(item)

                # Add recommendations
                for rec in recommendations[:3]:
                    item = QListWidgetItem(f"=ª {rec}")
                    item.setForeground(QColor("#2196F3"))
                    self.insights_list.addItem(item)

                if not insights and not recommendations:
                    self.insights_list.addItem("No insights available yet")

        except Exception as e:
            logger.error(f"Failed to load insights: {e}")

    def _view_all_goals(self):
        """Open goals management view."""
        logger.info("View all goals clicked")
        # TODO: Open goals management view

    def _view_all_achievements(self):
        """Open achievements view."""
        logger.info("View all achievements clicked")
        # TODO: Open achievements view


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AnalyticsDashboardView(user_id="test_user")
    window.resize(1000, 800)
    window.show()
    sys.exit(app.exec())
