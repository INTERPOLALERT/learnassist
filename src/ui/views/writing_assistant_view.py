"""
Academic Command Center - Writing Assistant View
UI for grammar checking and style analysis.
"""

import logging
import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QGroupBox, QProgressBar, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from features.writing.grammar_checker import GrammarChecker, ErrorSeverity
from features.writing.style_analyzer import StyleAnalyzer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class WritingAssistantView(QWidget):
    """
    Writing Assistant view for grammar and style checking.

    Features:
    - Text input area
    - Grammar checking with error highlighting
    - Style analysis with metrics
    - Real-time feedback
    - Improvement suggestions
    - Writing quality scores
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize writing assistant view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Initialize backend components
        self.grammar_checker = GrammarChecker()
        self.style_analyzer = StyleAnalyzer()

        # Current analysis results
        self.grammar_result = None
        self.style_result = None

        # Initialize UI
        self._init_ui()

        logger.info("Writing Assistant view initialized")

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("✍️ Writing Assistant")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Check button
        self.check_btn = QPushButton("🔍 Check Writing")
        self.check_btn.clicked.connect(self._on_check_clicked)
        self.check_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        header_layout.addWidget(self.check_btn)

        # Clear button
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self._on_clear_clicked)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        header_layout.addWidget(clear_btn)

        main_layout.addLayout(header_layout)

        # Main content layout (side by side)
        content_layout = QHBoxLayout()

        # Left side: Text editor
        editor_section = self._create_editor_section()
        content_layout.addWidget(editor_section, stretch=1)

        # Right side: Analysis results
        results_section = self._create_results_section()
        content_layout.addWidget(results_section, stretch=1)

        main_layout.addLayout(content_layout)

    def _create_editor_section(self) -> QFrame:
        """Create text editor section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("Your Text")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Paste or type your text here to check for grammar errors and style improvements...\n\nExample: This is a test sentance with some erors.")
        self.text_editor.setFont(QFont("Arial", 12))
        self.text_editor.setMinimumHeight(400)
        self.text_editor.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                background-color: #fafafa;
            }
        """)
        layout.addWidget(self.text_editor)

        # Word count
        self.word_count_label = QLabel("Words: 0 | Characters: 0")
        self.word_count_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(self.word_count_label)

        # Connect text change event
        self.text_editor.textChanged.connect(self._update_word_count)

        return section

    def _create_results_section(self) -> QFrame:
        """Create analysis results section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("Analysis Results")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Tabs for different analysis types
        self.results_tabs = QTabWidget()
        self.results_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
        """)

        # Overview tab
        overview_widget = self._create_overview_tab()
        self.results_tabs.addTab(overview_widget, "📊 Overview")

        # Grammar tab
        grammar_widget = self._create_grammar_tab()
        self.results_tabs.addTab(grammar_widget, "📝 Grammar")

        # Style tab
        style_widget = self._create_style_tab()
        self.results_tabs.addTab(style_widget, "🎨 Style")

        layout.addWidget(self.results_tabs)

        return section

    def _create_overview_tab(self) -> QWidget:
        """Create overview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Score cards
        scores_layout = QHBoxLayout()

        # Grammar score card
        self.grammar_score_card = self._create_score_card("Grammar", "0", "#3498db")
        scores_layout.addWidget(self.grammar_score_card)

        # Style score card
        self.style_score_card = self._create_score_card("Style", "0", "#9b59b6")
        scores_layout.addWidget(self.style_score_card)

        layout.addLayout(scores_layout)

        # Quick stats
        stats_group = QGroupBox("Quick Stats")
        stats_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout = QVBoxLayout()

        self.stats_label = QLabel("Run a check to see statistics")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("padding: 10px; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Overall suggestions
        suggestions_group = QGroupBox("📌 Key Suggestions")
        suggestions_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        suggestions_layout = QVBoxLayout()

        self.overall_suggestions_label = QLabel("Check your text to get personalized suggestions")
        self.overall_suggestions_label.setWordWrap(True)
        self.overall_suggestions_label.setStyleSheet("padding: 10px; font-size: 12px;")
        suggestions_layout.addWidget(self.overall_suggestions_label)

        suggestions_group.setLayout(suggestions_layout)
        layout.addWidget(suggestions_group)

        layout.addStretch()

        return widget

    def _create_grammar_tab(self) -> QWidget:
        """Create grammar errors tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scroll area for errors
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        self.grammar_errors_layout = QVBoxLayout(scroll_content)
        self.grammar_errors_layout.setSpacing(10)

        # Default message
        default_msg = QLabel("Run a check to see grammar errors")
        default_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_msg.setStyleSheet("color: #95a5a6; padding: 20px;")
        self.grammar_errors_layout.addWidget(default_msg)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def _create_style_tab(self) -> QWidget:
        """Create style analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scroll area for style metrics
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        self.style_metrics_layout = QVBoxLayout(scroll_content)
        self.style_metrics_layout.setSpacing(10)

        # Default message
        default_msg = QLabel("Run a check to see style analysis")
        default_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_msg.setStyleSheet("color: #95a5a6; padding: 20px;")
        self.style_metrics_layout.addWidget(default_msg)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def _create_score_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a score card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 6px;
                padding: 15px;
            }}
        """)
        card.setMinimumHeight(100)

        layout = QVBoxLayout(card)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Store reference for updates
        card.value_label = value_label

        return card

    def _update_word_count(self):
        """Update word count display."""
        text = self.text_editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"Words: {words} | Characters: {chars}")

    def _on_check_clicked(self):
        """Handle check button click."""
        text = self.text_editor.toPlainText()

        if not text.strip():
            self.stats_label.setText("⚠️ Please enter some text to check")
            return

        logger.info("Checking text...")

        # Run grammar check
        self.grammar_result = self.grammar_checker.check_text(text)
        grammar_score = self.grammar_checker.get_writing_score(text)

        # Run style analysis
        self.style_result = self.style_analyzer.analyze_text(text)

        # Update UI
        self._update_overview(grammar_score)
        self._update_grammar_errors()
        self._update_style_metrics()

        logger.info("Text check completed")

    def _update_overview(self, grammar_score: float):
        """Update overview tab."""
        # Update score cards
        self.grammar_score_card.value_label.setText(f"{grammar_score:.0f}")
        self.style_score_card.value_label.setText(f"{self.style_result['overall_score']:.0f}")

        # Update quick stats
        stats_text = f"""
        <b>Grammar:</b> {self.grammar_result['error_count']} issues found<br>
        <b>Error Rate:</b> {self.grammar_result['error_rate']}%<br>
        <b>Word Count:</b> {self.grammar_result['word_count']}<br>
        <b>Sentences:</b> {self.grammar_result['sentence_count']}<br>
        <br>
        <b>Readability:</b> {self.style_result['readability']['level']} ({self.style_result['readability']['score']:.0f})<br>
        <b>Avg Sentence Length:</b> {self.style_result['sentences']['avg_length']} words<br>
        <b>Passive Voice:</b> {self.style_result['passive_voice']['rate']}%
        """
        self.stats_label.setText(stats_text)

        # Combine suggestions
        all_suggestions = []

        # Add top grammar issues
        if self.grammar_result['error_count'] > 0:
            errors_by_type = self.grammar_result['errors_by_type']
            for error_type, count in sorted(errors_by_type.items(), key=lambda x: -x[1])[:2]:
                all_suggestions.append(f"• {count} {error_type} error(s) found")

        # Add style suggestions
        all_suggestions.extend(self.style_result['suggestions'][:3])

        self.overall_suggestions_label.setText("\n".join(all_suggestions[:5]))

    def _update_grammar_errors(self):
        """Update grammar errors tab."""
        # Clear existing
        while self.grammar_errors_layout.count():
            child = self.grammar_errors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.grammar_result or self.grammar_result['error_count'] == 0:
            no_errors = QLabel("✅ No grammar errors found!")
            no_errors.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_errors.setStyleSheet("color: #27ae60; padding: 20px; font-size: 14px; font-weight: bold;")
            self.grammar_errors_layout.addWidget(no_errors)
            return

        # Add errors
        for error in self.grammar_result['errors']:
            error_widget = self._create_error_widget(error)
            self.grammar_errors_layout.addWidget(error_widget)

        self.grammar_errors_layout.addStretch()

    def _create_error_widget(self, error: dict) -> QFrame:
        """Create an error display widget."""
        widget = QFrame()

        # Color based on severity
        if error['severity'] == ErrorSeverity.ERROR:
            bg_color = "#ffe6e6"
            border_color = "#e74c3c"
            icon = "❌"
        elif error['severity'] == ErrorSeverity.WARNING:
            bg_color = "#fff4e6"
            border_color = "#f39c12"
            icon = "⚠️"
        else:
            bg_color = "#e6f7ff"
            border_color = "#3498db"
            icon = "💡"

        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-left: 3px solid {border_color};
                border-radius: 4px;
                padding: 10px;
                margin: 2px 0;
            }}
        """)

        layout = QVBoxLayout(widget)
        layout.setSpacing(5)

        # Error header
        header = QLabel(f"{icon} <b>{error['type'].upper()}</b>")
        header.setFont(QFont("Arial", 11))
        layout.addWidget(header)

        # Error message
        message = QLabel(error['message'])
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 12px;")
        layout.addWidget(message)

        # Error text
        text_label = QLabel(f"Text: \"{error['text']}\"")
        text_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px;")
        layout.addWidget(text_label)

        # Suggestion
        if error.get('suggestion'):
            suggestion = QLabel(f"→ Suggestion: {error['suggestion']}")
            suggestion.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: bold;")
            layout.addWidget(suggestion)

        return widget

    def _update_style_metrics(self):
        """Update style metrics tab."""
        # Clear existing
        while self.style_metrics_layout.count():
            child = self.style_metrics_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.style_result:
            return

        # Readability section
        readability_group = QGroupBox("📖 Readability")
        readability_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        readability_layout = QVBoxLayout()

        readability_text = f"""
        <b>Score:</b> {self.style_result['readability']['score']:.1f}/100<br>
        <b>Level:</b> {self.style_result['readability']['level']}<br>
        <b>Avg Sentence Length:</b> {self.style_result['readability']['avg_sentence_length']} words<br>
        <b>Avg Word Length:</b> {self.style_result['readability']['avg_word_length']} letters
        """
        readability_label = QLabel(readability_text)
        readability_label.setWordWrap(True)
        readability_layout.addWidget(readability_label)

        readability_group.setLayout(readability_layout)
        self.style_metrics_layout.addWidget(readability_group)

        # Sentence structure section
        sentences_group = QGroupBox("📏 Sentence Structure")
        sentences_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        sentences_layout = QVBoxLayout()

        sentences_text = f"""
        <b>Total Sentences:</b> {self.style_result['sentences']['count']}<br>
        <b>Variety:</b> {self.style_result['sentences']['variety']}<br>
        <b>Short (&lt;10 words):</b> {self.style_result['sentences']['short_count']}<br>
        <b>Medium (10-20):</b> {self.style_result['sentences']['medium_count']}<br>
        <b>Long (&gt;20):</b> {self.style_result['sentences']['long_count']}
        """
        sentences_label = QLabel(sentences_text)
        sentences_label.setWordWrap(True)
        sentences_layout.addWidget(sentences_label)

        sentences_group.setLayout(sentences_layout)
        self.style_metrics_layout.addWidget(sentences_group)

        # Passive voice section
        passive_group = QGroupBox("🎯 Passive Voice")
        passive_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        passive_layout = QVBoxLayout()

        passive_text = f"""
        <b>Usage Rate:</b> {self.style_result['passive_voice']['rate']}%<br>
        <b>Quality:</b> {self.style_result['passive_voice']['quality']}<br>
        <b>Instances Found:</b> {self.style_result['passive_voice']['count']}
        """
        passive_label = QLabel(passive_text)
        passive_label.setWordWrap(True)
        passive_layout.addWidget(passive_label)

        passive_group.setLayout(passive_layout)
        self.style_metrics_layout.addWidget(passive_group)

        # Style suggestions
        suggestions_group = QGroupBox("💡 Style Suggestions")
        suggestions_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        suggestions_layout = QVBoxLayout()

        suggestions_text = "\n".join(self.style_result['suggestions'])
        suggestions_label = QLabel(suggestions_text)
        suggestions_label.setWordWrap(True)
        suggestions_layout.addWidget(suggestions_label)

        suggestions_group.setLayout(suggestions_layout)
        self.style_metrics_layout.addWidget(suggestions_group)

        self.style_metrics_layout.addStretch()

    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.text_editor.clear()
        self.grammar_result = None
        self.style_result = None

        # Reset UI
        self.grammar_score_card.value_label.setText("0")
        self.style_score_card.value_label.setText("0")
        self.stats_label.setText("Run a check to see statistics")
        self.overall_suggestions_label.setText("Check your text to get personalized suggestions")

        # Clear grammar errors
        while self.grammar_errors_layout.count():
            child = self.grammar_errors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        default_msg = QLabel("Run a check to see grammar errors")
        default_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_msg.setStyleSheet("color: #95a5a6; padding: 20px;")
        self.grammar_errors_layout.addWidget(default_msg)

        # Clear style metrics
        while self.style_metrics_layout.count():
            child = self.style_metrics_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        default_msg = QLabel("Run a check to see style analysis")
        default_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_msg.setStyleSheet("color: #95a5a6; padding: 20px;")
        self.style_metrics_layout.addWidget(default_msg)

    def refresh(self):
        """Refresh the view (called when navigating to this view)."""
        # Nothing to refresh for writing assistant
        pass


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    view = WritingAssistantView(user_id="test_user")
    view.setGeometry(100, 100, 1200, 800)
    view.show()

    sys.exit(app.exec())
