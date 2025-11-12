"""
Analytics Module - Phase 6 Sprint 3
Performance tracking, analytics, and student progress monitoring.

Components:
- Progress Tracker
- Performance Analytics Engine
- Goal Setting System
- Study Analytics Dashboard
- Achievement System

Author: Academic Command Center
Phase: 6 Sprint 3
"""

from .progress_tracker import ProgressTracker, ProgressReport
from .performance_analytics import PerformanceAnalytics
from .goal_system import GoalSystem, Goal
from .study_analytics import StudyAnalytics
from .achievement_system import AchievementSystem, Achievement

__all__ = [
    'ProgressTracker',
    'ProgressReport',
    'PerformanceAnalytics',
    'GoalSystem',
    'Goal',
    'StudyAnalytics',
    'AchievementSystem',
    'Achievement'
]
