"""
Main Application Window - Phase 9 Sprint 1
Central application window with navigation and view management.

Features:
- Menu bar with File, Edit, View, Tools, Help
- Sidebar navigation
- Central view area with stacked widgets
- Status bar
- Window state management
- View coordination

Author: Academic Command Center
Phase: 9 Sprint 1 - Deployment
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QMessageBox, QDialog, QLineEdit, QDialogButtonBox,
    QPushButton, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont, QKeySequence
from typing import Optional, Dict
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.database import DatabaseManager

# Import all views
try:
    from views.analytics_dashboard_view import AnalyticsDashboardView
    from views.progress_reports_view import ProgressReportsView
    from views.goals_view import GoalsView
    from views.achievements_view import AchievementsView
    from views.ai_settings_view import AISettingsView
    from views.assignments_view import AssignmentsView
    from views.study_timer_view import StudyTimerView
    from views.notes_view import NotesView
    from views.calendar_view import CalendarView
except ImportError as e:
    logging.warning(f"Some views not yet imported: {e}")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main Application Window.

    Central hub for the Academic Command Center application.
    """

    def __init__(self, user_id: str = "default_user"):
        """
        Initialize Main Window.

        Args:
            user_id: Current user ID
        """
        super().__init__()

        self.user_id = user_id
        self.db = DatabaseManager()

        # View registry
        self.views: Dict[str, QWidget] = {}

        # Current view
        self.current_view_name = None

        self._init_ui()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._load_views()

        # Navigate to dashboard by default
        self.navigate_to("Dashboard")

        # Auto-check achievements periodically
        self.achievement_timer = QTimer()
        self.achievement_timer.timeout.connect(self._check_achievements)
        self.achievement_timer.start(600000)  # Every 10 minutes

        logger.info(f"Main Window initialized for user: {user_id}")

    def _init_ui(self):
        """Initialize user interface."""

        self.setWindowTitle("Academic Command Center")
        self.setMinimumSize(1200, 800)

        # Center window on screen
        self.center_on_screen()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar and content area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar navigation
        self.sidebar = self._create_sidebar()
        splitter.addWidget(self.sidebar)

        # Content area (stacked widget for views)
        self.content_stack = QStackedWidget()
        self.content_stack.setFrameShape(QFrame.Shape.NoFrame)
        splitter.addWidget(self.content_stack)

        # Set splitter sizes (sidebar smaller)
        splitter.setSizes([250, 950])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

    def _create_sidebar(self) -> QWidget:
        """Create sidebar navigation."""

        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-right: 1px solid #34495E;
            }
            QListWidget {
                background-color: #2C3E50;
                color: white;
                border: none;
                font-size: 13px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
                margin: 2px 5px;
            }
            QListWidget::item:hover {
                background-color: #34495E;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 10)

        # App title in sidebar
        title_label = QLabel("Academic\nCommand Center")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px 10px;
                border-bottom: 1px solid #34495E;
            }
        """)
        layout.addWidget(title_label)

        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setIconSize(QSize(24, 24))

        # Add navigation items
        nav_items = [
            ("ð", "Dashboard"),
            ("ð", "Assignments"),
            ("â±ï¸", "Study Timer"),
            ("ð", "Notes"),
            ("ð", "Calendar"),
            ("ð¯", "Goals"),
            ("ð", "Achievements"),
            ("ð", "Progress Reports"),
            ("ð¤", "AI Tools"),
            ("âï¸", "Settings")
        ]

        for icon, name in nav_items:
            item = QListWidgetItem(f"{icon}  {name}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.nav_list.addItem(item)

        self.nav_list.currentItemChanged.connect(self._on_nav_item_changed)

        layout.addWidget(self.nav_list)

        # User info at bottom
        user_info = QLabel(f"ð¤ {self.user_id}")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_info.setStyleSheet("""
            QLabel {
                color: #BDC3C7;
                font-size: 11px;
                padding: 15px 10px;
                border-top: 1px solid #34495E;
            }
        """)
        layout.addWidget(user_info)

        sidebar.setLayout(layout)
        return sidebar

    def _create_menu_bar(self):
        """Create application menu bar."""

        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Assignment", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._new_assignment)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        export_action = QAction("&Export...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._export_data)
        file_menu.addAction(export_action)

        import_action = QAction("&Import...", self)
        import_action.triggered.connect(self._import_data)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        preferences_action = QAction("&Preferences", self)
        preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        preferences_action.triggered.connect(self._show_preferences)
        edit_menu.addAction(preferences_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        dashboard_action = QAction("&Dashboard", self)
        dashboard_action.setShortcut(QKeySequence("Ctrl+1"))
        dashboard_action.triggered.connect(lambda: self.navigate_to("Dashboard"))
        view_menu.addAction(dashboard_action)

        assignments_action = QAction("&Assignments", self)
        assignments_action.setShortcut(QKeySequence("Ctrl+2"))
        assignments_action.triggered.connect(lambda: self.navigate_to("Assignments"))
        view_menu.addAction(assignments_action)

        timer_action = QAction("Study &Timer", self)
        timer_action.setShortcut(QKeySequence("Ctrl+3"))
        timer_action.triggered.connect(lambda: self.navigate_to("Study Timer"))
        view_menu.addAction(timer_action)

        view_menu.addSeparator()

        fullscreen_action = QAction("&Full Screen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        sync_action = QAction("&Sync Now", self)
        sync_action.triggered.connect(self._sync_now)
        tools_menu.addAction(sync_action)

        check_achievements_action = QAction("Check &Achievements", self)
        check_achievements_action.triggered.connect(self._check_achievements)
        tools_menu.addAction(check_achievements_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        docs_action = QAction("&Documentation", self)
        docs_action.setShortcut(QKeySequence("F1"))
        docs_action.triggered.connect(self._show_documentation)
        help_menu.addAction(docs_action)

    def _create_toolbar(self):
        """Create application toolbar."""

        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Quick actions
        new_btn = QPushButton(" New")
        new_btn.clicked.connect(self._new_assignment)
        toolbar.addWidget(new_btn)

        toolbar.addSeparator()

        timer_btn = QPushButton("ñ Start Timer")
        timer_btn.clicked.connect(lambda: self.navigate_to("Study Timer"))
        toolbar.addWidget(timer_btn)

        toolbar.addSeparator()

        sync_btn = QPushButton("= Sync")
        sync_btn.clicked.connect(self._sync_now)
        toolbar.addWidget(sync_btn)

        toolbar.addSeparator()

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search assignments, notes...")
        self.search_input.setMaximumWidth(300)
        self.search_input.returnPressed.connect(self._perform_search)
        toolbar.addWidget(self.search_input)

    def _create_status_bar(self):
        """Create status bar."""

        statusbar = self.statusBar()

        self.status_label = QLabel("Ready")
        statusbar.addWidget(self.status_label)

        # Sync status
        self.sync_status_label = QLabel(" Synced")
        statusbar.addPermanentWidget(self.sync_status_label)

        # Achievement count
        self.achievement_label = QLabel("<Æ 0 achievements")
        statusbar.addPermanentWidget(self.achievement_label)

    def _load_views(self):
        """Load all application views."""

        try:
            # Analytics Dashboard
            dashboard = AnalyticsDashboardView(self.user_id, self.db)
            self._add_view("Dashboard", dashboard)

            # Progress Reports
            progress_reports = ProgressReportsView(self.user_id, self.db)
            self._add_view("Progress Reports", progress_reports)

            # Goals
            goals_view = GoalsView(self.user_id, self.db)
            self._add_view("Goals", goals_view)

            # Achievements
            achievements_view = AchievementsView(self.user_id, self.db)
            self._add_view("Achievements", achievements_view)

            # AI Settings
            ai_settings = AISettingsView(self.user_id, self.db)
            self._add_view("Settings", ai_settings)

            # Assignments View
            assignments_view = AssignmentsView(self.user_id, self.db)
            self._add_view("Assignments", assignments_view)

            # Placeholder views for not-yet-built sections
            study_timer_view = StudyTimerView(self.user_id, self.db)
            self._add_view("Study Timer", study_timer_view)

            notes_view = NotesView(self.user_id, self.db)
            self._add_view("Notes", notes_view)

            calendar_view = CalendarView(self.user_id, self.db)
            self._add_view("Calendar", calendar_view)

            self._add_placeholder_view("AI Tools", "ð¤ AI Tools View\n\nComing soon...")

            logger.info(f"Loaded {len(self.views)} views")

        except Exception as e:
            logger.error(f"Failed to load views: {e}")

    def _add_view(self, name: str, view: QWidget):
        """Add a view to the stack."""

        self.views[name] = view
        self.content_stack.addWidget(view)

    def _add_placeholder_view(self, name: str, text: str):
        """Add a placeholder view."""

        placeholder = QLabel(text)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("font-size: 18px; color: gray;")
        self._add_view(name, placeholder)

    def navigate_to(self, view_name: str):
        """Navigate to a specific view."""

        if view_name in self.views:
            view = self.views[view_name]
            self.content_stack.setCurrentWidget(view)
            self.current_view_name = view_name
            self.status_label.setText(f"Viewing: {view_name}")
            logger.info(f"Navigated to: {view_name}")
        else:
            logger.warning(f"View not found: {view_name}")

    def _on_nav_item_changed(self, current, previous):
        """Handle navigation item change."""

        if current:
            view_name = current.data(Qt.ItemDataRole.UserRole)
            self.navigate_to(view_name)

    def center_on_screen(self):
        """Center window on screen."""

        screen = self.screen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    # Menu action handlers
    def _new_assignment(self):
        """Create new assignment."""
        QMessageBox.information(self, "New Assignment", "Assignment creation dialog coming soon!")

    def _export_data(self):
        """Export data."""
        QMessageBox.information(self, "Export", "Export functionality available in Progress Reports view")

    def _import_data(self):
        """Import data."""
        QMessageBox.information(self, "Import", "Import functionality coming soon!")

    def _show_preferences(self):
        """Show preferences dialog."""
        self.navigate_to("Settings")

    def _toggle_fullscreen(self, checked):
        """Toggle fullscreen mode."""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()

    def _sync_now(self):
        """Trigger sync."""
        self.status_label.setText("Syncing...")
        QTimer.singleShot(2000, lambda: self.status_label.setText("Sync complete"))
        QTimer.singleShot(2000, lambda: self.sync_status_label.setText(" Synced"))

    def _check_achievements(self):
        """Check for new achievements."""
        try:
            from features.analytics.achievement_system import AchievementSystem

            achievement_system = AchievementSystem(self.user_id, self.db)
            result = achievement_system.check_achievements()

            if result.get('success'):
                newly_unlocked = result.get('newly_unlocked', [])

                if newly_unlocked:
                    messages = []
                    for achievement in newly_unlocked:
                        messages.append(
                            f"{achievement['icon']} {achievement['name']}\n"
                            f"+{achievement['points']} points"
                        )

                    QMessageBox.information(
                        self,
                        "< New Achievements!",
                        "\n\n".join(messages)
                    )

            # Update achievement count in status bar
            stats = achievement_system.get_user_stats()
            if stats.get('success'):
                count = stats['achievements_unlocked']
                self.achievement_label.setText(f"<Æ {count} achievements")

        except Exception as e:
            logger.error(f"Failed to check achievements: {e}")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Academic Command Center",
            "<h3>Academic Command Center</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A comprehensive learning management platform with:</p>"
            "<ul>"
            "<li>Study time tracking</li>"
            "<li>Assignment management</li>"
            "<li>AI-powered writing assistance</li>"
            "<li>Performance analytics</li>"
            "<li>Goal setting & achievements</li>"
            "</ul>"
            "<p>Built with PyQt6 and Python</p>"
        )

    def _show_documentation(self):
        """Show documentation."""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation available at:\nhttps://github.com/your-repo/docs"
        )

    def _perform_search(self):
        """Perform global search."""
        query = self.search_input.text()
        if query:
            QMessageBox.information(self, "Search", f"Search functionality for '{query}' coming soon!")

    def closeEvent(self, event):
        """Handle window close event."""

        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("Academic Command Center")
    app.setOrganizationName("Academic Command Center")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
