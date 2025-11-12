"""
Complete diagnostic script - checks everything
"""
import sys
import os
from pathlib import Path
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python():
    print_header("PYTHON INSTALLATION")
    print(f"Version: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Platform: {sys.platform}")

def check_directory_structure():
    print_header("DIRECTORY STRUCTURE")
    required_dirs = [
        'src', 'src/core', 'src/features', 'src/ui', 'src/views',
        'database', 'config', 'logs', 'temp'
    ]

    for dir_path in required_dirs:
        p = Path(dir_path)
        status = "✓" if p.exists() else "✗"
        print(f"{status} {dir_path}")

def check_critical_files():
    print_header("CRITICAL FILES")
    critical_files = [
        'src/main.py',
        'src/main_window.py',
        'src/core/database.py',
        'src/core/ai_router.py',
        'src/views/analytics_dashboard_view.py',
        'database/schema.sql',
        'requirements.txt',
    ]

    for file_path in critical_files:
        p = Path(file_path)
        if p.exists():
            size = p.stat().st_size
            print(f"✓ {file_path} ({size:,} bytes)")
        else:
            print(f"✗ {file_path} MISSING")

def check_encoding_issues():
    print_header("ENCODING CHECK")

    views_dir = Path('src/views')
    if not views_dir.exists():
        print("✗ Views directory not found")
        return

    for py_file in views_dir.glob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✓ {py_file.name}")
        except UnicodeDecodeError as e:
            print(f"✗ {py_file.name} - Encoding error at byte {e.start}")

def check_dependencies():
    print_header("PYTHON DEPENDENCIES")

    required_packages = [
        'PyQt6',
        'sqlalchemy',
        'cryptography',
        'google-generativeai',
        'groq',
        'openai',
        'spacy',
        'PyPDF2',
    ]

    for package in required_packages:
        try:
            __import__(package.replace('-', '_').lower())
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")

def check_spacy_model():
    print_header("SPACY MODEL")
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print(f"✓ en_core_web_sm loaded successfully")
            print(f"  Pipeline: {nlp.pipe_names}")
        except OSError:
            print("✗ en_core_web_sm NOT INSTALLED")
            print("  Run: python -m spacy download en_core_web_sm")
    except ImportError:
        print("✗ spaCy not installed")

def check_database():
    print_header("DATABASE")

    db_path = Path('database/acc_main.db')
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"✓ Database exists ({size:,} bytes)")

        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✓ Tables found: {len(tables)}")
            for table in tables[:5]:
                print(f"  - {table[0]}")
            if len(tables) > 5:
                print(f"  ... and {len(tables)-5} more")
            conn.close()
        except Exception as e:
            print(f"✗ Database error: {e}")
    else:
        print("✗ Database not found")

def check_encryption():
    print_header("ENCRYPTION")

    key_path = Path('config/encryption.key')
    if key_path.exists():
        size = key_path.stat().st_size
        print(f"✓ Encryption key exists ({size} bytes)")
    else:
        print("✗ Encryption key not found")

def main():
    print("="*60)
    print("  ACADEMIC COMMAND CENTER - DIAGNOSTIC TOOL")
    print("="*60)
    print(f"Current Directory: {os.getcwd()}")

    check_python()
    check_directory_structure()
    check_critical_files()
    check_encoding_issues()
    check_dependencies()
    check_spacy_model()
    check_database()
    check_encryption()

    print("\n" + "="*60)
    print("  DIAGNOSIS COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. If any ✗ marks above, fix those issues first")
    print("2. Run: python run_app.py")
    print("3. Check logs/errors.log if app crashes")

if __name__ == "__main__":
    main()
