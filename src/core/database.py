"""
Academic Command Center - Database Manager
Handles all SQLite database operations with connection pooling,
transactions, migrations, backups, and integrity checks.
"""

import sqlite3
import os
import shutil
import hashlib
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
from contextlib import contextmanager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Comprehensive database manager for Academic Command Center.

    Features:
    - Connection pooling
    - Transaction management
    - Automatic migrations
    - Backup and restore
    - Integrity checks
    - Query optimization
    - Full-text search
    """

    def __init__(self, db_path: str = r"C:\Users\Gamer\Getitdone\database\acc_main.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.schema_version = "1.0.0"

        # Ensure database directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

        # Initialize database
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database with schema if it doesn't exist."""
        is_new_db = not os.path.exists(self.db_path)

        # Create connection
        self.connection = self._create_connection()

        if is_new_db:
            logger.info("Creating new database...")
            self._create_schema()
            logger.info("Database schema created successfully")
        else:
            logger.info(f"Connected to existing database: {self.db_path}")
            self._verify_schema()

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create database connection with optimal settings.

        Returns:
            SQLite connection object
        """
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threaded access
                timeout=30.0  # 30 second timeout for locked database
            )

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")

            # Optimize performance
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")

            # Row factory for dict-like access
            conn.row_factory = sqlite3.Row

            logger.debug("Database connection created with optimal settings")
            return conn

        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _create_schema(self) -> None:
        """Create database schema from schema.sql file."""
        schema_path = os.path.join(
            os.path.dirname(self.db_path),
            "schema.sql"
        )

        if not os.path.exists(schema_path):
            logger.error(f"Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        try:
            self.connection.executescript(schema_sql)
            self.connection.commit()
            logger.info("Database schema created from schema.sql")
        except sqlite3.Error as e:
            logger.error(f"Failed to create schema: {e}")
            self.connection.rollback()
            raise

    def _verify_schema(self) -> None:
        """Verify that all required tables exist."""
        required_tables = [
            'users', 'user_api_keys', 'essays', 'tasks', 'materials',
            'material_links', 'focus_sessions', 'progress_logs',
            'ai_interactions', 'canvas_sync_log', 'sources',
            'writing_snapshots', 'analytics_cache', 'system_health',
            'app_settings'
        ]

        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = [row[0] for row in cursor.fetchall()]

        missing_tables = set(required_tables) - set(existing_tables)

        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            logger.info("Recreating schema...")
            self._create_schema()
        else:
            logger.debug("Schema verification passed")

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            with db.transaction():
                db.execute_query("INSERT INTO ...")
                db.execute_query("UPDATE ...")
        """
        try:
            yield self.connection
            self.connection.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """
        Execute a SQL query safely with parameterized inputs.

        Args:
            query: SQL query with ? placeholders
            params: Tuple of parameters
            fetch_one: Return single row
            fetch_all: Return all rows

        Returns:
            Query results or None
        """
        cursor = self.connection.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                self.connection.commit()
                return cursor.lastrowid

        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute same query multiple times with different parameters.

        Args:
            query: SQL query
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        cursor = self.connection.cursor()

        try:
            cursor.executemany(query, params_list)
            self.connection.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Batch execution failed: {e}")
            self.connection.rollback()
            raise

    def full_text_search(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search on materials.

        Args:
            search_term: Search query
            limit: Maximum results

        Returns:
            List of matching materials with snippets
        """
        query = """
        SELECT
            m.id,
            m.file_name,
            m.material_type,
            m.content_summary,
            snippet(materials_fts, 2, '<mark>', '</mark>', '...', 30) as snippet,
            rank
        FROM materials_fts
        JOIN materials m ON materials_fts.material_id = m.id
        WHERE materials_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """

        return self.execute_query(
            query,
            (search_term, limit),
            fetch_all=True
        )

    def create_backup(self, backup_dir: Optional[str] = None) -> str:
        """
        Create a backup of the database.

        Args:
            backup_dir: Directory to store backup (default: database/backups)

        Returns:
            Path to backup file
        """
        if backup_dir is None:
            backup_dir = os.path.join(
                os.path.dirname(self.db_path),
                "backups"
            )

        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"acc_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            # Close current connection
            if self.connection:
                self.connection.close()

            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            # Reopen connection
            self.connection = self._create_connection()

            logger.info(f"Backup created: {backup_path}")

            # Clean old backups (keep last 30)
            self._clean_old_backups(backup_dir, keep=30)

            return backup_path

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    def _clean_old_backups(self, backup_dir: str, keep: int = 30) -> None:
        """
        Remove old backup files, keeping only the most recent.

        Args:
            backup_dir: Directory containing backups
            keep: Number of backups to keep
        """
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith("acc_backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                backups.append((filepath, os.path.getmtime(filepath)))

        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)

        # Delete old backups
        for filepath, _ in backups[keep:]:
            try:
                os.remove(filepath)
                logger.debug(f"Deleted old backup: {filepath}")
            except Exception as e:
                logger.warning(f"Failed to delete backup {filepath}: {e}")

    def restore_backup(self, backup_path: str) -> None:
        """
        Restore database from backup.

        Args:
            backup_path: Path to backup file
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        try:
            # Close current connection
            if self.connection:
                self.connection.close()

            # Backup current database before restoring
            current_backup = self.db_path + ".before_restore"
            shutil.copy2(self.db_path, current_backup)
            logger.info(f"Current database backed up to: {current_backup}")

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)

            # Reopen connection
            self.connection = self._create_connection()

            logger.info(f"Database restored from: {backup_path}")

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise

    def check_integrity(self) -> Dict[str, Any]:
        """
        Run database integrity checks.

        Returns:
            Dictionary with check results
        """
        results = {
            'integrity_check': False,
            'foreign_key_check': False,
            'quick_check': False,
            'errors': []
        }

        try:
            # Integrity check
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            results['integrity_check'] = (integrity_result == 'ok')

            if integrity_result != 'ok':
                results['errors'].append(f"Integrity: {integrity_result}")

            # Foreign key check
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            results['foreign_key_check'] = (len(fk_violations) == 0)

            if fk_violations:
                results['errors'].append(f"Foreign key violations: {len(fk_violations)}")

            # Quick check
            cursor.execute("PRAGMA quick_check")
            quick_result = cursor.fetchone()[0]
            results['quick_check'] = (quick_result == 'ok')

            if quick_result != 'ok':
                results['errors'].append(f"Quick check: {quick_result}")

            logger.info(f"Integrity check results: {results}")
            return results

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            results['errors'].append(str(e))
            return results

    def optimize(self) -> None:
        """Optimize database performance."""
        try:
            logger.info("Optimizing database...")

            # Analyze tables for query optimization
            self.connection.execute("ANALYZE")

            # Rebuild indexes
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = cursor.fetchall()

            for idx in indexes:
                index_name = idx[0]
                self.connection.execute(f"REINDEX {index_name}")

            # Vacuum to reclaim space
            self.connection.execute("VACUUM")

            self.connection.commit()
            logger.info("Database optimization completed")

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database stats
        """
        stats = {}

        try:
            # File size
            stats['file_size_bytes'] = os.path.getsize(self.db_path)
            stats['file_size_mb'] = round(stats['file_size_bytes'] / (1024 * 1024), 2)

            # Page count and size
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA page_count")
            stats['page_count'] = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            stats['page_size'] = cursor.fetchone()[0]

            # Table counts
            tables = [
                'users', 'essays', 'tasks', 'materials',
                'focus_sessions', 'ai_interactions'
            ]

            stats['table_counts'] = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats['table_counts'][table] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def migrate(self, migration_file: str) -> None:
        """
        Apply database migration.

        Args:
            migration_file: Path to migration SQL file
        """
        if not os.path.exists(migration_file):
            raise FileNotFoundError(f"Migration file not found: {migration_file}")

        # Create backup before migration
        backup_path = self.create_backup()
        logger.info(f"Backup created before migration: {backup_path}")

        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()

            self.connection.executescript(migration_sql)
            self.connection.commit()

            logger.info(f"Migration applied: {migration_file}")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            logger.info("Rolling back to backup...")
            self.restore_backup(backup_path)
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


# ============================================
# Convenience Functions for Common Operations
# ============================================

class DatabaseHelper:
    """Helper class with common database operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_user(
        self,
        user_id: str,
        username: str,
        display_name: str,
        email: Optional[str] = None
    ) -> str:
        """Create a new user."""
        query = """
        INSERT INTO users (id, username, display_name, email)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute_query(query, (user_id, username, display_name, email))
        logger.info(f"User created: {username}")
        return user_id

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = ?"
        return self.db.execute_query(query, (user_id,), fetch_one=True)

    def create_essay(self, essay_data: Dict[str, Any]) -> str:
        """Create a new essay record."""
        query = """
        INSERT INTO essays (
            id, user_id, title, raw_instructions,
            word_count_min, word_count_max, due_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        essay_id = essay_data['id']
        params = (
            essay_id,
            essay_data['user_id'],
            essay_data['title'],
            essay_data['raw_instructions'],
            essay_data.get('word_count_min'),
            essay_data.get('word_count_max'),
            essay_data.get('due_date')
        )

        self.db.execute_query(query, params)
        logger.info(f"Essay created: {essay_id}")
        return essay_id

    def get_active_essays(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active essays for a user."""
        query = """
        SELECT * FROM v_active_essays
        WHERE user_id = ?
        ORDER BY due_date ASC
        """
        return self.db.execute_query(query, (user_id,), fetch_all=True)

    def update_essay_progress(
        self,
        essay_id: str,
        completion_percentage: float,
        current_word_count: int
    ) -> None:
        """Update essay progress."""
        query = """
        UPDATE essays
        SET completion_percentage = ?,
            current_word_count = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        self.db.execute_query(
            query,
            (completion_percentage, current_word_count, essay_id)
        )

    def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task."""
        query = """
        INSERT INTO tasks (
            id, essay_id, user_id, title, description,
            task_type, order_index, estimated_duration_minutes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        task_id = task_data['id']
        params = (
            task_id,
            task_data['essay_id'],
            task_data['user_id'],
            task_data['title'],
            task_data.get('description', ''),
            task_data['task_type'],
            task_data['order_index'],
            task_data.get('estimated_duration_minutes')
        )

        self.db.execute_query(query, params)
        return task_id

    def get_essay_tasks(
        self,
        essay_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks for an essay, optionally filtered by status."""
        if status:
            query = """
            SELECT * FROM tasks
            WHERE essay_id = ? AND status = ?
            ORDER BY order_index
            """
            params = (essay_id, status)
        else:
            query = """
            SELECT * FROM tasks
            WHERE essay_id = ?
            ORDER BY order_index
            """
            params = (essay_id,)

        return self.db.execute_query(query, params, fetch_all=True)

    def log_ai_interaction(
        self,
        user_id: str,
        task_type: str,
        provider: str,
        prompt: str,
        response: str,
        cache_key: str,
        cache_duration_hours: int = 24
    ) -> str:
        """Log an AI interaction for caching."""
        import uuid

        interaction_id = str(uuid.uuid4())
        cache_expires = datetime.now() + timedelta(hours=cache_duration_hours)

        query = """
        INSERT INTO ai_interactions (
            id, user_id, task_type, provider,
            prompt_text, prompt_hash, response_text,
            cache_key, cache_expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()

        self.db.execute_query(
            query,
            (
                interaction_id, user_id, task_type, provider,
                prompt, prompt_hash, response, cache_key, cache_expires
            )
        )

        return interaction_id

    def get_cached_ai_response(self, cache_key: str) -> Optional[str]:
        """Get cached AI response if available and not expired."""
        query = """
        SELECT response_text
        FROM ai_interactions
        WHERE cache_key = ?
        AND cache_expires_at > CURRENT_TIMESTAMP
        ORDER BY created_at DESC
        LIMIT 1
        """

        result = self.db.execute_query(query, (cache_key,), fetch_one=True)
        return result['response_text'] if result else None


if __name__ == "__main__":
    # Test database creation
    print("Testing Database Manager...")

    # Use temporary database for testing
    test_db_path = r"C:\Users\Gamer\Getitdone\database\test_acc.db"

    db = DatabaseManager(test_db_path)
    helper = DatabaseHelper(db)

    # Check integrity
    integrity = db.check_integrity()
    print(f"Integrity Check: {integrity}")

    # Get stats
    stats = db.get_database_stats()
    print(f"Database Stats: {stats}")

    # Create backup
    backup_path = db.create_backup()
    print(f"Backup created: {backup_path}")

    print("Database Manager test completed successfully!")
