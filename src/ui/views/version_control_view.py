"""
Academic Command Center - Version Control View
UI for managing essay snapshots and viewing version history.
"""

import logging
import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem, QGroupBox,
    QMessageBox, QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox, QTextEdit, QComboBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.version_control.snapshot_manager import SnapshotManager, SnapshotType
from features.version_control.diff_viewer import DiffViewer, ChangeType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CreateSnapshotDialog(QDialog):
    """Dialog for creating a manual snapshot."""

    def __init__(self, parent=None):
        """Initialize create snapshot dialog."""
        super().__init__(parent)

        self.setWindowTitle("Create Snapshot")
        self.setMinimumWidth(400)

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Create a manual snapshot of the current essay version.\n"
            "This allows you to save the current state before making major changes."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px;")
        layout.addWidget(instructions)

        # Form
        form_layout = QFormLayout()

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("e.g., Before major revision")
        form_layout.addRow("Label:", self.label_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_label(self) -> str:
        """Get entered label."""
        return self.label_input.text().strip()


class CompareSnapshotsDialog(QDialog):
    """Dialog for comparing two snapshots."""

    def __init__(self, snapshots, parent=None):
        """
        Initialize compare snapshots dialog.

        Args:
            snapshots: List of available snapshots
            parent: Parent widget
        """
        super().__init__(parent)

        self.snapshots = snapshots

        self.setWindowTitle("Compare Snapshots")
        self.setMinimumSize(900, 600)

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Selection section
        selection_layout = QHBoxLayout()

        # Snapshot 1
        left_layout = QVBoxLayout()
        left_label = QLabel("Original Version:")
        left_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        left_layout.addWidget(left_label)

        self.snapshot1_combo = QComboBox()
        for snap in self.snapshots:
            label = f"{snap['snapshot_label']} - {snap['created_at'][:16]}"
            self.snapshot1_combo.addItem(label, snap['id'])
        left_layout.addWidget(self.snapshot1_combo)

        selection_layout.addLayout(left_layout)

        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont("Arial", 24))
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        selection_layout.addWidget(arrow_label)

        # Snapshot 2
        right_layout = QVBoxLayout()
        right_label = QLabel("Modified Version:")
        right_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        right_layout.addWidget(right_label)

        self.snapshot2_combo = QComboBox()
        for snap in self.snapshots:
            label = f"{snap['snapshot_label']} - {snap['created_at'][:16]}"
            self.snapshot2_combo.addItem(label, snap['id'])
        if len(self.snapshots) > 1:
            self.snapshot2_combo.setCurrentIndex(1)
        right_layout.addWidget(self.snapshot2_combo)

        selection_layout.addLayout(right_layout)

        layout.addLayout(selection_layout)

        # Compare button
        compare_btn = QPushButton("🔍 Compare")
        compare_btn.clicked.connect(self._on_compare_clicked)
        compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(compare_btn)

        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Click 'Compare' to view differences...")
        layout.addWidget(self.results_text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _on_compare_clicked(self):
        """Handle compare button click."""
        snap1_id = self.snapshot1_combo.currentData()
        snap2_id = self.snapshot2_combo.currentData()

        if snap1_id == snap2_id:
            self.results_text.setPlainText("Please select two different snapshots to compare.")
            return

        # Emit signal or call parent method to perform comparison
        self.compare_requested(snap1_id, snap2_id)

    def compare_requested(self, snap1_id, snap2_id):
        """
        Request comparison (to be connected to parent).

        Args:
            snap1_id: First snapshot ID
            snap2_id: Second snapshot ID
        """
        # This will be overridden or connected in the parent
        pass

    def display_comparison(self, comparison_text: str):
        """
        Display comparison results.

        Args:
            comparison_text: Formatted comparison text
        """
        self.results_text.setPlainText(comparison_text)


class VersionControlView(QWidget):
    """
    Version control view for managing essay snapshots.

    Features:
    - Snapshot timeline
    - Create manual snapshots
    - Compare snapshots
    - Restore from snapshot
    - View snapshot details
    - Snapshot statistics
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize version control view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize backend
        self.snapshot_manager = SnapshotManager(self.user_id, self.db)
        self.diff_viewer = DiffViewer()

        # Current essay (for demo, we'll use the first essay)
        self.current_essay_id = None

        # Initialize UI
        self._init_ui()

        # Load data
        self.refresh()

        logger.info("Version control view initialized")

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("🔄 Version Control")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Essay selector
        self.essay_selector = QComboBox()
        self.essay_selector.setMinimumWidth(250)
        self.essay_selector.currentIndexChanged.connect(self._on_essay_changed)
        header_layout.addWidget(QLabel("Essay:"))
        header_layout.addWidget(self.essay_selector)

        # Create snapshot button
        create_btn = QPushButton("📸 Create Snapshot")
        create_btn.clicked.connect(self._on_create_snapshot_clicked)
        create_btn.setStyleSheet("""
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
        header_layout.addWidget(create_btn)

        main_layout.addLayout(header_layout)

        # Statistics section
        stats_section = self._create_statistics_section()
        main_layout.addWidget(stats_section)

        # Splitter for snapshots list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Snapshots list
        snapshots_section = self._create_snapshots_section()
        splitter.addWidget(snapshots_section)

        # Right: Snapshot details
        details_section = self._create_details_section()
        splitter.addWidget(details_section)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, stretch=1)

    def _create_statistics_section(self) -> QFrame:
        """Create statistics section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        section.setMaximumHeight(120)

        layout = QHBoxLayout(section)

        # Statistics cards
        self.total_snapshots_card = self._create_stat_card("Total Snapshots", "0", "#3498db")
        layout.addWidget(self.total_snapshots_card)

        self.manual_snapshots_card = self._create_stat_card("Manual", "0", "#2ecc71")
        layout.addWidget(self.manual_snapshots_card)

        self.auto_snapshots_card = self._create_stat_card("Auto-saved", "0", "#9b59b6")
        layout.addWidget(self.auto_snapshots_card)

        self.last_snapshot_card = self._create_stat_card("Last Snapshot", "Never", "#f39c12")
        layout.addWidget(self.last_snapshot_card)

        return section

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a statistics card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        card.setMinimumHeight(70)

        layout = QVBoxLayout(card)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Store reference for updates
        card.value_label = value_label

        return card

    def _create_snapshots_section(self) -> QFrame:
        """Create snapshots list section."""
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
        title_layout = QHBoxLayout()
        title = QLabel("📋 Snapshot History")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self.refresh)
        title_layout.addWidget(refresh_btn)

        layout.addLayout(title_layout)

        # Snapshots list
        self.snapshots_list = QListWidget()
        self.snapshots_list.itemClicked.connect(self._on_snapshot_selected)
        layout.addWidget(self.snapshots_list)

        return section

    def _create_details_section(self) -> QFrame:
        """Create snapshot details section."""
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
        title = QLabel("📄 Snapshot Details")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Details display
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select a snapshot to view details...")
        layout.addWidget(self.details_text)

        # Action buttons
        button_layout = QHBoxLayout()

        self.restore_btn = QPushButton("↩️ Restore This Version")
        self.restore_btn.clicked.connect(self._on_restore_clicked)
        self.restore_btn.setEnabled(False)
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.restore_btn)

        self.compare_btn = QPushButton("🔍 Compare Versions")
        self.compare_btn.clicked.connect(self._on_compare_clicked)
        self.compare_btn.setEnabled(False)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.compare_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

        return section

    def _load_essays(self):
        """Load essays into selector."""
        self.essay_selector.clear()

        query = """
        SELECT id, title
        FROM essays
        WHERE user_id = ?
        ORDER BY updated_at DESC
        LIMIT 20
        """

        essays = self.db.execute_query(
            query,
            (self.user_id,),
            fetch_all=True
        )

        if essays:
            for essay in essays:
                self.essay_selector.addItem(essay['title'], essay['id'])
            self.current_essay_id = essays[0]['id']
        else:
            self.essay_selector.addItem("No essays found", None)
            self.current_essay_id = None

    def _on_essay_changed(self, index):
        """Handle essay selection change."""
        essay_id = self.essay_selector.currentData()
        if essay_id:
            self.current_essay_id = essay_id
            self._update_snapshots()
            self._update_statistics()

    def _on_create_snapshot_clicked(self):
        """Handle create snapshot button click."""
        if not self.current_essay_id:
            QMessageBox.warning(self, "No Essay", "Please select an essay first.")
            return

        dialog = CreateSnapshotDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            label = dialog.get_label()

            # Get current essay content
            query = "SELECT content FROM essays WHERE id = ? AND user_id = ?"
            essay = self.db.execute_query(
                query,
                (self.current_essay_id, self.user_id),
                fetch_one=True
            )

            if not essay or not essay.get('content'):
                QMessageBox.warning(self, "Error", "Essay content not found.")
                return

            # Create snapshot
            result = self.snapshot_manager.create_snapshot(
                self.current_essay_id,
                essay['content'],
                snapshot_type=SnapshotType.MANUAL,
                label=label if label else None
            )

            if result['success']:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Snapshot created successfully!\nLabel: {result['label']}"
                )
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"Failed to create snapshot: {result.get('error')}")

    def _on_snapshot_selected(self, item):
        """Handle snapshot selection."""
        snapshot_id = item.data(Qt.ItemDataRole.UserRole)

        if snapshot_id:
            result = self.snapshot_manager.get_snapshot(snapshot_id)

            if result['success']:
                snapshot = result['snapshot']

                # Display details
                details = f"""Label: {snapshot['snapshot_label']}
Type: {snapshot['snapshot_type']}
Created: {snapshot['created_at'][:19].replace('T', ' ')}
Word Count: {snapshot['word_count']}

--- Content Preview ---
{snapshot['content_text'][:500]}...
"""
                self.details_text.setPlainText(details)

                # Enable buttons
                self.restore_btn.setEnabled(True)
                self.compare_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)

    def _on_restore_clicked(self):
        """Handle restore button click."""
        selected_items = self.snapshots_list.selectedItems()
        if not selected_items:
            return

        snapshot_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            "This will replace the current essay content with this snapshot.\n"
            "A backup of the current version will be created automatically.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.snapshot_manager.restore_snapshot(snapshot_id, create_backup=True)

            if result['success']:
                QMessageBox.information(
                    self,
                    "Restored",
                    "Essay restored successfully from snapshot!\nBackup created."
                )
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"Failed to restore: {result.get('error')}")

    def _on_compare_clicked(self):
        """Handle compare button click."""
        if not self.current_essay_id:
            return

        # Get all snapshots for this essay
        result = self.snapshot_manager.get_snapshots(self.current_essay_id)

        if not result['success'] or len(result['snapshots']) < 2:
            QMessageBox.information(
                self,
                "Not Enough Snapshots",
                "You need at least 2 snapshots to compare."
            )
            return

        dialog = CompareSnapshotsDialog(result['snapshots'], self)

        # Connect comparison logic
        def perform_comparison(snap1_id, snap2_id):
            comparison = self.snapshot_manager.compare_snapshots(snap1_id, snap2_id)

            if comparison['success']:
                # Generate comparison text
                diff = comparison['differences']
                comp_text = f"""=== COMPARISON RESULTS ===

Snapshot 1: {comparison['snapshot1']['label']}
Created: {comparison['snapshot1']['created_at'][:19]}
Word Count: {comparison['snapshot1']['word_count']}

Snapshot 2: {comparison['snapshot2']['label']}
Created: {comparison['snapshot2']['created_at'][:19]}
Word Count: {comparison['snapshot2']['word_count']}

--- Changes ---
Word Count Difference: {diff['word_count_diff']} words
Lines Difference: {diff['lines_diff']} lines

--- Detailed Diff ---
{self._generate_simple_diff(diff['content1'], diff['content2'])}
"""
                dialog.display_comparison(comp_text)
            else:
                dialog.display_comparison(f"Error: {comparison.get('error')}")

        dialog.compare_requested = perform_comparison

        dialog.exec()

    def _generate_simple_diff(self, text1: str, text2: str) -> str:
        """Generate simple text diff."""
        result = self.diff_viewer.compare_texts(text1, text2)

        if not result['success']:
            return "Error generating diff"

        summary = self.diff_viewer.get_change_summary(result['statistics'])

        diff_text = f"\n{summary}\n\n"

        # Show first few changes
        for change in result['changes'][:10]:
            if change['type'] == ChangeType.ADDED:
                diff_text += f"\n[ADDED at line {change['line_start']}]\n{change['content']}\n"
            elif change['type'] == ChangeType.REMOVED:
                diff_text += f"\n[REMOVED from line {change['line_start']}]\n{change['content']}\n"
            elif change['type'] == ChangeType.MODIFIED:
                diff_text += f"\n[MODIFIED lines {change['line_start_old']}-{change['line_end_old']}]\n"

        return diff_text

    def _on_delete_clicked(self):
        """Handle delete button click."""
        selected_items = self.snapshots_list.selectedItems()
        if not selected_items:
            return

        snapshot_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this snapshot?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.snapshot_manager.delete_snapshot(snapshot_id)

            if result['success']:
                QMessageBox.information(self, "Deleted", "Snapshot deleted successfully.")
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete: {result.get('error')}")

    def _update_statistics(self):
        """Update statistics display."""
        if not self.current_essay_id:
            return

        stats = self.snapshot_manager.get_snapshot_statistics(self.current_essay_id)

        if stats['success']:
            self.total_snapshots_card.value_label.setText(str(stats['total_snapshots']))
            self.manual_snapshots_card.value_label.setText(str(stats['manual_count']))
            self.auto_snapshots_card.value_label.setText(str(stats['auto_count']))

            if stats.get('last_snapshot'):
                last_time = stats['last_snapshot'][:16].replace('T', ' ')
                self.last_snapshot_card.value_label.setText(last_time)
            else:
                self.last_snapshot_card.value_label.setText("Never")

    def _update_snapshots(self):
        """Update snapshots list."""
        self.snapshots_list.clear()

        if not self.current_essay_id:
            return

        result = self.snapshot_manager.get_snapshots(self.current_essay_id)

        if result['success'] and result['snapshots']:
            for snapshot in result['snapshots']:
                snapshot_time = snapshot['created_at'][:16].replace('T', ' ')
                snapshot_type = snapshot['snapshot_type']

                # Type icon
                type_icon = "📸" if snapshot_type == "manual" else "💾"

                item_text = f"{type_icon} {snapshot['snapshot_label']}\n" \
                           f"   {snapshot_time} - {snapshot['word_count']} words"

                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, snapshot['id'])
                self.snapshots_list.addItem(item)
        else:
            item = QListWidgetItem("No snapshots yet.\nCreate one to get started!")
            item.setForeground(Qt.GlobalColor.gray)
            self.snapshots_list.addItem(item)

    def refresh(self):
        """Refresh the view."""
        logger.info("Refreshing version control view...")

        self._load_essays()
        self._update_statistics()
        self._update_snapshots()

        # Clear details
        self.details_text.clear()
        self.restore_btn.setEnabled(False)
        self.compare_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        logger.info("Version control view refreshed")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    view = VersionControlView(user_id="test_user")
    view.setGeometry(100, 100, 1200, 800)
    view.show()

    sys.exit(app.exec())
