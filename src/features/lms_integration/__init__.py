"""
LMS Integration Module
Provides integration with multiple Learning Management Systems.

Supported Platforms:
- Canvas (existing integration in Phase 4)
- Blackboard
- Moodle

Author: Academic Command Center
Phase: 6 Sprint 1
"""

from .integration_manager import LMSIntegrationManager, LMSPlatform

__all__ = ['LMSIntegrationManager', 'LMSPlatform']
