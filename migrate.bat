@echo off
echo ================================================
echo   DATABASE MIGRATION
echo ================================================
echo.

venv\Scripts\activate
python run_migration.py
pause
