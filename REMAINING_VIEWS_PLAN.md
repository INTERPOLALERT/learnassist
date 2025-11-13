# Remaining Views - Detailed Implementation Plan

## Overview

We need to build 5 remaining views to complete the Academic Command Center:
1. **Assignments View** (Priority: HIGH)
2. **Study Timer View** (Priority: HIGH)
3. **Notes View** (Priority: MEDIUM)
4. **Calendar View** (Priority: MEDIUM)
5. **AI Tools View** (Priority: LOW)

**Total Estimated Time:** 4-6 sessions
**Total Estimated Lines:** ~12,000-15,000 lines

---

## Phase 2: Assignments View (Priority: HIGH)

### Overview
Complete assignment tracking system for homework, projects, exams, and quizzes.

### Features Required
**Core Features:**
- ✅ Assignment list with status filters (All, Pending, In Progress, Completed, Overdue)
- ✅ Create/Edit assignment dialog
- ✅ Subject categorization (uses subjects table)
- ✅ Due date tracking with countdown
- ✅ Priority levels (Low, Medium, High)
- ✅ Grade recording and GPA calculation
- ✅ Attachment support (PDFs, docs)
- ✅ Notes/description field
- ✅ Search and sort functionality

**Advanced Features:**
- ✅ Canvas LMS sync (import assignments)
- ✅ Quick add from toolbar
- ✅ Bulk actions (mark complete, delete)
- ✅ Color-coded by subject
- ✅ Progress percentage tracking
- ✅ Assignment types (Homework, Quiz, Exam, Project, Lab)

### UI Components
```
┌─────────────────────────────────────────────┐
│ [+] New Assignment  [⟳] Sync Canvas  [🔍]  │
├─────────────────────────────────────────────┤
│ Filters: [All] [Pending] [Overdue] [Done]  │
├─────────────────────────────────────────────┤
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ 📚 Math Homework #5          HIGH   │   │
│ │ Due: Tomorrow (1 day left) 🔴       │   │
│ │ Grade: Not submitted                │   │
│ │ [Edit] [Complete] [Delete]          │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ 🧪 Chemistry Lab Report      MEDIUM │   │
│ │ Due: Nov 20 (8 days left) 🟡        │   │
│ │ Grade: 85/100 (B)                   │   │
│ │ [Edit] [View] [Delete]              │   │
│ └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Database Integration
**Tables Used:**
- `assignments` (main storage) ✅ Already created in migration
- `subjects` (categorization) ✅ Already created in migration
- `user_api_keys` (Canvas sync) ✅ Exists
- `canvas_sync_log` (sync tracking) ✅ Exists

**Queries Needed:**
- SELECT with filters (status, subject, date range)
- INSERT new assignments
- UPDATE assignment details/grades
- DELETE assignments
- Canvas sync import

### Backend Components Needed
**Existing Components (Reuse):**
- DatabaseManager ✅
- Canvas LMS Integration Manager ✅ (from Phase 6)

**New Components:**
- AssignmentManager class (CRUD operations)
- Grade calculator utility

### Complexity
**Estimated Lines:** ~3,500 lines
**Estimated Time:** 1 session
**Difficulty:** Medium
**Dependencies:** None (database ready, subjects table exists)

### Implementation Steps
1. Create AssignmentManager class (backend)
2. Build assignment list widget
3. Create add/edit dialog
4. Implement filters and search
5. Add Canvas sync integration
6. Test CRUD operations
7. Add keyboard shortcuts

---

## Phase 3: Study Timer View (Priority: HIGH)

### Overview
Pomodoro timer with focus tracking and session analytics.

### Features Required
**Core Features:**
- ✅ Pomodoro timer (25min work, 5min short break, 15min long break)
- ✅ Start/Stop/Pause/Skip controls
- ✅ Visual timer display with progress ring
- ✅ Audio/visual notifications on completion
- ✅ Session type selector (Work, Break, Long Break)
- ✅ Auto-start next session option
- ✅ Session counter (completed pomodoros)

**Focus Tracking:**
- ✅ Interruption counter (track distractions)
- ✅ Session notes (what did you accomplish?)
- ✅ Link to assignment/task
- ✅ Subject categorization
- ✅ Focus score calculation

**Analytics:**
- ✅ Today's total study time
- ✅ Current streak (consecutive days)
- ✅ Best streak record
- ✅ Completed sessions this week
- ✅ Average focus score

### UI Components
```
┌─────────────────────────────────────────────┐
│           FOCUS SESSION                     │
│                                             │
│           ┌───────────┐                     │
│           │           │                     │
│           │   24:35   │  ← Big circular    │
│           │           │     progress ring   │
│           └───────────┘                     │
│                                             │
│     [▶ Start] [⏸ Pause] [⏹ Stop] [⏭ Skip] │
│                                             │
├─────────────────────────────────────────────┤
│ Session Type: [Work ▼]  25 minutes         │
│ Subject: [Math ▼]                           │
│ Assignment: [Homework #5 ▼] (optional)     │
├─────────────────────────────────────────────┤
│ 📊 Today's Stats:                           │
│   • Study Time: 2h 30m                      │
│   • Sessions: 6 completed                   │
│   • Focus Score: 87%                        │
│   • Streak: 5 days 🔥                       │
├─────────────────────────────────────────────┤
│ Session Notes:                              │
│ [Text area for quick notes...]             │
└─────────────────────────────────────────────┘
```

### Database Integration
**Tables Used:**
- `focus_sessions` ✅ Already exists (added `subject` column in migration)
- `subjects` ✅ For categorization
- `assignments` ✅ For linking

**Queries Needed:**
- INSERT new session on completion
- SELECT today's sessions (stats)
- SELECT streak calculation
- UPDATE session notes/scores

### Backend Components Needed
**Existing Components (Reuse):**
- DatabaseManager ✅
- Study Analytics ✅ (from Phase 6)

**New Components:**
- PomodoroTimer class (QTimer-based)
- FocusSessionManager class (session CRUD)
- Notification system (audio alerts)

### Complexity
**Estimated Lines:** ~2,800 lines
**Estimated Time:** 1 session
**Difficulty:** Medium
**Dependencies:** None

### Implementation Steps
1. Create PomodoroTimer class
2. Build timer UI with circular progress
3. Add notification system
4. Create session tracking
5. Build statistics panel
6. Add session notes dialog
7. Integrate with achievements

---

## Phase 4: Notes View (Priority: MEDIUM)

### Overview
Quick note-taking system with organization and search.

### Features Required
**Core Features:**
- ✅ Note list with search
- ✅ Create/Edit/Delete notes
- ✅ Rich text editor (bold, italic, lists, links)
- ✅ Tags for organization
- ✅ Link to assignments/subjects
- ✅ Favorites/pinning
- ✅ Last edited timestamp
- ✅ Note preview in list

**Organization:**
- ✅ Tag filtering
- ✅ Subject filtering
- ✅ Search by content
- ✅ Sort by date/title/subject

**Advanced Features:**
- ✅ Quick notes (floating widget)
- ✅ Markdown support (optional)
- ✅ Export notes (txt, md, pdf)
- ✅ Note templates

### UI Components
```
┌─────────────────────────────────────────────┐
│ [+] New Note  [🔍] Search  [📋] Templates   │
├───────────┬─────────────────────────────────┤
│           │ Math Study Notes                │
│ 📝 All    │ Last edited: 2 hours ago        │
│ ⭐ Favs   │                                 │
│ 🏷️ Tags   │ Key concepts for midterm:       │
│   #math   │ - Derivatives: d/dx rules       │
│   #exam   │ - Chain rule applications       │
│ 📚 Subj   │ - Product rule...               │
│   Math    │                                 │
│   Chem    │ [Edit] [Delete] [⭐] [Export]   │
│           │                                 │
│           ├─────────────────────────────────┤
│           │ Chemistry Lab Notes             │
│           │ Last edited: Yesterday          │
│           │                                 │
│           │ Experiment results from...      │
│           │                                 │
└───────────┴─────────────────────────────────┘
```

### Database Integration
**Tables Used:**
- `notes` table ⚠️ **NEEDS TO BE CREATED**
- `note_tags` table ⚠️ **NEEDS TO BE CREATED**
- `subjects` ✅ For categorization
- `assignments` ✅ For linking

**New Tables Schema:**
```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    subject_id TEXT,
    assignment_id TEXT,
    tags TEXT,  -- JSON array
    is_favorite BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id)
);
```

### Backend Components Needed
**Existing Components (Reuse):**
- DatabaseManager ✅
- Export Manager ✅ (for exporting notes)

**New Components:**
- NotesManager class (CRUD)
- Rich text editor widget

### Complexity
**Estimated Lines:** ~2,500 lines
**Estimated Time:** 1 session
**Difficulty:** Medium
**Dependencies:** Need to create `notes` table

### Implementation Steps
1. Create notes database table
2. Build NotesManager class
3. Create note list widget
4. Build rich text editor
5. Implement tagging system
6. Add search functionality
7. Integrate export features

---

## Phase 5: Calendar View (Priority: MEDIUM)

### Overview
Visual calendar showing assignments, deadlines, study sessions, and goals.

### Features Required
**Core Features:**
- ✅ Month/Week/Day view switcher
- ✅ Assignment deadlines displayed
- ✅ Study session blocks
- ✅ Goal target dates
- ✅ Color-coded by subject
- ✅ Click date to see details
- ✅ Quick add event from calendar

**Display Options:**
- ✅ Show/hide assignments
- ✅ Show/hide study sessions
- ✅ Show/hide goals
- ✅ Subject filter
- ✅ Today highlight

**Integrations:**
- ✅ Sync with assignments table
- ✅ Sync with focus_sessions table
- ✅ Sync with goals table
- ✅ Canvas calendar import

### UI Components
```
┌─────────────────────────────────────────────┐
│ [Month] [Week] [Day]     November 2025  ◀ ▶│
├─────────────────────────────────────────────┤
│  Sun    Mon    Tue    Wed    Thu    Fri Sat│
│                                             │
│         10     11     12     13     14   15 │
│                      TODAY                  │
│         📚Math  🧪Chem  🎯Goal               │
│         Due    Lab    Due                   │
│                                             │
│   17    18     19     20     21     22   23 │
│                                             │
│   ⏱2h   ⏱1h           📚Exam               │
│   Study Study          Due                  │
│                                             │
├─────────────────────────────────────────────┤
│ Show: [✓] Assignments [✓] Sessions [ ] Goals│
│ Subject: [All ▼]                            │
└─────────────────────────────────────────────┘
```

### Database Integration
**Tables Used:**
- `assignments` ✅ (due dates)
- `focus_sessions` ✅ (study times)
- `goals` ✅ (target dates)
- `subjects` ✅ (color coding)

**Queries Needed:**
- SELECT assignments by date range
- SELECT focus sessions by date range
- SELECT goals by date range
- Aggregate events by day

### Backend Components Needed
**Existing Components (Reuse):**
- DatabaseManager ✅
- All existing managers ✅

**New Components:**
- CalendarManager class (event aggregation)
- Calendar widget (QCalendarWidget customization)

### Complexity
**Estimated Lines:** ~2,200 lines
**Estimated Time:** 1 session
**Difficulty:** Medium
**Dependencies:** Needs Assignments View completed first

### Implementation Steps
1. Build CalendarManager class
2. Create month view widget
3. Add week/day views
4. Implement event display
5. Add click handlers
6. Implement filters
7. Add quick add dialog

---

## Phase 6: AI Tools View (Priority: LOW)

### Overview
Quick access panel for AI-powered writing assistance.

### Features Required
**Core Features:**
- ✅ Quick essay analysis
- ✅ Grammar/spell checker
- ✅ Text summarizer
- ✅ Citation generator
- ✅ Paraphraser
- ✅ Writing prompts generator

**Input Methods:**
- ✅ Paste text directly
- ✅ Select assignment to analyze
- ✅ Upload file (docx, txt, pdf)

**Output:**
- ✅ Results display panel
- ✅ Copy to clipboard
- ✅ Save to notes
- ✅ Export results

### UI Components
```
┌─────────────────────────────────────────────┐
│ AI WRITING ASSISTANT                        │
├─────────────────────────────────────────────┤
│ Tool: [Quick Analysis ▼]                    │
│ [📝 Essay Analyzer] [✍️ Grammar Check]      │
│ [📄 Summarizer] [📚 Citations]              │
│ [🔄 Paraphraser] [💡 Writing Prompts]       │
├─────────────────────────────────────────────┤
│ Input:                                      │
│ ┌───────────────────────────────────────┐  │
│ │ [Paste text here or upload file...]  │  │
│ │                                       │  │
│ │                                       │  │
│ └───────────────────────────────────────┘  │
│ [📁 Upload File] [📋 From Assignment]      │
├─────────────────────────────────────────────┤
│ [🚀 Analyze]                                │
├─────────────────────────────────────────────┤
│ Results:                                    │
│ ┌───────────────────────────────────────┐  │
│ │ Analysis results appear here...       │  │
│ │                                       │  │
│ └───────────────────────────────────────┘  │
│ [💾 Save to Notes] [📋 Copy] [📤 Export]   │
└─────────────────────────────────────────────┘
```

### Database Integration
**Tables Used:**
- `ai_interactions` ✅ (caching)
- `notes` ⚠️ (saving results - will be created in Phase 4)
- `assignments` ✅ (loading text)

**Queries Needed:**
- Cache AI results
- Save to notes
- Load assignment text

### Backend Components Needed
**Existing Components (Reuse):**
- AI Router ✅ (from Phase 2)
- Essay Analyzer ✅ (from Phase 6)
- Writing Coach ✅ (from Phase 6)
- Content Summarizer ✅ (from Phase 6)
- Research Assistant ✅ (from Phase 6)

**New Components:**
- AIToolsManager class (orchestration)
- File upload handler

### Complexity
**Estimated Lines:** ~2,000 lines
**Estimated Time:** 0.5-1 session
**Difficulty:** Low (mostly UI, backend exists)
**Dependencies:** All AI components already built

### Implementation Steps
1. Create AIToolsManager class
2. Build tool selector UI
3. Create input panel
4. Build results display
5. Add file upload
6. Integrate existing AI components
7. Add save/export features

---

## Implementation Priority & Order

### Recommended Build Order:
1. **Phase 2: Assignments View** (FIRST - highest value, database ready)
2. **Phase 3: Study Timer View** (SECOND - complements assignments)
3. **Phase 4: Notes View** (THIRD - needs new table, good for capturing ideas)
4. **Phase 5: Calendar View** (FOURTH - synthesizes all other views)
5. **Phase 6: AI Tools View** (LAST - nice-to-have, uses existing backend)

### Why This Order?
1. **Assignments** = Core functionality students need most
2. **Timer** = Pairs perfectly with assignments (study for assignment X)
3. **Notes** = Supports both assignments and timer (capture insights while studying)
4. **Calendar** = Brings everything together visually
5. **AI Tools** = Polish/bonus feature

---

## Database Schema Updates Needed

### New Tables Required:
```sql
-- For Notes View (Phase 4)
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    subject_id TEXT,
    assignment_id TEXT,
    tags TEXT,  -- JSON array: ["important", "exam"]
    is_favorite BOOLEAN DEFAULT 0,
    is_pinned BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id)
);

CREATE INDEX idx_notes_user ON notes(user_id);
CREATE INDEX idx_notes_subject ON notes(subject_id);
CREATE INDEX idx_notes_favorite ON notes(is_favorite);
```

### Existing Tables - No Changes:
- ✅ `assignments` - Ready to use
- ✅ `focus_sessions` - Ready to use (has `subject` column now)
- ✅ `goals` - Ready to use (has `target_date` now)
- ✅ `subjects` - Ready to use
- ✅ `achievements` - Ready to use

---

## Total Estimates

| View | Lines | Sessions | Difficulty | Priority | Database Ready? |
|------|-------|----------|------------|----------|----------------|
| Assignments | 3,500 | 1 | Medium | HIGH | ✅ Yes |
| Study Timer | 2,800 | 1 | Medium | HIGH | ✅ Yes |
| Notes | 2,500 | 1 | Medium | MEDIUM | ⚠️ Need table |
| Calendar | 2,200 | 1 | Medium | MEDIUM | ✅ Yes |
| AI Tools | 2,000 | 0.5-1 | Low | LOW | ✅ Yes |
| **TOTAL** | **13,000** | **4.5-5** | - | - | - |

---

## Success Criteria

Each view will be considered complete when:
1. ✅ All core features implemented
2. ✅ CRUD operations working
3. ✅ Integration with existing systems tested
4. ✅ UI is responsive and polished
5. ✅ Database queries optimized
6. ✅ No errors in logs
7. ✅ User can complete real workflows

---

## Next Steps

**Immediate Action:**
1. Review this plan
2. Approve build order
3. Start Phase 2: Assignments View

**Questions for You:**
1. Do you approve this order? (Assignments → Timer → Notes → Calendar → AI Tools)
2. Any features you want to add/remove from each view?
3. Should we build all 5 or prioritize just the top 3?

Let me know and we'll start building! 🚀
