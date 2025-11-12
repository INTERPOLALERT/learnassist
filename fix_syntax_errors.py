"""
Fix common syntax errors in Python files
"""
import re
from pathlib import Path

def fix_unterminated_strings(filepath):
    """Fix unterminated string literals"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified = False
        fixed_lines = []

        for i, line in enumerate(lines, 1):
            original_line = line

            # Fix: f"" {var}" -> f"{var}"
            if 'f""' in line and '")' in line:
                line = re.sub(r'f""\s*{', 'f"{', line)
                if line != original_line:
                    print(f"  Line {i}: Fixed f-string")
                    modified = True

            # Fix: f'' {var}' -> f'{var}'
            if "f''" in line and "')" in line:
                line = re.sub(r"f''\s*{", "f'{", line)
                if line != original_line:
                    print(f"  Line {i}: Fixed f-string")
                    modified = True

            # Fix: " {var}" at start of f-string
            line = re.sub(r'f"\s*"\s*{', 'f"{', line)

            # Fix: ' {var}' at start of f-string
            line = re.sub(r"f'\s*'\s*{", "f'{", line)

            if line != original_line:
                modified = True

            fixed_lines.append(line)

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            return True

        return False

    except Exception as e:
        print(f"  Error: {e}")
        return False

def fix_specific_file():
    """Fix the known problem file"""
    filepath = Path('src/views/progress_reports_view.py')

    if not filepath.exists():
        print(f"✗ File not found: {filepath}")
        return False

    print(f"Fixing: {filepath}")

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the specific error: f"" {insight}" -> f"{insight}"
    original = content

    # Pattern 1: f"" {var}"
    content = re.sub(r'f""\s*{([^}]+)}"\)', r'f"{\1}")', content)

    # Pattern 2: lines.append(f"" {insight}")
    content = re.sub(r'lines\.append\(f""\s*{([^}]+)}"\)', r'lines.append(f"{\1}")', content)

    # General fix: any f"" { pattern
    content = re.sub(r'f""\s*{', 'f"{', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Fixed syntax errors")
        return True
    else:
        print("⚠ No changes needed")
        return False

def scan_all_files():
    """Scan all Python files for similar issues"""
    print("\nScanning all Python files for syntax issues...")

    fixed_count = 0
    for py_file in Path('src').rglob('*.py'):
        if fix_unterminated_strings(py_file):
            print(f"✓ Fixed: {py_file}")
            fixed_count += 1

    if fixed_count == 0:
        print("✓ No syntax issues found in other files")
    else:
        print(f"\n✓ Fixed {fixed_count} files")

def validate_syntax(filepath):
    """Check if file has valid Python syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, filepath, 'exec')
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in {filepath}:")
        print(f"  Line {e.lineno}: {e.msg}")
        if e.text:
            print(f"  {e.text.strip()}")
        return False

def main():
    print("="*60)
    print("  FIX SYNTAX ERRORS")
    print("="*60)

    # Fix the specific problem file
    print("\n[1/3] Fixing progress_reports_view.py...")
    fix_specific_file()

    # Scan for other issues
    print("\n[2/3] Scanning for similar issues...")
    scan_all_files()

    # Validate the fix
    print("\n[3/3] Validating fix...")
    filepath = Path('src/views/progress_reports_view.py')
    if validate_syntax(filepath):
        print(f"✓ {filepath} syntax is now valid")
    else:
        print(f"✗ {filepath} still has syntax errors")
        print("\nManual fix needed at line 589:")
        print("  Change: lines.append(f\"\" {insight}\")")
        print("  To:     lines.append(f\"{insight}\")")

    print("\n" + "="*60)
    print("  DONE")
    print("="*60)
    print("\nNow run: python run_app.py")

if __name__ == "__main__":
    main()
