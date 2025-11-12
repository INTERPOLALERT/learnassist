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
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Verify PyQt6 installation
echo Checking PyQt6 installation...
python -c "import PyQt6.QtCore; print('PyQt6 version:', PyQt6.QtCore.PYQT_VERSION_STR)" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ================================================
    echo   FIXING PYQT6 DLL ERROR
    echo ================================================
    echo.
    echo PyQt6 DLL error detected. This usually means:
    echo 1. Missing Microsoft Visual C++ Redistributable
    echo 2. Corrupted PyQt6 installation
    echo.
    echo Attempting to fix by reinstalling PyQt6...
    echo.
    pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip -y
    pip install PyQt6==6.6.1
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to reinstall PyQt6
        echo.
        echo Please install Microsoft Visual C++ Redistributable:
        echo https://aka.ms/vs/17/release/vc_redist.x64.exe
        echo.
        echo Then run this script again.
        pause
        exit /b 1
    )
    echo.
    echo [OK] PyQt6 reinstalled successfully
    echo.
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

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

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
