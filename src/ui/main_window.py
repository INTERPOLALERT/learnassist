"""
Academic Command Center - Main Window
PyQt6 desktop interface with sidebar navigation.
"""

import logging
import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window with sidebar navigation.

    Structure:
    - Left sidebar: Navigation buttons
    - Right content: Stacked widget with different views
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize main window.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Window configuration
        self.setWindowTitle("Academic Command Center")
        self.setMinimumSize(1200, 800)

        # Initialize UI
        self._init_ui()

        # Show dashboard by default
        self.show_dashboard()

        logger.info("Main window initialized")

    def _init_ui(self):
        """Initialize the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout (horizontal: sidebar + content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Create content area (stacked widget for different views)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, stretch=1)

        # Create views (will be added to stack)
        self._create_views()

    def _create_sidebar(self) -> QWidget:
        """
        Create sidebar with navigation buttons.

        Returns:
            Sidebar widget
        """
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-right: 1px solid #34495e;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                text-align: left;
                padding: 15px 20px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #3498db;
                border-left: 4px solid #2980b9;
            }
            QLabel {
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title
        title_label = QLabel("Academic\nCommand Center")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #34495e;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Navigation buttons
        self.nav_buttons = {}

        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("essays", "📝 Essays"),
            ("tasks", "✓ Tasks"),
            ("materials", "📚 Materials"),
            ("focus", "🎯 Focus Mode"),
            ("analytics", "📈 Analytics"),
            ("settings", "⚙️ Settings")
        ]

        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)

        # Spacer
        layout.addStretch()

        # User info at bottom
        user_label = QLabel(f"👤 {self.user_id}")
        user_label.setStyleSheet("font-size: 12px; color: #bdc3c7; padding: 10px;")
        layout.addWidget(user_label)

        return sidebar

    def _create_views(self):
        """Create all view widgets and add to stack."""
        # Import views
        from .views.dashboard_view import DashboardView
        from .views.essay_view import EssayView
        from .views.task_view import TaskView
        from .views.material_view import MaterialView
        from .views.settings_view import SettingsView

        # Create view instances
        self.views = {
            'dashboard': DashboardView(self.user_id, self.db),
            'essays': EssayView(self.user_id, self.db),
            'tasks': TaskView(self.user_id, self.db),
            'materials': MaterialView(self.user_id, self.db),
            'settings': SettingsView(self.user_id, self.db)
        }

        # Placeholder views for not-yet-implemented features
        self.views['focus'] = self._create_placeholder("Focus Mode - Coming Soon!")
        self.views['analytics'] = self._create_placeholder("Analytics - Coming Soon!")

        # Add all views to stack
        for view in self.views.values():
            self.content_stack.addWidget(view)

    def _create_placeholder(self, text: str) -> QWidget:
        """Create placeholder widget for unimplemented features."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #95a5a6;")

        layout.addWidget(label)

        return widget

    def _navigate_to(self, view_key: str):
        """
        Navigate to a different view.

        Args:
            view_key: Key of view to show
        """
        # Uncheck all buttons
        for btn in self.nav_buttons.values():
            btn.setChecked(False)

        # Check selected button
        if view_key in self.nav_buttons:
            self.nav_buttons[view_key].setChecked(True)

        # Switch to view
        if view_key in self.views:
            view = self.views[view_key]
            self.content_stack.setCurrentWidget(view)

            # Refresh view data if it has a refresh method
            if hasattr(view, 'refresh'):
                view.refresh()

            logger.info(f"Navigated to: {view_key}")

    def show_dashboard(self):
        """Show dashboard view."""
        self._navigate_to('dashboard')

    def show_essays(self):
        """Show essays view."""
        self._navigate_to('essays')

    def show_tasks(self):
        """Show tasks view."""
        self._navigate_to('tasks')

    def show_materials(self):
        """Show materials view."""
        self._navigate_to('materials')

    def show_settings(self):
        """Show settings view."""
        self._navigate_to('settings')


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = MainWindow(user_id="test_user")
    window.show()

    sys.exit(app.exec())
