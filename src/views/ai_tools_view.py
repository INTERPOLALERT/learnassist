"""
AI Tools View - Phase 6 Sprint 1
Quick access panel for AI-powered study features
"""
import logging
from typing import List, Dict, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QLineEdit, QScrollArea, QFrame, QMessageBox,
    QComboBox, QSpinBox, QTabWidget, QListWidget, QListWidgetItem,
    QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class AIToolsView(QWidget):
    """AI Tools View - AI-powered study assistance."""

    def __init__(self, user_id: str, db_manager):
        """
        Initialize AI Tools View.

        Args:
            user_id: Current user ID
            db_manager: DatabaseManager instance
        """
        super().__init__()
        self.user_id = user_id
        self.db = db_manager

        # Check AI availability
        self.ai_available = self._check_ai_availability()

        self._init_ui()

        logger.info("AI Tools View initialized")

    def _check_ai_availability(self) -> bool:
        """Check if AI services are configured."""
        try:
            # Check if AI settings exist
            query = "SELECT gemini_api_key FROM ai_settings WHERE user_id = ?"
            result = self.db.fetch_one(query, (self.user_id,))

            if result and result[0]:
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to check AI availability: {e}")
            return False

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        if not self.ai_available:
            # Show setup message if AI not configured
            setup_widget = self._create_setup_widget()
            layout.addWidget(setup_widget, 1)
        else:
            # Show AI tools tabs
            tabs = self._create_tabs()
            layout.addWidget(tabs, 1)

    def _create_header(self) -> QWidget:
        """Create header with title."""
        header = QFrame()
        header.setStyleSheet("background: #8e44ad; border-radius: 8px; padding: 15px;")

        layout = QHBoxLayout(header)

        # Title
        title = QLabel("🤖 AI Study Assistant")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Status indicator
        if self.ai_available:
            status = QLabel("✓ AI Ready")
            status.setStyleSheet("""
                background: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            """)
        else:
            status = QLabel("⚠ Setup Required")
            status.setStyleSheet("""
                background: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            """)
        layout.addWidget(status)

        return header

    def _create_setup_widget(self) -> QWidget:
        """Create setup instructions widget."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                padding: 30px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon = QLabel("⚙️")
        icon.setStyleSheet("font-size: 64px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        # Title
        title = QLabel("AI Assistant Setup Required")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "To use AI-powered study features, you need to configure your AI settings.\n\n"
            "Please go to Settings → AI Settings and add your Gemini API key.\n\n"
            "You can get a free API key from Google AI Studio:\n"
            "https://makersuite.google.com/app/apikey"
        )
        instructions.setStyleSheet("""
            color: #7f8c8d;
            font-size: 14px;
            padding: 20px;
        """)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Go to Settings button
        settings_btn = QPushButton("Go to Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        settings_btn.clicked.connect(self._go_to_settings)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return container

    def _create_tabs(self) -> QWidget:
        """Create tabs for different AI tools."""
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)

        # Chat Assistant Tab
        chat_tab = self._create_chat_tab()
        tabs.addTab(chat_tab, "💬 Chat Assistant")

        # Note Summarizer Tab
        summarizer_tab = self._create_summarizer_tab()
        tabs.addTab(summarizer_tab, "📝 Summarize Notes")

        # Quiz Generator Tab
        quiz_tab = self._create_quiz_tab()
        tabs.addTab(quiz_tab, "📊 Generate Quiz")

        # Flashcard Creator Tab
        flashcard_tab = self._create_flashcard_tab()
        tabs.addTab(flashcard_tab, "🎴 Create Flashcards")

        # Study Plan Tab
        study_plan_tab = self._create_study_plan_tab()
        tabs.addTab(study_plan_tab, "📅 Study Plan")

        return tabs

    def _create_chat_tab(self) -> QWidget:
        """Create chat assistant tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info box
        info = QLabel(
            "💡 Ask the AI assistant anything about your studies!\n"
            "It can help explain concepts, solve problems, or provide study tips."
        )
        info.setStyleSheet("""
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 6px;
            color: #2c3e50;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                background: #f8f9fa;
                font-size: 13px;
            }
        """)
        self.chat_history.setPlaceholderText("Chat history will appear here...")
        layout.addWidget(self.chat_history, 1)

        # Input area
        input_layout = QHBoxLayout()

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your question here...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        self.chat_input.returnPressed.connect(self._send_chat_message)
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        send_btn.clicked.connect(self._send_chat_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        return container

    def _create_summarizer_tab(self) -> QWidget:
        """Create note summarizer tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info box
        info = QLabel(
            "📝 Select a note to generate an AI-powered summary.\n"
            "Perfect for quick reviews and exam preparation!"
        )
        info.setStyleSheet("""
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 6px;
            color: #2c3e50;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Note selection
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Select Note:"))

        self.note_combo = QComboBox()
        self.note_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                min-width: 300px;
            }
        """)
        self._load_notes_list()
        select_layout.addWidget(self.note_combo, 1)

        summarize_btn = QPushButton("Generate Summary")
        summarize_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        summarize_btn.clicked.connect(self._generate_summary)
        select_layout.addWidget(summarize_btn)

        layout.addLayout(select_layout)

        # Summary output
        layout.addWidget(QLabel("Summary:"))
        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                background: white;
                font-size: 13px;
            }
        """)
        self.summary_output.setPlaceholderText("Summary will appear here...")
        layout.addWidget(self.summary_output, 1)

        return container

    def _create_quiz_tab(self) -> QWidget:
        """Create quiz generator tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info box
        info = QLabel(
            "📊 Generate a quiz from your notes to test your knowledge.\n"
            "Choose the number of questions and difficulty level."
        )
        info.setStyleSheet("""
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 6px;
            color: #2c3e50;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Quiz settings
        settings_layout = QGridLayout()

        # Note selection
        settings_layout.addWidget(QLabel("Select Note:"), 0, 0)
        self.quiz_note_combo = QComboBox()
        self.quiz_note_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self._load_notes_list(self.quiz_note_combo)
        settings_layout.addWidget(self.quiz_note_combo, 0, 1)

        # Number of questions
        settings_layout.addWidget(QLabel("Questions:"), 1, 0)
        self.num_questions = QSpinBox()
        self.num_questions.setRange(5, 20)
        self.num_questions.setValue(10)
        self.num_questions.setStyleSheet("""
            QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        settings_layout.addWidget(self.num_questions, 1, 1)

        # Difficulty
        settings_layout.addWidget(QLabel("Difficulty:"), 2, 0)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentText("Medium")
        self.difficulty_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        settings_layout.addWidget(self.difficulty_combo, 2, 1)

        layout.addLayout(settings_layout)

        # Generate button
        generate_btn = QPushButton("🎲 Generate Quiz")
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #e67e22;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #d35400;
            }
        """)
        generate_btn.clicked.connect(self._generate_quiz)
        layout.addWidget(generate_btn)

        # Quiz output
        layout.addWidget(QLabel("Generated Quiz:"))
        self.quiz_output = QTextEdit()
        self.quiz_output.setReadOnly(True)
        self.quiz_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                background: white;
                font-size: 13px;
            }
        """)
        self.quiz_output.setPlaceholderText("Quiz questions will appear here...")
        layout.addWidget(self.quiz_output, 1)

        return container

    def _create_flashcard_tab(self) -> QWidget:
        """Create flashcard generator tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info box
        info = QLabel(
            "🎴 Generate flashcards from your notes for quick study sessions.\n"
            "AI will create question-answer pairs automatically."
        )
        info.setStyleSheet("""
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 6px;
            color: #2c3e50;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Settings
        settings_layout = QHBoxLayout()

        settings_layout.addWidget(QLabel("Select Note:"))
        self.flashcard_note_combo = QComboBox()
        self.flashcard_note_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self._load_notes_list(self.flashcard_note_combo)
        settings_layout.addWidget(self.flashcard_note_combo, 1)

        settings_layout.addWidget(QLabel("Number:"))
        self.num_flashcards = QSpinBox()
        self.num_flashcards.setRange(5, 30)
        self.num_flashcards.setValue(15)
        self.num_flashcards.setStyleSheet("""
            QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        settings_layout.addWidget(self.num_flashcards)

        generate_btn = QPushButton("Generate Flashcards")
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """)
        generate_btn.clicked.connect(self._generate_flashcards)
        settings_layout.addWidget(generate_btn)

        layout.addLayout(settings_layout)

        # Flashcards output
        layout.addWidget(QLabel("Generated Flashcards:"))
        self.flashcards_output = QTextEdit()
        self.flashcards_output.setReadOnly(True)
        self.flashcards_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                background: white;
                font-size: 13px;
            }
        """)
        self.flashcards_output.setPlaceholderText("Flashcards will appear here...")
        layout.addWidget(self.flashcards_output, 1)

        return container

    def _create_study_plan_tab(self) -> QWidget:
        """Create study plan generator tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info box
        info = QLabel(
            "📅 Generate a personalized study plan based on your assignments and goals.\n"
            "AI will help you organize your time effectively."
        )
        info.setStyleSheet("""
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 6px;
            color: #2c3e50;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Settings
        settings_layout = QGridLayout()

        settings_layout.addWidget(QLabel("Study Goal:"), 0, 0)
        self.study_goal_input = QLineEdit()
        self.study_goal_input.setPlaceholderText("e.g., Prepare for midterm exams")
        self.study_goal_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        settings_layout.addWidget(self.study_goal_input, 0, 1)

        settings_layout.addWidget(QLabel("Time Available (days):"), 1, 0)
        self.days_available = QSpinBox()
        self.days_available.setRange(1, 90)
        self.days_available.setValue(14)
        self.days_available.setStyleSheet("""
            QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        settings_layout.addWidget(self.days_available, 1, 1)

        settings_layout.addWidget(QLabel("Hours per day:"), 2, 0)
        self.hours_per_day = QSpinBox()
        self.hours_per_day.setRange(1, 12)
        self.hours_per_day.setValue(3)
        self.hours_per_day.setStyleSheet("""
            QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        settings_layout.addWidget(self.hours_per_day, 2, 1)

        layout.addLayout(settings_layout)

        # Generate button
        generate_btn = QPushButton("📊 Generate Study Plan")
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #16a085;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #138d75;
            }
        """)
        generate_btn.clicked.connect(self._generate_study_plan)
        layout.addWidget(generate_btn)

        # Plan output
        layout.addWidget(QLabel("Your Study Plan:"))
        self.study_plan_output = QTextEdit()
        self.study_plan_output.setReadOnly(True)
        self.study_plan_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                background: white;
                font-size: 13px;
            }
        """)
        self.study_plan_output.setPlaceholderText("Study plan will appear here...")
        layout.addWidget(self.study_plan_output, 1)

        return container

    def _load_notes_list(self, combo: Optional[QComboBox] = None):
        """Load notes into combo box."""
        try:
            query = "SELECT id, title FROM notes WHERE user_id = ? ORDER BY updated_at DESC LIMIT 50"
            results = self.db.fetch_all(query, (self.user_id,))

            target = combo if combo else self.note_combo
            target.clear()
            target.addItem("-- Select a note --", None)

            for row in results:
                target.addItem(row[1], row[0])

        except Exception as e:
            logger.error(f"Failed to load notes: {e}")

    def _send_chat_message(self):
        """Send chat message to AI."""
        message = self.chat_input.text().strip()
        if not message:
            return

        # Add user message to history
        self.chat_history.append(f"<b>You:</b> {message}<br>")

        # Clear input
        self.chat_input.clear()

        # Placeholder response (real implementation would call AI service)
        self.chat_history.append(
            f"<b>AI Assistant:</b> <i>AI integration coming soon! "
            f"This feature will provide intelligent responses to your study questions.</i><br><br>"
        )

        # Scroll to bottom
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )

    def _generate_summary(self):
        """Generate note summary."""
        note_id = self.note_combo.currentData()
        if not note_id:
            QMessageBox.warning(self, "Warning", "Please select a note")
            return

        try:
            # Get note content
            query = "SELECT title, content FROM notes WHERE id = ?"
            result = self.db.fetch_one(query, (note_id,))

            if not result:
                QMessageBox.warning(self, "Warning", "Note not found")
                return

            title, content = result

            # Placeholder summary (real implementation would call AI service)
            self.summary_output.setText(
                f"📝 Summary of: {title}\n\n"
                f"[AI Summary Feature]\n\n"
                f"This feature will analyze your note content and generate:\n"
                f"• Key points and main ideas\n"
                f"• Important concepts to remember\n"
                f"• Suggested areas for further study\n\n"
                f"Note length: {len(content)} characters\n\n"
                f"AI integration coming soon!"
            )

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate summary: {e}")

    def _generate_quiz(self):
        """Generate quiz from note."""
        note_id = self.quiz_note_combo.currentData()
        if not note_id:
            QMessageBox.warning(self, "Warning", "Please select a note")
            return

        num_questions = self.num_questions.value()
        difficulty = self.difficulty_combo.currentText()

        # Placeholder quiz (real implementation would call AI service)
        self.quiz_output.setText(
            f"📊 Quiz Generated\n\n"
            f"Questions: {num_questions}\n"
            f"Difficulty: {difficulty}\n\n"
            f"[AI Quiz Generation Feature]\n\n"
            f"This feature will create:\n"
            f"• Multiple choice questions\n"
            f"• True/false questions\n"
            f"• Short answer questions\n\n"
            f"All based on your note content with answer keys included.\n\n"
            f"AI integration coming soon!"
        )

    def _generate_flashcards(self):
        """Generate flashcards from note."""
        note_id = self.flashcard_note_combo.currentData()
        if not note_id:
            QMessageBox.warning(self, "Warning", "Please select a note")
            return

        num_cards = self.num_flashcards.value()

        # Placeholder flashcards (real implementation would call AI service)
        self.flashcards_output.setText(
            f"🎴 Flashcards Generated\n\n"
            f"Number of cards: {num_cards}\n\n"
            f"[AI Flashcard Generation Feature]\n\n"
            f"This feature will create question-answer pairs:\n\n"
            f"Card 1:\n"
            f"Q: What is the main concept?\n"
            f"A: [Generated from note content]\n\n"
            f"Card 2:\n"
            f"Q: Define key term...\n"
            f"A: [Generated from note content]\n\n"
            f"AI integration coming soon!"
        )

    def _generate_study_plan(self):
        """Generate personalized study plan."""
        goal = self.study_goal_input.text().strip()
        if not goal:
            QMessageBox.warning(self, "Warning", "Please enter a study goal")
            return

        days = self.days_available.value()
        hours = self.hours_per_day.value()

        # Placeholder plan (real implementation would call AI service)
        self.study_plan_output.setText(
            f"📅 Personalized Study Plan\n\n"
            f"Goal: {goal}\n"
            f"Duration: {days} days\n"
            f"Daily commitment: {hours} hours\n"
            f"Total study time: {days * hours} hours\n\n"
            f"[AI Study Plan Generation Feature]\n\n"
            f"This feature will create:\n"
            f"• Day-by-day breakdown of topics\n"
            f"• Prioritized assignment schedule\n"
            f"• Practice session recommendations\n"
            f"• Review intervals based on spaced repetition\n"
            f"• Break times and rest days\n\n"
            f"AI integration coming soon!"
        )

    def _go_to_settings(self):
        """Navigate to settings view."""
        # Signal parent window to navigate
        try:
            main_window = self.window()
            if hasattr(main_window, 'navigate_to'):
                main_window.navigate_to("Settings")
        except Exception as e:
            logger.error(f"Failed to navigate to settings: {e}")
