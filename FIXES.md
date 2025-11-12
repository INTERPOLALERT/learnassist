# Academic Command Center - Fixes Guide

This document lists all identified issues and their fixes after first launch.

## 🔧 Problem Summary

After installing and launching the app, the following issues were identified:

1. ❌ Missing Python dependency: `google-generativeai`
2. ❌ Database schema mismatch - missing tables
3. ❌ Database schema mismatch - missing columns
4. ❌ Missing view imports (caused by #1)
5. ⚠️ Missing placeholder views (expected behavior)

---

## ✅ Fix #1: Install Missing Dependency

**Problem:**
```
WARNING:root:Some views not yet imported: No module named 'google.generativeai'
```

**Cause:** The `google-generativeai` package is in `requirements.txt` but wasn't installed in your virtual environment.

**Fix:**
```batch
cd C:\Users\Gamer\Getitdone
call venv\Scripts\activate
pip install google-generativeai==0.3.2
```

**Verify:**
```batch
python -c "import google.generativeai; print('✓ google-generativeai installed')"
```

---

## ✅ Fix #2: Update Database Schema

**Problem:**
```
ERROR:core.database:Query execution failed: no such table: assignments
ERROR:core.database:Query execution failed: no such table: achievements
ERROR:core.database:Query execution failed: no such table: subjects
ERROR:core.database:Query execution failed: no such column: subject
ERROR:core.database:Query execution failed: no such column: target_date
ERROR:core.database:Query execution failed: table goals has no column named category
```

**Cause:** The database schema (created during installation) is missing several tables and columns that the application code expects.

**Missing Tables:**
- `assignments` (code expects this, but schema only has `tasks`)
- `achievements`
- `subjects`

**Missing Columns:**
- `focus_sessions.subject`
- `goals.target_date`
- `goals.category`
- `goals.unit`
- `goals.start_date`
- `goals.is_smart`

**Fix:**

Run the database migration script:

```batch
cd C:\Users\Gamer\Getitdone
migrate.bat
```

Or manually:
```batch
cd C:\Users\Gamer\Getitdone
call venv\Scripts\activate
python run_migration.py
```

**What the migration does:**
1. Creates `assignments` table with full schema
2. Creates `subjects` table for organizing courses
3. Creates `achievements` table with 5 default achievements
4. Adds `subject` column to `focus_sessions`
5. Adds `category`, `target_date`, `unit`, `start_date`, `is_smart` columns to `goals`
6. Seeds default achievements including "First Steps" (unlocked)
7. Migrates existing `goals.deadline` to `goals.target_date`

**Verify:**
```batch
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); cursor = conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name IN ('assignments', 'subjects', 'achievements')\"); print('✓ Tables:', [r[0] for r in cursor.fetchall()])"
```

---

## ✅ Fix #3: Missing View Imports (Auto-Fixed by Fix #1)

**Problem:**
```
ERROR:__main__:Failed to load views: name 'AISettingsView' is not defined
```

**Cause:** The `AISettingsView` import was failing because it depends on other modules that import `google.generativeai`. The import failure was silently caught and logged as a warning.

**Fix:** This is automatically fixed when you install `google-generativeai` (Fix #1).

**Verify:** After fixing #1 and restarting the app, you should see:
```
✓ Settings view loads without errors
✓ AI Settings panel accessible from sidebar
```

---

## ⚠️ Fix #4: Missing Placeholder Views (Expected Behavior)

**Problem:**
```
WARNING:__main__:View not found: Settings
WARNING:__main__:View not found: AI Tools
WARNING:__main__:View not found: Calendar
WARNING:__main__:View not found: Notes
WARNING:__main__:View not found: Study Timer
WARNING:__main__:View not found: Assignments
```

**Cause:** These views show placeholder pages with "Coming soon..." messages. This is expected behavior - the core views are implemented, but some secondary features are marked for future development.

**Status:**
- ✅ **Dashboard** - Fully functional
- ✅ **Progress Reports** - Fully functional
- ✅ **Goals** - Fully functional (after migration)
- ✅ **Achievements** - Fully functional (after migration)
- ✅ **Settings** - Fixed by installing google-generativeai
- ⚠️ **AI Tools** - Placeholder (planned feature)
- ⚠️ **Assignments** - Placeholder (can be implemented using assignments table)
- ⚠️ **Study Timer** - Placeholder (planned feature)
- ⚠️ **Notes** - Placeholder (planned feature)
- ⚠️ **Calendar** - Placeholder (planned feature)

**No fix needed** - These warnings are informational and don't affect core functionality.

---

## 🚀 Complete Fix Procedure

Run these commands in order:

```batch
# 1. Navigate to installation directory
cd C:\Users\Gamer\Getitdone

# 2. Activate virtual environment
call venv\Scripts\activate

# 3. Install missing dependency
pip install google-generativeai==0.3.2

# 4. Run database migration
python run_migration.py

# 5. Launch the app
python run_app.py
```

Or use the shortcuts:
```batch
cd C:\Users\Gamer\Getitdone
migrate.bat    # Runs database migration
start.bat      # Launches app with all checks
```

---

## 📊 After Fixes - Expected Behavior

After applying all fixes, you should see:

**✅ Clean Startup:**
```
✓ Database connected
✓ Encryption service ready
✓ API manager ready
✓ All services initialized successfully
```

**✅ Working Features:**
- Dashboard with performance metrics
- Progress Reports (last 7, 30, 90 days)
- Goals management (create, track, complete)
- Achievements system (5 default achievements)
- AI Settings panel

**⚠️ Expected Warnings (Normal):**
- "View not found" for placeholder views (AI Tools, Calendar, Notes, etc.)
- These are planned features, not bugs

**✅ No Errors:**
- No "no such table" errors
- No "no such column" errors
- No "module not found" errors

---

## 🔍 Troubleshooting

**If migration fails:**
```batch
# Check database exists
dir database\acc_main.db

# Backup database first
copy database\acc_main.db database\acc_main.db.backup

# Try migration again
python run_migration.py
```

**If google-generativeai won't install:**
```batch
# Upgrade pip first
python -m pip install --upgrade pip

# Try installing again
pip install google-generativeai==0.3.2

# Or try without version pin
pip install google-generativeai
```

**If app still has errors:**
```batch
# Run diagnostic
python diagnose.py

# Check logs
type logs\app.log
```

---

## 📝 Summary

| Issue | Severity | Fix | Status |
|-------|----------|-----|--------|
| Missing google-generativeai | High | `pip install google-generativeai==0.3.2` | ✅ Ready |
| Missing database tables | High | Run `migrate.bat` | ✅ Ready |
| Missing database columns | High | Run `migrate.bat` | ✅ Ready |
| AISettingsView import fail | Medium | Fixed by installing google-generativeai | ✅ Auto-fixed |
| Placeholder views | Low | Expected behavior | ℹ️ Normal |

**Total Critical Issues:** 3
**Total Fixes Required:** 2 (dependency install + migration)
**Estimated Fix Time:** 2-3 minutes

---

## 🎯 Quick Start After Fixes

```batch
# One-time setup
cd C:\Users\Gamer\Getitdone
call venv\Scripts\activate
pip install google-generativeai==0.3.2
python run_migration.py

# Daily use
cd C:\Users\Gamer\Getitdone
start.bat
```

That's it! Your Academic Command Center should now be fully functional. 🎉
