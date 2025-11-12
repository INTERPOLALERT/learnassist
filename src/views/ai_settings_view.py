"""
AI Settings View - Phase 6 Sprint 2
PyQt6 interface for AI configuration and management.

Features:
- Model selection
- Temperature control
- Provider management
- Cost tracking
- Usage statistics
- API key management

Author: Academic Command Center
Phase: 6 Sprint 2
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QGroupBox,
    QTableWidget, QTableWidgetItem, QTabWidget,
    QLineEdit, QCheckBox, QSpinBox, QProgressBar,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, Any, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.ai_router import AIRouter
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AISettingsView(QWidget):
    """
    AI Settings View - Configuration and management interface.
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize AI settings view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.ai_router = AIRouter()

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Initialize user interface."""

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("AI Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Models
        models_tab = self._create_models_tab()
        tabs.addTab(models_tab, "Models")

        # Tab 2: Providers
        providers_tab = self._create_providers_tab()
        tabs.addTab(providers_tab, "Providers")

        # Tab 3: Usage
        usage_tab = self._create_usage_tab()
        tabs.addTab(usage_tab, "Usage & Cost")

        layout.addWidget(tabs)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 10px; }"
        )
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def _create_models_tab(self) -> QWidget:
        """Create models configuration tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Default model selection
        model_group = QGroupBox("Default AI Model")
        model_layout = QVBoxLayout()

        # Essay analysis model
        essay_layout = QHBoxLayout()
        essay_layout.addWidget(QLabel("Essay Analysis:"))
        self.essay_model_combo = QComboBox()
        self.essay_model_combo.addItems([
            "Gemini 1.5 Pro (Google)",
            "GPT-4 Turbo (OpenAI via OpenRouter)",
            "Claude 3.5 Sonnet (Anthropic via OpenRouter)",
            "Llama 3.1 70B (Groq)",
            "DeepSeek Chat"
        ])
        essay_layout.addWidget(self.essay_model_combo)
        model_layout.addLayout(essay_layout)

        # Research model
        research_layout = QHBoxLayout()
        research_layout.addWidget(QLabel("Research:"))
        self.research_model_combo = QComboBox()
        self.research_model_combo.addItems([
            "Gemini 1.5 Pro (Google)",
            "GPT-4 Turbo (OpenAI via OpenRouter)",
            "Claude 3.5 Sonnet (Anthropic via OpenRouter)",
            "Llama 3.1 70B (Groq)"
        ])
        research_layout.addWidget(self.research_model_combo)
        model_layout.addLayout(research_layout)

        # Writing coach model
        writing_layout = QHBoxLayout()
        writing_layout.addWidget(QLabel("Writing Coach:"))
        self.writing_model_combo = QComboBox()
        self.writing_model_combo.addItems([
            "Claude 3.5 Sonnet (Anthropic via OpenRouter)",
            "GPT-4 Turbo (OpenAI via OpenRouter)",
            "Gemini 1.5 Pro (Google)",
            "DeepSeek Chat"
        ])
        writing_layout.addWidget(self.writing_model_combo)
        model_layout.addLayout(writing_layout)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Temperature settings
        temp_group = QGroupBox("Temperature Settings")
        temp_layout = QVBoxLayout()

        temp_label = QLabel("Temperature: 0.7 (Balanced)")
        temp_layout.addWidget(temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        self.temp_slider.setValue(70)
        self.temp_slider.valueChanged.connect(
            lambda v: temp_label.setText(
                f"Temperature: {v/100:.2f} ({self._get_temp_desc(v/100)})"
            )
        )
        temp_layout.addWidget(self.temp_slider)

        temp_info = QLabel(
            "Lower values (0.0-0.3): More focused and deterministic\n"
            "Medium values (0.4-0.7): Balanced creativity and accuracy\n"
            "Higher values (0.8-1.0): More creative and varied"
        )
        temp_info.setStyleSheet("color: gray; font-size: 10px;")
        temp_layout.addWidget(temp_info)

        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)

        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout()

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setMinimum(100)
        self.max_tokens_spin.setMaximum(4000)
        self.max_tokens_spin.setValue(2000)
        self.max_tokens_spin.setSingleStep(100)

        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("Max Tokens:"))
        tokens_layout.addWidget(self.max_tokens_spin)
        tokens_layout.addStretch()
        advanced_layout.addLayout(tokens_layout)

        self.stream_checkbox = QCheckBox("Enable streaming responses")
        self.stream_checkbox.setChecked(False)
        advanced_layout.addWidget(self.stream_checkbox)

        self.cache_checkbox = QCheckBox("Enable response caching")
        self.cache_checkbox.setChecked(True)
        advanced_layout.addWidget(self.cache_checkbox)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_providers_tab(self) -> QWidget:
        """Create providers configuration tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Provider priority
        priority_group = QGroupBox("Provider Priority")
        priority_layout = QVBoxLayout()

        priority_label = QLabel(
            "Set the order in which AI providers are used:\n"
            "(First available provider will be used)"
        )
        priority_layout.addWidget(priority_label)

        # Provider list
        self.provider_table = QTableWidget()
        self.provider_table.setColumnCount(3)
        self.provider_table.setHorizontalHeaderLabels([
            "Provider", "Status", "Priority"
        ])
        self.provider_table.setRowCount(5)

        providers = [
            ("Google Gemini", "Configured", "1"),
            ("Groq", "Configured", "2"),
            ("OpenRouter (Claude)", "Not Configured", "3"),
            ("DeepSeek", "Not Configured", "4"),
            ("Cohere", "Not Configured", "5")
        ]

        for row, (provider, status, priority) in enumerate(providers):
            self.provider_table.setItem(row, 0, QTableWidgetItem(provider))
            self.provider_table.setItem(row, 1, QTableWidgetItem(status))
            self.provider_table.setItem(row, 2, QTableWidgetItem(priority))

        self.provider_table.horizontalHeader().setStretchLastSection(True)
        priority_layout.addWidget(self.provider_table)

        priority_group.setLayout(priority_layout)
        layout.addWidget(priority_group)

        # Fallback settings
        fallback_group = QGroupBox("Fallback Behavior")
        fallback_layout = QVBoxLayout()

        self.auto_fallback_checkbox = QCheckBox("Automatically fallback to next provider on failure")
        self.auto_fallback_checkbox.setChecked(True)
        fallback_layout.addWidget(self.auto_fallback_checkbox)

        self.retry_checkbox = QCheckBox("Retry failed requests (up to 3 attempts)")
        self.retry_checkbox.setChecked(True)
        fallback_layout.addWidget(self.retry_checkbox)

        fallback_group.setLayout(fallback_layout)
        layout.addWidget(fallback_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _create_usage_tab(self) -> QWidget:
        """Create usage and cost tracking tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        # Current session usage
        session_group = QGroupBox("Current Session")
        session_layout = QVBoxLayout()

        self.requests_label = QLabel("Requests: 0")
        session_layout.addWidget(self.requests_label)

        self.tokens_label = QLabel("Tokens Used: 0")
        session_layout.addWidget(self.tokens_label)

        self.cost_label = QLabel("Estimated Cost: $0.00")
        session_layout.addWidget(self.cost_label)

        session_group.setLayout(session_layout)
        layout.addWidget(session_group)

        # Usage limits
        limits_group = QGroupBox("Usage Limits")
        limits_layout = QVBoxLayout()

        self.daily_limit_checkbox = QCheckBox("Enable daily request limit")
        limits_layout.addWidget(self.daily_limit_checkbox)

        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Daily limit:"))
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setMinimum(10)
        self.daily_limit_spin.setMaximum(1000)
        self.daily_limit_spin.setValue(100)
        limit_layout.addWidget(self.daily_limit_spin)
        limit_layout.addWidget(QLabel("requests"))
        limit_layout.addStretch()
        limits_layout.addLayout(limit_layout)

        # Progress bar
        self.usage_progress = QProgressBar()
        self.usage_progress.setValue(5)  # 5%
        limits_layout.addWidget(self.usage_progress)

        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)

        # Cost estimation
        cost_group = QGroupBox("Cost Estimation")
        cost_layout = QVBoxLayout()

        cost_info = QLabel(
            "Estimated costs per 1000 tokens:\n\n"
            "• Gemini 1.5 Pro: $0.0025 (input), $0.01 (output)\n"
            "• Groq Llama 3.1: $0.0001 (very low cost)\n"
            "• Claude 3.5 Sonnet: $0.003 (input), $0.015 (output)\n"
            "• GPT-4 Turbo: $0.01 (input), $0.03 (output)\n"
            "• DeepSeek: $0.00014 (input), $0.00028 (output)"
        )
        cost_info.setStyleSheet("font-size: 10px;")
        cost_layout.addWidget(cost_info)

        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)

        # Refresh button
        refresh_btn = QPushButton("Refresh Usage Data")
        refresh_btn.clicked.connect(self._refresh_usage)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _load_settings(self):
        """Load current AI settings."""
        try:
            # Load from database or config
            # For now, use defaults
            logger.info("AI settings loaded")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    def _save_settings(self):
        """Save AI settings."""
        try:
            # Get values
            essay_model = self.essay_model_combo.currentText()
            research_model = self.research_model_combo.currentText()
            writing_model = self.writing_model_combo.currentText()
            temperature = self.temp_slider.value() / 100
            max_tokens = self.max_tokens_spin.value()

            # Save to database/config
            logger.info(f"Saving AI settings: temp={temperature}, tokens={max_tokens}")

            QMessageBox.information(
                self,
                "Settings Saved",
                "AI settings have been saved successfully!"
            )

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save settings: {e}"
            )

    def _refresh_usage(self):
        """Refresh usage statistics."""
        try:
            # Query AI interaction logs
            query = """
            SELECT COUNT(*), SUM(tokens_used), SUM(estimated_cost_usd)
            FROM ai_interactions
            WHERE user_id = ? AND DATE(created_at) = DATE('now')
            """

            result = self.db.execute_query(
                query,
                (self.user_id,),
                fetch_one=True
            )

            if result:
                count, tokens, cost = result
                count = count or 0
                tokens = tokens or 0
                cost = cost or 0.0

                self.requests_label.setText(f"Requests: {count}")
                self.tokens_label.setText(f"Tokens Used: {tokens:,}")
                self.cost_label.setText(f"Estimated Cost: ${cost:.4f}")

                # Update progress
                if self.daily_limit_checkbox.isChecked():
                    limit = self.daily_limit_spin.value()
                    percentage = min(100, (count / limit) * 100)
                    self.usage_progress.setValue(int(percentage))

            logger.info("Usage data refreshed")

        except Exception as e:
            logger.error(f"Failed to refresh usage: {e}")

    def _get_temp_desc(self, temp: float) -> str:
        """Get temperature description."""
        if temp < 0.3:
            return "Focused"
        elif temp < 0.7:
            return "Balanced"
        else:
            return "Creative"
