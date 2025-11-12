"""
Complete App Launcher - Handles all checks and fixes automatically
"""
import sys
import os
import subprocess
from pathlib import Path

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_spacy():
    """Check and install spaCy model if needed"""
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✓ spaCy model installed")
            return True
        except OSError:
            print("⚠ spaCy model not found, installing...")
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
            print("✓ spaCy model installed")
            return True
    except ImportError:
        print("⚠ spaCy not installed, installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "spacy"], check=True)
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
        print("✓ spaCy installed")
        return True
    except Exception as e:
        print(f"✗ Error with spaCy: {e}")
        return False

def check_encoding():
    """Quick check for encoding and syntax issues"""
    problem_files = [
        'src/views/analytics_dashboard_view.py',
        'src/views/progress_reports_view.py',
        'src/main_window.py'
    ]

    for filepath in problem_files:
        p = Path(filepath)
        if not p.exists():
            continue

        try:
            # Check encoding
            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check syntax
            compile(content, str(p), 'exec')

        except UnicodeDecodeError:
            print(f"✗ Encoding error in {p.name}")
            return False
        except SyntaxError as e:
            print(f"✗ Syntax error in {p.name} line {e.lineno}")
            return False

    print("✓ File encodings and syntax OK")
    return True

def check_database():
    """Check database exists and is accessible"""
    db_path = Path('database/acc_main.db')
    if db_path.exists():
        print(f"✓ Database found ({db_path.stat().st_size // 1024} KB)")
        return True
    else:
        print("⚠ Database not found, will be created on first run")
        return True

def check_encryption():
    """Check encryption key exists"""
    key_path = Path('config/encryption.key')
    if key_path.exists():
        print("✓ Encryption key found")
        return True
    else:
        print("⚠ Encryption key not found, will be created on first run")
        return True

def run_app():
    """Launch the application"""
    print_section("STARTING APPLICATION")

    try:
        # Change to src directory and run
        sys.path.insert(0, str(Path('src').absolute()))

        # Import and run main
        from main import main
        main()

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()

        print("\n" + "="*60)
        print("TROUBLESHOOTING:")
        print("="*60)
        print("1. Check logs/errors.log for details")
        print("2. Ensure all API keys are configured")
        print("3. Try running: python src/main.py")
        print("4. Report this error with logs")
        return False

    return True

def main():
    """Main launcher"""
    print_section("ACADEMIC COMMAND CENTER - LAUNCHER")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Working Directory: {os.getcwd()}")

    print_section("PRE-FLIGHT CHECKS")

    checks = [
        ("Encoding", check_encoding),
        ("Database", check_database),
        ("Encryption", check_encryption),
        ("spaCy", check_spacy),
    ]

    all_passed = True
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"✗ {name} check failed: {e}")
            all_passed = False

    if not all_passed:
        print("\n⚠ Some checks failed but attempting to start anyway...")

    # Launch app
    run_app()

if __name__ == "__main__":
    main()
