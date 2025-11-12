# USER GUIDE - Academic Command Center

**Version**: 1.0.0
**Platform**: Windows 11
**Last Updated**: November 12, 2025

---

## TABLE OF CONTENTS

1. [Getting Started](#getting-started)
2. [First-Time Setup](#first-time-setup)
3. [Basic Workflow](#basic-workflow)
4. [Feature Guides](#feature-guides)
5. [Tips & Best Practices](#tips--best-practices)
6. [FAQ](#faq)

---

## GETTING STARTED

### What is Academic Command Center?

Academic Command Center (ACC) is a comprehensive Windows desktop application that helps students manage academic essays from assignment to submission. It combines AI-powered assistance, task management, productivity tracking, and LMS integration into one unified tool.

### Key Features

- **AI-Powered Essay Parser**: Automatically analyzes assignment instructions
- **Smart Task Generation**: Breaks essays into actionable subtasks
- **Pomodoro Focus Timer**: 25/5/15 minute work/break cycles
- **Analytics Dashboard**: Track productivity, progress, and trends
- **Writing Assistant**: Grammar and style checking
- **Citation Manager**: Harvard, APA, and MLA formatting
- **Version Control**: Snapshot essays and compare versions
- **Canvas Integration**: Sync grades and assignments from Canvas LMS

---

## FIRST-TIME SETUP

### Step 1: Installation

1. Run `installlearn.bat`
2. Wait 5-10 minutes for installation
3. Installation creates:
   - Virtual environment
   - Database with 21 tables
   - Encryption keys
   - Directory structure

### Step 2: Launch Application

1. Double-click `startlearn.bat`
2. Application window opens
3. You'll see the Dashboard view

### Step 3: Configure API Keys

**Required for AI features:**

1. Click **Settings** in sidebar (⚙️)
2. Go to **API Keys** tab
3. Add API keys for:
   - **Google Gemini** (essay parsing, analysis)
   - **Groq** (task generation)
   - **Optional**: DeepSeek, Claude, Cohere

**How to get API keys:**
- Gemini: https://makersuite.google.com/app/apikey
- Groq: https://console.groq.com/keys
- DeepSeek: https://platform.deepseek.com/
- OpenRouter (Claude): https://openrouter.ai/keys
- Cohere: https://dashboard.cohere.com/api-keys

4. Click **Save** after entering each key
5. Click **Verify** to test connection

### Step 4: (Optional) Configure Canvas

If your school uses Canvas LMS:

1. Go to Settings → Canvas Settings
2. Enter Canvas URL: `https://canvas.yourschool.edu`
3. Enter API Token:
   - Log into Canvas
   - Go to Account → Settings
   - Click "New Access Token"
   - Copy token and paste here
4. Click **Save**
5. Click **Test Connection**

---

## BASIC WORKFLOW

### Creating Your First Essay

1. **Navigate to Essays**
   - Click **📝 Essays** in sidebar
   - Click **+ New Essay** button

2. **Add Assignment Instructions**
   - Paste assignment text directly
   - Or upload PDF/DOCX file
   - Or click **Import from Canvas**

3. **AI Parses Requirements**
   - App extracts:
     - Word count (e.g., "1500-2000 words")
     - Source requirements (e.g., "5 academic sources")
     - Citation style (e.g., "APA 7th edition")
     - Due date
     - Rubric items

4. **Tasks Auto-Generated**
   - Click **✓ Tasks** in sidebar
   - See breakdown of research, writing, editing tasks
   - Each task has:
     - Priority (High/Medium/Low)
     - Time estimate
     - Status (Not Started/In Progress/Complete)

5. **Work Through Tasks**
   - Click **🎯 Focus Mode**
   - Select a task
   - Click **Start** for Pomodoro session
   - Work for 25 minutes
   - Take 5-minute break
   - Repeat 4 cycles, then 15-minute break

6. **Track Progress**
   - Click **📈 Analytics**
   - View:
     - Total hours worked
     - Tasks completed
     - Focus score
     - Productivity trends

7. **Use Writing Assistant**
   - Click **✍️ Writing Assistant**
   - Enter or paste essay text
   - Click **Check Grammar**
   - Click **Analyze Style**
   - Review errors and suggestions
   - Apply corrections

8. **Manage Citations**
   - Click **📚 Citations**
   - Add sources (books, articles, websites)
   - Generate citations in Harvard/APA/MLA
   - Copy to clipboard
   - Generate full bibliography

9. **Create Snapshots**
   - Click **🔄 Version Control**
   - Click **📸 Create Snapshot**
   - Enter label (e.g., "Before major revision")
   - Click **Save**
   - Later: Compare versions or restore

10. **Sync Grades (Canvas)**
    - Click **🎓 Canvas**
    - Click **Sync Now**
    - View grade statistics
    - See sync history

---

## FEATURE GUIDES

### Focus Mode - Pomodoro Timer

**What it does**: Helps you maintain focus with 25-minute work sessions

**How to use**:
1. Click **🎯 Focus Mode**
2. Select task from dropdown
3. Click **Start**
4. Timer counts down from 25:00
5. Work until timer reaches 0:00
6. Break starts automatically (5 minutes)
7. After 4 work sessions, long break (15 minutes)

**Tips**:
- Click **Pause** if you need to stop briefly
- Click **Skip Break** to continue working
- Track interruptions (if distracted, click **Log Distraction**)
- View session history at bottom of screen

**Session Tracking**:
- All sessions saved to database
- Focus score calculated based on interruptions
- Data feeds into Analytics Dashboard

---

### Analytics Dashboard

**What it does**: Provides insights into productivity patterns

**Metrics Tracked**:
- **Total Hours**: Time spent on all tasks
- **Tasks Completed**: Count of finished tasks
- **Focus Score**: Average from Pomodoro sessions (0-100)
- **Current Streak**: Consecutive days working

**Trends**:
- Productivity over time (last 30 days)
- Time distribution (research vs writing)
- Task completion by priority
- Focus score trends

**Goals**:
- Set daily/weekly/monthly goals
- Track progress toward goals
- Get alerts when goals completed

**Using Analytics**:
1. Click **📈 Analytics**
2. View overview cards at top
3. Scroll to see charts
4. Check **Goals** tab to create goals
5. View **Insights** panel for recommendations

---

### Writing Assistant

**What it does**: Checks grammar and analyzes writing style

**Grammar Checking**:
- Detects:
  - Spelling errors
  - Grammar mistakes
  - Punctuation errors
  - Subject-verb agreement
  - Tense consistency

**Style Analysis**:
- Readability score (Flesch Reading Ease)
- Sentence variety (length distribution)
- Passive voice detection
- Transition word usage
- Academic writing issues

**How to use**:
1. Click **✍️ Writing Assistant**
2. Enter text in editor (or paste)
3. Click **Check Grammar**
4. Review errors (red = error, yellow = warning)
5. Click error to see suggestion
6. Click **Apply** to fix
7. Click **Analyze Style** for readability

**Tips**:
- Run checks frequently (every few paragraphs)
- Address high-priority errors first
- Use style suggestions to improve flow
- Aim for readability score of 60-70 for academic writing

---

### Citation Manager

**What it does**: Manages sources and generates formatted citations

**Supported Formats**:
- Harvard
- APA 7th edition
- MLA 9th edition

**Supported Source Types**:
- Books
- Journal articles
- Websites
- Conference papers
- Theses/dissertations

**How to use**:
1. Click **📚 Citations**
2. Click **+ Add Source**
3. Select source type (book, article, etc.)
4. Fill in fields:
   - Title (required)
   - Author (required)
   - Year (required)
   - Publisher/Journal
   - URL/DOI
5. Click **Save**
6. Select citation style from dropdown
7. Click **Copy Citation** to copy to clipboard
8. Click **Generate Bibliography** for full reference list

**Link to Essays**:
- Click **Link to Essay** button
- Select essay from dropdown
- Source now associated with essay
- Bibliography will include only linked sources

---

### Version Control

**What it does**: Creates snapshots of essays for version history

**Snapshot Types**:
- **Manual**: You create manually with custom label
- **Auto**: Created automatically (every 30 min or 50+ word changes)
- **Before Major Edit**: Created before restore operations

**How to use**:
1. Click **🔄 Version Control**
2. Select essay from dropdown
3. Click **📸 Create Snapshot**
4. Enter label (e.g., "First draft complete")
5. Click **Save**

**Comparing Versions**:
1. Click **🔍 Compare Versions**
2. Select two snapshots from dropdowns
3. Click **Compare**
4. View differences:
   - Word count change
   - Lines added/removed
   - Side-by-side comparison

**Restoring**:
1. Select snapshot from list
2. Click **↩️ Restore This Version**
3. Confirm (backup created automatically)
4. Essay content reverted to snapshot

**Tips**:
- Create snapshot before major changes
- Use descriptive labels
- Compare versions to see progress
- Auto-snapshots provide safety net

---

### Canvas Integration

**What it does**: Syncs grades and assignments from Canvas LMS

**Setup**:
1. Click **🎓 Canvas**
2. Click **Setup**
3. Enter Canvas URL and API token
4. Click **Save**

**Syncing**:
1. Click **Sync Now**
2. Wait for sync to complete
3. View grade statistics:
   - Total graded assignments
   - Average grade
   - Highest grade
   - Lowest grade
   - Grade distribution (A/B/C/etc.)

**Features**:
- Automatic grade import
- Statistics dashboard
- Sync history log
- Integration with Essays view

---

## TIPS & BEST PRACTICES

### Productivity Tips

1. **Start with Focus Mode**: Use Pomodoro timer for deep work
2. **Work in Morning**: Most productive hours are typically 9 AM - 12 PM
3. **Set Daily Goals**: Create achievable daily goals in Analytics
4. **Take Breaks**: Don't skip Pomodoro breaks
5. **Track Everything**: More data = better insights

### Writing Tips

1. **Check Often**: Run grammar check every few paragraphs
2. **Save Snapshots**: Create snapshot before major revisions
3. **Use Citations Early**: Add sources as you research
4. **Watch Readability**: Aim for 60-70 for academic writing
5. **Review Style**: Check passive voice and transitions

### Organization Tips

1. **Descriptive Task Names**: Be specific (not just "Write")
2. **Link Everything**: Link sources to essays, tasks to focus sessions
3. **Use Labels**: Label snapshots descriptively
4. **Regular Backups**: Backup `database/acc_main.db` weekly
5. **Clean Up**: Delete completed essays/tasks periodically

### Avoiding Common Mistakes

1. **Don't Skip Setup**: Configure API keys before using AI features
2. **Don't Ignore Errors**: Check logs if something fails
3. **Don't Lose Encryption Key**: Backup `config/encryption.key`
4. **Don't Rush**: Focus sessions work best when uninterrupted
5. **Don't Forget Sync**: Sync Canvas regularly for up-to-date grades

---

## FAQ

### General

**Q: Can I use ACC without AI API keys?**
A: Most features work, but essay parsing and task generation require Gemini/Groq.

**Q: Is my data secure?**
A: Yes. All API keys encrypted with AES-256. Data stored locally, not in cloud.

**Q: Can I use on multiple computers?**
A: Yes, but you need to copy `config/encryption.key` and `database/acc_main.db`.

**Q: How much do API keys cost?**
A: Very low. Typical essay costs $0.05-$0.15 total. Gemini/Groq have free tiers.

**Q: Can I export my essays?**
A: Currently supports copying text. Phase 6 will add DOCX/PDF export.

### Features

**Q: How accurate is the grammar checker?**
A: Detects common errors. Not as comprehensive as Grammarly but good for basics.

**Q: Can I customize citation styles?**
A: Harvard, APA, and MLA are built-in. Custom styles not yet supported.

**Q: What's a good focus score?**
A: 80-100 is excellent, 60-80 is good, below 60 needs improvement.

**Q: How often should I create snapshots?**
A: Auto-snapshots handle most cases. Create manual ones before major changes.

**Q: Does Canvas sync work with all schools?**
A: Works with standard Canvas LMS. Some customized installations may vary.

### Troubleshooting

**Q: Application won't start**
A: Check `logs/app.log`. Ensure virtual environment activated.

**Q: Database locked error**
A: Close all app instances. Delete `.db-wal` and `.db-shm` files.

**Q: API key verification fails**
A: Check internet connection. Verify key is correct. Try regenerating key.

**Q: Focus timer not counting down**
A: Refresh view. Check if application is active (not minimized).

**Q: Grades not syncing**
A: Verify Canvas token is valid. Check Canvas URL is correct.

---

## KEYBOARD SHORTCUTS

*(Coming in future update)*

---

## GETTING HELP

**Documentation**: See README.md for technical details

**Logs**: Check `logs/app.log` for error messages

**GitHub Issues**: Report bugs at [repository URL]

**Email Support**: support@academiccommandcenter.com

---

**Enjoy using Academic Command Center!** 🎓

