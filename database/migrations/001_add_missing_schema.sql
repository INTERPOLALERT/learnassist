-- ============================================
-- Migration: Add Missing Tables and Columns
-- Date: 2025-11-12
-- Description: Fixes schema mismatches between database and code
-- ============================================

-- Add subject column to focus_sessions
ALTER TABLE focus_sessions ADD COLUMN subject TEXT;

-- Update goals table structure
ALTER TABLE goals ADD COLUMN category TEXT DEFAULT 'short_term';
ALTER TABLE goals ADD COLUMN target_date DATE;
ALTER TABLE goals ADD COLUMN start_date DATE;
ALTER TABLE goals ADD COLUMN unit TEXT;
ALTER TABLE goals ADD COLUMN is_smart BOOLEAN DEFAULT 0;

-- Migrate existing deadline to target_date
UPDATE goals SET target_date = date(deadline) WHERE deadline IS NOT NULL;

-- Create assignments table (alias to tasks with extended columns)
CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    subject_id TEXT,

    -- Assignment Details
    title TEXT NOT NULL,
    description TEXT,
    assignment_type TEXT,  -- homework, quiz, exam, project

    -- Dates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    submitted_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Status & Progress
    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, submitted
    priority TEXT DEFAULT 'medium',  -- low, medium, high
    completion_percentage REAL DEFAULT 0.0,

    -- Grading
    grade REAL,
    max_grade REAL DEFAULT 100.0,
    grade_letter TEXT,

    -- Canvas Integration
    canvas_assignment_id TEXT,
    canvas_course_id TEXT,

    -- Notes
    notes TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
);

-- Create subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Subject Details
    name TEXT NOT NULL,
    code TEXT,  -- e.g., CS101
    description TEXT,
    color TEXT DEFAULT '#3498db',  -- Hex color for UI
    icon TEXT,  -- Emoji or icon name

    -- Semester Info
    semester TEXT,
    year INTEGER,

    -- Professor/Instructor
    instructor_name TEXT,
    instructor_email TEXT,

    -- Schedule
    schedule_days TEXT,  -- JSON array: ["Mon", "Wed", "Fri"]
    schedule_time TEXT,  -- e.g., "10:00-11:30"
    location TEXT,

    -- Canvas Integration
    canvas_course_id TEXT,

    -- Status
    is_active BOOLEAN DEFAULT 1,
    is_favorite BOOLEAN DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, name, semester, year)
);

-- Create achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Achievement Details
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,  -- study, writing, goals, consistency

    -- Badge/Icon
    icon TEXT,  -- Emoji or icon name
    color TEXT DEFAULT '#f39c12',  -- Hex color

    -- Points & Level
    points INTEGER DEFAULT 0,
    tier TEXT DEFAULT 'bronze',  -- bronze, silver, gold, platinum

    -- Unlock Criteria
    criteria_type TEXT,  -- sessions_count, study_hours, streak_days, etc.
    criteria_target INTEGER,

    -- Progress
    current_progress INTEGER DEFAULT 0,
    is_unlocked BOOLEAN DEFAULT 0,
    unlocked_at TIMESTAMP,

    -- Display
    display_order INTEGER DEFAULT 0,
    is_hidden BOOLEAN DEFAULT 0,  -- Secret achievements

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, name)
);

-- Create indexes for new tables
CREATE INDEX IF NOT EXISTS idx_assignments_user ON assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_subject ON assignments(subject_id);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date);
CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments(status);

CREATE INDEX IF NOT EXISTS idx_subjects_user ON subjects(user_id);
CREATE INDEX IF NOT EXISTS idx_subjects_active ON subjects(is_active);

CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_achievements_unlocked ON achievements(is_unlocked);

-- Seed some default achievements
INSERT OR IGNORE INTO achievements (id, user_id, name, description, category, icon, points, tier, criteria_type, criteria_target, current_progress)
VALUES
    ('ach_first_steps', 'default_user', 'First Steps', 'Started using Academic Command Center', 'general', '👣', 10, 'bronze', 'app_opened', 1, 1),
    ('ach_study_warrior', 'default_user', 'Study Warrior', 'Complete 10 study sessions', 'study', '⚔️', 50, 'silver', 'sessions_count', 10, 0),
    ('ach_consistent_learner', 'default_user', 'Consistent Learner', 'Study for 7 days in a row', 'consistency', '📅', 100, 'gold', 'streak_days', 7, 0),
    ('ach_time_master', 'default_user', 'Time Master', 'Study for 50 hours total', 'study', '⏰', 200, 'gold', 'study_hours', 50, 0),
    ('ach_goal_crusher', 'default_user', 'Goal Crusher', 'Complete 5 goals', 'goals', '🎯', 75, 'silver', 'goals_completed', 5, 0);

-- Unlock the "First Steps" achievement
UPDATE achievements SET is_unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
WHERE user_id = 'default_user' AND name = 'First Steps';
