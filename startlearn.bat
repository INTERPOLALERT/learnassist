@echo off
REM ============================================
REM Academic Command Center - Application Launcher
REM ============================================

set INSTALL_DIR=C:\Users\Gamer\Getitdone

REM Change to installation directory
cd /d "%INSTALL_DIR%"

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run installlearn.bat first to set up the application.
    echo.
    pause
    exit /b 1
)

REM Check if database exists
if not exist database\acc_main.db (
    echo ERROR: Database not found!
    echo.
    echo Please run installlearn.bat first to set up the application.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Clear console
cls

REM Display banner
echo.
echo ================================================
echo   ACADEMIC COMMAND CENTER
echo ================================================
echo.
echo Starting application...
echo.

REM Run the application
python src\main.py

REM If application exits with error
if %errorlevel% neq 0 (
    echo.
    echo ================================================
    echo   APPLICATION ERROR
    echo ================================================
    echo.
    echo The application exited with an error.
    echo.
    echo Check logs\app.log for details.
    echo.
    pause
    exit /b 1
)

REM Normal exit
echo.
echo Application closed.
echo.
