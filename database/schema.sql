-- ============================================
-- ACADEMIC COMMAND CENTER - DATABASE SCHEMA
-- SQLite Database Schema
-- Version: 1.0.0
-- ============================================

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode = WAL;

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT,
    avatar_path TEXT,
    theme_preference TEXT DEFAULT 'light',  -- light, dark
    language_preference TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    settings_json TEXT,  -- JSON blob for user preferences
    is_active BOOLEAN DEFAULT 1
);

-- ============================================
-- USER API KEYS TABLE (Encrypted)
-- ============================================
CREATE TABLE IF NOT EXISTS user_api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,  -- gemini, groq, deepseek, openrouter, cohere, canvas
    api_key_encrypted BLOB NOT NULL,  -- Encrypted API key
    api_key_iv BLOB NOT NULL,  -- Initialization vector for encryption
    display_name TEXT,  -- User-friendly name
    is_enabled BOOLEAN DEFAULT 1,
    daily_request_limit INTEGER DEFAULT 1000,
    current_daily_requests INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP,
    verification_status TEXT DEFAULT 'pending',  -- pending, verified, failed
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, provider)
);

-- ============================================
-- ESSAYS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS essays (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    canvas_assignment_id TEXT,

    -- Basic Info
    title TEXT NOT NULL,
    raw_instructions TEXT NOT NULL,
    course_name TEXT,
    course_code TEXT,

    -- Requirements
    word_count_min INTEGER,
    word_count_max INTEGER,
    required_sources_min INTEGER,
    required_sources_max INTEGER,
    citation_style TEXT,  -- Harvard, APA, MLA
    due_date TIMESTAMP,
    week_number INTEGER,

    -- AI-Parsed Data (JSON)
    extracted_requirements TEXT,  -- JSON array of requirement objects
    key_concepts TEXT,  -- JSON array of concept strings
    task_verbs TEXT,  -- JSON array of verb strings
    implicit_structure TEXT,  -- JSON object with structure
    rubric_criteria TEXT,  -- JSON object with rubric checklist
    knowledge_gaps TEXT,  -- JSON array of missing concepts

    -- Progress
    status TEXT DEFAULT 'not_started',  -- not_started, researching, planning, writing, editing, completed, submitted
    current_word_count INTEGER DEFAULT 0,
    completion_percentage REAL DEFAULT 0.0,

    -- Grades & Feedback
    submitted_date TIMESTAMP,
    grade_received REAL,
    grade_letter TEXT,
    tutor_feedback TEXT,
    tutor_feedback_json TEXT,  -- Structured feedback

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_worked_on TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_essays_user_status ON essays(user_id, status);
CREATE INDEX IF NOT EXISTS idx_essays_due_date ON essays(due_date);
CREATE INDEX IF NOT EXISTS idx_essays_canvas_id ON essays(canvas_assignment_id);

-- ============================================
-- TASKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Task Details
    title TEXT NOT NULL,
    description TEXT,
    task_type TEXT NOT NULL,  -- research, planning, writing, editing, citation, formatting, submission
    section_name TEXT,  -- Which essay section this relates to

    -- Ordering & Dependencies
    order_index INTEGER NOT NULL,
    depends_on_task_ids TEXT,  -- JSON array of task IDs
    blocks_task_ids TEXT,  -- JSON array of tasks that can't start until this is done

    -- Time Estimation
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    time_estimate_confidence TEXT DEFAULT 'low',  -- low, medium, high

    -- Priority
    priority_score REAL DEFAULT 0.5,
    urgency_factor REAL,
    impact_factor REAL,
    difficulty_factor REAL,

    -- Rubric Alignment
    rubric_criteria_addressed TEXT,  -- JSON array of rubric criterion names

    -- Target Metrics
    target_word_count INTEGER,
    target_source_count INTEGER,

    -- Status
    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, skipped, blocked
    completed_at TIMESTAMP,
    skipped_reason TEXT,

    -- Verification
    verification_question TEXT,
    verification_answer TEXT,
    verified BOOLEAN DEFAULT 0,

    -- Output
    output_description TEXT,
    output_location TEXT,  -- File path or reference

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_for DATE,

    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_essay ON tasks(essay_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_order ON tasks(essay_id, order_index);

-- ============================================
-- MATERIALS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS materials (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- File Info
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- pdf, docx, pptx, txt, jpg, png
    file_size_bytes INTEGER,
    file_path TEXT NOT NULL,  -- Local path or cloud URL
    file_hash TEXT,  -- SHA256 hash for duplicate detection

    -- Extracted Content
    extracted_text TEXT,
    extracted_text_length INTEGER,
    page_count INTEGER,

    -- AI Analysis
    content_summary TEXT,
    key_concepts TEXT,  -- JSON array
    topic_tags TEXT,  -- JSON array
    material_type TEXT,  -- lecture_notes, reading, textbook_chapter, handout, diagram
    subject_area TEXT,
    difficulty_level TEXT,  -- introductory, intermediate, advanced

    -- Organization
    week_number INTEGER,
    module_name TEXT,
    course_name TEXT,
    custom_tags TEXT,  -- JSON array of user-added tags

    -- Search
    search_embedding BLOB,  -- Vector embedding for semantic search (optional)

    -- Metadata
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_materials_user ON materials(user_id);
CREATE INDEX IF NOT EXISTS idx_materials_type ON materials(material_type);
CREATE INDEX IF NOT EXISTS idx_materials_week ON materials(week_number);
CREATE INDEX IF NOT EXISTS idx_materials_hash ON materials(file_hash);

-- Full-text search for materials
CREATE VIRTUAL TABLE IF NOT EXISTS materials_fts USING fts5(
    material_id,
    file_name,
    extracted_text,
    content_summary,
    key_concepts,
    content='materials',
    content_rowid='rowid'
);

-- ============================================
-- MATERIAL LINKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS material_links (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    material_id TEXT NOT NULL,

    -- Relevance
    relevance_score REAL DEFAULT 0.5,
    why_relevant TEXT,
    linked_by TEXT DEFAULT 'auto',  -- auto, manual

    -- Usage Tracking
    times_referenced INTEGER DEFAULT 0,
    specific_pages TEXT,  -- JSON array of page numbers used
    quotes_extracted TEXT,  -- JSON array of quotes

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,

    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
    UNIQUE(essay_id, material_id)
);

-- ============================================
-- FOCUS SESSIONS TABLE (Phase 3 Pomodoro)
-- ============================================
CREATE TABLE IF NOT EXISTS focus_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    task_id TEXT,
    essay_id TEXT,

    -- Session Details (Pomodoro)
    session_type TEXT NOT NULL,  -- work, short_break, long_break
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    completed BOOLEAN DEFAULT 1,

    -- Focus Metrics
    interruptions INTEGER DEFAULT 0,
    focus_score REAL DEFAULT 100.0,

    -- Legacy fields (optional)
    planned_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    words_written INTEGER DEFAULT 0,
    sources_found INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    distractions_count INTEGER DEFAULT 0,
    distraction_details TEXT,
    focus_quality INTEGER,
    energy_level_before INTEGER,
    energy_level_after INTEGER,
    time_of_day TIME,
    day_of_week INTEGER,
    distractions_blocked BOOLEAN DEFAULT 0,
    blocked_sites TEXT,
    session_notes TEXT,
    what_accomplished TEXT,
    abandoned_reason TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_focus_user ON focus_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_focus_task ON focus_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_focus_date ON focus_sessions(started_at);

-- ============================================
-- PROGRESS LOGS TABLE (Phase 3 Daily Progress)
-- ============================================
CREATE TABLE IF NOT EXISTS progress_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    essay_id TEXT,
    task_id TEXT,

    -- Daily Metrics
    focus_sessions INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    productivity_score REAL DEFAULT 0.0,
    tasks_completed INTEGER DEFAULT 0,

    -- Legacy Event Details
    event_type TEXT,
    event_description TEXT,
    event_data TEXT,
    total_words_count INTEGER,
    completion_percentage REAL,
    tasks_completed_count INTEGER,
    tasks_remaining_count INTEGER,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE SET NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    UNIQUE(user_id, date)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_progress_user_date ON progress_logs(user_id, created_at);

-- ============================================
-- GOALS TABLE (Phase 3 Progress Tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Goal Details
    title TEXT NOT NULL,
    description TEXT,
    goal_type TEXT NOT NULL,  -- daily, weekly, monthly, semester, custom

    -- Metrics
    metric TEXT NOT NULL,  -- sessions, tasks, minutes, essays
    target_value INTEGER NOT NULL,
    current_value INTEGER DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'not_started',  -- not_started, in_progress, completed, failed
    deadline TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_deadline ON goals(deadline);

-- ============================================
-- AI INTERACTIONS TABLE (Caching & Tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS ai_interactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Request Details
    task_type TEXT NOT NULL,  -- parse_essay, generate_tasks, analyze_material, etc.
    provider TEXT NOT NULL,  -- gemini, groq, deepseek, openrouter
    model TEXT,

    -- Prompt & Response
    prompt_text TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,  -- For cache key
    response_text TEXT,
    response_json TEXT,  -- Structured response

    -- Metadata
    tokens_used INTEGER,
    estimated_cost_usd REAL,
    response_time_ms INTEGER,

    -- Caching
    cache_key TEXT UNIQUE,
    cache_expires_at TIMESTAMP,
    cache_hit BOOLEAN DEFAULT 0,

    -- Status
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    fallback_used BOOLEAN DEFAULT 0,

    -- Context
    essay_id TEXT,
    task_id TEXT,
    material_id TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE SET NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ai_cache_key ON ai_interactions(cache_key);
CREATE INDEX IF NOT EXISTS idx_ai_user_date ON ai_interactions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_ai_provider ON ai_interactions(provider);

-- ============================================
-- CANVAS SYNC LOG TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS canvas_sync_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Sync Details
    sync_type TEXT NOT NULL,  -- full, incremental, manual
    sync_status TEXT NOT NULL,  -- in_progress, completed, failed

    -- Stats
    assignments_synced INTEGER DEFAULT 0,
    files_downloaded INTEGER DEFAULT 0,
    rubrics_synced INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Details
    error_details TEXT,  -- JSON array of errors
    sync_summary TEXT,  -- Human-readable summary

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_canvas_sync_user ON canvas_sync_log(user_id);

-- ============================================
-- SOURCES TABLE (Citation Management)
-- ============================================
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    essay_id TEXT,
    material_id TEXT,  -- Link to uploaded material if applicable

    -- Citation Details
    source_type TEXT NOT NULL,  -- book, journal_article, website, lecture, other
    author TEXT,
    year INTEGER,
    title TEXT NOT NULL,
    publication TEXT,
    publisher TEXT,
    pages TEXT,
    url TEXT,
    doi TEXT,
    access_date DATE,

    -- Citation Formats (Pre-generated)
    citation_harvard TEXT,
    citation_apa TEXT,
    citation_mla TEXT,

    -- Usage
    times_cited INTEGER DEFAULT 0,
    specific_quotes TEXT,  -- JSON array of quotes with page numbers

    -- Notes
    notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE SET NULL,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE SET NULL
);

-- ============================================
-- WRITING SNAPSHOTS TABLE (Version History)
-- ============================================
CREATE TABLE IF NOT EXISTS writing_snapshots (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Content
    content_text TEXT NOT NULL,
    content_html TEXT,
    word_count INTEGER,

    -- Snapshot Details
    snapshot_type TEXT DEFAULT 'auto',  -- auto, manual, before_major_edit
    snapshot_label TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_snapshots_essay ON writing_snapshots(essay_id, created_at);

-- ============================================
-- ANALYTICS CACHE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_cache (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Cache Details
    metric_name TEXT NOT NULL,
    metric_value TEXT NOT NULL,  -- JSON blob
    time_period TEXT,  -- daily, weekly, monthly

    -- Validity
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, metric_name, time_period)
);

-- ============================================
-- SYSTEM HEALTH TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS system_health (
    id TEXT PRIMARY KEY,
    check_type TEXT NOT NULL,  -- database, api, storage, performance
    status TEXT NOT NULL,  -- healthy, warning, error
    details TEXT,  -- JSON blob
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- APP SETTINGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT OR IGNORE INTO app_settings (key, value, description) VALUES
    ('schema_version', '1.0.0', 'Database schema version'),
    ('installation_date', datetime('now'), 'When app was first installed'),
    ('data_retention_days', '365', 'How long to keep old data'),
    ('auto_backup_enabled', '1', 'Enable automatic backups'),
    ('backup_frequency_hours', '24', 'Backup frequency'),
    ('theme', 'light', 'Default theme'),
    ('language', 'en', 'Default language');

-- ============================================
-- EXPORT HISTORY TABLE (Phase 6)
-- ============================================
CREATE TABLE IF NOT EXISTS export_history (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    essay_id TEXT NOT NULL,

    -- Export Details
    format TEXT NOT NULL,  -- docx, pdf, latex, markdown, html, txt
    template TEXT,  -- apa, mla, chicago, harvard, generic
    file_path TEXT NOT NULL,
    file_size INTEGER,

    -- Metadata
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_export_history_user ON export_history(user_id, exported_at);
CREATE INDEX IF NOT EXISTS idx_export_history_essay ON export_history(essay_id, exported_at);

-- ============================================
-- TRIGGERS
-- ============================================

-- Update essay updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_essay_timestamp
AFTER UPDATE ON essays
BEGIN
    UPDATE essays SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update task updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_task_timestamp
AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update essay last_worked_on when task is updated
CREATE TRIGGER IF NOT EXISTS update_essay_last_worked
AFTER UPDATE ON tasks
WHEN NEW.status != OLD.status
BEGIN
    UPDATE essays SET last_worked_on = CURRENT_TIMESTAMP WHERE id = NEW.essay_id;
END;

-- Reset daily API request counts
CREATE TRIGGER IF NOT EXISTS reset_api_daily_counts
AFTER UPDATE ON user_api_keys
WHEN NEW.last_reset_date < CURRENT_DATE
BEGIN
    UPDATE user_api_keys
    SET current_daily_requests = 0, last_reset_date = CURRENT_DATE
    WHERE id = NEW.id;
END;

-- ============================================
-- VIEWS (Useful Queries)
-- ============================================

-- Active essays with progress
CREATE VIEW IF NOT EXISTS v_active_essays AS
SELECT
    e.id,
    e.user_id,
    e.title,
    e.due_date,
    e.status,
    e.completion_percentage,
    e.current_word_count,
    e.word_count_max,
    COUNT(t.id) as total_tasks,
    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
    julianday(e.due_date) - julianday('now') as days_until_due
FROM essays e
LEFT JOIN tasks t ON e.id = t.essay_id
WHERE e.status NOT IN ('completed', 'submitted')
GROUP BY e.id;

-- User productivity stats
CREATE VIEW IF NOT EXISTS v_user_productivity AS
SELECT
    user_id,
    DATE(started_at) as session_date,
    COUNT(*) as session_count,
    SUM(actual_duration_minutes) as total_minutes,
    AVG(focus_quality) as avg_focus_quality,
    SUM(words_written) as total_words,
    SUM(distractions_count) as total_distractions
FROM focus_sessions
WHERE completed = 1
GROUP BY user_id, DATE(started_at);

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
SELECT 'Database schema created successfully!' as message;
