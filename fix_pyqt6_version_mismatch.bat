@echo off
REM ============================================
REM Fix PyQt6 Version Mismatch - Quick Fix
REM ============================================

echo.
echo ================================================
echo   FIXING PYQT6 VERSION MISMATCH
echo ================================================
echo.

set INSTALL_DIR=C:\Users\Gamer\Getitdone

cd /d "%INSTALL_DIR%"

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Problem detected: PyQt6 6.6.1 is incompatible with PyQt6-Qt6 6.10.0
echo.
echo Fixing by upgrading PyQt6 to match Qt bindings...
echo.

pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip PyQt6-WebEngine PyQt6-Charts -y

echo.
echo Installing latest compatible PyQt6 versions...
pip install --no-cache-dir PyQt6==6.7.0 PyQt6-WebEngine==6.7.0 PyQt6-Charts==6.7.0

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install PyQt6
    pause
    exit /b 1
)

echo.
echo Testing PyQt6 import...
python -c "import PyQt6.QtCore; print('SUCCESS! PyQt6 version:', PyQt6.QtCore.PYQT_VERSION_STR)"

if errorlevel 1 (
    echo.
    echo [ERROR] PyQt6 still has issues
    pause
    exit /b 1
)

echo.
echo ================================================
echo   FIX COMPLETE!
echo ================================================
echo.
echo PyQt6 is now working correctly.
echo You can run startlearn.bat to start the application!
echo.
pause
