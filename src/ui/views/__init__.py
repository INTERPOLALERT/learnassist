"""
Academic Command Center - UI Views
All view components for the application.
"""

from .dashboard_view import DashboardView
from .essay_view import EssayView
from .task_view import TaskView
from .material_view import MaterialView
from .settings_view import SettingsView
from .focus_view import FocusView
from .analytics_view import AnalyticsView
from .writing_assistant_view import WritingAssistantView

__all__ = [
    "DashboardView",
    "EssayView",
    "TaskView",
    "MaterialView",
    "SettingsView",
    "FocusView",
    "AnalyticsView",
    "WritingAssistantView"
]

