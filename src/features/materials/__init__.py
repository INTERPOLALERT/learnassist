"""
Academic Command Center - Materials Library Module
Complete material upload, processing, and management system.
"""

from .materials_manager import MaterialsManager
from .content_processor import ContentProcessor
from .auto_tagger import AutoTagger

__all__ = [
    'MaterialsManager',
    'ContentProcessor',
    'AutoTagger'
]
