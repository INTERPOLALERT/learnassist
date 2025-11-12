"""
Academic Command Center - Main Application Entry Point
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Import core services
from core.database import DatabaseManager
from core.encryption import EncryptionService
from core.api_manager import APIKeyManager


# Setup logging
def setup_logging():
    """Configure application logging."""
    log_dir = Path("C:\\Users\\Gamer\\Getitdone\\logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Academic Command Center Starting")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("=" * 60)

    return logger


class AcademicCommandCenter:
    """Main application controller."""

    def __init__(self):
        """Initialize application."""
        self.logger = setup_logging()
        self.app = None
        self.main_window = None

        # Core services
        self.db = None
        self.encryption = None
        self.api_manager = None

        # Current user (for now, use default user)
        self.current_user_id = "default_user"

    def initialize_services(self) -> bool:
        """
        Initialize core application services.

        Returns:
            True if successful
        """
        try:
            self.logger.info("Initializing core services...")

            # Database
            self.logger.info("Connecting to database...")
            self.db = DatabaseManager()
            self.logger.info("✓ Database connected")

            # Encryption
            self.logger.info("Loading encryption service...")
            self.encryption = EncryptionService()
            if not self.encryption.verify_master_key():
                raise Exception("Encryption key verification failed")
            self.logger.info("✓ Encryption service ready")

            # API Manager
            self.logger.info("Initializing API manager...")
            self.api_manager = APIKeyManager(
                self.current_user_id,
                self.db,
                self.encryption
            )
            self.logger.info("✓ API manager ready")

            # Check/create default user
            self._ensure_default_user()

            self.logger.info("All services initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}", exc_info=True)
            return False

    def _ensure_default_user(self):
        """Create default user if doesn't exist."""
        query = "SELECT id FROM users WHERE id = ?"
        result = self.db.execute_query(
            query,
            (self.current_user_id,),
            fetch_one=True
        )

        if not result:
            # Create default user
            query = """
            INSERT INTO users (id, username, display_name)
            VALUES (?, ?, ?)
            """
            self.db.execute_query(
                query,
                (self.current_user_id, "default", "Default User")
            )
            self.logger.info("Created default user")

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Exit code
        """
        try:
            # Initialize services
            if not self.initialize_services():
                self.show_error_dialog(
                    "Initialization Failed",
                    "Failed to initialize core services. Check logs for details."
                )
                return 1

            # Create Qt application
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Academic Command Center")
            self.app.setOrganizationName("LearnAssist")

            # Set application style
            self.app.setStyle("Fusion")  # Modern cross-platform style

            # Create main window with full UI
            from ui.main_window import MainWindow

            self.main_window = MainWindow(
                user_id=self.current_user_id,
                db_manager=self.db
            )
            self.main_window.setGeometry(100, 100, 1400, 900)

            # Show window
            self.main_window.show()

            self.logger.info("Application started successfully")

            # Run event loop
            exit_code = self.app.exec()

            self.logger.info(f"Application exited with code: {exit_code}")
            return exit_code

        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            self.show_error_dialog(
                "Application Error",
                f"An unexpected error occurred:\n\n{str(e)}\n\nCheck logs for details."
            )
            return 1

        finally:
            # Cleanup
            if self.db:
                self.db.close()
            self.logger.info("Application shutdown complete")

    def show_error_dialog(self, title: str, message: str):
        """Show error message dialog."""
        try:
            if not self.app:
                self.app = QApplication(sys.argv)

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
        except:
            # Fallback to console if GUI fails
            print(f"\n[ERROR] {title}")
            print(message)


def main():
    """Application entry point."""
    app = AcademicCommandCenter()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
