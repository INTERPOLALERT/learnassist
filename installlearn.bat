@echo off
REM ============================================
REM Academic Command Center - Windows Installer
REM ============================================

echo.
echo ================================================
echo   ACADEMIC COMMAND CENTER - INSTALLATION
echo ================================================
echo.

REM Set installation directory
set INSTALL_DIR=C:\Users\Gamer\Getitdone

echo [1/10] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.11 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

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
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

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
echo.

echo [5/10] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

echo [6/10] Installing Python dependencies...
echo This may take 5-10 minutes, please wait...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo.
    echo Try running manually: pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo [7/10] Downloading spaCy language model...
python -m spacy download en_core_web_sm --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Failed to download spaCy model (optional)
    echo You can download it later with: python -m spacy download en_core_web_sm
)
echo [OK] spaCy model downloaded
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
