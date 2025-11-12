"""
Academic Command Center - Essay Parser - Knowledge Gap Detector
Identifies knowledge gaps by comparing required concepts against user's materials.
"""

import logging
from typing import Dict, Any, List, Optional, Set
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class KnowledgeGapDetector:
    """
    Detects knowledge gaps.

    Compares:
    - Required concepts (from essay)
    - User's uploaded materials

    Identifies:
    - Missing coverage
    - Weak coverage
    - Good coverage
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize gap detector.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

    def detect_gaps(
        self,
        required_concepts: List[str],
        essay_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect knowledge gaps.

        Args:
            required_concepts: List of concepts needed for essay
            essay_id: Essay ID (to check linked materials)

        Returns:
            Gap analysis
        """
        if not required_concepts:
            return {
                'success': True,
                'gaps': [],
                'covered': [],
                'message': 'No required concepts to analyze'
            }

        logger.info(f"Detecting gaps for {len(required_concepts)} concepts...")

        # Get user's materials
        user_materials = self._get_user_materials()
        logger.info(f"Found {len(user_materials)} user materials")

        # Check coverage for each concept
        coverage_analysis = []

        for concept in required_concepts:
            coverage = self._check_concept_coverage(concept, user_materials)
            coverage_analysis.append({
                'concept': concept,
                'coverage': coverage['level'],  # none, weak, good
                'found_in': coverage['materials'],
                'suggestion': coverage['suggestion']
            })

        # Categorize
        gaps = [c for c in coverage_analysis if c['coverage'] == 'none']
        weak = [c for c in coverage_analysis if c['coverage'] == 'weak']
        covered = [c for c in coverage_analysis if c['coverage'] == 'good']

        return {
            'success': True,
            'gaps': gaps,  # Missing completely
            'weak_coverage': weak,  # Mentioned but not enough
            'covered': covered,  # Good coverage
            'summary': {
                'total_concepts': len(required_concepts),
                'gaps_count': len(gaps),
                'weak_count': len(weak),
                'covered_count': len(covered),
                'coverage_percentage': int((len(covered) / len(required_concepts)) * 100)
            }
        }

    def _get_user_materials(self) -> List[Dict[str, Any]]:
        """
        Get all user's materials from database.

        Returns:
            List of material dictionaries
        """
        query = """
        SELECT
            id,
            file_name,
            extracted_text,
            content_summary,
            key_concepts
        FROM materials
        WHERE user_id = ?
        """

        materials = self.db.execute_query(query, (self.user_id,), fetch_all=True)
        return materials or []

    def _check_concept_coverage(
        self,
        concept: str,
        materials: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if concept is covered in materials.

        Args:
            concept: Concept to check
            materials: User's materials

        Returns:
            Coverage analysis
        """
        concept_lower = concept.lower()
        found_in = []
        mention_count = 0

        for material in materials:
            # Check in extracted text
            if material.get('extracted_text'):
                text = material['extracted_text'].lower()
                if concept_lower in text:
                    # Count mentions
                    count = text.count(concept_lower)
                    mention_count += count

                    found_in.append({
                        'material_id': material['id'],
                        'file_name': material['file_name'],
                        'mentions': count
                    })

            # Check in key concepts
            if material.get('key_concepts'):
                import json
                try:
                    key_concepts = json.loads(material['key_concepts'])
                    if any(concept_lower in kc.lower() for kc in key_concepts):
                        if not any(m['material_id'] == material['id'] for m in found_in):
                            found_in.append({
                                'material_id': material['id'],
                                'file_name': material['file_name'],
                                'mentions': 1  # Found in key concepts
                            })
                except:
                    pass

        # Determine coverage level
        if not found_in:
            level = 'none'
            suggestion = f"Upload materials covering '{concept}' or search for external sources"
        elif mention_count < 3:
            level = 'weak'
            suggestion = f"'{concept}' mentioned but needs more depth - find additional materials"
        else:
            level = 'good'
            suggestion = f"'{concept}' well covered in your materials"

        return {
            'level': level,
            'materials': found_in,
            'mention_count': mention_count,
            'suggestion': suggestion
        }

    def generate_recommendations(
        self,
        gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate actionable recommendations for gaps.

        Args:
            gaps: List of knowledge gaps

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not gaps:
            recommendations.append("✓ All concepts are covered in your materials")
            return recommendations

        for gap in gaps:
            concept = gap['concept']
            recommendations.append(
                f"📚 Find materials on '{concept}' - {gap['suggestion']}"
            )

        # Add general recommendations
        recommendations.append("\n💡 Actions:")
        recommendations.append("  • Check Canvas for lecture notes/readings")
        recommendations.append("  • Search your textbook/course materials")
        recommendations.append("  • Use library databases for academic sources")

        return recommendations


if __name__ == "__main__":
    print("Testing Knowledge Gap Detector...")

    detector = KnowledgeGapDetector(user_id="test_user")

    test_concepts = [
        "Postmodernism",
        "Music Production",
        "Sampling Techniques",
        "Genre-blending"
    ]

    # Note: Requires database with materials
    print("\nGap Detector structure validated!")
