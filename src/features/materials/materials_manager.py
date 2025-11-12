"""
Academic Command Center - Materials Library - Materials Manager
Main orchestrator for material upload, processing, and management.
"""

import logging
import uuid
import json
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager, DatabaseHelper
from core.ai_router import AIRouter
from .content_processor import ContentProcessor
from .auto_tagger import AutoTagger

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MaterialsManager:
    """
    Main materials manager orchestrator.

    Workflow:
    1. Upload file (copy to storage)
    2. Process content (extract text)
    3. Auto-tag (extract concepts)
    4. Save to database
    5. Suggest essay links (optional)
    """

    def __init__(
        self,
        user_id: str,
        storage_dir: Optional[str] = None,
        db_manager: Optional[DatabaseManager] = None,
        ai_router: Optional[AIRouter] = None
    ):
        """
        Initialize materials manager.

        Args:
            user_id: Current user ID
            storage_dir: Directory for file storage
            db_manager: Database manager instance
            ai_router: AI Router instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.db_helper = DatabaseHelper(self.db)
        self.ai_router = ai_router or AIRouter(user_id)

        # Setup storage directory
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # Default: data/materials/{user_id}
            self.storage_dir = Path('data') / 'materials' / user_id

        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.content_processor = ContentProcessor()
        self.auto_tagger = AutoTagger(user_id, self.ai_router)

    def upload_material(
        self,
        file_path: str,
        course_name: Optional[str] = None,
        material_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload and process a material.

        Args:
            file_path: Path to file
            course_name: Course name (optional)
            material_type: Type (lecture_note, textbook, article, etc.)

        Returns:
            Upload result with material_id
        """
        logger.info("=" * 60)
        logger.info(f"Uploading material: {file_path}")
        logger.info("=" * 60)

        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'File not found'
                }

            file_name = os.path.basename(file_path)
            logger.info(f"File: {file_name}")

            # Step 1: Copy file to storage
            logger.info("[1/4] Copying file to storage...")
            storage_result = self._store_file(file_path)

            if not storage_result['success']:
                return storage_result

            stored_path = storage_result['stored_path']
            file_size = storage_result['file_size']
            logger.info(f"✓ File stored: {stored_path}")

            # Step 2: Extract content
            logger.info("[2/4] Extracting content...")
            extraction_result = self.content_processor.process_file(stored_path)

            if not extraction_result['success']:
                # Clean up stored file
                self._delete_file(stored_path)
                return {
                    'success': False,
                    'error': f"Content extraction failed: {extraction_result.get('error')}"
                }

            extracted_text = extraction_result['extracted_text']
            metadata = extraction_result['metadata']
            logger.info(f"✓ Extracted {metadata['word_count']} words")

            # Step 3: Auto-tag
            logger.info("[3/4] Auto-tagging...")
            tagging_result = self.auto_tagger.tag_material(
                extracted_text,
                file_name
            )

            if not tagging_result['success']:
                logger.warning("Auto-tagging failed, using empty tags")
                key_concepts = []
                content_summary = ""
                tags = []
                academic_level = "unknown"
            else:
                key_concepts = tagging_result['key_concepts']
                content_summary = tagging_result['content_summary']
                tags = tagging_result['tags']
                academic_level = tagging_result['academic_level']

            logger.info(f"✓ Generated {len(key_concepts)} concepts, {len(tags)} tags")

            # Step 4: Save to database
            logger.info("[4/4] Saving to database...")
            material_id = str(uuid.uuid4())

            material_data = {
                'id': material_id,
                'user_id': self.user_id,
                'file_name': file_name,
                'file_path': stored_path,
                'file_type': metadata['file_type'],
                'file_size': file_size,
                'course_name': course_name,
                'material_type': material_type or 'general',
                'extracted_text': extracted_text,
                'content_summary': content_summary,
                'key_concepts': json.dumps(key_concepts),
                'tags': json.dumps(tags),
                'word_count': metadata['word_count'],
                'academic_level': academic_level,
                'uploaded_at': datetime.now().isoformat()
            }

            self._save_material(material_data)
            logger.info(f"✓ Material saved with ID: {material_id}")

            logger.info("=" * 60)
            logger.info("Upload completed successfully!")
            logger.info("=" * 60)

            return {
                'success': True,
                'material_id': material_id,
                'file_name': file_name,
                'word_count': metadata['word_count'],
                'concepts': key_concepts,
                'summary': content_summary
            }

        except Exception as e:
            logger.error(f"Material upload failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def link_material_to_essay(
        self,
        material_id: str,
        essay_id: str,
        relevance_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Link a material to an essay.

        Args:
            material_id: Material ID
            essay_id: Essay ID
            relevance_score: Relevance score (0-100)

        Returns:
            Link result
        """
        try:
            link_id = str(uuid.uuid4())

            query = """
            INSERT INTO material_links (
                id, material_id, essay_id, relevance_score, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    link_id,
                    material_id,
                    essay_id,
                    relevance_score,
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Linked material {material_id} to essay {essay_id}")

            return {
                'success': True,
                'link_id': link_id
            }

        except Exception as e:
            logger.error(f"Failed to link material: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def suggest_essay_links(self, material_id: str) -> Dict[str, Any]:
        """
        Suggest which essays this material could be linked to.

        Args:
            material_id: Material ID

        Returns:
            Suggestions with relevance scores
        """
        # Get material
        material = self._get_material(material_id)
        if not material:
            return {
                'success': False,
                'error': 'Material not found'
            }

        material_concepts = json.loads(material.get('key_concepts', '[]'))

        # Get all user's essays
        essays = self._get_user_essays()

        suggestions = []

        for essay in essays:
            essay_concepts = json.loads(essay.get('key_concepts', '[]'))

            # Calculate relevance
            link_result = self.auto_tagger.suggest_material_links(
                material_concepts,
                essay_concepts
            )

            if link_result['should_link']:
                suggestions.append({
                    'essay_id': essay['id'],
                    'essay_title': essay['title'],
                    'relevance_score': link_result['relevance_score'],
                    'matching_concepts': link_result['matching_concepts']
                })

        # Sort by relevance
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)

        return {
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        }

    def get_material(self, material_id: str) -> Dict[str, Any]:
        """Get material by ID."""
        material = self._get_material(material_id)

        if not material:
            return {
                'success': False,
                'error': 'Material not found'
            }

        return {
            'success': True,
            'material': material
        }

    def list_materials(
        self,
        course_name: Optional[str] = None,
        material_type: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List user's materials with optional filters.

        Args:
            course_name: Filter by course
            material_type: Filter by type
            search_query: Search in file names and tags

        Returns:
            List of materials
        """
        query_parts = ["SELECT * FROM materials WHERE user_id = ?"]
        params = [self.user_id]

        if course_name:
            query_parts.append("AND course_name = ?")
            params.append(course_name)

        if material_type:
            query_parts.append("AND material_type = ?")
            params.append(material_type)

        if search_query:
            query_parts.append("AND (file_name LIKE ? OR tags LIKE ?)")
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern])

        query_parts.append("ORDER BY uploaded_at DESC")

        query = " ".join(query_parts)

        materials = self.db.execute_query(query, tuple(params), fetch_all=True)

        return {
            'success': True,
            'materials': materials or [],
            'count': len(materials) if materials else 0
        }

    def delete_material(self, material_id: str) -> Dict[str, Any]:
        """
        Delete a material.

        Args:
            material_id: Material ID

        Returns:
            Deletion result
        """
        try:
            # Get material
            material = self._get_material(material_id)
            if not material:
                return {
                    'success': False,
                    'error': 'Material not found'
                }

            # Delete file
            file_path = material.get('file_path')
            if file_path:
                self._delete_file(file_path)

            # Delete from database
            query = "DELETE FROM materials WHERE id = ?"
            self.db.execute_query(query, (material_id,))

            # Delete links
            link_query = "DELETE FROM material_links WHERE material_id = ?"
            self.db.execute_query(link_query, (material_id,))

            logger.info(f"Deleted material {material_id}")

            return {
                'success': True,
                'message': 'Material deleted'
            }

        except Exception as e:
            logger.error(f"Failed to delete material: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _store_file(self, source_path: str) -> Dict[str, Any]:
        """Copy file to storage directory."""
        try:
            file_name = os.path.basename(source_path)
            file_size = os.path.getsize(source_path)

            # Create unique filename
            unique_name = f"{uuid.uuid4()}_{file_name}"
            dest_path = self.storage_dir / unique_name

            # Copy file
            shutil.copy2(source_path, dest_path)

            return {
                'success': True,
                'stored_path': str(dest_path),
                'file_size': file_size
            }

        except Exception as e:
            logger.error(f"Failed to store file: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _delete_file(self, file_path: str):
        """Delete file from storage."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")

    def _save_material(self, material_data: Dict[str, Any]):
        """Save material to database."""
        query = """
        INSERT INTO materials (
            id, user_id, file_name, file_path, file_type, file_size,
            course_name, material_type, extracted_text, content_summary,
            key_concepts, tags, word_count, academic_level, uploaded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(
            query,
            (
                material_data['id'],
                material_data['user_id'],
                material_data['file_name'],
                material_data['file_path'],
                material_data['file_type'],
                material_data['file_size'],
                material_data['course_name'],
                material_data['material_type'],
                material_data['extracted_text'],
                material_data['content_summary'],
                material_data['key_concepts'],
                material_data['tags'],
                material_data['word_count'],
                material_data['academic_level'],
                material_data['uploaded_at']
            )
        )

    def _get_material(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get material from database."""
        query = "SELECT * FROM materials WHERE id = ?"
        return self.db.execute_query(query, (material_id,), fetch_one=True)

    def _get_user_essays(self) -> List[Dict[str, Any]]:
        """Get all user's essays."""
        query = "SELECT * FROM essays WHERE user_id = ? ORDER BY created_at DESC"
        return self.db.execute_query(query, (self.user_id,), fetch_all=True) or []


if __name__ == "__main__":
    print("Testing Materials Manager...")

    manager = MaterialsManager(user_id="test_user")

    print("\nMaterials Manager structure validated!")
    print("\nUsage:")
    print("  manager.upload_material(file_path, course_name, material_type)")
    print("  manager.link_material_to_essay(material_id, essay_id)")
    print("  manager.suggest_essay_links(material_id)")
    print("  manager.list_materials(course_name, material_type, search_query)")
    print("  manager.delete_material(material_id)")
