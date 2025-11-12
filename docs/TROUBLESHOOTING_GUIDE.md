# TROUBLESHOOTING GUIDE - Academic Command Center

**Version**: 1.0.0
**Last Updated**: November 12, 2025

---

## TABLE OF CONTENTS

1. [Installation Issues](#installation-issues)
2. [Application Won't Start](#application-wont-start)
3. [Database Errors](#database-errors)
4. [API Issues](#api-issues)
5. [UI Problems](#ui-problems)
6. [Performance Issues](#performance-issues)
7. [Feature-Specific Issues](#feature-specific-issues)
8. [Data Recovery](#data-recovery)

---

## INSTALLATION ISSUES

### Python Not Found

**Error**: `'python' is not recognized as an internal or external command`

**Cause**: Python not installed or not in PATH

**Solution**:
1. Download Python 3.11+ from https://www.python.org/downloads/
2. Run installer
3. ✅ **CHECK "Add Python to PATH"** (important!)
4. Complete installation
5. Open new Command Prompt
6. Test: `python --version`
7. Re-run `installlearn.bat`

**Alternative**: Use `py` instead of `python` on Windows

---

### Wrong Python Version

**Error**: `Python 3.11 or later is required! You have Python 3.9`

**Solution**:
1. Uninstall old Python
2. Install Python 3.11+ from python.org
3. Re-run `installlearn.bat`

**Check version**: `python --version`

---

### pip Install Fails

**Error**: `Failed to install dependencies`

**Solutions**:

**1. Upgrade pip**:
```batch
python -m pip install --upgrade pip
```

**2. Install manually**:
```batch
cd C:\Users\Gamer\Getitdone
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Check internet connection**

**4. Try without --quiet**:
```batch
pip install -r requirements.txt
```
(Shows detailed error messages)

**5. Install problematic package separately**:
```batch
pip install PyQt6
pip install -r requirements.txt
```

---

### Virtual Environment Failed

**Error**: `Failed to create virtual environment`

**Solutions**:

**1. Ensure venv module installed**:
```batch
python -m pip install virtualenv
```

**2. Create manually**:
```batch
cd C:\Users\Gamer\Getitdone
python -m venv venv
```

**3. Use virtualenv instead**:
```batch
pip install virtualenv
virtualenv venv
```

---

### Permission Denied

**Error**: `Access is denied` or `Permission denied`

**Solutions**:

**1. Run as Administrator**:
- Right-click `installlearn.bat`
- Select "Run as administrator"

**2. Check antivirus**: Temporarily disable during installation

**3. Choose different directory**: Change INSTALL_DIR in script

---

### Database Initialization Failed

**Error**: `Database initialization failed`

**Solutions**:

**1. Check permissions**: Ensure write access to `database/` folder

**2. Delete existing database**:
```batch
del database\acc_main.db
```
Then re-run installer

**3. Check schema.sql exists**:
```batch
dir database\schema.sql
```

**4. Apply schema manually**:
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); schema = open('database/schema.sql', 'r').read(); conn.executescript(schema); conn.close()"
```

---

## APPLICATION WON'T START

### Virtual Environment Not Found

**Error**: `Virtual environment not found!`

**Cause**: Installation incomplete or venv deleted

**Solution**:
1. Re-run `installlearn.bat`
2. Wait for complete installation
3. Check `venv/` folder exists

---

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'PyQt6'`

**Cause**: Dependencies not installed

**Solution**:
```batch
cd C:\Users\Gamer\Getitdone
venv\Scripts\activate
pip install -r requirements.txt
```

---

### Application Crashes on Launch

**Check logs**:
```batch
type logs\app.log
```

**Common causes**:
1. Database corruption
2. Missing config files
3. Port already in use
4. Graphics driver issues (PyQt6)

**Solutions**:

**1. Check database**:
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); print('Database OK')"
```

**2. Recreate encryption key**:
```batch
python -c "from src.core.encryption import EncryptionService; enc = EncryptionService()"
```

**3. Update graphics drivers**: For PyQt6 rendering

**4. Check Python path**:
```batch
python -c "import sys; print(sys.path)"
```

---

### Black/Blank Window

**Symptom**: Application opens but window is black/empty

**Cause**: PyQt6 rendering issue

**Solutions**:

**1. Update graphics drivers**

**2. Try software rendering**:
```batch
set QT_OPENGL=software
python src\main.py
```

**3. Reinstall PyQt6**:
```batch
pip uninstall PyQt6
pip install PyQt6
```

**4. Check display scaling**: Set to 100% in Windows Settings

---

## DATABASE ERRORS

### Database Locked

**Error**: `database is locked`

**Cause**: Multiple application instances or crashed process

**Solutions**:

**1. Close all instances**:
- Check Task Manager for python.exe
- Kill all python processes

**2. Delete lock files**:
```batch
del database\acc_main.db-wal
del database\acc_main.db-shm
```

**3. Wait 30 seconds**: SQLite timeout

**4. Restart computer**: Last resort

---

### Database Corrupted

**Error**: `database disk image is malformed`

**Cause**: Power loss, crash, or disk error

**Solutions**:

**1. Restore from backup**:
```batch
copy database\backups\acc_main_YYYY-MM-DD.db database\acc_main.db
```

**2. Try recovery**:
```batch
sqlite3 database\acc_main.db ".recover" > recovered.sql
sqlite3 database\acc_main_new.db < recovered.sql
```

**3. Last resort - recreate**: (loses all data)
```batch
del database\acc_main.db
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); schema = open('database/schema.sql').read(); conn.executescript(schema); conn.close()"
```

---

### Foreign Key Constraint Failed

**Error**: `FOREIGN KEY constraint failed`

**Cause**: Data integrity issue

**Solutions**:

**1. Check data**:
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); cursor = conn.cursor(); cursor.execute('PRAGMA foreign_key_check'); print(cursor.fetchall())"
```

**2. Disable foreign keys temporarily** (not recommended)

**3. Fix data manually**: Ensure referenced records exist

---

## API ISSUES

### API Key Verification Fails

See API_SETUP_GUIDE.md for detailed solutions

**Quick checks**:
1. Internet connection working?
2. Key copied correctly?
3. Key hasn't expired?
4. Provider service up? (check status page)

---

### Rate Limit Exceeded

**Error**: `429 Too Many Requests` or `Rate limit exceeded`

**Solutions**:
1. Wait 60 seconds
2. Reduce request frequency
3. Upgrade to paid tier (higher limits)

**Rate limits**:
- Gemini: 60 req/min (free)
- Groq: 30 req/min (free)
- DeepSeek: 60 req/min (free)

---

### API Timeout

**Error**: `Request timeout` or `Connection timeout`

**Solutions**:
1. Check internet connection
2. Try again (may be temporary)
3. Check provider status page
4. Increase timeout in settings (if available)

---

### Insufficient Credits

**Error**: `Insufficient credits` (OpenRouter, DeepSeek)

**Solutions**:
1. Add credits to account
2. Check spending limits
3. Use free-tier providers instead

---

## UI PROBLEMS

### Window Won't Resize

**Solution**:
1. Close application
2. Delete window settings (if exists)
3. Relaunch

---

### Text Too Small/Large

**Solution**:
1. Windows Settings → Display
2. Set scaling to 100%
3. Restart application

---

### Buttons Not Responding

**Solutions**:
1. Check if modal dialog open (behind window)
2. Restart application
3. Check logs for errors

---

### Charts Not Displaying

**Symptom**: Analytics charts show blank/empty

**Solutions**:
1. Check data exists (complete some tasks first)
2. Refresh view (switch away and back)
3. Check matplotlib installed:
```batch
pip install matplotlib
```

---

## PERFORMANCE ISSUES

### Slow Startup

**Causes**:
1. Large database (1000+ records)
2. Many API keys to decrypt
3. Disk I/O issues

**Solutions**:
1. Archive old essays/tasks
2. Store database on SSD
3. Defragment database:
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); conn.execute('VACUUM'); conn.close()"
```

---

### UI Lag/Freezing

**Causes**:
1. Long-running AI operations
2. Large text processing
3. Too many records displayed

**Solutions**:
1. Process smaller chunks of text
2. Paginate large lists
3. Clear completed items
4. Close unused views

---

### High Memory Usage

**Normal usage**: 200-500 MB

**High usage** (1+ GB):
1. Memory leak (restart app)
2. Very large essays/materials
3. Many open views

**Solutions**:
1. Restart application
2. Process smaller sections
3. Close unused views
4. Upgrade RAM

---

## FEATURE-SPECIFIC ISSUES

### Focus Mode Timer Not Counting

**Solutions**:
1. Click into window (ensure app has focus)
2. Check if timer paused
3. Refresh view (switch away and back)
4. Restart application

---

### Grammar Check Finds No Errors

**Possible reasons**:
1. Text actually has no detectable errors
2. Grammar checker needs tuning
3. Text too short (minimum length)

**Test**: Try with intentional errors

---

### Citations Not Formatting Correctly

**Check**:
1. All required fields filled (Author, Year, Title)
2. Source type selected correctly
3. Citation style selected

**Solution**: Re-enter source with correct fields

---

### Canvas Sync Not Working

**See API_SETUP_GUIDE.md** for Canvas troubleshooting

**Quick checks**:
1. Canvas URL correct?
2. Access token valid?
3. Token permissions sufficient?
4. Canvas service up?

---

### Snapshots Not Creating

**Check**:
1. Essay exists and has content
2. Disk space available
3. Database not locked

**Test**:
```batch
python -c "from src.features.version_control.snapshot_manager import SnapshotManager; mgr = SnapshotManager('test'); print('OK')"
```

---

## DATA RECOVERY

### Lost Encryption Key

**Problem**: `config/encryption.key` deleted or corrupted

**Impact**: Cannot decrypt API keys (UNRECOVERABLE)

**Solution**:
1. Generate new encryption key (automatic on restart)
2. Re-enter all API keys in Settings
3. **Prevention**: Backup encryption.key regularly!

---

### Database Deleted

**Problem**: `acc_main.db` accidentally deleted

**Solutions**:

**1. Restore from backup**:
```batch
copy database\backups\acc_main_YYYY-MM-DD.db database\acc_main.db
```

**2. Check Recycle Bin**

**3. Use file recovery tool** (if recent deletion)

**4. Recreate** (loses all data):
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); schema = open('database/schema.sql').read(); conn.executescript(schema); conn.close()"
```

---

### Backup Database

**Manual backup**:
```batch
copy database\acc_main.db database\backups\acc_main_%date:~-4,4%-%date:~-10,2%-%date:~-7,2%.db
```

**Automated backups**: ACC creates daily backups automatically

**Backup locations**:
- `database/backups/` (automatic)
- External drive (manual)
- Cloud storage (manual)

---

### Export All Data

**Essays to text files**:
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); essays = conn.execute('SELECT title, content FROM essays').fetchall(); [open(f'{e[0]}.txt', 'w').write(e[1]) for e in essays]"
```

**Database to SQL**:
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); [print(line) for line in conn.iterdump()]" > backup.sql
```

---

## LOGGING AND DIAGNOSTICS

### Check Application Logs

**Location**: `logs/app.log`

**View**:
```batch
type logs\app.log
```

**Last 50 lines**:
```batch
powershell Get-Content logs\app.log -Tail 50
```

**Search for errors**:
```batch
findstr /i "error" logs\app.log
```

---

### Enable Debug Logging

**Edit `src/main.py`**:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    ...
)
```

---

### Check System Info

```batch
python -c "import sys; import platform; print(f'Python: {sys.version}'); print(f'Platform: {platform.platform()}')"
```

---

### Test Database Connection

```batch
python -c "from src.core.database import DatabaseManager; db = DatabaseManager(); print(f'Tables: {len(db.execute_query(\"SELECT name FROM sqlite_master WHERE type='table'\", fetch_all=True))}')"
```

---

### Test AI Router

```batch
python -c "from src.core.ai_router import AIRouter; router = AIRouter(); print('AI Router OK')"
```

---

## GETTING MORE HELP

### Before Asking for Help

1. ✅ Check this guide
2. ✅ Check logs (`logs/app.log`)
3. ✅ Try basic troubleshooting
4. ✅ Search error message online

### When Asking for Help, Include:

1. **Error message** (exact text)
2. **Steps to reproduce**
3. **Relevant log entries**
4. **System info**:
   - Windows version
   - Python version
   - ACC version
5. **What you've tried**

### Contact Support

**Email**: support@academiccommandcenter.com

**GitHub Issues**: [repository URL]

**Include**:
- Description
- Error message
- Log file (attach logs/app.log)
- Screenshots (if UI issue)

---

## PREVENTIVE MAINTENANCE

### Regular Backups

✅ Backup weekly:
- `database/acc_main.db`
- `config/encryption.key`

✅ Store backups:
- External drive
- Cloud storage (encrypted)

---

### Keep Updated

✅ Update Python packages:
```batch
venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

✅ Check for ACC updates (if available)

---

### Database Maintenance

✅ Monthly cleanup:
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); conn.execute('VACUUM'); conn.close()"
```

✅ Delete old temporary files:
```batch
del /q temp\*
```

---

### Monitor Disk Space

- Database grows with usage
- Ensure 1+ GB free space
- Move old backups to external storage

---

**Stay productive with ACC!** 💪

