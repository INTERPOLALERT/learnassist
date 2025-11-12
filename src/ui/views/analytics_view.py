"""
Academic Command Center - Analytics View
Comprehensive analytics dashboard with productivity insights.
"""

import logging
import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.analytics.analytics_engine import AnalyticsEngine
from features.analytics.progress_tracker import ProgressTracker

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AnalyticsView(QWidget):
    """
    Analytics dashboard view.

    Displays:
    - Productivity overview metrics
    - Daily trend charts
    - Time distribution analysis
    - Performance insights
    - Active goals progress
    - Comparison metrics
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize analytics view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize backend components
        self.analytics = AnalyticsEngine(self.user_id, self.db)
        self.progress = ProgressTracker(self.user_id, self.db)

        # Time period selection
        self.current_period = 30  # days

        # Initialize UI
        self._init_ui()

        # Load initial data
        self.refresh()

        logger.info("Analytics view initialized")

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header with title and period selector
        header_layout = QHBoxLayout()

        title = QLabel("📈 Analytics Dashboard")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Period selector
        period_label = QLabel("Time Period:")
        period_label.setFont(QFont("Arial", 12))
        header_layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 Days", "Last 30 Days", "Last 90 Days"])
        self.period_combo.setCurrentIndex(1)  # Default: 30 days
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        self.period_combo.setMinimumWidth(150)
        header_layout.addWidget(self.period_combo)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # Section 1: Overview Cards
        overview_section = self._create_overview_section()
        scroll_layout.addWidget(overview_section)

        # Section 2: Performance Insights
        insights_section = self._create_insights_section()
        scroll_layout.addWidget(insights_section)

        # Section 3: Active Goals
        goals_section = self._create_goals_section()
        scroll_layout.addWidget(goals_section)

        # Section 4: Time Distribution
        time_dist_section = self._create_time_distribution_section()
        scroll_layout.addWidget(time_dist_section)

        # Section 5: Trends
        trends_section = self._create_trends_section()
        scroll_layout.addWidget(trends_section)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def _create_overview_section(self) -> QFrame:
        """Create overview cards section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("Productivity Overview")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Cards grid
        cards_grid = QGridLayout()
        cards_grid.setSpacing(10)

        # Create cards (will be populated in refresh)
        self.overview_cards = {}

        card_specs = [
            ('sessions', 'Focus Sessions', '#3498db'),
            ('hours', 'Study Hours', '#2ecc71'),
            ('focus_score', 'Avg Focus Score', '#f39c12'),
            ('tasks', 'Tasks Completed', '#9b59b6'),
            ('completion_rate', 'Task Rate', '#e74c3c'),
            ('essays', 'Essays Written', '#1abc9c')
        ]

        for i, (key, label, color) in enumerate(card_specs):
            card = self._create_metric_card(label, "...", color)
            self.overview_cards[key] = card
            cards_grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(cards_grid)

        return section

    def _create_metric_card(self, label: str, value: str, color: str) -> QFrame:
        """Create a metric card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 6px;
                padding: 15px;
            }}
        """)
        card.setMinimumHeight(100)

        layout = QVBoxLayout(card)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        title_label = QLabel(label)
        title_label.setFont(QFont("Arial", 12))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Store reference to value label for updates
        card.value_label = value_label

        return card

    def _create_insights_section(self) -> QFrame:
        """Create performance insights section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("💡 Performance Insights")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Insights container
        self.insights_container = QVBoxLayout()
        layout.addLayout(self.insights_container)

        # Recommendations title
        rec_title = QLabel("✨ Recommendations")
        rec_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        rec_title.setStyleSheet("margin-top: 10px;")
        layout.addWidget(rec_title)

        # Recommendations container
        self.recommendations_container = QVBoxLayout()
        layout.addLayout(self.recommendations_container)

        return section

    def _create_goals_section(self) -> QFrame:
        """Create active goals section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("🎯 Active Goals")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Goals container
        self.goals_container = QVBoxLayout()
        layout.addLayout(self.goals_container)

        return section

    def _create_time_distribution_section(self) -> QFrame:
        """Create time distribution section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("⏰ Time Distribution")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Time distribution info
        self.time_dist_label = QLabel("Loading...")
        self.time_dist_label.setWordWrap(True)
        self.time_dist_label.setStyleSheet("padding: 10px; font-size: 13px;")
        layout.addWidget(self.time_dist_label)

        # Hourly breakdown
        hourly_title = QLabel("Hourly Breakdown:")
        hourly_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        hourly_title.setStyleSheet("margin-top: 10px;")
        layout.addWidget(hourly_title)

        self.hourly_container = QVBoxLayout()
        layout.addLayout(self.hourly_container)

        return section

    def _create_trends_section(self) -> QFrame:
        """Create trends section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("📊 Productivity Trends")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Trend info
        self.trend_label = QLabel("Loading...")
        self.trend_label.setWordWrap(True)
        self.trend_label.setStyleSheet("padding: 10px; font-size: 13px;")
        layout.addWidget(self.trend_label)

        return section

    def _on_period_changed(self, index: int):
        """Handle period selection change."""
        periods = [7, 30, 90]
        self.current_period = periods[index]
        self.refresh()

    def refresh(self):
        """Refresh all analytics data."""
        logger.info("Refreshing analytics data...")

        # Update overview cards
        self._update_overview_cards()

        # Update insights
        self._update_insights()

        # Update goals
        self._update_goals()

        # Update time distribution
        self._update_time_distribution()

        # Update trends
        self._update_trends()

        logger.info("Analytics data refreshed")

    def _update_overview_cards(self):
        """Update overview metric cards."""
        try:
            overview = self.analytics.get_productivity_overview(days=self.current_period)

            if overview['success']:
                # Focus sessions
                self.overview_cards['sessions'].value_label.setText(
                    str(overview['focus']['work_sessions'])
                )

                # Study hours
                self.overview_cards['hours'].value_label.setText(
                    f"{overview['focus']['total_hours']}"
                )

                # Focus score
                self.overview_cards['focus_score'].value_label.setText(
                    f"{overview['focus']['avg_focus_score']:.0f}%"
                )

                # Tasks completed
                self.overview_cards['tasks'].value_label.setText(
                    str(overview['tasks']['completed'])
                )

                # Task completion rate
                self.overview_cards['completion_rate'].value_label.setText(
                    f"{overview['tasks']['completion_rate']:.0f}%"
                )

                # Essays
                self.overview_cards['essays'].value_label.setText(
                    str(overview['essays']['completed'])
                )

        except Exception as e:
            logger.error(f"Failed to update overview cards: {e}")

    def _update_insights(self):
        """Update performance insights."""
        try:
            # Clear existing
            while self.insights_container.count():
                child = self.insights_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            while self.recommendations_container.count():
                child = self.recommendations_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Get new insights
            insights_data = self.analytics.get_performance_insights()

            if insights_data['success']:
                # Add insights
                for insight in insights_data['insights']:
                    label = QLabel(f"• {insight}")
                    label.setWordWrap(True)
                    label.setStyleSheet("padding: 5px; font-size: 13px;")
                    self.insights_container.addWidget(label)

                # Add recommendations
                for rec in insights_data['recommendations']:
                    label = QLabel(f"→ {rec}")
                    label.setWordWrap(True)
                    label.setStyleSheet("padding: 5px; font-size: 13px; color: #27ae60;")
                    self.recommendations_container.addWidget(label)

        except Exception as e:
            logger.error(f"Failed to update insights: {e}")

    def _update_goals(self):
        """Update active goals display."""
        try:
            # Clear existing
            while self.goals_container.count():
                child = self.goals_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Get active goals
            goals_data = self.progress.get_active_goals()

            if goals_data['success'] and goals_data['goals']:
                for goal in goals_data['goals'][:5]:  # Show top 5
                    goal_widget = self._create_goal_widget(goal)
                    self.goals_container.addWidget(goal_widget)
            else:
                no_goals = QLabel("No active goals. Create goals to track your progress!")
                no_goals.setStyleSheet("padding: 10px; color: #95a5a6; font-style: italic;")
                self.goals_container.addWidget(no_goals)

        except Exception as e:
            logger.error(f"Failed to update goals: {e}")

    def _create_goal_widget(self, goal: dict) -> QFrame:
        """Create a goal progress widget."""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 10px;
                margin: 5px 0;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setSpacing(5)

        # Goal title
        title = QLabel(goal['title'])
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Progress info
        progress_text = f"{goal['current_value']} / {goal['target_value']} {goal['metric']}"
        progress_label = QLabel(progress_text)
        progress_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(progress_label)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(goal['percentage']))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{goal['percentage']:.0f}%")
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        layout.addWidget(progress_bar)

        return widget

    def _update_time_distribution(self):
        """Update time distribution display."""
        try:
            time_dist = self.analytics.get_time_distribution(days=self.current_period)

            if time_dist['success']:
                # Summary text
                summary_parts = []

                if time_dist['peak_hour']:
                    hour = time_dist['peak_hour']['hour']
                    minutes = time_dist['peak_hour']['total_minutes']
                    summary_parts.append(f"Peak productivity hour: {hour:02d}:00 ({minutes} minutes)")

                if time_dist['peak_day']:
                    day_name = time_dist['peak_day']['day_name']
                    minutes = time_dist['peak_day']['total_minutes']
                    summary_parts.append(f"Most productive day: {day_name} ({minutes} minutes)")

                if summary_parts:
                    self.time_dist_label.setText("\n".join(summary_parts))
                else:
                    self.time_dist_label.setText("Not enough data yet. Complete more focus sessions!")

                # Clear hourly container
                while self.hourly_container.count():
                    child = self.hourly_container.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                # Show top hours
                if time_dist['hourly_distribution']:
                    sorted_hours = sorted(
                        time_dist['hourly_distribution'],
                        key=lambda x: x['total_minutes'],
                        reverse=True
                    )[:5]

                    for hour_data in sorted_hours:
                        hour_text = f"{hour_data['hour']:02d}:00 - {hour_data['total_minutes']} min ({hour_data['session_count']} sessions)"
                        hour_label = QLabel(hour_text)
                        hour_label.setStyleSheet("padding: 3px; font-size: 12px;")
                        self.hourly_container.addWidget(hour_label)

        except Exception as e:
            logger.error(f"Failed to update time distribution: {e}")

    def _update_trends(self):
        """Update productivity trends display."""
        try:
            trends = self.analytics.get_daily_trends(days=min(14, self.current_period))

            if trends['success']:
                if trends['trend'] == 'no_data':
                    self.trend_label.setText("Start tracking sessions to see your productivity trends!")
                elif trends['trend'] == 'insufficient_data':
                    self.trend_label.setText(f"Tracked {trends.get('days_analyzed', 0)} days. Keep going to see trends!")
                else:
                    trend_emoji = {
                        'improving': '📈',
                        'stable': '➡️',
                        'declining': '📉'
                    }
                    trend_text = {
                        'improving': 'Your productivity is improving! Keep up the great work!',
                        'stable': 'Your productivity is stable. You\'re maintaining consistency.',
                        'declining': 'Your productivity has declined. Time to refocus and rebuild momentum.'
                    }

                    emoji = trend_emoji.get(trends['trend'], '')
                    text = trend_text.get(trends['trend'], '')

                    self.trend_label.setText(f"{emoji} {text}\n\nAnalyzed {trends.get('days_analyzed', 0)} days of data.")

        except Exception as e:
            logger.error(f"Failed to update trends: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    view = AnalyticsView(user_id="test_user")
    view.setGeometry(100, 100, 1000, 800)
    view.show()

    sys.exit(app.exec())
