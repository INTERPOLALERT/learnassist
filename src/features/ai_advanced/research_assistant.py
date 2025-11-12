"""
Research Assistant
AI-powered research tool for finding and evaluating academic sources.

Features:
- Academic source finding
- Source quality evaluation
- Citation suggestion
- Research gap identification
- Topic exploration
- Keyword generation

Author: Academic Command Center
Phase: 6 Sprint 2
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class AcademicSource:
    """Represents an academic source."""
    title: str
    authors: List[str]
    year: int
    publication: str
    source_type: str  # journal, book, conference, website
    url: Optional[str]
    doi: Optional[str]
    abstract: str
    relevance_score: float  # 0-100
    credibility_score: float  # 0-100
    citation_suggestion: str


@dataclass
class ResearchGap:
    """Identified research gap."""
    description: str
    importance: str  # low, medium, high
    potential_contribution: str
    related_sources: List[str]


@dataclass
class ResearchPlan:
    """Research plan for essay topic."""
    topic: str
    key_questions: List[str]
    search_keywords: List[str]
    suggested_sources: List[AcademicSource]
    research_gaps: List[ResearchGap]
    methodology_suggestions: List[str]


class ResearchAssistant:
    """
    AI-powered Research Assistant.

    Helps students with:
    - Finding relevant academic sources
    - Evaluating source credibility
    - Generating citations
    - Identifying research gaps
    - Planning research approach
    """

    def __init__(
        self,
        user_id: str,
        ai_router: Optional[AIRouter] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Research Assistant.

        Args:
            user_id: Current user ID
            ai_router: AI router instance
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter()
        self.db = db_manager or DatabaseManager()

        logger.info("Research Assistant initialized")

    def create_research_plan(
        self,
        topic: str,
        essay_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive research plan for topic.

        Args:
            topic: Research topic or essay question
            essay_requirements: Optional essay requirements text

        Returns:
            Research plan with sources and strategies
        """
        try:
            logger.info(f"Creating research plan for: {topic}")

            # Generate key questions
            questions = self._generate_research_questions(topic, essay_requirements)

            # Generate search keywords
            keywords = self._generate_keywords(topic)

            # Find suggested sources
            sources = self._suggest_sources(topic, keywords)

            # Identify research gaps
            gaps = self._identify_research_gaps(topic, sources)

            # Suggest methodology
            methodology = self._suggest_methodology(topic, essay_requirements)

            plan = ResearchPlan(
                topic=topic,
                key_questions=questions,
                search_keywords=keywords,
                suggested_sources=sources,
                research_gaps=gaps,
                methodology_suggestions=methodology
            )

            return {
                'success': True,
                'topic': topic,
                'questions': questions,
                'keywords': keywords,
                'sources': [self._source_to_dict(s) for s in sources],
                'gaps': [self._gap_to_dict(g) for g in gaps],
                'methodology': methodology
            }

        except Exception as e:
            logger.error(f"Research plan creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def evaluate_source(
        self,
        title: str,
        authors: List[str],
        publication: str,
        year: int,
        abstract: str
    ) -> Dict[str, Any]:
        """
        Evaluate credibility and relevance of a source.

        Args:
            title: Source title
            authors: List of author names
            publication: Publication name
            year: Publication year
            abstract: Abstract or summary

        Returns:
            Evaluation scores and feedback
        """
        try:
            logger.info(f"Evaluating source: {title}")

            # Evaluate credibility
            credibility = self._evaluate_credibility(
                publication, authors, year
            )

            # Generate citation
            citation = self._generate_citation(
                title, authors, publication, year
            )

            # Analyze content
            analysis = self._analyze_source_content(abstract)

            return {
                'success': True,
                'credibility_score': credibility['score'],
                'credibility_factors': credibility['factors'],
                'citation': citation,
                'key_themes': analysis.get('themes', []),
                'methodology': analysis.get('methodology', 'Unknown'),
                'recommendations': credibility['recommendations']
            }

        except Exception as e:
            logger.error(f"Source evaluation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def find_sources(
        self,
        topic: str,
        max_sources: int = 10,
        source_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Find academic sources for topic.

        Args:
            topic: Research topic
            max_sources: Maximum sources to return
            source_types: Filter by types (journal, book, etc.)

        Returns:
            List of suggested sources
        """
        try:
            logger.info(f"Finding sources for: {topic}")

            # Generate search strategy
            keywords = self._generate_keywords(topic)

            # Suggest sources based on topic
            sources = self._suggest_sources(topic, keywords, max_sources)

            # Filter by type if specified
            if source_types:
                sources = [
                    s for s in sources
                    if s.source_type in source_types
                ]

            return {
                'success': True,
                'sources': [self._source_to_dict(s) for s in sources],
                'keywords_used': keywords,
                'count': len(sources)
            }

        except Exception as e:
            logger.error(f"Source finding failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_research_questions(
        self,
        topic: str,
        requirements: Optional[str]
    ) -> List[str]:
        """Generate key research questions."""
        try:
            context = f"Topic: {topic}"
            if requirements:
                context += f"\n\nRequirements: {requirements[:500]}"

            prompt = f"""Generate 5 key research questions for this topic:

{context}

Questions should:
- Be specific and focused
- Guide the research process
- Be answerable through research
- Build upon each other

Return as JSON array: ["question 1", "question 2", ...]
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="research",
                max_tokens=400
            )

            if result.get('success'):
                questions = self._extract_json_list(result.get('text', '[]'))
                return questions[:5]

            return self._fallback_questions(topic)

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._fallback_questions(topic)

    def _generate_keywords(self, topic: str) -> List[str]:
        """Generate search keywords."""
        try:
            prompt = f"""Generate 8-10 effective search keywords for academic research on:

{topic}

Include:
- Main concepts
- Related terms
- Technical terms
- Alternative phrasings

Return as JSON array: ["keyword1", "keyword2", ...]
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="research",
                max_tokens=200
            )

            if result.get('success'):
                keywords = self._extract_json_list(result.get('text', '[]'))
                return keywords[:10]

            return self._fallback_keywords(topic)

        except Exception as e:
            logger.error(f"Keyword generation failed: {e}")
            return self._fallback_keywords(topic)

    def _suggest_sources(
        self,
        topic: str,
        keywords: List[str],
        max_sources: int = 10
    ) -> List[AcademicSource]:
        """Suggest potential academic sources."""
        try:
            keyword_str = ", ".join(keywords[:5])

            prompt = f"""Suggest {max_sources} academic sources for research on:

Topic: {topic}
Keywords: {keyword_str}

For each source, provide:
- Title
- Authors (list)
- Year
- Publication (journal/book name)
- Type (journal/book/conference)
- Brief abstract
- Why it's relevant

Return as JSON array of source objects.
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="research",
                max_tokens=1500
            )

            if result.get('success'):
                sources_data = self._extract_json_list(result.get('text', '[]'))

                sources = []
                for data in sources_data[:max_sources]:
                    try:
                        source = AcademicSource(
                            title=data.get('title', 'Unknown'),
                            authors=data.get('authors', ['Unknown']),
                            year=data.get('year', datetime.now().year),
                            publication=data.get('publication', 'Unknown'),
                            source_type=data.get('type', 'journal'),
                            url=data.get('url'),
                            doi=data.get('doi'),
                            abstract=data.get('abstract', ''),
                            relevance_score=self._calculate_relevance(
                                data.get('abstract', ''),
                                topic
                            ),
                            credibility_score=75.0,  # Default
                            citation_suggestion=self._generate_citation(
                                data.get('title', ''),
                                data.get('authors', []),
                                data.get('publication', ''),
                                data.get('year', 2024)
                            )
                        )
                        sources.append(source)
                    except Exception as e:
                        logger.warning(f"Failed to parse source: {e}")
                        continue

                return sources

            return self._fallback_sources(topic)

        except Exception as e:
            logger.error(f"Source suggestion failed: {e}")
            return self._fallback_sources(topic)

    def _identify_research_gaps(
        self,
        topic: str,
        sources: List[AcademicSource]
    ) -> List[ResearchGap]:
        """Identify potential research gaps."""
        try:
            source_summaries = "\n".join([
                f"- {s.title} ({s.year}): {s.abstract[:150]}"
                for s in sources[:5]
            ])

            prompt = f"""Based on these sources about "{topic}", identify potential research gaps:

{source_summaries}

Identify 2-3 gaps where further research could contribute. Return as JSON array:
[
    {{
        "description": "gap description",
        "importance": "high/medium/low",
        "potential_contribution": "what new research could add"
    }}
]
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="research",
                max_tokens=500
            )

            if result.get('success'):
                gaps_data = self._extract_json_list(result.get('text', '[]'))

                gaps = []
                for data in gaps_data[:3]:
                    gap = ResearchGap(
                        description=data.get('description', ''),
                        importance=data.get('importance', 'medium'),
                        potential_contribution=data.get('potential_contribution', ''),
                        related_sources=[s.title for s in sources[:3]]
                    )
                    gaps.append(gap)

                return gaps

            return []

        except Exception as e:
            logger.error(f"Gap identification failed: {e}")
            return []

    def _suggest_methodology(
        self,
        topic: str,
        requirements: Optional[str]
    ) -> List[str]:
        """Suggest research methodology."""
        try:
            context = f"Topic: {topic}"
            if requirements:
                context += f"\nRequirements: {requirements[:300]}"

            prompt = f"""Suggest research methodology approaches for:

{context}

Provide 3-4 specific methodology suggestions. Return as JSON array.
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="research",
                max_tokens=300
            )

            if result.get('success'):
                return self._extract_json_list(result.get('text', '[]'))

            return [
                "Literature review of existing research",
                "Analysis of primary sources",
                "Comparative analysis approach"
            ]

        except Exception as e:
            logger.error(f"Methodology suggestion failed: {e}")
            return ["Literature review approach"]

    def _evaluate_credibility(
        self,
        publication: str,
        authors: List[str],
        year: int
    ) -> Dict[str, Any]:
        """Evaluate source credibility."""
        score = 50.0
        factors = []
        recommendations = []

        # Check publication year
        current_year = datetime.now().year
        age = current_year - year

        if age <= 5:
            score += 20
            factors.append("Recent publication (within 5 years)")
        elif age <= 10:
            score += 10
            factors.append("Relatively recent (within 10 years)")
        else:
            factors.append(f"Older source ({age} years old)")
            recommendations.append("Consider finding more recent sources")

        # Check author count (collaboration indicator)
        if len(authors) >= 2:
            score += 10
            factors.append("Multiple authors (collaborative research)")

        # Check publication type (heuristic)
        if any(word in publication.lower() for word in ['journal', 'review', 'science', 'research']):
            score += 20
            factors.append("Published in academic journal")

        return {
            'score': min(100, score),
            'factors': factors,
            'recommendations': recommendations
        }

    def _analyze_source_content(self, abstract: str) -> Dict[str, Any]:
        """Analyze source content from abstract."""
        try:
            prompt = f"""Analyze this academic abstract:

{abstract[:500]}

Extract:
1. Main themes (2-3)
2. Research methodology used

Return as JSON:
{{
    "themes": ["theme1", "theme2"],
    "methodology": "methodology type"
}}
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=200
            )

            if result.get('success'):
                return self._extract_json_dict(result.get('text', '{}'))

            return {
                'themes': [],
                'methodology': 'Unknown'
            }

        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {'themes': [], 'methodology': 'Unknown'}

    def _generate_citation(
        self,
        title: str,
        authors: List[str],
        publication: str,
        year: int
    ) -> str:
        """Generate APA-style citation."""
        if not authors:
            authors = ['Unknown']

        # Format authors
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} & {authors[1]}"
        else:
            author_str = f"{authors[0]} et al."

        # Generate citation
        citation = f"{author_str} ({year}). {title}. {publication}."

        return citation

    def _calculate_relevance(self, abstract: str, topic: str) -> float:
        """Calculate relevance score (simple keyword matching)."""
        if not abstract or not topic:
            return 50.0

        topic_words = set(topic.lower().split())
        abstract_words = set(abstract.lower().split())

        overlap = len(topic_words & abstract_words)
        relevance = min(100, (overlap / max(len(topic_words), 1)) * 100 + 30)

        return relevance

    def _fallback_questions(self, topic: str) -> List[str]:
        """Fallback research questions."""
        return [
            f"What is the current state of research on {topic}?",
            f"What are the main debates or controversies regarding {topic}?",
            f"What methodologies are commonly used to study {topic}?",
            f"What are the implications of {topic}?",
            f"What future research is needed on {topic}?"
        ]

    def _fallback_keywords(self, topic: str) -> List[str]:
        """Fallback keywords from topic."""
        words = topic.split()
        keywords = [topic] + words
        return keywords[:10]

    def _fallback_sources(self, topic: str) -> List[AcademicSource]:
        """Fallback placeholder sources."""
        return [
            AcademicSource(
                title=f"Research on {topic}",
                authors=["Academic Researcher"],
                year=datetime.now().year - 1,
                publication="Academic Journal",
                source_type="journal",
                url=None,
                doi=None,
                abstract=f"Placeholder abstract for {topic} research.",
                relevance_score=70.0,
                credibility_score=75.0,
                citation_suggestion=f"Researcher, A. ({datetime.now().year - 1}). Research on {topic}. Academic Journal."
            )
        ]

    def _extract_json_list(self, text: str) -> List:
        """Extract JSON array from text."""
        try:
            import json
            start = text.find('[')
            if start != -1:
                end = text.rfind(']')
                if end != -1:
                    return json.loads(text[start:end+1])
            return json.loads(text)
        except:
            return []

    def _extract_json_dict(self, text: str) -> Dict:
        """Extract JSON object from text."""
        try:
            import json
            start = text.find('{')
            if start != -1:
                end = text.rfind('}')
                if end != -1:
                    return json.loads(text[start:end+1])
            return json.loads(text)
        except:
            return {}

    def _source_to_dict(self, source: AcademicSource) -> Dict[str, Any]:
        """Convert AcademicSource to dictionary."""
        return {
            'title': source.title,
            'authors': source.authors,
            'year': source.year,
            'publication': source.publication,
            'source_type': source.source_type,
            'url': source.url,
            'doi': source.doi,
            'abstract': source.abstract,
            'relevance_score': source.relevance_score,
            'credibility_score': source.credibility_score,
            'citation': source.citation_suggestion
        }

    def _gap_to_dict(self, gap: ResearchGap) -> Dict[str, Any]:
        """Convert ResearchGap to dictionary."""
        return {
            'description': gap.description,
            'importance': gap.importance,
            'potential_contribution': gap.potential_contribution,
            'related_sources': gap.related_sources
        }


def create_research_assistant(
    user_id: str,
    ai_router: Optional[AIRouter] = None,
    db_manager: Optional[DatabaseManager] = None
) -> ResearchAssistant:
    """
    Factory function to create Research Assistant.

    Args:
        user_id: Current user ID
        ai_router: AI router instance
        db_manager: Database manager instance

    Returns:
        ResearchAssistant instance
    """
    return ResearchAssistant(user_id, ai_router, db_manager)
