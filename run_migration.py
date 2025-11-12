"""
Database Migration Runner
Applies missing schema changes to existing database
"""
import sqlite3
from pathlib import Path
import sys

def run_migration():
    print("="*60)
    print("  DATABASE MIGRATION - SCHEMA UPDATE")
    print("="*60)

    db_path = Path('database/acc_main.db')
    migration_path = Path('database/migrations/001_add_missing_schema.sql')

    if not db_path.exists():
        print("✗ Database not found at:", db_path)
        print("  Run installlearn.bat first to create the database")
        return False

    if not migration_path.exists():
        print("✗ Migration file not found at:", migration_path)
        return False

    print(f"\n✓ Database found: {db_path}")
    print(f"✓ Migration file: {migration_path}")

    try:
        # Read migration SQL
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Connect to database
        print("\nConnecting to database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute migration
        print("Applying migration...")
        cursor.executescript(migration_sql)

        # Commit changes
        conn.commit()

        # Verify new tables exist
        print("\nVerifying migration...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['assignments', 'subjects', 'achievements']
        missing_tables = [t for t in required_tables if t not in tables]

        if missing_tables:
            print(f"✗ Missing tables: {missing_tables}")
            return False

        print("✓ All required tables exist:")
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")

        # Check new columns in goals table
        cursor.execute("PRAGMA table_info(goals)")
        goals_columns = [row[1] for row in cursor.fetchall()]
        required_cols = ['category', 'target_date', 'unit', 'start_date', 'is_smart']

        print("\n✓ Goals table columns:")
        for col in required_cols:
            status = "✓" if col in goals_columns else "✗"
            print(f"  {status} {col}")

        # Check subject column in focus_sessions
        cursor.execute("PRAGMA table_info(focus_sessions)")
        focus_columns = [row[1] for row in cursor.fetchall()]
        has_subject = 'subject' in focus_columns
        print(f"\n{'✓' if has_subject else '✗'} focus_sessions.subject column")

        conn.close()

        print("\n" + "="*60)
        print("  MIGRATION COMPLETE!")
        print("="*60)
        print("\n✓ Database schema updated successfully")
        print("✓ Missing tables added: assignments, subjects, achievements")
        print("✓ Missing columns added to goals and focus_sessions")
        print("\nYou can now run the app: python run_app.py")

        return True

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
