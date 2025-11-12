@echo off
REM ============================================
REM Fix PyQt6 DLL Error - Quick Fix Script
REM ============================================

echo.
echo ================================================
echo   FIXING PYQT6 DLL ERROR
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
echo Uninstalling current PyQt6...
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip -y

echo.
echo Installing PyQt6 6.6.1 (stable version)...
pip install PyQt6==6.6.1

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install PyQt6
    echo.
    echo You may need to install Microsoft Visual C++ Redistributable:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   FIX COMPLETE!
echo ================================================
echo.
echo Testing PyQt6 import...
python -c "import PyQt6.QtCore; print('SUCCESS: PyQt6 version:', PyQt6.QtCore.PYQT_VERSION_STR)"

if errorlevel 1 (
    echo.
    echo [ERROR] PyQt6 still has issues
    echo.
    echo Please install Microsoft Visual C++ Redistributable:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

echo.
echo You can now run startlearn.bat to start the application!
echo.
pause
