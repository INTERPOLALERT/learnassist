"""
Academic Command Center - Canvas Integration View
UI for Canvas LMS integration and grade tracking.
"""

import logging
import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.canvas.canvas_sync import CanvasSyncManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CanvasSetupDialog(QDialog):
    """Dialog for Canvas API setup."""

    def __init__(self, parent=None):
        """Initialize Canvas setup dialog."""
        super().__init__(parent)

        self.setWindowTitle("Canvas LMS Setup")
        self.setMinimumWidth(500)

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Enter your Canvas LMS credentials to sync grades and assignments.\n\n"
            "You can find your API key in Canvas Settings → Approved Integrations."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px;")
        layout.addWidget(instructions)

        # Form
        form_layout = QFormLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://canvas.university.edu")
        form_layout.addRow("Canvas URL:", self.url_input)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Your Canvas API token")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API Key:", self.api_key_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_credentials(self):
        """Get entered credentials."""
        return {
            'url': self.url_input.text().strip(),
            'api_key': self.api_key_input.text().strip()
        }


class CanvasView(QWidget):
    """
    Canvas integration view.

    Features:
    - Canvas connection status
    - Grade synchronization
    - Grade statistics
    - Graded assignments list
    - Pending submissions
    - Sync history
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize Canvas view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize backend
        self.canvas_manager = CanvasSyncManager(self.user_id, self.db)

        # Initialize UI
        self._init_ui()

        # Load data
        self.refresh()

        logger.info("Canvas view initialized")

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("🎓 Canvas Integration")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Setup button
        setup_btn = QPushButton("⚙️ Setup")
        setup_btn.clicked.connect(self._on_setup_clicked)
        setup_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(setup_btn)

        # Sync button
        self.sync_btn = QPushButton("🔄 Sync Grades")
        self.sync_btn.clicked.connect(self._on_sync_clicked)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        header_layout.addWidget(self.sync_btn)

        main_layout.addLayout(header_layout)

        # Connection status
        self.status_label = QLabel("⚠️ Canvas not configured")
        self.status_label.setStyleSheet("""
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            font-size: 13px;
            border-left: 4px solid #f39c12;
        """)
        main_layout.addWidget(self.status_label)

        # Statistics section
        stats_section = self._create_statistics_section()
        main_layout.addWidget(stats_section)

        # Two-column layout for assignments
        content_layout = QHBoxLayout()

        # Left: Graded assignments
        graded_section = self._create_graded_assignments_section()
        content_layout.addWidget(graded_section)

        # Right: Sync history
        history_section = self._create_sync_history_section()
        content_layout.addWidget(history_section)

        main_layout.addLayout(content_layout)

    def _create_statistics_section(self) -> QFrame:
        """Create grade statistics section."""
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
        title = QLabel("📊 Grade Statistics")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Statistics cards
        cards_layout = QHBoxLayout()

        self.total_graded_card = self._create_stat_card("Total Graded", "0", "#3498db")
        cards_layout.addWidget(self.total_graded_card)

        self.average_grade_card = self._create_stat_card("Average Grade", "0%", "#2ecc71")
        cards_layout.addWidget(self.average_grade_card)

        self.highest_grade_card = self._create_stat_card("Highest Grade", "0%", "#f39c12")
        cards_layout.addWidget(self.highest_grade_card)

        self.lowest_grade_card = self._create_stat_card("Lowest Grade", "0%", "#e74c3c")
        cards_layout.addWidget(self.lowest_grade_card)

        layout.addLayout(cards_layout)

        # Grade distribution
        self.distribution_label = QLabel("No grade data available")
        self.distribution_label.setStyleSheet("padding: 10px; font-size: 12px;")
        layout.addWidget(self.distribution_label)

        return section

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a statistics card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 6px;
                padding: 15px;
            }}
        """)
        card.setMinimumHeight(80)

        layout = QVBoxLayout(card)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Store reference for updates
        card.value_label = value_label

        return card

    def _create_graded_assignments_section(self) -> QFrame:
        """Create graded assignments section."""
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
        title = QLabel("✅ Graded Assignments")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Assignments list
        self.graded_list = QListWidget()
        layout.addWidget(self.graded_list)

        return section

    def _create_sync_history_section(self) -> QFrame:
        """Create sync history section."""
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
        title = QLabel("📝 Sync History")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # History list
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)

        return section

    def _on_setup_clicked(self):
        """Handle setup button click."""
        dialog = CanvasSetupDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            credentials = dialog.get_credentials()

            if not credentials['url'] or not credentials['api_key']:
                QMessageBox.warning(self, "Validation Error", "Both Canvas URL and API key are required!")
                return

            # Save credentials
            result = self.canvas_manager.set_canvas_credentials(
                credentials['api_key'],
                credentials['url']
            )

            if result['success']:
                QMessageBox.information(self, "Success", "Canvas credentials saved successfully!")
                self.status_label.setText("✅ Canvas connected")
                self.status_label.setStyleSheet("""
                    background-color: #d4edda;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 13px;
                    border-left: 4px solid #28a745;
                """)
            else:
                QMessageBox.critical(self, "Error", f"Failed to save credentials: {result.get('error')}")

    def _on_sync_clicked(self):
        """Handle sync button click."""
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("⏳ Syncing...")

        # Perform sync (simulated)
        result = self.canvas_manager.sync_grades(simulate=True)

        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄 Sync Grades")

        if result['success']:
            QMessageBox.information(
                self,
                "Sync Complete",
                f"Successfully synced {result['assignments_synced']} assignments!\n"
                f"Duration: {result['duration_seconds']} seconds"
            )
            self.refresh()
        else:
            QMessageBox.critical(self, "Sync Failed", f"Error: {result.get('error')}")

    def _update_statistics(self):
        """Update grade statistics display."""
        stats = self.canvas_manager.get_grade_statistics()

        if stats['success']:
            self.total_graded_card.value_label.setText(str(stats['total_graded']))
            self.average_grade_card.value_label.setText(f"{stats['average_grade']:.1f}%")
            self.highest_grade_card.value_label.setText(f"{stats.get('highest_grade', 0):.1f}%")
            self.lowest_grade_card.value_label.setText(f"{stats.get('lowest_grade', 0):.1f}%")

            # Update distribution
            if stats['total_graded'] > 0:
                dist = stats['grade_distribution']
                dist_text = f"Grade Distribution: " \
                           f"A: {dist.get('A', 0)} | " \
                           f"B: {dist.get('B', 0)} | " \
                           f"C: {dist.get('C', 0)} | " \
                           f"Below C: {dist.get('Below C', 0)}"
                self.distribution_label.setText(dist_text)
            else:
                self.distribution_label.setText("No grade data available")

    def _update_graded_assignments(self):
        """Update graded assignments list."""
        self.graded_list.clear()

        result = self.canvas_manager.get_graded_assignments()

        if result['success'] and result['assignments']:
            for assignment in result['assignments']:
                grade_str = f"{assignment.get('grade_received', 0):.1f}%"
                letter = assignment.get('grade_letter', '')
                course = assignment.get('course_name', 'Unknown')
                title = assignment.get('title', 'Untitled')

                item_text = f"{course} - {title}\nGrade: {grade_str} ({letter})"

                item = QListWidgetItem(item_text)
                self.graded_list.addItem(item)
        else:
            item = QListWidgetItem("No graded assignments yet.\nRun a sync to fetch grades from Canvas.")
            item.setForeground(Qt.GlobalColor.gray)
            self.graded_list.addItem(item)

    def _update_sync_history(self):
        """Update sync history display."""
        self.history_list.clear()

        result = self.canvas_manager.get_sync_history(limit=10)

        if result['success'] and result['history']:
            for sync in result['history']:
                sync_time = sync.get('started_at', '')[:16].replace('T', ' ')
                status = sync.get('sync_status', 'unknown')
                summary = sync.get('sync_summary', '')
                assignments = sync.get('assignments_synced', 0)

                status_icon = "✅" if status == "completed" else "❌"

                item_text = f"{status_icon} {sync_time} - {assignments} assignments\n{summary}"

                item = QListWidgetItem(item_text)
                self.history_list.addItem(item)
        else:
            item = QListWidgetItem("No sync history yet.\nClick 'Sync Grades' to get started.")
            item.setForeground(Qt.GlobalColor.gray)
            self.history_list.addItem(item)

    def refresh(self):
        """Refresh the view."""
        logger.info("Refreshing Canvas view...")

        self._update_statistics()
        self._update_graded_assignments()
        self._update_sync_history()

        logger.info("Canvas view refreshed")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    view = CanvasView(user_id="test_user")
    view.setGeometry(100, 100, 1200, 800)
    view.show()

    sys.exit(app.exec())
