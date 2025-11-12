"""
Smart Essay Analyzer
Advanced AI-powered essay analysis for argument structure and quality.

Features:
- Argument detection (claims, evidence, reasoning)
- Thesis strength evaluation
- Logical flow analysis
- Counterargument identification
- Coherence scoring
- Structure analysis

Author: Academic Command Center
Phase: 6 Sprint 2
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.ai_router import AIRouter
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """Represents a claim in the essay."""
    text: str
    location: str  # paragraph number or location
    evidence: List[str]
    strength: str  # weak, moderate, strong
    reasoning: str


@dataclass
class ThesisAnalysis:
    """Thesis statement analysis."""
    statement: str
    location: str
    clarity_score: float  # 0-100
    specificity_score: float  # 0-100
    arguability_score: float  # 0-100
    overall_score: float  # 0-100
    suggestions: List[str]


@dataclass
class ArgumentStructure:
    """Overall argument structure."""
    claims: List[Claim]
    thesis: ThesisAnalysis
    coherence_score: float  # 0-100
    logical_flow_score: float  # 0-100
    counterarguments: List[str]
    missing_elements: List[str]


class SmartEssayAnalyzer:
    """
    Smart Essay Analyzer using advanced AI.

    Analyzes essays for:
    - Argument structure (claims, evidence, reasoning)
    - Thesis strength and clarity
    - Logical coherence and flow
    - Counterargument identification
    - Structural quality
    """

    def __init__(
        self,
        user_id: str,
        ai_router: Optional[AIRouter] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize Smart Essay Analyzer.

        Args:
            user_id: Current user ID
            ai_router: AI router instance
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.ai_router = ai_router or AIRouter()
        self.db = db_manager or DatabaseManager()

        logger.info("Smart Essay Analyzer initialized")

    def analyze_essay(
        self,
        essay_text: str,
        essay_type: str = "argumentative"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive essay analysis.

        Args:
            essay_text: Full essay text
            essay_type: Type of essay (argumentative, analytical, persuasive)

        Returns:
            Complete analysis results
        """
        try:
            logger.info(f"Analyzing {len(essay_text)} character essay")

            # Analyze thesis
            thesis_analysis = self._analyze_thesis(essay_text)

            # Detect claims and evidence
            claims = self._detect_claims(essay_text)

            # Analyze logical flow
            flow_score = self._analyze_logical_flow(essay_text, claims)

            # Detect counterarguments
            counterarguments = self._detect_counterarguments(essay_text)

            # Calculate coherence
            coherence_score = self._calculate_coherence(essay_text)

            # Identify missing elements
            missing_elements = self._identify_missing_elements(
                thesis_analysis,
                claims,
                counterarguments
            )

            # Build argument structure
            structure = ArgumentStructure(
                claims=claims,
                thesis=thesis_analysis,
                coherence_score=coherence_score,
                logical_flow_score=flow_score,
                counterarguments=counterarguments,
                missing_elements=missing_elements
            )

            # Generate overall recommendations
            recommendations = self._generate_recommendations(structure)

            return {
                'success': True,
                'thesis': self._thesis_to_dict(thesis_analysis),
                'claims': [self._claim_to_dict(c) for c in claims],
                'coherence_score': coherence_score,
                'flow_score': flow_score,
                'counterarguments': counterarguments,
                'missing_elements': missing_elements,
                'recommendations': recommendations,
                'overall_score': self._calculate_overall_score(structure)
            }

        except Exception as e:
            logger.error(f"Essay analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _analyze_thesis(self, essay_text: str) -> ThesisAnalysis:
        """Analyze thesis statement."""
        try:
            prompt = f"""Analyze the thesis statement in this essay:

{essay_text[:2000]}

Provide analysis in JSON format:
{{
    "statement": "the thesis statement text",
    "location": "paragraph number or introduction/conclusion",
    "clarity_score": 0-100,
    "specificity_score": 0-100,
    "arguability_score": 0-100,
    "suggestions": ["suggestion 1", "suggestion 2"]
}}

Focus on:
- Is the thesis clear and specific?
- Is it arguable (not just a fact)?
- Does it make a strong claim?
- Is it properly placed?
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=500
            )

            if result.get('success'):
                response_text = result.get('text', '{}')

                # Extract JSON from response
                analysis_data = self._extract_json(response_text)

                clarity = analysis_data.get('clarity_score', 50)
                specificity = analysis_data.get('specificity_score', 50)
                arguability = analysis_data.get('arguability_score', 50)

                return ThesisAnalysis(
                    statement=analysis_data.get('statement', 'Not clearly identified'),
                    location=analysis_data.get('location', 'Unknown'),
                    clarity_score=clarity,
                    specificity_score=specificity,
                    arguability_score=arguability,
                    overall_score=(clarity + specificity + arguability) / 3,
                    suggestions=analysis_data.get('suggestions', [])
                )
            else:
                # Fallback analysis
                return self._fallback_thesis_analysis(essay_text)

        except Exception as e:
            logger.error(f"Thesis analysis failed: {e}")
            return self._fallback_thesis_analysis(essay_text)

    def _detect_claims(self, essay_text: str) -> List[Claim]:
        """Detect claims and supporting evidence."""
        try:
            prompt = f"""Identify the main claims in this essay and their supporting evidence:

{essay_text[:3000]}

Return JSON array:
[
    {{
        "claim": "the claim statement",
        "location": "paragraph number",
        "evidence": ["evidence 1", "evidence 2"],
        "strength": "weak/moderate/strong",
        "reasoning": "how evidence supports claim"
    }}
]

Find 3-5 main claims with their evidence.
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=800
            )

            if result.get('success'):
                response_text = result.get('text', '[]')
                claims_data = self._extract_json(response_text)

                if isinstance(claims_data, list):
                    return [
                        Claim(
                            text=c.get('claim', ''),
                            location=c.get('location', 'Unknown'),
                            evidence=c.get('evidence', []),
                            strength=c.get('strength', 'moderate'),
                            reasoning=c.get('reasoning', '')
                        )
                        for c in claims_data
                    ]

            # Fallback
            return self._fallback_claim_detection(essay_text)

        except Exception as e:
            logger.error(f"Claim detection failed: {e}")
            return self._fallback_claim_detection(essay_text)

    def _analyze_logical_flow(
        self,
        essay_text: str,
        claims: List[Claim]
    ) -> float:
        """Analyze logical flow and transitions."""
        try:
            prompt = f"""Analyze the logical flow and transitions in this essay.

Essay has {len(claims)} main claims.

First 1500 characters:
{essay_text[:1500]}

Rate the logical flow from 0-100 based on:
- Smooth transitions between paragraphs
- Logical progression of ideas
- Clear connections between claims
- Proper use of transition words

Return only a number from 0-100.
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=50
            )

            if result.get('success'):
                response_text = result.get('text', '50')

                # Extract number
                try:
                    score = float(''.join(filter(str.isdigit, response_text[:10])))
                    return min(100, max(0, score))
                except:
                    return 60.0

            return 60.0

        except Exception as e:
            logger.error(f"Flow analysis failed: {e}")
            return 60.0

    def _detect_counterarguments(self, essay_text: str) -> List[str]:
        """Detect counterarguments or opposing views."""
        try:
            prompt = f"""Identify any counterarguments or opposing viewpoints addressed in this essay:

{essay_text[:2000]}

Return JSON array of counterarguments:
["counterargument 1", "counterargument 2"]

If no counterarguments found, return empty array [].
"""

            result = self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=300
            )

            if result.get('success'):
                response_text = result.get('text', '[]')
                counterargs = self._extract_json(response_text)

                if isinstance(counterargs, list):
                    return counterargs

            return []

        except Exception as e:
            logger.error(f"Counterargument detection failed: {e}")
            return []

    def _calculate_coherence(self, essay_text: str) -> float:
        """Calculate overall coherence score."""
        try:
            # Simple heuristic: check for transition words and paragraph structure
            paragraphs = essay_text.split('\n\n')

            transition_words = [
                'however', 'therefore', 'furthermore', 'moreover', 'additionally',
                'consequently', 'nevertheless', 'thus', 'hence', 'meanwhile',
                'in addition', 'for example', 'for instance', 'in contrast',
                'on the other hand', 'similarly', 'likewise'
            ]

            transition_count = sum(
                essay_text.lower().count(word)
                for word in transition_words
            )

            # Score based on transitions per paragraph
            transitions_per_para = transition_count / max(len(paragraphs), 1)
            coherence_score = min(100, transitions_per_para * 20 + 40)

            return coherence_score

        except Exception as e:
            logger.error(f"Coherence calculation failed: {e}")
            return 50.0

    def _identify_missing_elements(
        self,
        thesis: ThesisAnalysis,
        claims: List[Claim],
        counterarguments: List[str]
    ) -> List[str]:
        """Identify missing argumentative elements."""
        missing = []

        # Check thesis
        if thesis.overall_score < 60:
            missing.append("Strong, clear thesis statement")

        # Check claims
        if len(claims) < 3:
            missing.append("Sufficient supporting claims (found only {})".format(len(claims)))

        # Check evidence
        weak_claims = [c for c in claims if c.strength == 'weak']
        if len(weak_claims) > len(claims) / 2:
            missing.append("Stronger evidence for claims")

        # Check counterarguments
        if not counterarguments:
            missing.append("Counterargument acknowledgment and refutation")

        return missing

    def _generate_recommendations(self, structure: ArgumentStructure) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []

        # Thesis recommendations
        if structure.thesis.overall_score < 70:
            recommendations.append(
                f"Strengthen your thesis statement (current score: {structure.thesis.overall_score:.0f}/100)"
            )
            recommendations.extend(structure.thesis.suggestions[:2])

        # Claims recommendations
        weak_claims = [c for c in structure.claims if c.strength == 'weak']
        if weak_claims:
            recommendations.append(
                f"Provide stronger evidence for {len(weak_claims)} claim(s)"
            )

        # Flow recommendations
        if structure.logical_flow_score < 70:
            recommendations.append(
                "Improve logical flow with better transitions between paragraphs"
            )

        # Coherence recommendations
        if structure.coherence_score < 70:
            recommendations.append(
                "Enhance coherence by using more transition words and phrases"
            )

        # Counterargument recommendations
        if not structure.counterarguments:
            recommendations.append(
                "Address potential counterarguments to strengthen your position"
            )

        # Missing elements
        for element in structure.missing_elements:
            recommendations.append(f"Add: {element}")

        return recommendations[:10]  # Limit to top 10

    def _calculate_overall_score(self, structure: ArgumentStructure) -> float:
        """Calculate overall essay quality score."""
        scores = [
            structure.thesis.overall_score,
            structure.coherence_score,
            structure.logical_flow_score,
        ]

        # Bonus for counterarguments
        if structure.counterarguments:
            scores.append(85)
        else:
            scores.append(50)

        # Average claim strength
        if structure.claims:
            strength_map = {'weak': 50, 'moderate': 70, 'strong': 90}
            avg_claim_strength = sum(
                strength_map.get(c.strength, 60) for c in structure.claims
            ) / len(structure.claims)
            scores.append(avg_claim_strength)

        return sum(scores) / len(scores)

    def _fallback_thesis_analysis(self, essay_text: str) -> ThesisAnalysis:
        """Fallback thesis analysis without AI."""
        # Try to find first sentence that looks like a thesis
        sentences = essay_text.split('.')

        potential_thesis = sentences[0] if sentences else "Not found"

        return ThesisAnalysis(
            statement=potential_thesis[:200],
            location="Beginning",
            clarity_score=50.0,
            specificity_score=50.0,
            arguability_score=50.0,
            overall_score=50.0,
            suggestions=["Use AI analysis for detailed feedback"]
        )

    def _fallback_claim_detection(self, essay_text: str) -> List[Claim]:
        """Fallback claim detection without AI."""
        paragraphs = essay_text.split('\n\n')

        claims = []
        for i, para in enumerate(paragraphs[:5]):  # First 5 paragraphs
            if len(para) > 100:  # Substantial paragraph
                claims.append(Claim(
                    text=para[:150] + "...",
                    location=f"Paragraph {i+1}",
                    evidence=[],
                    strength="moderate",
                    reasoning="Auto-detected paragraph"
                ))

        return claims

    def _extract_json(self, text: str) -> Any:
        """Extract JSON from AI response."""
        try:
            # Try to find JSON in text
            start = text.find('{')
            if start == -1:
                start = text.find('[')

            if start != -1:
                # Find matching closing bracket
                if text[start] == '{':
                    end = text.rfind('}')
                else:
                    end = text.rfind(']')

                if end != -1:
                    json_str = text[start:end+1]
                    return json.loads(json_str)

            # Try parsing entire text
            return json.loads(text)

        except Exception as e:
            logger.warning(f"JSON extraction failed: {e}")
            return {} if '{' in text else []

    def _thesis_to_dict(self, thesis: ThesisAnalysis) -> Dict[str, Any]:
        """Convert ThesisAnalysis to dictionary."""
        return {
            'statement': thesis.statement,
            'location': thesis.location,
            'clarity_score': thesis.clarity_score,
            'specificity_score': thesis.specificity_score,
            'arguability_score': thesis.arguability_score,
            'overall_score': thesis.overall_score,
            'suggestions': thesis.suggestions
        }

    def _claim_to_dict(self, claim: Claim) -> Dict[str, Any]:
        """Convert Claim to dictionary."""
        return {
            'text': claim.text,
            'location': claim.location,
            'evidence': claim.evidence,
            'strength': claim.strength,
            'reasoning': claim.reasoning
        }


def create_analyzer(
    user_id: str,
    ai_router: Optional[AIRouter] = None,
    db_manager: Optional[DatabaseManager] = None
) -> SmartEssayAnalyzer:
    """
    Factory function to create Smart Essay Analyzer.

    Args:
        user_id: Current user ID
        ai_router: AI router instance
        db_manager: Database manager instance

    Returns:
        SmartEssayAnalyzer instance
    """
    return SmartEssayAnalyzer(user_id, ai_router, db_manager)
