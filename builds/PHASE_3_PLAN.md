# PHASE 3 - DEVELOPMENT PLAN

**Project**: Academic Command Center
**Phase**: Phase 3 - Advanced Features
**Status**: 🚀 **STARTING**
**Target**: Enhanced productivity and insights
**Estimated Code**: ~3,500 lines across 12 components

---

## PHASE 3 OBJECTIVES

Build advanced features that enhance student productivity, provide actionable insights, and streamline the writing process.

### Key Goals

1. **Increase Focus**: Pomodoro timer with distraction tracking
2. **Provide Insights**: Analytics dashboard with productivity metrics
3. **Improve Writing**: AI-powered grammar and style checking
4. **Enhance Workflow**: Citation management and version control

---

## MODULE 1: FOCUS MODE (Priority: HIGH)

**Purpose**: Help students maintain focus and track productive work sessions

**Components to Build** (4 modules, ~900 lines):

### 1.1 Pomodoro Timer (`pomodoro_timer.py` - 250 lines)
**Features**:
- 25-minute work sessions + 5-minute breaks
- Long break (15 minutes) after 4 sessions
- Start/pause/stop controls
- Audio notifications
- Session counter
- Auto-start next session (optional)

**Timer States**:
- IDLE → WORKING → BREAK → WORKING → ... → LONG_BREAK
- Database logging of all sessions
- Integration with task tracking

**Key Methods**:
- `start_session(task_id)` - Begin focus session
- `pause_session()` - Pause timer
- `complete_session()` - Mark session complete
- `skip_break()` - Skip break and start next session

### 1.2 Session Manager (`session_manager.py` - 220 lines)
**Features**:
- Session history tracking
- Task-session linking
- Daily/weekly session summaries
- Session interruption handling
- Focus score calculation

**Session Data Stored**:
```python
{
    'session_id': uuid,
    'task_id': uuid,
    'start_time': datetime,
    'end_time': datetime,
    'duration_minutes': int,
    'completed': bool,
    'interruptions': int,
    'focus_score': float  # 0-100 based on interruptions
}
```

**Key Methods**:
- `create_session(task_id)` - Start new session
- `end_session(session_id)` - Complete session
- `get_session_history(days)` - Retrieve history
- `calculate_focus_score()` - Compute focus quality

### 1.3 Focus View UI (`focus_view.py` - 350 lines)
**Features**:
- Large timer display (countdown)
- Current task display
- Start/pause/stop buttons
- Session progress (1 of 4, etc.)
- Daily session count
- Focus score indicator
- Today's completed tasks list

**UI Layout**:
```
┌─────────────────────────────────────┐
│         Focus Mode                  │
├─────────────────────────────────────┤
│                                     │
│          25:00                      │
│      (Large Timer)                  │
│                                     │
│  Current Task: Write Introduction   │
│  Session: 2 of 4                    │
│  Focus Score: 85%                   │
│                                     │
│  [Start] [Pause] [Skip Break]      │
│                                     │
│  Today's Sessions: 6                │
│  ✓ Research: Postmodernism (3 sess)│
│  ✓ Outline: Introduction (1 sess)  │
│  → Write Introduction (2 sess)      │
└─────────────────────────────────────┘
```

**Integration**:
- Links to Task Manager (auto-complete tasks)
- Updates progress logs
- Integrates with Analytics

### 1.4 Distraction Logger (`distraction_logger.py` - 80 lines)
**Features**:
- Manual distraction logging (button click)
- Distraction categorization (social media, email, other)
- Distraction frequency tracking
- Impact on focus score

**Key Methods**:
- `log_distraction(session_id, category)` - Record distraction
- `get_distraction_stats(date_range)` - Analyze patterns

---

## MODULE 2: ANALYTICS DASHBOARD (Priority: HIGH)

**Purpose**: Provide insights into productivity patterns and progress

**Components to Build** (3 modules, ~850 lines):

### 2.1 Progress Tracker (`progress_tracker.py` - 300 lines)
**Features**:
- Daily progress logging
- Task completion tracking
- Time spent per essay
- Milestone detection
- Streak tracking (consecutive work days)

**Metrics Tracked**:
- Tasks completed per day
- Time spent (total and per task type)
- Essay progress (% complete)
- Focus sessions per day
- Productivity score (0-100)

**Database Integration**:
- Queries `tasks`, `focus_sessions`, `progress_logs`
- Aggregates data by day/week/month
- Calculates trends and patterns

**Key Methods**:
- `log_daily_progress(date)` - Record day's work
- `calculate_productivity_score(date)` - Compute score
- `detect_milestones()` - Find achievements
- `get_streak_count()` - Count consecutive days

### 2.2 Analytics Engine (`analytics_engine.py` - 350 lines)
**Features**:
- Time distribution analysis (research vs writing)
- Task completion rate calculation
- Average time estimates vs actual
- Peak productivity hours detection
- Essay progress forecasting

**Analysis Types**:

**A. Time Analysis**:
- Time spent by task type (research/writing)
- Time spent by priority level
- Time spent by essay
- Time spent by day of week
- Time spent by hour of day

**B. Performance Analysis**:
- Task completion rate (completed/total)
- On-time completion rate
- Estimate accuracy (actual/estimated)
- Focus score trends
- Session completion rate

**C. Trend Analysis**:
- Productivity over time (improving/declining)
- Task backlog trends
- Deadline pressure patterns
- Focus quality trends

**Key Methods**:
- `analyze_time_distribution(date_range)` - Time breakdown
- `calculate_completion_rates()` - Success metrics
- `detect_peak_hours()` - Best work times
- `forecast_completion(essay_id)` - Predict finish date
- `generate_insights()` - AI-powered recommendations

### 2.3 Analytics View UI (`analytics_view.py` - 200 lines)
**Features**:
- Overview statistics cards
- Time distribution charts (pie/bar charts)
- Productivity trend graph (line chart)
- Task completion funnel
- Focus session calendar heatmap
- Insights and recommendations

**UI Sections**:

**A. Overview Cards** (4 cards):
- Total hours worked (this week)
- Tasks completed (this week)
- Average focus score
- Current streak (days)

**B. Charts**:
- Time distribution pie chart (research vs writing)
- Productivity line graph (last 30 days)
- Task completion bar chart (by priority)
- Focus session heatmap (GitHub-style)

**C. Insights Panel**:
- "You're most productive at 10 AM"
- "Your focus improves on Tuesdays"
- "You complete 85% of high-priority tasks"
- "Your writing tasks take 20% longer than estimated"

**Libraries Needed**:
- `matplotlib` or `pyqtgraph` for charts
- Custom visualization widgets

---

## MODULE 3: WRITING ASSISTANT (Priority: MEDIUM)

**Purpose**: Improve writing quality with AI-powered feedback

**Components to Build** (2 modules, ~600 lines):

### 3.1 Grammar Checker (`grammar_checker.py` - 350 lines)
**Features**:
- Real-time grammar checking using DeepSeek AI
- Style suggestions
- Readability analysis (Flesch-Kincaid)
- Word choice improvements
- Sentence structure feedback

**Grammar Check Types**:
- Spelling errors
- Grammar mistakes
- Punctuation errors
- Subject-verb agreement
- Tense consistency
- Passive voice detection
- Wordiness detection

**DeepSeek Integration**:
```python
def check_grammar(text):
    prompt = f"""
    Check this academic text for grammar and style issues.
    Provide specific suggestions for improvement.

    Text:
    {text[:2000]}

    Return JSON:
    {{
      "issues": [
        {{"type": "grammar", "text": "...", "suggestion": "...", "position": [start, end]}},
        ...
      ],
      "readability_score": float,
      "overall_feedback": "..."
    }}
    """

    result = ai_router.execute_task({
        'task_type': 'grammar_check',
        'payload': {'prompt': prompt, 'model': 'deepseek-coder'}
    })

    return parse_result(result)
```

**Key Methods**:
- `check_text(text)` - Full grammar check
- `check_paragraph(paragraph)` - Quick check
- `calculate_readability(text)` - Flesch-Kincaid score
- `suggest_improvements(text)` - Style suggestions

### 3.2 Writing View UI (`writing_view.py` - 250 lines)
**Features**:
- Large text editor
- Real-time grammar highlighting
- Suggestions sidebar
- Word count tracker
- Readability score display
- Save/load drafts
- Export to DOCX

**UI Layout**:
```
┌─────────────────────────────┬──────────┐
│   Writing Assistant         │ Issues   │
├─────────────────────────────┤  (5)     │
│                             │          │
│  Essay: Cultural Analysis   │ Grammar  │
│  Section: Introduction      │ - Line 5 │
│                             │ - Line 12│
│  [Large Text Editor]        │          │
│                             │ Style    │
│  The postmodern era has...  │ - Line 3 │
│                             │          │
│                             │ Read: 65 │
│  Words: 247 / 250           │ (Grade 10│
│  Readability: 65            │          │
│                             │ [Check]  │
│  [Save] [Export] [Check]    │ [Apply]  │
└─────────────────────────────┴──────────┘
```

**Key Features**:
- Click on issue to highlight in text
- Apply suggestions with one click
- Auto-save every 30 seconds
- Track revision history

---

## MODULE 4: CITATION MANAGER (Priority: MEDIUM)

**Purpose**: Manage sources and generate citations

**Components to Build** (2 modules, ~550 lines):

### 4.1 Source Manager (`source_manager.py` - 350 lines)
**Features**:
- Add sources (manual or auto-import)
- Store source metadata (author, title, year, etc.)
- Generate citations in multiple styles
- Create bibliographies
- Link sources to essays

**Source Types Supported**:
- Book
- Journal article
- Website
- Conference paper
- Thesis/dissertation
- Other

**Citation Styles**:
- APA 7th edition
- MLA 9th edition
- Chicago 17th edition
- Harvard
- IEEE

**Key Methods**:
- `add_source(source_data)` - Add new source
- `generate_citation(source_id, style)` - Format citation
- `create_bibliography(essay_id, style)` - Generate reference list
- `import_from_doi(doi)` - Auto-import from DOI
- `link_to_essay(source_id, essay_id)` - Create link

### 4.2 Citation View UI (`citation_view.py` - 200 lines)
**Features**:
- Source list with search/filter
- Add source dialog
- Citation preview
- Copy citation button
- Generate bibliography button
- Link to essays

**UI Layout**:
```
┌─────────────────────────────────────┐
│   Citation Manager                  │
│  [+ Add Source] [Import DOI]        │
├─────────────────────────────────────┤
│  Search: [________] Style: [APA ▼] │
├─────────────────────────────────────┤
│                                     │
│  📚 Baudrillard, J. (1994)          │
│     Simulacra and Simulation        │
│     [Copy Citation] [Link to Essay] │
│                                     │
│  📄 Smith, A. (2020)                │
│     Postmodernism in Music          │
│     [Copy Citation] [Link to Essay] │
│                                     │
│  [Generate Bibliography]            │
└─────────────────────────────────────┘
```

---

## MODULE 5: ENHANCED CANVAS INTEGRATION (Priority: LOW)

**Purpose**: Improve Canvas LMS integration

**Components to Build** (1 module, ~300 lines):

### 5.1 Canvas Sync Manager (`canvas_sync_manager.py` - 300 lines)
**Features**:
- Auto-sync assignments (scheduled)
- Download assignment files
- Upload completed essays
- Grade fetching
- Announcement notifications
- Calendar integration

**Sync Features**:
- One-click sync all courses
- Automatic daily sync (background)
- Conflict resolution
- Sync history tracking

**Key Methods**:
- `sync_all_courses()` - Full sync
- `sync_course(course_id)` - Single course
- `download_assignment_files(assignment_id)` - Get files
- `upload_submission(essay_id)` - Submit to Canvas
- `fetch_grades()` - Get grade updates

---

## MODULE 6: VERSION CONTROL (Priority: LOW)

**Purpose**: Track essay revisions and enable rollback

**Components to Build** (1 module, ~300 lines):

### 6.1 Version Manager (`version_manager.py` - 300 lines)
**Features**:
- Auto-save snapshots every 5 minutes
- Manual snapshot creation
- Compare versions (diff view)
- Restore previous versions
- Version notes/comments

**Snapshot Data**:
```python
{
    'snapshot_id': uuid,
    'essay_id': uuid,
    'content': text,
    'word_count': int,
    'created_at': datetime,
    'note': str,
    'auto_saved': bool
}
```

**Key Methods**:
- `create_snapshot(essay_id, content, note)` - Save version
- `get_version_history(essay_id)` - List snapshots
- `compare_versions(v1_id, v2_id)` - Show diff
- `restore_version(snapshot_id)` - Revert to version

---

## PHASE 3 IMPLEMENTATION PRIORITY

### Sprint 1: Focus & Productivity (Week 1)
**Priority**: HIGH
**Estimated**: 900 lines, 1-2 days

1. ✅ Pomodoro Timer
2. ✅ Session Manager
3. ✅ Focus View UI
4. ✅ Distraction Logger

**Goal**: Enable students to track focused work sessions

### Sprint 2: Analytics & Insights (Week 1-2)
**Priority**: HIGH
**Estimated**: 850 lines, 1-2 days

1. ✅ Progress Tracker
2. ✅ Analytics Engine
3. ✅ Analytics View UI with charts

**Goal**: Provide actionable insights on productivity

### Sprint 3: Writing Assistant (Week 2)
**Priority**: MEDIUM
**Estimated**: 600 lines, 1 day

1. ✅ Grammar Checker
2. ✅ Writing View UI

**Goal**: Improve writing quality with AI feedback

### Sprint 4: Citations & Enhancements (Week 2-3)
**Priority**: MEDIUM
**Estimated**: 550 lines, 1 day

1. ✅ Source Manager
2. ✅ Citation View UI

**Goal**: Simplify citation management

### Sprint 5: Canvas & Versions (Week 3)
**Priority**: LOW
**Estimated**: 600 lines, 1 day

1. ✅ Canvas Sync Manager
2. ✅ Version Manager

**Goal**: Enhance integration and safety

---

## TECHNICAL REQUIREMENTS

### New Dependencies

**Charting Libraries**:
```
matplotlib==3.8.2           # For analytics charts
pyqtgraph==0.13.3          # PyQt6-native charting (alternative)
```

**Additional AI**:
```
# DeepSeek already in requirements for grammar checking
```

**Audio**:
```
pygame==2.5.2              # For timer notifications
```

### Database Schema Updates

**New Tables** (3 tables):

```sql
-- Focus sessions
CREATE TABLE focus_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    task_id TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_minutes INTEGER,
    session_type TEXT,  -- 'work', 'short_break', 'long_break'
    completed BOOLEAN DEFAULT 0,
    interruptions INTEGER DEFAULT 0,
    focus_score REAL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Progress logs (daily summaries)
CREATE TABLE progress_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    tasks_completed INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    focus_sessions INTEGER DEFAULT 0,
    average_focus_score REAL,
    productivity_score REAL,
    streak_days INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date)
);

-- Sources (citations)
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- book, article, website, etc.
    title TEXT NOT NULL,
    authors TEXT,  -- JSON array
    year INTEGER,
    publisher TEXT,
    url TEXT,
    doi TEXT,
    additional_metadata TEXT,  -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Source links to essays
CREATE TABLE essay_sources (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    used_in_text BOOLEAN DEFAULT 1,
    FOREIGN KEY (essay_id) REFERENCES essays(id),
    FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

**Tables Already Exist** (from Phase 1):
- `writing_snapshots` - For version control
- `analytics_cache` - For caching analytics calculations

---

## SUCCESS CRITERIA

Phase 3 will be considered complete when:

✅ Students can use Focus Mode to track work sessions
✅ Analytics dashboard provides meaningful insights
✅ Writing Assistant catches grammar errors
✅ Citation manager simplifies bibliography creation
✅ Canvas sync works automatically
✅ Version control enables rollback

**Total**: ~3,500 lines of new code across 12 components

---

## TESTING PLAN

### Unit Tests

1. **Focus Mode Tests**:
   - Test timer countdown
   - Test session completion
   - Test break transitions
   - Test interruption logging

2. **Analytics Tests**:
   - Test metric calculations
   - Test trend detection
   - Test forecast accuracy
   - Test insight generation

3. **Writing Assistant Tests**:
   - Test grammar checking with sample text
   - Test readability scoring
   - Test suggestion formatting

4. **Citation Tests**:
   - Test citation generation (all styles)
   - Test bibliography formatting
   - Test DOI import

### Integration Tests

1. **Focus → Analytics**: Session data flows to analytics
2. **Writing → Grammar**: Text editor integrates with checker
3. **Citations → Essays**: Sources link to essays correctly
4. **Canvas → Essays**: Assignments sync to database

---

## PHASE 3 ROADMAP

**Week 1**: Focus Mode + Analytics
**Week 2**: Writing Assistant + Citations
**Week 3**: Canvas Sync + Version Control + Testing

**Total Estimated Time**: 2-3 weeks
**Lines of Code**: ~3,500 new lines
**New Components**: 12 modules
**UI Views Added**: 3 (Focus, Analytics, Writing)

---

## NEXT STEPS

1. **Start Sprint 1**: Build Focus Mode
   - Begin with Pomodoro Timer
   - Create Session Manager
   - Build Focus View UI
   - Add Distraction Logger

2. **Update Database**: Add new tables

3. **Test Focus Mode**: Ensure timer works correctly

4. **Move to Sprint 2**: Build Analytics Dashboard

---

**Plan Created**: November 12, 2025
**Phase 3 Status**: 🚀 **READY TO START**
**First Target**: Focus Mode Module
**Estimated First Module**: 900 lines, 1-2 days
