"""
Achievements Display View - Phase 6 Sprint 4
Badge gallery, achievement tracking, and gamification progress.

Features:
- Achievement gallery with 17 achievements
- Progress tracking for locked achievements
- User stats (level, points, rank)
- Category filtering
- Badge display with tiers
- Recent unlocks

Author: Academic Command Center
Phase: 6 Sprint 4
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QScrollArea, QFrame,
    QGridLayout, QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from typing import Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database import DatabaseManager
from features.analytics.achievement_system import AchievementSystem

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AchievementCard(QFrame):
    """Custom widget for displaying an achievement."""

    def __init__(self, achievement: dict, parent=None):
        super().__init__(parent)
        self.achievement = achievement
        self._init_ui()

    def _init_ui(self):
        """Initialize achievement card UI."""

        layout = QVBoxLayout()

        # Determine colors based on tier and status
        if self.achievement['unlocked']:
            border_color = self._get_tier_color(self.achievement['tier'])
            bg_color = "#f5f5f5"
        else:
            border_color = "#cccccc"
            bg_color = "#fafafa"

        self.setStyleSheet(f"""
            QFrame {{
                border: 3px solid {border_color};
                border-radius: 10px;
                background-color: {bg_color};
                padding: 10px;
            }}
        """)

        # Icon and tier
        header_layout = QHBoxLayout()

        icon_label = QLabel(self.achievement['icon'])
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        header_layout.addWidget(icon_label)

        header_layout.addStretch()

        tier_label = QLabel(self.achievement['tier'].upper())
        tier_label.setStyleSheet(f"color: {border_color}; font-weight: bold; font-size: 10px;")
        header_layout.addWidget(tier_label)

        layout.addLayout(header_layout)

        # Name
        name_label = QLabel(self.achievement['name'])
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(12)
        name_label.setFont(name_font)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Description
        desc_label = QLabel(self.achievement['description'])
        desc_label.setStyleSheet("font-size: 10px; color: gray;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Points
        points_label = QLabel(f"+{self.achievement['points']} points")
        points_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #FF9800;")
        layout.addWidget(points_label)

        # Progress or unlock date
        if self.achievement['unlocked']:
            unlock_label = QLabel(f" Unlocked")
            unlock_label.setStyleSheet("font-size: 10px; color: #4CAF50; font-weight: bold;")
            layout.addWidget(unlock_label)
        else:
            # Progress bar
            progress_label = QLabel(f"Progress: {self.achievement['progress']}/{self.achievement['requirement_value']}")
            progress_label.setStyleSheet("font-size: 9px; color: gray;")
            layout.addWidget(progress_label)

            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            progress_bar.setValue(int(self.achievement['progress_percentage']))
            progress_bar.setTextVisible(False)
            progress_bar.setMaximumHeight(8)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                }
                QProgressBar::chunk {
                    background-color: #2196F3;
                }
            """)
            layout.addWidget(progress_bar)

        self.setLayout(layout)

    def _get_tier_color(self, tier: str) -> str:
        """Get color based on tier."""

        colors = {
            'bronze': '#CD7F32',
            'silver': '#C0C0C0',
            'gold': '#FFD700',
            'platinum': '#E5E4E2'
        }
        return colors.get(tier, '#999999')


class AchievementsView(QWidget):
    """
    Achievements Display View - Badge gallery and progress.
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Achievements View.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize achievement system
        self.achievement_system = AchievementSystem(user_id, self.db)

        self._init_ui()
        self._load_achievements()

    def _init_ui(self):
        """Initialize user interface."""

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Achievements")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # User stats section
        stats_section = self._create_stats_section()
        layout.addWidget(stats_section)

        # Filter section
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Category:")
        filter_layout.addWidget(filter_label)

        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All",
            "Study",
            "Streak",
            "Grades",
            "Goals",
            "Assignments",
            "Special"
        ])
        self.category_filter.currentTextChanged.connect(self._filter_achievements)
        filter_layout.addWidget(self.category_filter)

        filter_layout.addStretch()

        # Check for new achievements button
        check_btn = QPushButton("Check for New Achievements")
        check_btn.clicked.connect(self._check_new_achievements)
        check_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 8px 16px; }"
        )
        filter_layout.addWidget(check_btn)

        layout.addLayout(filter_layout)

        # Achievements grid (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.achievements_widget = QWidget()
        self.achievements_layout = QGridLayout()
        self.achievements_layout.setSpacing(15)
        self.achievements_widget.setLayout(self.achievements_layout)

        scroll.setWidget(self.achievements_widget)

        layout.addWidget(scroll)

        self.setLayout(layout)

    def _create_stats_section(self) -> QGroupBox:
        """Create user statistics section."""

        section = QGroupBox("Your Progress")
        layout = QHBoxLayout()

        # Level card
        level_card = self._create_stat_card("Level", "0", "#2196F3")
        layout.addWidget(level_card)

        # Points card
        points_card = self._create_stat_card("Points", "0", "#FF9800")
        layout.addWidget(points_card)

        # Rank card
        rank_card = self._create_stat_card("Rank", "Novice", "#9C27B0")
        layout.addWidget(rank_card)

        # Progress card
        progress_card = self._create_stat_card("Unlocked", "0/17", "#4CAF50")
        layout.addWidget(progress_card)

        self.level_card = level_card
        self.points_card = points_card
        self.rank_card = rank_card
        self.progress_card = progress_card

        section.setLayout(layout)
        return section

    def _create_stat_card(self, title: str, value: str, color: str) -> QGroupBox:
        """Create a stat card widget."""

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
        value_label.setObjectName(f"{title.lower()}_value")
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def _load_achievements(self):
        """Load achievements data."""

        try:
            # Load user stats
            stats = self.achievement_system.get_user_stats()
            if stats.get('success'):
                # Update stat cards
                level_value = self.level_card.findChild(QLabel, "level_value")
                if level_value:
                    level_value.setText(str(stats['level']))

                points_value = self.points_card.findChild(QLabel, "points_value")
                if points_value:
                    points_value.setText(str(stats['total_points']))

                rank_value = self.rank_card.findChild(QLabel, "rank_value")
                if rank_value:
                    rank_value.setText(stats['rank'])

                progress_value = self.progress_card.findChild(QLabel, "unlocked_value")
                if progress_value:
                    progress_value.setText(f"{stats['achievements_unlocked']}/{stats['total_achievements']}")

            # Load achievements
            self._display_achievements()

        except Exception as e:
            logger.error(f"Failed to load achievements: {e}")

    def _display_achievements(self, category: str = "All"):
        """Display achievements in grid."""

        try:
            # Clear existing
            while self.achievements_layout.count():
                item = self.achievements_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get achievements
            if category == "All":
                achievements_data = self.achievement_system.get_all_achievements()
            else:
                category_map = {
                    "Study": "study",
                    "Streak": "streak",
                    "Grades": "grades",
                    "Goals": "goals",
                    "Assignments": "assignments",
                    "Special": "special"
                }
                achievements_data = self.achievement_system.get_achievements_by_category(
                    category_map.get(category, "study")
                )

            if achievements_data.get('success'):
                achievements = achievements_data['achievements']

                # Display in grid (3 columns)
                row = 0
                col = 0
                max_cols = 3

                for achievement in achievements:
                    card = AchievementCard(achievement)
                    card.setMinimumHeight(200)
                    self.achievements_layout.addWidget(card, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                # Add empty state if no achievements
                if not achievements:
                    no_achievements_label = QLabel("No achievements in this category yet")
                    no_achievements_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    no_achievements_label.setStyleSheet("color: gray; font-size: 14px; padding: 40px;")
                    self.achievements_layout.addWidget(no_achievements_label, 0, 0, 1, max_cols)

        except Exception as e:
            logger.error(f"Failed to display achievements: {e}")

    def _filter_achievements(self):
        """Filter achievements by category."""

        category = self.category_filter.currentText()
        self._display_achievements(category)

    def _check_new_achievements(self):
        """Check for newly unlocked achievements."""

        try:
            from PyQt6.QtWidgets import QMessageBox

            result = self.achievement_system.check_achievements()

            if result.get('success'):
                newly_unlocked = result.get('newly_unlocked', [])

                if newly_unlocked:
                    # Show unlock message
                    messages = []
                    for achievement in newly_unlocked:
                        messages.append(
                            f"{achievement['icon']} {achievement['name']}\n"
                            f"{achievement['description']}\n"
                            f"+{achievement['points']} points ({achievement['tier'].upper()})"
                        )

                    QMessageBox.information(
                        self,
                        "< New Achievements Unlocked!",
                        "\n\n".join(messages)
                    )

                    # Reload
                    self._load_achievements()
                else:
                    QMessageBox.information(
                        self,
                        "No New Achievements",
                        "Keep working toward your goals to unlock more achievements!"
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to check achievements:\n{result.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(f"Failed to check new achievements: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AchievementsView(user_id="test_user")
    window.resize(1000, 800)
    window.show()
    sys.exit(app.exec())
