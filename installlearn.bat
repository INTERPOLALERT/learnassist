@echo off
REM ============================================
REM Academic Command Center - Windows Installer
REM ============================================

echo.
echo ================================================
echo   ACADEMIC COMMAND CENTER - INSTALLATION
echo ================================================
echo.
echo Script location: %~dp0
echo.

REM Set installation directory
set INSTALL_DIR=C:\Users\Gamer\Getitdone
echo Installation target: %INSTALL_DIR%
echo.

echo [1/10] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.11 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
python --version
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check if Python 3.11+
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11 or later is required!
    echo You have Python %PYTHON_VERSION%
    pause
    exit /b 1
)

echo [OK] Python version is compatible
echo.

echo [2/10] Creating directory structure...
if not exist "%INSTALL_DIR%" (
    echo Creating installation directory: %INSTALL_DIR%
    mkdir "%INSTALL_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create installation directory!
        echo Please check permissions or create manually.
        pause
        exit /b 1
    )
)
echo Changing to installation directory: %INSTALL_DIR%
cd /d "%INSTALL_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to change to installation directory!
    echo Directory: %INSTALL_DIR%
    pause
    exit /b 1
)
echo Current directory: %CD%
echo.

REM Create all necessary directories
mkdir config 2>nul
mkdir database 2>nul
mkdir database\backups 2>nul
mkdir database\migrations 2>nul
mkdir logs 2>nul
mkdir temp 2>nul
mkdir temp\uploads 2>nul
mkdir resources 2>nul
mkdir resources\icons 2>nul
mkdir resources\images 2>nul
mkdir builds 2>nul
mkdir builds\audit_reports 2>nul

echo [OK] Directories created
echo.

echo [2.5/10] Copying application files...
set SCRIPT_DIR=%~dp0
echo Copying from: %SCRIPT_DIR%
echo Copying to: %INSTALL_DIR%

REM Copy source code
if exist "%SCRIPT_DIR%src" (
    echo Copying src folder...
    xcopy "%SCRIPT_DIR%src" "%INSTALL_DIR%\src\" /E /I /Y /Q
    if errorlevel 1 (
        echo [ERROR] Failed to copy src folder
        pause
        exit /b 1
    )
) else (
    echo [WARNING] src folder not found in script directory
)

REM Copy requirements.txt
if exist "%SCRIPT_DIR%requirements.txt" (
    echo Copying requirements.txt...
    copy "%SCRIPT_DIR%requirements.txt" "%INSTALL_DIR%\requirements.txt" >nul
)

REM Copy config files if they exist
if exist "%SCRIPT_DIR%config" (
    echo Copying config folder...
    xcopy "%SCRIPT_DIR%config" "%INSTALL_DIR%\config\" /E /I /Y /Q
)

REM Copy database schema
if exist "%SCRIPT_DIR%database\schema.sql" (
    echo Copying database schema...
    copy "%SCRIPT_DIR%database\schema.sql" "%INSTALL_DIR%\database\schema.sql" >nul
)

echo [OK] Application files copied
echo.

echo [3/10] Creating Python virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

echo [4/10] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo Checking Python location:
where python
echo.

echo [5/10] Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [WARNING] pip upgrade failed, but continuing...
    echo This is usually not critical.
) else (
    echo [OK] pip upgraded
)
echo.

echo [6/10] Checking Python dependencies...
REM Check if key packages are already installed
python -c "import PyQt6; import groq; import google.generativeai" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Dependencies already installed, skipping...
    goto :skip_deps
)

echo Installing dependencies (this may take 5-10 minutes)...

REM Try to install from requirements.txt in the current directory (already copied)
if exist "requirements.txt" (
    echo Found requirements.txt, installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo.
        echo Try running manually: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
    goto :skip_deps
)

echo [WARNING] requirements.txt not found
echo Attempting to install core packages directly...
pip install PyQt6 groq google-generativeai anthropic cohere python-docx reportlab cryptography requests canvasapi spacy
if errorlevel 1 (
    echo [ERROR] Failed to install core packages
    pause
    exit /b 1
)
echo [OK] Core dependencies installed

:skip_deps
echo.

echo [7/10] Downloading spaCy language model...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo [WARNING] Failed to download spaCy model (optional)
    echo You can download it later with: python -m spacy download en_core_web_sm
) else (
    echo [OK] spaCy model downloaded
)
echo.

echo [8/10] Installing Tesseract OCR...
REM Check if Tesseract is already installed
where tesseract >nul 2>&1
if %errorlevel% equ 0 (
    echo Tesseract already installed, skipping...
) else (
    echo Tesseract not found. You need to install it manually.
    echo.
    echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Install to: C:\Program Files\Tesseract-OCR\
    echo.
    echo Press any key to continue installation (you can install Tesseract later)...
    pause >nul
)
echo.

echo [9/10] Initializing database...
python -c "from src.core.database import DatabaseManager; db = DatabaseManager(); print('Database initialized successfully!')"
if %errorlevel% neq 0 (
    echo [ERROR] Database initialization failed
    pause
    exit /b 1
)
echo [OK] Database initialized

echo [9.5/10] Applying database schema...
python -c "import sqlite3; conn = sqlite3.connect('database/acc_main.db'); schema = open('database/schema.sql', 'r').read(); conn.executescript(schema); conn.commit(); conn.close(); print('Schema applied successfully!')"
if %errorlevel% neq 0 (
    echo [ERROR] Database schema application failed
    pause
    exit /b 1
)
echo [OK] Database schema applied (21 tables created)
echo.

echo [10/10] Creating encryption keys...
python -c "from src.core.encryption import EncryptionService; enc = EncryptionService(); enc.verify_master_key()"
if %errorlevel% neq 0 (
    echo [ERROR] Encryption setup failed
    pause
    exit /b 1
)
echo [OK] Encryption keys created
echo.

echo ================================================
echo   INSTALLATION COMPLETE!
echo ================================================
echo.
echo Academic Command Center has been installed to:
echo %INSTALL_DIR%
echo.
echo IMPORTANT SECURITY NOTICE:
echo - Your master encryption key is stored in: config\encryption.key
echo - BACKUP THIS FILE! If lost, encrypted API keys cannot be recovered.
echo - Do NOT share this file with anyone.
echo.
echo To start the application:
echo 1. Double-click startlearn.bat
echo 2. Or run: python src\main.py
echo.
echo First-time setup:
echo 1. Go to Settings ^> API Keys
echo 2. Add your AI API keys (Gemini, Groq, etc.)
echo 3. Optionally add your Canvas LMS token
echo.
echo Need help? See README.md for detailed instructions.
echo.
pause
