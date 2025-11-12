# PHASE 5 - EXTENDED FEATURES DEVELOPMENT PLAN

**Project**: Academic Command Center
**Phase**: Phase 5 - Extended Features
**Status**: 🚀 **READY TO START**
**Scope**: ALL 5 feature categories
**Estimated Code**: ~12,000 lines across 35+ components
**Timeline**: 4-6 weeks

---

## PHASE 5 OBJECTIVES

Build advanced features that take the Academic Command Center beyond the original scope, transforming it into a comprehensive academic productivity suite.

### Key Goals

1. **Enable Export**: Students can submit work in any required format (DOCX, PDF, LaTeX, Markdown)
2. **Enhance AI**: Intelligent assistance for research, outlining, and paraphrasing
3. **Enable Collaboration**: Work across devices with cloud sync and peer collaboration
4. **Provide Insights**: Predictive analytics, grade prediction, and smart notifications
5. **Ensure Quality**: Plagiarism checking, readability optimization, and academic tone analysis

---

## SPRINT OVERVIEW

| Sprint | Category | Modules | Lines | Days |
|--------|----------|---------|-------|------|
| Sprint 1 | Export & Integration | 6 | ~2,400 | 3-4 |
| Sprint 2 | Advanced AI Features | 6 | ~2,200 | 3-4 |
| Sprint 3 | Productivity & Insights | 5 | ~2,800 | 3-5 |
| Sprint 4 | Writing Quality | 5 | ~2,400 | 3-4 |
| Sprint 5 | Collaboration & Sync | 6 | ~2,200 | 4-5 |
| **Total** | **5 categories** | **28+** | **~12,000** | **16-22** |

---

## SPRINT 1: EXPORT & INTEGRATION FEATURES

**Priority**: HIGH (Students need to submit work)
**Estimated**: 2,400 lines, 3-4 days

### Module 1.1: Export Manager (`export_manager.py` - 450 lines)

**Purpose**: Central export coordination

**Features**:
- Export essays to multiple formats
- Template management (APA, MLA, Chicago)
- Format validation
- Export history tracking
- Batch export support

**Key Methods**:
```python
def export_essay(essay_id, format, template=None, options={}):
    # Coordinates export to specified format
    # Returns: {'success': bool, 'file_path': str, 'format': str}

def get_available_templates(format):
    # Returns available templates for format

def validate_export(content, format):
    # Pre-export validation
```

**Export Formats Supported**:
- DOCX (Microsoft Word)
- PDF (styled, professional)
- LaTeX (academic submissions)
- Markdown (GitHub, web publishing)
- HTML (web preview)
- Plain text

---

### Module 1.2: DOCX Exporter (`docx_exporter.py` - 400 lines)

**Purpose**: Export to Microsoft Word format

**Features**:
- Full formatting (headings, paragraphs, lists)
- Citation formatting
- Cover page generation
- Header/footer support
- Page numbering
- Table of contents generation
- Track changes compatible

**Dependencies**: `python-docx`

**Template Support**:
- APA 7th edition
- MLA 9th edition
- Chicago 17th edition
- Custom templates

**Key Methods**:
```python
def export_to_docx(essay_data, template='apa', options={}):
    # Create styled DOCX file
    # Returns file path

def apply_template(doc, template_name):
    # Apply formatting template

def generate_cover_page(doc, essay_metadata):
    # Create formatted cover page
```

---

### Module 1.3: PDF Exporter (`pdf_exporter.py` - 350 lines)

**Purpose**: Export to PDF with professional styling

**Features**:
- High-quality PDF generation
- Custom fonts and styling
- Embedded citations
- Bookmarks for sections
- Metadata (title, author, keywords)
- Page margins and layout

**Dependencies**: `reportlab` or `weasyprint`

**Key Methods**:
```python
def export_to_pdf(essay_data, template='apa', options={}):
    # Generate styled PDF
    # Returns file path

def add_watermark(pdf_path, watermark_text):
    # Add draft watermark (optional)
```

---

### Module 1.4: LaTeX Exporter (`latex_exporter.py` - 350 lines)

**Purpose**: Export to LaTeX for academic submissions

**Features**:
- LaTeX document generation
- BibTeX citation support
- Academic journal templates
- Math equation support
- Figure and table formatting

**Templates**:
- IEEE conference papers
- ACM format
- LNCS (Springer)
- Generic article
- Custom preambles

**Key Methods**:
```python
def export_to_latex(essay_data, template='article', options={}):
    # Generate LaTeX source
    # Returns .tex file path

def generate_bibtex(sources):
    # Create BibTeX file from sources
```

---

### Module 1.5: LMS Integration Manager (`lms_integration_manager.py` - 450 lines)

**Purpose**: Integrate with multiple LMS platforms

**Features**:
- Unified LMS interface
- Plugin architecture for platforms
- Assignment sync across platforms
- Grade aggregation
- Submission tracking

**Supported Platforms**:
- Canvas LMS (already integrated)
- Blackboard Learn
- Moodle
- Google Classroom
- D2L/Brightspace

**Key Methods**:
```python
def register_lms_plugin(platform_name, plugin_class):
    # Add new LMS platform

def sync_assignments(platform, course_id):
    # Sync assignments from platform

def submit_essay(essay_id, platform, assignment_id):
    # Submit to LMS
```

---

### Module 1.6: Export View UI (`export_view.py` - 400 lines)

**Purpose**: User interface for export operations

**Features**:
- Format selector (DOCX, PDF, LaTeX, Markdown)
- Template chooser
- Export options configuration
- Preview before export
- Export history
- Batch export UI

**UI Layout**:
```
┌─────────────────────────────────────┐
│   Export Essay                      │
├─────────────────────────────────────┤
│  Essay: [Cultural Analysis ▼]      │
│  Format: [DOCX ▼]                   │
│  Template: [APA 7th ▼]              │
│                                     │
│  Options:                           │
│  ☑ Include cover page               │
│  ☑ Include table of contents        │
│  ☑ Include citations                │
│  ☐ Add page numbers                 │
│                                     │
│  [Preview] [Export]                 │
│                                     │
│  Recent Exports:                    │
│  • essay1.docx (APA) - 2 hours ago │
│  • essay2.pdf (MLA) - Yesterday    │
└─────────────────────────────────────┘
```

---

## SPRINT 2: ADVANCED AI FEATURES

**Priority**: HIGH (Enhances core functionality)
**Estimated**: 2,200 lines, 3-4 days

### Module 2.1: Outline Generator (`outline_generator.py` - 400 lines)

**Purpose**: AI-powered essay outline generation

**Features**:
- Generate outlines from assignment instructions
- Multi-level structure (I, A, 1, a)
- Section recommendations
- Research question suggestions
- Source recommendations
- Time estimates per section

**AI Provider**: Gemini or Claude

**Key Methods**:
```python
def generate_outline(essay_id, style='hierarchical'):
    # Generate outline from requirements
    # Returns: {'sections': [...], 'research_questions': [...]}

def suggest_section_structure(topic, word_count):
    # Recommend section breakdown
```

**Outline Styles**:
- Hierarchical (I, A, 1, a)
- Topic sentence outlines
- Thesis-driven outlines
- Argument-based outlines

---

### Module 2.2: Research Assistant (`research_assistant.py` - 450 lines)

**Purpose**: AI-powered research guidance

**Features**:
- Generate search queries for topics
- Suggest research directions
- Extract key quotes from materials
- Identify connections between sources
- Recommend additional sources
- Create research summaries

**Key Methods**:
```python
def generate_search_queries(topic, requirements):
    # Create effective search queries
    # Returns: ['query1', 'query2', ...]

def extract_key_quotes(material_id, topic):
    # Find relevant quotes in material

def suggest_connections(source_ids):
    # Identify relationships between sources

def generate_research_summary(material_ids):
    # Create comprehensive research summary
```

**AI Integration**:
- Uses uploaded materials for context
- Queries AI for recommendations
- Caches results for performance

---

### Module 2.3: Paraphrasing Tool (`paraphrase_tool.py` - 350 lines)

**Purpose**: AI-powered paraphrasing and rewriting

**Features**:
- Rephrase sentences/paragraphs
- Maintain original meaning
- Improve academic tone
- Multiple rephrase options
- Citation preservation
- Plagiarism risk assessment

**Key Methods**:
```python
def paraphrase_text(text, style='academic', options={}):
    # Rephrase text while maintaining meaning
    # Returns: {'original': str, 'paraphrased': [str, str, str]}

def improve_tone(text):
    # Make more academic/formal
```

**Paraphrase Styles**:
- Academic (formal, scholarly)
- Simplified (easier to understand)
- Expanded (more detail)
- Condensed (more concise)

**Safety Features**:
- Original always preserved
- Multiple options shown
- User selects preferred version
- Not a plagiarism enabler - used for legitimate rewriting

---

### Module 2.4: Material Summarizer (`material_summarizer.py` - 350 lines)

**Purpose**: AI-powered document summarization

**Features**:
- Automatic summaries of uploaded materials
- Key points extraction
- Quote identification
- Concept mapping
- Multi-document synthesis

**Key Methods**:
```python
def summarize_material(material_id, length='medium'):
    # Create summary of material
    # Returns: {'summary': str, 'key_points': [...], 'quotes': [...]}

def extract_key_concepts(material_id):
    # Identify main concepts

def synthesize_materials(material_ids, topic):
    # Combine multiple materials on topic
```

**Summary Lengths**:
- Brief (2-3 sentences)
- Medium (1 paragraph)
- Detailed (multiple paragraphs with structure)

---

### Module 2.5: AI Assistant Manager (`ai_assistant_manager.py` - 350 lines)

**Purpose**: Central coordinator for AI features

**Features**:
- Route requests to appropriate AI
- Manage AI conversations
- Context management
- Cost tracking per feature
- Usage quotas and limits

**Key Methods**:
```python
def execute_ai_task(task_type, payload, user_id):
    # Route to appropriate AI function
    # Returns result with cost tracking

def get_ai_usage_stats(user_id, date_range):
    # Track AI feature usage and costs
```

---

### Module 2.6: AI Assistant View UI (`ai_assistant_view.py` - 300 lines)

**Purpose**: User interface for AI tools

**Features**:
- Outline generator interface
- Research assistant panel
- Paraphrasing tool
- Summarization interface
- AI chat for questions

**UI Sections**:
- Outline Generator tab
- Research Assistant tab
- Paraphrasing Tool tab
- Material Summarizer tab
- AI Chat tab

---

## SPRINT 3: PRODUCTIVITY & INSIGHTS

**Priority**: MEDIUM (Enhances analytics)
**Estimated**: 2,800 lines, 3-5 days

### Module 3.1: Grade Predictor (`grade_predictor.py` - 500 lines)

**Purpose**: Predict essay grades before submission

**Features**:
- Rubric compliance analysis
- Historical grade correlation
- Weakness identification
- Improvement recommendations
- Confidence score

**Prediction Factors**:
- Word count vs requirement
- Source count vs requirement
- Rubric item completion
- Grammar/style scores
- Historical performance
- Time spent on essay

**Key Methods**:
```python
def predict_grade(essay_id):
    # Predict grade based on multiple factors
    # Returns: {
    #   'predicted_grade': float,
    #   'confidence': float,
    #   'rubric_coverage': {...},
    #   'weaknesses': [...],
    #   'recommendations': [...]
    # }

def analyze_rubric_compliance(essay_id):
    # Check rubric item completion

def identify_weaknesses(essay_id):
    # Find areas needing improvement
```

---

### Module 3.2: Advanced Analytics Engine (`advanced_analytics.py` - 600 lines)

**Purpose**: Extended analytics beyond Phase 3

**New Metrics**:
- Writing velocity (words/hour by section)
- Productivity by hour of day (heatmap)
- Task completion patterns
- Procrastination detection
- Deadline pressure correlation
- Quality vs time spent analysis

**Key Methods**:
```python
def calculate_writing_velocity(essay_id):
    # Words per hour by section

def generate_productivity_heatmap(user_id, days=30):
    # Hour/day productivity matrix

def detect_procrastination_patterns(user_id):
    # Identify late-start tendencies

def analyze_quality_vs_time(user_id):
    # Correlation between time spent and grades
```

**Insights Generated**:
- "You write 30% faster in the morning"
- "You start 80% of essays within 2 days of deadline"
- "Essays with 5+ days work time average 7% higher grades"

---

### Module 3.3: Notification Manager (`notification_manager.py` - 450 lines)

**Purpose**: Smart notifications and reminders

**Features**:
- Deadline reminders (configurable)
- Task overdue alerts
- Canvas grade posted notifications
- Daily/weekly progress summaries
- Milestone celebrations
- Custom notification rules

**Notification Types**:
- Desktop notifications (Windows toast)
- Email notifications (optional)
- In-app notifications
- Calendar integration

**Smart Timing**:
- 7 days before deadline
- 3 days before deadline
- 1 day before deadline
- 12 hours before deadline
- 2 hours before deadline

**Key Methods**:
```python
def schedule_notification(event_type, trigger_time, message, options={}):
    # Schedule future notification

def send_notification(notification_id):
    # Deliver notification via channels

def get_notification_history(user_id):
    # Retrieve sent notifications
```

---

### Module 3.4: Deadline Predictor (`deadline_predictor.py` - 400 lines)

**Purpose**: Predict if deadlines will be met

**Features**:
- Completion time estimation
- Deadline risk assessment
- Recommended work schedule
- Progress tracking against prediction
- Alert if falling behind

**Prediction Factors**:
- Tasks remaining
- Average task completion time
- Available days
- Historical productivity
- Current velocity

**Key Methods**:
```python
def predict_completion_date(essay_id):
    # Estimate finish date
    # Returns: {
    #   'estimated_completion': date,
    #   'deadline': date,
    #   'risk_level': str,  # low, medium, high
    #   'recommended_schedule': [...]
    # }

def calculate_deadline_risk(essay_id):
    # Assess likelihood of meeting deadline
```

**Risk Levels**:
- **Low**: On track, 3+ days buffer
- **Medium**: Tight timeline, 1-2 days buffer
- **High**: Behind schedule, needs acceleration

---

### Module 3.5: Productivity Insights View UI (`productivity_insights_view.py` - 850 lines)

**Purpose**: Enhanced analytics UI

**New Visualizations**:
- Writing velocity chart (words/hour over time)
- Productivity heatmap (GitHub-style calendar)
- Grade prediction dashboard
- Deadline risk indicators
- Quality vs time scatter plot
- Procrastination patterns

**Interactive Features**:
- Drill down into specific days
- Filter by essay or task type
- Export insights as images
- Share insights (screenshots)

---

## SPRINT 4: WRITING QUALITY FEATURES

**Priority**: MEDIUM (Direct quality improvement)
**Estimated**: 2,400 lines, 3-4 days

### Module 4.1: Plagiarism Checker (`plagiarism_checker.py` - 550 lines)

**Purpose**: Detect potential plagiarism issues

**Features**:
- Check against uploaded sources
- Detect improper paraphrasing
- Citation coverage analysis
- Originality percentage
- Highlight suspicious passages
- Suggest citations

**Checking Methods**:
- Exact match detection
- Fuzzy match detection
- Paraphrase detection (AI-assisted)
- Citation verification

**Key Methods**:
```python
def check_plagiarism(essay_id):
    # Check essay against sources
    # Returns: {
    #   'originality_score': float,  # 0-100%
    #   'matches': [...],
    #   'citation_coverage': float,
    #   'suggestions': [...]
    # }

def detect_matches(text, source_ids):
    # Find text matches in sources

def verify_citations(essay_id):
    # Check if all quotes are cited
```

**Safety & Ethics**:
- Local checking only (privacy)
- Educational tool, not enforcement
- Helps students learn proper citation
- Encourages academic integrity

---

### Module 4.2: Readability Optimizer (`readability_optimizer.py` - 400 lines)

**Purpose**: Improve text readability

**Features**:
- Sentence complexity analysis
- Suggest simpler alternatives
- Flag overly long sentences (25+ words)
- Identify difficult words
- Vocabulary level indicator
- Grade level assessment

**Key Methods**:
```python
def analyze_readability(text):
    # Comprehensive readability analysis
    # Returns: {
    #   'flesch_reading_ease': float,
    #   'grade_level': float,
    #   'complex_sentences': [...],
    #   'difficult_words': [...],
    #   'suggestions': [...]
    # }

def suggest_simplifications(sentence):
    # Propose simpler alternatives

def assess_vocabulary_level(text):
    # Determine vocabulary complexity
```

**Readability Scores**:
- Flesch Reading Ease
- Flesch-Kincaid Grade Level
- Gunning Fog Index
- SMOG Index

---

### Module 4.3: Academic Tone Checker (`academic_tone_checker.py` - 450 lines)

**Purpose**: Ensure academic tone and style

**Features**:
- Detect informal language
- Flag personal pronouns (I, we, you)
- Identify colloquialisms
- Suggest formal alternatives
- Check hedging language (may, might, could)
- Verify academic vocabulary

**Checks Performed**:
- Informality detection
- Personal pronoun usage
- Contractions (don't → do not)
- Slang and colloquialisms
- Emotional language
- Hedge words (appropriate use)

**Key Methods**:
```python
def check_academic_tone(text):
    # Analyze academic appropriateness
    # Returns: {
    #   'tone_score': float,  # 0-100
    #   'informal_instances': [...],
    #   'personal_pronouns': [...],
    #   'suggestions': [...]
    # }

def suggest_formal_alternative(informal_phrase):
    # Provide academic alternative
```

---

### Module 4.4: Writing Quality Manager (`writing_quality_manager.py` - 400 lines)

**Purpose**: Coordinate all quality checks

**Features**:
- Run all quality checks at once
- Comprehensive quality report
- Priority ranking of issues
- Track improvements over time
- Quality score calculation

**Key Methods**:
```python
def run_all_checks(essay_id):
    # Execute all quality checks
    # Returns comprehensive report

def calculate_quality_score(essay_id):
    # Overall quality score (0-100)
    # Based on: grammar, style, plagiarism, readability, tone

def generate_quality_report(essay_id):
    # Detailed quality assessment
```

**Quality Score Breakdown**:
- Grammar: 20%
- Style: 20%
- Originality: 20%
- Readability: 20%
- Academic Tone: 20%

---

### Module 4.5: Writing Quality View UI (`writing_quality_view.py` - 600 lines)

**Purpose**: User interface for quality tools

**Features**:
- Plagiarism checker interface
- Readability optimizer panel
- Academic tone checker
- Comprehensive quality dashboard
- Before/after comparisons

**UI Sections**:
```
┌─────────────────────────────────────┐
│   Writing Quality Dashboard         │
├─────────────────────────────────────┤
│  Overall Quality Score: 87/100      │
│  [███████████████░░░]                │
│                                     │
│  Grammar:      92/100 ✓             │
│  Style:        85/100 ⚠             │
│  Originality:  95/100 ✓             │
│  Readability:  78/100 ⚠             │
│  Academic Tone: 84/100 ⚠            │
│                                     │
│  [Run All Checks] [View Report]    │
│                                     │
│  Top Issues:                        │
│  • 3 long sentences (25+ words)    │
│  • 5 instances of personal pronouns│
│  • 2 uncited quotations            │
└─────────────────────────────────────┘
```

---

## SPRINT 5: COLLABORATION & SYNC FEATURES

**Priority**: MEDIUM (Multi-device/collaboration)
**Estimated**: 2,200 lines, 4-5 days

### Module 5.1: Cloud Sync Manager (`cloud_sync_manager.py` - 500 lines)

**Purpose**: Synchronize data across devices

**Features**:
- Cloud storage integration (Google Drive, Dropbox, OneDrive)
- Offline-first architecture
- Conflict resolution
- Selective sync (choose what to sync)
- Sync history and logs
- Bandwidth optimization

**Sync Targets**:
- Essays (content, metadata)
- Tasks (status, progress)
- Materials (files, analysis)
- Settings (preferences, API keys encrypted)
- Focus sessions (history)
- Analytics data

**Key Methods**:
```python
def init_cloud_sync(provider, credentials):
    # Initialize cloud sync

def sync_now(force=False):
    # Trigger immediate sync

def resolve_conflict(local_data, remote_data, strategy='manual'):
    # Handle sync conflicts

def get_sync_status():
    # Current sync state
```

**Conflict Resolution Strategies**:
- Manual (user chooses)
- Latest wins
- Merge (where possible)
- Keep both (create versions)

---

### Module 5.2: Collaboration Manager (`collaboration_manager.py` - 450 lines)

**Purpose**: Enable peer collaboration

**Features**:
- Share essays with peers
- Comment and suggestion system
- Track changes by collaborator
- Permission management (view, comment, edit)
- Collaboration history
- @mention notifications

**Key Methods**:
```python
def share_essay(essay_id, user_email, permission='comment'):
    # Share essay with another user

def add_comment(essay_id, section_id, comment_text, user_id):
    # Add comment to essay section

def add_suggestion(essay_id, selection, suggested_text, user_id):
    # Suggest text change

def accept_suggestion(suggestion_id):
    # Apply suggested change
```

**Permission Levels**:
- View only (read access)
- Comment (view + add comments)
- Suggest (view + add suggestions)
- Edit (full editing access)

---

### Module 5.3: Multi-User Database Manager (`multi_user_db.py` - 400 lines)

**Purpose**: Handle multi-user data management

**Features**:
- User account management
- Essay sharing tables
- Comment/suggestion storage
- Permission tracking
- Activity logs

**New Database Tables**:
```sql
-- Shared essays
CREATE TABLE shared_essays (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    shared_with_user_id TEXT NOT NULL,
    permission_level TEXT NOT NULL,
    shared_at TIMESTAMP NOT NULL,
    FOREIGN KEY (essay_id) REFERENCES essays(id)
);

-- Comments
CREATE TABLE essay_comments (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    section_ref TEXT,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    resolved BOOLEAN DEFAULT 0,
    FOREIGN KEY (essay_id) REFERENCES essays(id)
);

-- Suggestions
CREATE TABLE essay_suggestions (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    selection_start INTEGER NOT NULL,
    selection_end INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    suggested_text TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (essay_id) REFERENCES essays(id)
);
```

---

### Module 5.4: Activity Feed (`activity_feed.py` - 350 lines)

**Purpose**: Track collaboration activity

**Features**:
- Real-time activity feed
- Comment notifications
- Suggestion notifications
- Share notifications
- Activity history

**Key Methods**:
```python
def get_activity_feed(user_id, limit=50):
    # Recent activity for user

def log_activity(activity_type, user_id, essay_id, details):
    # Record activity event
```

---

### Module 5.5: Collaboration View UI (`collaboration_view.py` - 500 lines)

**Purpose**: User interface for collaboration

**Features**:
- Shared essays list
- Comment panel
- Suggestions panel
- Activity feed
- Share dialog
- Permission management UI

**UI Layout**:
```
┌─────────────────────────────────────┐
│   Collaboration                     │
├─────────────────────────────────────┤
│  [My Essays] [Shared with Me]      │
│                                     │
│  Shared with Me:                    │
│  • Essay 1 (Sarah) - Comment       │
│    3 new comments                   │
│  • Essay 2 (John) - View           │
│                                     │
│  My Shared Essays:                  │
│  • Cultural Analysis               │
│    Shared with: Sarah (Edit)       │
│                 John (Comment)      │
│                                     │
│  Activity Feed:                     │
│  • Sarah commented on Essay 1      │
│  • John suggested edit on Essay 2  │
│  • You accepted suggestion         │
└─────────────────────────────────────┘
```

---

## TECHNICAL REQUIREMENTS

### New Dependencies

**Export**:
```
python-docx==1.1.0         # DOCX generation
reportlab==4.0.7           # PDF generation
weasyprint==60.1           # PDF from HTML (alternative)
mistune==3.0.2             # Markdown processing
```

**AI Features**:
```
# No new dependencies - uses existing AI router
```

**Collaboration & Sync**:
```
pydrive2==1.17.0           # Google Drive integration
dropbox==11.36.2           # Dropbox integration
onedrivesdk==1.1.8         # OneDrive integration (if needed)
```

**Quality Checking**:
```
language-tool-python==2.7.1  # Advanced grammar (optional)
textstat==0.7.3              # Readability statistics
```

---

## DATABASE SCHEMA UPDATES

### New Tables (6 tables)

```sql
-- Export history
CREATE TABLE export_history (
    id TEXT PRIMARY KEY,
    essay_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    format TEXT NOT NULL,
    template TEXT,
    file_path TEXT,
    exported_at TIMESTAMP NOT NULL,
    file_size INTEGER,
    FOREIGN KEY (essay_id) REFERENCES essays(id)
);

-- AI interactions (extended)
-- Already exists, add new task types

-- Notifications
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Cloud sync log
CREATE TABLE sync_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    sync_direction TEXT NOT NULL,
    items_synced INTEGER DEFAULT 0,
    conflicts INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Shared essays (see Module 5.3)
CREATE TABLE shared_essays (...);

-- Essay comments (see Module 5.3)
CREATE TABLE essay_comments (...);

-- Essay suggestions (see Module 5.3)
CREATE TABLE essay_suggestions (...);
```

---

## IMPLEMENTATION PRIORITY

### Sprint 1: Export & Integration (Week 1)
**Priority**: HIGH
**Days**: 3-4

Build export functionality first - students need to submit work.

**Deliverables**:
1. Export Manager
2. DOCX Exporter (with templates)
3. PDF Exporter
4. LaTeX Exporter
5. LMS Integration Manager (Blackboard, Moodle)
6. Export View UI

**Testing**: Export essays to all formats, verify formatting

---

### Sprint 2: Advanced AI Features (Week 1-2)
**Priority**: HIGH
**Days**: 3-4

Enhance AI capabilities - big value add.

**Deliverables**:
1. Outline Generator
2. Research Assistant
3. Paraphrasing Tool
4. Material Summarizer
5. AI Assistant Manager
6. AI Assistant View UI

**Testing**: Generate outlines, test paraphrasing, verify summaries

---

### Sprint 3: Productivity & Insights (Week 2)
**Priority**: MEDIUM
**Days**: 3-5

Expand analytics - helps students improve.

**Deliverables**:
1. Grade Predictor
2. Advanced Analytics Engine
3. Notification Manager
4. Deadline Predictor
5. Productivity Insights View UI

**Testing**: Verify grade predictions, test notifications

---

### Sprint 4: Writing Quality (Week 3)
**Priority**: MEDIUM
**Days**: 3-4

Quality checks - direct writing improvement.

**Deliverables**:
1. Plagiarism Checker
2. Readability Optimizer
3. Academic Tone Checker
4. Writing Quality Manager
5. Writing Quality View UI

**Testing**: Check plagiarism detection, verify tone analysis

---

### Sprint 5: Collaboration & Sync (Week 3-4)
**Priority**: MEDIUM
**Days**: 4-5

Enable multi-device/collaboration - modern workflow.

**Deliverables**:
1. Cloud Sync Manager
2. Collaboration Manager
3. Multi-User Database Manager
4. Activity Feed
5. Collaboration View UI

**Testing**: Test sync, verify collaboration features

---

## ESTIMATED TOTALS

### Code Volume
- **Sprint 1**: 2,400 lines
- **Sprint 2**: 2,200 lines
- **Sprint 3**: 2,800 lines
- **Sprint 4**: 2,400 lines
- **Sprint 5**: 2,200 lines
- **TOTAL**: ~12,000 lines

### Timeline
- **Sprint 1**: 3-4 days
- **Sprint 2**: 3-4 days
- **Sprint 3**: 3-5 days
- **Sprint 4**: 3-4 days
- **Sprint 5**: 4-5 days
- **TOTAL**: 16-22 days (3-4.5 weeks)

### Module Count
- **Backend Modules**: 22
- **UI Views**: 6
- **TOTAL**: 28+ components

---

## SUCCESS CRITERIA

Phase 5 will be considered complete when:

✅ Students can export essays to DOCX, PDF, LaTeX, Markdown
✅ Multiple LMS platforms supported (Canvas, Blackboard, Moodle)
✅ AI can generate outlines and research guidance
✅ Paraphrasing tool helps with rewriting
✅ Grade predictor provides pre-submission estimates
✅ Smart notifications alert about deadlines
✅ Plagiarism checker validates originality
✅ Readability and tone tools improve quality
✅ Cloud sync enables multi-device workflow
✅ Collaboration features allow peer review

**Total Phase 5**: ~12,000 new lines across 28+ components

---

## PHASE 5 ROADMAP

**Week 1**: Export & Integration + AI Features (Sprints 1-2)
**Week 2**: Productivity & Insights (Sprint 3)
**Week 3**: Writing Quality (Sprint 4)
**Week 4**: Collaboration & Sync (Sprint 5)

**Total Estimated Time**: 3-4.5 weeks
**Lines of Code**: ~12,000 new lines
**New Components**: 28+ modules
**UI Views Added**: 6 new views

---

## COMBINED PROJECT TOTALS (After Phase 5)

| Phase | Code | Modules |
|-------|------|---------|
| Phase 1 | 3,500 | 8 |
| Phase 2 | 7,585 | 23 |
| Phase 3 | 8,160 | 24 |
| Phase 5 | 12,000 | 28 |
| **TOTAL** | **31,245** | **83** |

Plus Phase 4 (documentation, testing, polish) - non-code deliverables

---

## NEXT STEPS

**Option A: Start Phase 5 Now** 🚀
- Begin Sprint 1 (Export & Integration)
- Deliver DOCX, PDF, LaTeX exporters
- Add Blackboard and Moodle integration

**Option B: Complete Phase 4 First** 📚
- Finish documentation (User Guide, API Setup)
- Complete end-to-end testing
- Polish UX (loading indicators, shortcuts)
- Package for distribution
- Then start Phase 5

**Recommendation**: Complete Phase 4 first for a stable v1.0.0 release, then add Phase 5 features in v1.1.0+

---

**Plan Created**: November 12, 2025
**Phase 5 Status**: 🚀 **READY TO START**
**First Target**: Either Phase 4 (documentation) or Phase 5 Sprint 1 (export)
**Estimated Phase 5 Completion**: 3-4.5 weeks

