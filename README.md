# Academic Command Center (ACC)

**Production-Ready Desktop Application for Windows 11**

A comprehensive Python desktop application that helps students manage academic essays from assignment to submission with AI-powered assistance, task management, and Canvas LMS integration.

---

## 📋 Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [Usage Guide](#usage-guide)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## ✨ Features

### Phase 1: Foundation (✅ COMPLETE)
- **Database System**: SQLite database with full schema, migrations, backups
- **Encryption Service**: AES-256-CBC encryption for API keys and sensitive data
- **AI Router**: Intelligent routing to multiple AI providers (Gemini, Groq, DeepSeek, Claude via OpenRouter, Cohere)
- **API Key Management**: Secure storage and management of API keys
- **Canvas Integration**: Sync assignments, files, and grades from Canvas LMS

### Phase 2: Core Features (🚧 COMING SOON)
- **Essay Parser**: AI-powered parsing of assignment instructions
- **Task Manager**: Automatic breakdown of essays into actionable subtasks
- **Materials Library**: Upload and organize lecture notes, readings, and resources
- **Writing Assistant**: Rich text editor with inline AI help
- **Focus System**: Pomodoro timer with distraction blocking
- **Analytics Dashboard**: Track progress and productivity patterns

### Phase 3-5: Advanced Features (📅 PLANNED)
- Full UI implementation
- Canvas two-way sync
- Grammar checking
- Citation management
- Grade prediction
- And much more...

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 11 (64-bit)
- **Python**: 3.11 or later
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **Internet**: Required for AI API calls

### Recommended
- **RAM**: 8 GB or more
- **Storage**: 5 GB free space
- **Display**: 1920x1080 or higher

---

## 📥 Installation

### Quick Install (Recommended)

1. **Download the repository** to your desired location

2. **Run the installer**:
   ```
   Double-click: installlearn.bat
   ```

3. **Wait for installation** (5-10 minutes):
   - Python dependencies will be installed
   - Database will be initialized
   - Encryption keys will be generated

4. **Done!** You'll see a success message when complete.

### Manual Installation

If the automated installer fails:

```batch
# Navigate to installation directory
cd C:\Users\Gamer\Getitdone

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from src.core.database import DatabaseManager; DatabaseManager()"

# Initialize encryption
python -c "from src.core.encryption import EncryptionService; EncryptionService()"
```

---

## 🚀 First-Time Setup

### 1. Launch the Application

```batch
Double-click: startlearn.bat
```

Or manually:
```batch
cd C:\Users\Gamer\Getitdone
venv\Scripts\activate
python src\main.py
```

### 2. Configure API Keys

The application uses various AI APIs. You need to add your API keys:

#### **Required APIs** (for core functionality):

**Google Gemini** (Essay parsing, analysis):
- Get key from: https://makersuite.google.com/app/apikey
- Free tier: 60 requests/minute
- Cost: ~$0.00025 per 1K tokens

**Groq** (Task generation):
- Get key from: https://console.groq.com/keys
- Free tier available
- Cost: ~$0.0001 per 1K tokens

#### **Optional APIs** (enhanced features):

**DeepSeek** (Grammar checking):
- Get key from: https://platform.deepseek.com/
- Cost: ~$0.00014 per 1K tokens

**OpenRouter** (Claude for complex reasoning):
- Get key from: https://openrouter.ai/keys
- Cost: ~$0.003 per 1K tokens

**Cohere** (Semantic search):
- Get key from: https://dashboard.cohere.com/api-keys
- Free tier available
- Cost: ~$0.0002 per 1K tokens

**Canvas LMS** (Assignment sync):
- Go to Canvas → Account → Settings → New Access Token
- Enter your institution's Canvas URL

#### **Adding Keys in App**:

1. Go to **Settings** → **API Keys**
2. For each provider:
   - Click **Add Key**
   - Paste your API key
   - Click **Save**
   - Click **Verify** to test

---

## 📖 Usage Guide

### Basic Workflow

1. **Import Assignment**
   - Paste instructions directly
   - Upload PDF/DOCX
   - Or sync from Canvas

2. **AI Parses Requirements**
   - Extracts word count, sources needed, etc.
   - Identifies key concepts
   - Decodes rubric into checklist

3. **Tasks Generated**
   - Specific research tasks
   - Writing tasks per section
   - Editing and citation tasks

4. **Work Through Tasks**
   - Start focus sessions
   - Get AI assistance while writing
   - Track progress

5. **Submit**
   - Validate against rubric
   - Format correctly
   - Submit to Canvas (or manually)

---

## 🏗️ Architecture

### Directory Structure
```
C:\Users\Gamer\Getitdone\
│
├── config\                  # Configuration files
│   └── encryption.key       # Master encryption key (BACKUP THIS!)
│
├── database\                # SQLite database
│   ├── acc_main.db         # Main database file
│   ├── schema.sql          # Database schema
│   └── backups\            # Automatic backups
│
├── src\                     # Source code
│   ├── core\               # Core services
│   │   ├── database.py     # Database manager
│   │   ├── encryption.py   # Encryption service
│   │   ├── ai_router.py    # AI request router
│   │   ├── api_manager.py  # API key manager
│   │   └── canvas_client.py # Canvas integration
│   │
│   ├── features\           # Feature modules
│   │   ├── essay_parser\
│   │   ├── task_manager\
│   │   ├── materials\
│   │   ├── writing\
│   │   ├── focus\
│   │   └── analytics\
│   │
│   └── ui\                 # User interface
│
├── logs\                   # Application logs
├── temp\                   # Temporary files
├── resources\              # Icons, images, etc.
│
├── installlearn.bat        # Installer
├── startlearn.bat          # Launcher
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Core Components

**Database Manager** (`src/core/database.py`)
- SQLite with WAL mode for concurrency
- Automatic backups
- Migration support
- Full-text search

**Encryption Service** (`src/core/encryption.py`)
- AES-256-CBC encryption
- Unique IV per encryption
- Master key protection

**AI Router** (`src/core/ai_router.py`)
- Request queueing (prevents simultaneous calls)
- Response caching
- Automatic fallback
- Cost tracking

**API Manager** (`src/core/api_manager.py`)
- Secure API key storage
- Provider enable/disable
- Usage tracking
- Key verification

**Canvas Client** (`src/core/canvas_client.py`)
- Assignment sync
- File downloads
- Rubric extraction
- Submission tracking

---

## 🔧 Troubleshooting

### Installation Issues

**Problem**: Python not found
```
Solution: Install Python 3.11+ from python.org
Make sure to check "Add Python to PATH"
```

**Problem**: pip install fails
```
Solution: Update pip first
python -m pip install --upgrade pip
Then retry: pip install -r requirements.txt
```

**Problem**: Permission denied
```
Solution: Run Command Prompt as Administrator
```

### Runtime Issues

**Problem**: Database locked
```
Solution: Close all instances of the app
Delete database\acc_main.db-wal and acc_main.db-shm
Restart app
```

**Problem**: API key verification fails
```
Solution:
1. Check internet connection
2. Verify key is copied correctly (no extra spaces)
3. Check API key is active on provider's website
4. Try regenerating the key
```

**Problem**: Encryption key error
```
Solution: DO NOT delete encryption.key!
If you did:
- All encrypted API keys are lost (unrecoverable)
- You'll need to re-enter all API keys
- A new encryption key will be generated automatically
```

### Logs

Check logs for detailed error messages:
- **Application log**: `logs\app.log`
- **Error log**: `logs\errors.log`
- **AI interactions**: Database → `ai_interactions` table

---

## ❓ FAQ

### General

**Q: Is my data secure?**
A: Yes. All API keys are encrypted with AES-256. Data is stored locally on your computer, not in the cloud.

**Q: Do I need all the API keys?**
A: No. Minimum: Gemini + Groq. Others are optional but enhance functionality.

**Q: How much do the API costs?**
A: Very low. A typical essay might cost $0.05-$0.15 total. The app shows real-time cost tracking.

**Q: Can I use this without Canvas?**
A: Yes! Canvas integration is optional. You can paste assignment instructions manually.

### Technical

**Q: Can I use this on Mac/Linux?**
A: Currently Windows-only, but the code is mostly portable. Mac/Linux support may come later.

**Q: Where is my data stored?**
A: Everything is in `C:\Users\Gamer\Getitdone\database\acc_main.db`

**Q: Can I export my data?**
A: Yes, the database is standard SQLite. You can export to CSV/JSON using database tools.

**Q: What if I lose my encryption key?**
A: Encrypted API keys cannot be recovered. You'll need to re-enter them. **Always backup `config\encryption.key`!**

### Features

**Q: Can it write my essay for me?**
A: No. It assists with research, organization, and editing, but you write your own essay.

**Q: Will my tutor know I used AI?**
A: The app helps you write better, but you're still writing. Use AI assistance ethically according to your institution's policies.

**Q: Can I use my own AI API keys?**
A: Yes! That's required actually. You need your own API keys for Gemini, Groq, etc.

---

## 📞 Support

For issues, questions, or feedback:
- **GitHub Issues**: [Report a bug](https://github.com/yourusername/academic-command-center/issues)
- **Email**: support@academiccommandcenter.com
- **Documentation**: Check `docs/` folder for detailed guides

---

## 📝 License

Copyright © 2024 Academic Command Center

All rights reserved. This software is for educational use only.

---

## 🙏 Acknowledgments

Built with:
- **Python 3.11+**
- **PyQt6** - GUI framework
- **SQLite** - Database
- **Google Gemini** - AI processing
- **Groq** - Fast AI inference
- **Canvas LMS API** - Assignment integration

---

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (COMPLETE)
- Core services
- Database
- Encryption
- AI routing
- API management

### 🚧 Phase 2: Core Features (IN PROGRESS)
- Essay parser
- Task generator
- Materials library
- Basic UI

### 📅 Phase 3: User Interface (PLANNED)
- Full PyQt6 UI
- Dashboard
- Settings screens

### 📅 Phase 4: Writing & Productivity (PLANNED)
- Writing assistant
- Focus system
- Analytics

### 📅 Phase 5: Polish & Deploy (PLANNED)
- Packaging
- Installer improvements
- Documentation
- Testing

---

**Last Updated**: November 22, 2024
**Version**: 1.0.0-alpha (Phase 1)
