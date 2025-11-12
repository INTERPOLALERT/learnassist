"""
Fix all common issues automatically
"""
import sys
import os
import subprocess
from pathlib import Path

def fix_spacy():
    """Install spaCy model"""
    print("\n[FIXING] Installing spaCy model...")
    try:
        subprocess.run([
            sys.executable, "-m", "spacy", "download", "en_core_web_sm"
        ], check=True)
        print("✓ spaCy model installed")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install spaCy model")
        return False

def fix_missing_dirs():
    """Create missing directories"""
    print("\n[FIXING] Creating missing directories...")
    dirs = ['logs', 'temp', 'temp/uploads', 'database/backups', 'config']

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print("✓ Directories created")

def fix_database():
    """Initialize database if missing"""
    print("\n[FIXING] Checking database...")

    db_path = Path('database/acc_main.db')
    if not db_path.exists():
        print("Creating database...")
        try:
            sys.path.insert(0, 'src')
            from core.database import DatabaseManager
            db = DatabaseManager()
            print("✓ Database created")
        except Exception as e:
            print(f"✗ Database creation failed: {e}")
            return False
    else:
        print("✓ Database exists")

    return True

def fix_encryption():
    """Initialize encryption if missing"""
    print("\n[FIXING] Checking encryption...")

    key_path = Path('config/encryption.key')
    if not key_path.exists():
        print("Creating encryption key...")
        try:
            sys.path.insert(0, 'src')
            from core.encryption import EncryptionService
            enc = EncryptionService()
            print("✓ Encryption key created")
        except Exception as e:
            print(f"✗ Encryption creation failed: {e}")
            return False
    else:
        print("✓ Encryption key exists")

    return True

def main():
    print("="*60)
    print("  FIX EVERYTHING - AUTO REPAIR")
    print("="*60)

    fixes = [
        ("Missing Directories", fix_missing_dirs),
        ("Database", fix_database),
        ("Encryption", fix_encryption),
        ("spaCy Model", fix_spacy),
    ]

    for name, fix_func in fixes:
        try:
            fix_func()
        except Exception as e:
            print(f"✗ {name} fix failed: {e}")

    print("\n" + "="*60)
    print("  REPAIRS COMPLETE")
    print("="*60)
    print("\nRun: python run_app.py")

if __name__ == "__main__":
    main()
