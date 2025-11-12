"""
Advanced AI Features Module
Intelligent AI-powered tools for writing and research.

Components:
- Smart Essay Analyzer: Argument detection and thesis evaluation
- Research Assistant: Source finding and citation suggestions
- Writing Coach: Personalized feedback and style improvements
- Content Summarizer: Article summarization and key points

Author: Academic Command Center
Phase: 6 Sprint 2
"""

from .essay_analyzer import SmartEssayAnalyzer
from .research_assistant import ResearchAssistant
from .writing_coach import WritingCoach
from .content_summarizer import ContentSummarizer

__all__ = [
    'SmartEssayAnalyzer',
    'ResearchAssistant',
    'WritingCoach',
    'ContentSummarizer'
]
