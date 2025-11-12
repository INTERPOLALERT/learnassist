"""
Academic Command Center - Settings View
Manage application settings and API keys.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QMessageBox,
    QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager
from core.api_manager import APIKeyManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SettingsView(QWidget):
    """Settings and configuration view."""

    def __init__(self, user_id: str, db_manager: DatabaseManager):
        """
        Initialize settings view.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        super().__init__()

        self.user_id = user_id
        self.db = db_manager
        self.api_manager = APIKeyManager(user_id, db_manager)

        self._init_ui()
        self.refresh()

    def _init_ui(self):
        """Initialize user interface."""
        # Main scrollable layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)

        # Page title
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # API Keys Section
        api_section = self._create_api_section()
        main_layout.addWidget(api_section)

        # About Section
        about_section = self._create_about_section()
        main_layout.addWidget(about_section)

        # Stretch to push everything to top
        main_layout.addStretch()

        scroll.setWidget(scroll_content)

        # Set scroll as main widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _create_api_section(self) -> QFrame:
        """Create API keys configuration section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 25px;
            }
        """)

        layout = QVBoxLayout(section)

        # Section title
        title = QLabel("AI Provider API Keys")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Configure your API keys for AI providers. "
            "The app will use these to parse essays, generate tasks, and auto-tag materials."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(desc)

        # API key inputs
        self.api_inputs = {}

        providers = [
            ('gemini', 'Gemini API Key', 'Primary parser - Essay analysis'),
            ('groq', 'Groq API Key', 'Fast parsing - Requirement extraction'),
            ('deepseek', 'DeepSeek API Key', 'Grammar checking'),
            ('claude', 'Claude API Key (OpenRouter)', 'Advanced reasoning - Rubric decoding'),
            ('cohere', 'Cohere API Key', 'Embeddings - Material matching')
        ]

        for provider_id, label, description in providers:
            provider_frame = self._create_api_input(provider_id, label, description)
            layout.addWidget(provider_frame)
            layout.addSpacing(10)

        return section

    def _create_api_input(self, provider_id: str, label: str, description: str) -> QFrame:
        """Create API key input field."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(frame)

        # Label and description
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(label_widget)

        desc_widget = QLabel(description)
        desc_widget.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(desc_widget)

        # Input row
        input_layout = QHBoxLayout()

        # API key input
        input_field = QLineEdit()
        input_field.setPlaceholderText(f"Enter your {label}...")
        input_field.setEchoMode(QLineEdit.EchoMode.Password)
        input_field.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        input_layout.addWidget(input_field, stretch=1)

        # Show/Hide button
        show_btn = QPushButton("Show")
        show_btn.setFixedWidth(60)
        show_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        show_btn.clicked.connect(
            lambda: self._toggle_password_visibility(input_field, show_btn)
        )
        input_layout.addWidget(show_btn)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(60)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_btn.clicked.connect(
            lambda: self._save_api_key(provider_id, input_field.text())
        )
        input_layout.addWidget(save_btn)

        layout.addLayout(input_layout)

        # Store reference
        self.api_inputs[provider_id] = input_field

        return frame

    def _create_about_section(self) -> QFrame:
        """Create about section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 25px;
            }
        """)

        layout = QVBoxLayout(section)

        # Title
        title = QLabel("About Academic Command Center")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info
        info_text = """
        <p><b>Version:</b> 1.0.0 (Phase 2)</p>
        <p><b>Description:</b> AI-powered academic workflow manager for Windows</p>
        <p>
        <b>Features:</b><br>
        • Essay Parser: Transform instructions into structured data<br>
        • Task Manager: Generate prioritized task breakdowns<br>
        • Materials Library: Upload and auto-tag study materials<br>
        • Knowledge Gap Detection: Identify missing concepts<br>
        • AI-Powered Analysis: Multiple providers for optimal results
        </p>
        <p><b>Database Location:</b> ./data/academic_command_center.db</p>
        <p><b>Platform:</b> Windows 11</p>
        """

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setStyleSheet("color: #34495e; line-height: 1.6;")
        layout.addWidget(info_label)

        return section

    def refresh(self):
        """Refresh settings view."""
        logger.info("Refreshing settings...")

        # Load existing API keys (masked)
        try:
            query = "SELECT provider_name FROM user_api_keys WHERE user_id = ?"
            keys = self.db.execute_query(query, (self.user_id,), fetch_all=True)

            configured_providers = [k['provider_name'] for k in keys] if keys else []

            # Show which providers have keys configured
            for provider_id, input_field in self.api_inputs.items():
                if provider_id in configured_providers:
                    input_field.setPlaceholderText("✓ API key configured")
                    input_field.setStyleSheet("""
                        QLineEdit {
                            padding: 8px;
                            border: 2px solid #2ecc71;
                            border-radius: 4px;
                            background-color: white;
                        }
                    """)
                else:
                    input_field.setPlaceholderText(f"No API key configured")

        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")

    def _toggle_password_visibility(self, input_field: QLineEdit, button: QPushButton):
        """Toggle password visibility."""
        if input_field.echoMode() == QLineEdit.EchoMode.Password:
            input_field.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText("Hide")
        else:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText("Show")

    def _save_api_key(self, provider: str, api_key: str):
        """Save API key."""
        if not api_key or not api_key.strip():
            QMessageBox.warning(self, "Error", "Please enter an API key")
            return

        try:
            result = self.api_manager.store_key(provider, api_key.strip())

            if result['success']:
                QMessageBox.information(
                    self,
                    "Success",
                    f"{provider.title()} API key saved successfully!"
                )

                # Clear input and refresh
                self.api_inputs[provider].clear()
                self.refresh()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save API key:\n{result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            QMessageBox.critical(self, "Error", f"Error saving API key:\n{str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    db = DatabaseManager()
    view = SettingsView("test_user", db)
    view.show()

    sys.exit(app.exec())
