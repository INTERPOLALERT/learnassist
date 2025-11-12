"""
Academic Command Center - Task Manager Module
Complete task generation and management system.
"""

from .task_manager import TaskManager
from .research_generator import ResearchTaskGenerator
from .writing_generator import WritingTaskGenerator
from .time_estimator import TimeEstimator
from .priority_calculator import PriorityCalculator

__all__ = [
    'TaskManager',
    'ResearchTaskGenerator',
    'WritingTaskGenerator',
    'TimeEstimator',
    'PriorityCalculator'
]
