"""
Academic Command Center - Version Control - Snapshot Manager
Manages essay snapshots for version control and history tracking.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SnapshotType:
    """Snapshot type constants."""
    AUTO = "auto"
    MANUAL = "manual"
    BEFORE_MAJOR_EDIT = "before_major_edit"


class SnapshotManager:
    """
    Manages essay snapshots for version control.

    Features:
    - Create snapshots (auto, manual, before major edits)
    - List snapshots for an essay
    - Compare snapshots
    - Restore from snapshot
    - Auto-snapshot on major changes
    - Snapshot statistics
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize snapshot manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        logger.info(f"Snapshot manager initialized for user {user_id}")

    def create_snapshot(
        self,
        essay_id: str,
        content_text: str,
        snapshot_type: str = SnapshotType.MANUAL,
        label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new snapshot of an essay.

        Args:
            essay_id: Essay ID
            content_text: Content to snapshot
            snapshot_type: Type of snapshot (auto, manual, before_major_edit)
            label: Optional custom label

        Returns:
            Result with snapshot ID
        """
        try:
            snapshot_id = str(uuid.uuid4())

            # Calculate word count
            word_count = len(content_text.split())

            # Generate default label if not provided
            if not label:
                if snapshot_type == SnapshotType.AUTO:
                    label = f"Auto-save {datetime.now().strftime('%I:%M %p')}"
                elif snapshot_type == SnapshotType.MANUAL:
                    label = f"Manual snapshot {datetime.now().strftime('%b %d, %Y')}"
                elif snapshot_type == SnapshotType.BEFORE_MAJOR_EDIT:
                    label = f"Before edit {datetime.now().strftime('%I:%M %p')}"

            # Insert snapshot
            query = """
            INSERT INTO writing_snapshots (
                id, essay_id, user_id, content_text,
                word_count, snapshot_type, snapshot_label, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    snapshot_id,
                    essay_id,
                    self.user_id,
                    content_text,
                    word_count,
                    snapshot_type,
                    label,
                    datetime.now().isoformat()
                )
            )

            logger.info(f"Created snapshot {snapshot_id} for essay {essay_id}")

            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'word_count': word_count,
                'label': label
            }

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_snapshots(
        self,
        essay_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get all snapshots for an essay.

        Args:
            essay_id: Essay ID
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshots
        """
        try:
            query = """
            SELECT
                id, essay_id, content_text, word_count,
                snapshot_type, snapshot_label, created_at
            FROM writing_snapshots
            WHERE essay_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """

            snapshots = self.db.execute_query(
                query,
                (essay_id, self.user_id, limit),
                fetch_all=True
            )

            return {
                'success': True,
                'snapshots': snapshots or [],
                'count': len(snapshots) if snapshots else 0
            }

        except Exception as e:
            logger.error(f"Failed to get snapshots: {e}")
            return {
                'success': False,
                'error': str(e),
                'snapshots': []
            }

    def get_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Get a specific snapshot by ID.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot data
        """
        try:
            query = """
            SELECT
                id, essay_id, content_text, word_count,
                snapshot_type, snapshot_label, created_at
            FROM writing_snapshots
            WHERE id = ? AND user_id = ?
            """

            snapshot = self.db.execute_query(
                query,
                (snapshot_id, self.user_id),
                fetch_one=True
            )

            if not snapshot:
                return {
                    'success': False,
                    'error': 'Snapshot not found'
                }

            return {
                'success': True,
                'snapshot': snapshot
            }

        except Exception as e:
            logger.error(f"Failed to get snapshot: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Delete a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Success status
        """
        try:
            query = """
            DELETE FROM writing_snapshots
            WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(query, (snapshot_id, self.user_id))

            logger.info(f"Deleted snapshot {snapshot_id}")

            return {
                'success': True,
                'message': 'Snapshot deleted'
            }

        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def restore_snapshot(
        self,
        snapshot_id: str,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Restore an essay from a snapshot.

        Args:
            snapshot_id: Snapshot ID to restore
            create_backup: Whether to create backup of current content

        Returns:
            Restored content and success status
        """
        try:
            # Get snapshot
            snapshot_result = self.get_snapshot(snapshot_id)
            if not snapshot_result['success']:
                return snapshot_result

            snapshot = snapshot_result['snapshot']
            essay_id = snapshot['essay_id']

            # Get current essay content for backup
            if create_backup:
                current_query = "SELECT content FROM essays WHERE id = ? AND user_id = ?"
                current_essay = self.db.execute_query(
                    current_query,
                    (essay_id, self.user_id),
                    fetch_one=True
                )

                if current_essay and current_essay.get('content'):
                    # Create backup snapshot
                    self.create_snapshot(
                        essay_id,
                        current_essay['content'],
                        snapshot_type=SnapshotType.BEFORE_MAJOR_EDIT,
                        label="Backup before restore"
                    )

            # Restore content to essay
            update_query = """
            UPDATE essays
            SET
                content = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
            """

            self.db.execute_query(
                update_query,
                (
                    snapshot['content_text'],
                    datetime.now().isoformat(),
                    essay_id,
                    self.user_id
                )
            )

            logger.info(f"Restored essay {essay_id} from snapshot {snapshot_id}")

            return {
                'success': True,
                'message': 'Essay restored from snapshot',
                'content': snapshot['content_text'],
                'word_count': snapshot['word_count']
            }

        except Exception as e:
            logger.error(f"Failed to restore snapshot: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def should_auto_snapshot(
        self,
        essay_id: str,
        new_content: str
    ) -> bool:
        """
        Determine if an auto-snapshot should be created.

        Logic: Create snapshot if 30+ minutes since last snapshot
        or significant content change (50+ words difference).

        Args:
            essay_id: Essay ID
            new_content: New content to compare

        Returns:
            Whether to create auto-snapshot
        """
        try:
            # Get most recent snapshot
            query = """
            SELECT content_text, word_count, created_at
            FROM writing_snapshots
            WHERE essay_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """

            last_snapshot = self.db.execute_query(
                query,
                (essay_id, self.user_id),
                fetch_one=True
            )

            if not last_snapshot:
                # No snapshots yet, create one
                return True

            # Check time difference
            last_time = datetime.fromisoformat(last_snapshot['created_at'])
            minutes_elapsed = (datetime.now() - last_time).total_seconds() / 60

            if minutes_elapsed >= 30:
                logger.debug(f"Auto-snapshot: 30+ minutes elapsed")
                return True

            # Check content difference
            old_word_count = last_snapshot['word_count']
            new_word_count = len(new_content.split())
            word_diff = abs(new_word_count - old_word_count)

            if word_diff >= 50:
                logger.debug(f"Auto-snapshot: 50+ words changed ({word_diff})")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check auto-snapshot: {e}")
            return False

    def get_snapshot_statistics(self, essay_id: str) -> Dict[str, Any]:
        """
        Get statistics for snapshots of an essay.

        Args:
            essay_id: Essay ID

        Returns:
            Snapshot statistics
        """
        try:
            query = """
            SELECT
                COUNT(*) as total_snapshots,
                SUM(CASE WHEN snapshot_type = 'manual' THEN 1 ELSE 0 END) as manual_count,
                SUM(CASE WHEN snapshot_type = 'auto' THEN 1 ELSE 0 END) as auto_count,
                MAX(created_at) as last_snapshot,
                MIN(created_at) as first_snapshot
            FROM writing_snapshots
            WHERE essay_id = ? AND user_id = ?
            """

            stats = self.db.execute_query(
                query,
                (essay_id, self.user_id),
                fetch_one=True
            )

            if not stats or stats['total_snapshots'] == 0:
                return {
                    'success': True,
                    'total_snapshots': 0,
                    'manual_count': 0,
                    'auto_count': 0
                }

            return {
                'success': True,
                'total_snapshots': stats['total_snapshots'],
                'manual_count': stats['manual_count'],
                'auto_count': stats['auto_count'],
                'last_snapshot': stats['last_snapshot'],
                'first_snapshot': stats['first_snapshot']
            }

        except Exception as e:
            logger.error(f"Failed to get snapshot statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def compare_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two snapshots.

        Args:
            snapshot_id_1: First snapshot ID
            snapshot_id_2: Second snapshot ID

        Returns:
            Comparison data
        """
        try:
            # Get both snapshots
            snap1 = self.get_snapshot(snapshot_id_1)
            snap2 = self.get_snapshot(snapshot_id_2)

            if not snap1['success'] or not snap2['success']:
                return {
                    'success': False,
                    'error': 'One or both snapshots not found'
                }

            s1 = snap1['snapshot']
            s2 = snap2['snapshot']

            # Calculate differences
            word_diff = s2['word_count'] - s1['word_count']
            content1_lines = s1['content_text'].split('\n')
            content2_lines = s2['content_text'].split('\n')

            # Simple line-based comparison
            lines_added = len(content2_lines) - len(content1_lines)

            return {
                'success': True,
                'snapshot1': {
                    'id': s1['id'],
                    'label': s1['snapshot_label'],
                    'created_at': s1['created_at'],
                    'word_count': s1['word_count']
                },
                'snapshot2': {
                    'id': s2['id'],
                    'label': s2['snapshot_label'],
                    'created_at': s2['created_at'],
                    'word_count': s2['word_count']
                },
                'differences': {
                    'word_count_diff': word_diff,
                    'lines_diff': lines_added,
                    'content1': s1['content_text'],
                    'content2': s2['content_text']
                }
            }

        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    print("Testing Snapshot Manager...")

    manager = SnapshotManager(user_id="test_user")

    # Test create snapshot
    result = manager.create_snapshot(
        essay_id="test_essay_1",
        content_text="This is a test essay with some content. " * 20,
        snapshot_type=SnapshotType.MANUAL,
        label="Test Snapshot 1"
    )
    print(f"\nCreate snapshot: {result['success']}")
    snapshot1_id = result.get('snapshot_id')

    # Create another snapshot
    result2 = manager.create_snapshot(
        essay_id="test_essay_1",
        content_text="This is a test essay with updated content and more words. " * 25,
        snapshot_type=SnapshotType.MANUAL,
        label="Test Snapshot 2"
    )
    print(f"Create second snapshot: {result2['success']}")
    snapshot2_id = result2.get('snapshot_id')

    # Test get snapshots
    snapshots = manager.get_snapshots(essay_id="test_essay_1")
    print(f"\nGet snapshots: {snapshots['count']} found")

    # Test snapshot statistics
    stats = manager.get_snapshot_statistics(essay_id="test_essay_1")
    print(f"\nSnapshot statistics:")
    print(f"  Total: {stats.get('total_snapshots', 0)}")
    print(f"  Manual: {stats.get('manual_count', 0)}")
    print(f"  Auto: {stats.get('auto_count', 0)}")

    # Test compare snapshots
    if snapshot1_id and snapshot2_id:
        comparison = manager.compare_snapshots(snapshot1_id, snapshot2_id)
        if comparison['success']:
            print(f"\nSnapshot comparison:")
            print(f"  Word diff: {comparison['differences']['word_count_diff']}")
            print(f"  Lines diff: {comparison['differences']['lines_diff']}")

    # Test should auto-snapshot
    should_snap = manager.should_auto_snapshot(
        "test_essay_1",
        "Completely new content with lots of changes. " * 50
    )
    print(f"\nShould auto-snapshot: {should_snap}")

    print("\nSnapshot Manager validated!")
