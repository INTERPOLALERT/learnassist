"""
Academic Command Center - API Key Manager
User-facing interface for managing AI API keys and Canvas tokens.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .database import DatabaseManager
from .encryption import EncryptionService

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Manages API keys for AI providers and Canvas LMS.

    Features:
    - Add/update/delete API keys
    - Enable/disable providers
    - Verify API key validity
    - Track usage and limits
    """

    # Supported providers
    SUPPORTED_PROVIDERS = {
        'gemini': 'Google Gemini',
        'groq': 'Groq',
        'deepseek': 'DeepSeek',
        'openrouter': 'OpenRouter (Claude)',
        'cohere': 'Cohere',
        'canvas': 'Canvas LMS'
    }

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None,
        encryption: Optional[EncryptionService] = None
    ):
        """
        Initialize API Key Manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
            encryption: Encryption service instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()
        self.encryption = encryption or EncryptionService()

    def add_or_update_key(
        self,
        provider: str,
        api_key: str,
        display_name: Optional[str] = None,
        daily_limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Add new API key or update existing one.

        Args:
            provider: Provider name (gemini, groq, etc.)
            api_key: Plain text API key
            display_name: User-friendly name
            daily_limit: Daily request limit

        Returns:
            Result dictionary
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            return {
                'success': False,
                'error': f'Unsupported provider: {provider}'
            }

        try:
            # Encrypt API key
            encrypted_hex, iv_hex = self.encryption.encrypt_to_hex(api_key)

            # Check if key already exists
            existing = self._get_key_record(provider)

            if existing:
                # Update existing
                query = """
                UPDATE user_api_keys
                SET api_key_encrypted = ?,
                    api_key_iv = ?,
                    display_name = ?,
                    daily_request_limit = ?,
                    verification_status = 'pending',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND provider = ?
                """
                params = (
                    encrypted_hex, iv_hex,
                    display_name or self.SUPPORTED_PROVIDERS[provider],
                    daily_limit,
                    self.user_id, provider
                )
                self.db.execute_query(query, params)
                logger.info(f"Updated API key for {provider}")
                action = 'updated'

            else:
                # Insert new
                key_id = str(uuid.uuid4())
                query = """
                INSERT INTO user_api_keys (
                    id, user_id, provider,
                    api_key_encrypted, api_key_iv,
                    display_name, daily_request_limit
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    key_id, self.user_id, provider,
                    encrypted_hex, iv_hex,
                    display_name or self.SUPPORTED_PROVIDERS[provider],
                    daily_limit
                )
                self.db.execute_query(query, params)
                logger.info(f"Added new API key for {provider}")
                action = 'added'

            return {
                'success': True,
                'provider': provider,
                'action': action
            }

        except Exception as e:
            logger.error(f"Failed to add/update key for {provider}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_key(self, provider: str) -> Optional[str]:
        """
        Get decrypted API key for provider.

        Args:
            provider: Provider name

        Returns:
            Decrypted API key or None
        """
        record = self._get_key_record(provider)
        if not record:
            return None

        try:
            decrypted = self.encryption.decrypt_from_hex(
                record['api_key_encrypted'],
                record['api_key_iv']
            )
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt key for {provider}: {e}")
            return None

    def _get_key_record(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get full key record from database."""
        query = """
        SELECT *
        FROM user_api_keys
        WHERE user_id = ? AND provider = ?
        """
        return self.db.execute_query(query, (self.user_id, provider), fetch_one=True)

    def list_all_keys(self) -> List[Dict[str, Any]]:
        """
        List all API keys (without exposing actual keys).

        Returns:
            List of key information dictionaries
        """
        query = """
        SELECT
            provider,
            display_name,
            is_enabled,
            daily_request_limit,
            current_daily_requests,
            verification_status,
            last_verified,
            created_at
        FROM user_api_keys
        WHERE user_id = ?
        ORDER BY provider
        """
        return self.db.execute_query(query, (self.user_id,), fetch_all=True)

    def enable_provider(self, provider: str, enabled: bool = True) -> bool:
        """
        Enable or disable a provider.

        Args:
            provider: Provider name
            enabled: True to enable, False to disable

        Returns:
            True if successful
        """
        try:
            query = """
            UPDATE user_api_keys
            SET is_enabled = ?
            WHERE user_id = ? AND provider = ?
            """
            self.db.execute_query(query, (1 if enabled else 0, self.user_id, provider))
            logger.info(f"{'Enabled' if enabled else 'Disabled'} provider: {provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to toggle provider {provider}: {e}")
            return False

    def delete_key(self, provider: str) -> bool:
        """
        Delete API key for provider.

        Args:
            provider: Provider name

        Returns:
            True if successful
        """
        try:
            query = "DELETE FROM user_api_keys WHERE user_id = ? AND provider = ?"
            self.db.execute_query(query, (self.user_id, provider))
            logger.info(f"Deleted API key for {provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete key for {provider}: {e}")
            return False

    def verify_key(self, provider: str) -> Dict[str, Any]:
        """
        Verify that an API key works by making a test call.

        Args:
            provider: Provider to verify

        Returns:
            Verification result
        """
        api_key = self.get_key(provider)
        if not api_key:
            return {
                'success': False,
                'error': 'No API key found for this provider'
            }

        try:
            # Make test API call based on provider
            if provider == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content("Say 'test'")
                success = bool(response.text)

            elif provider == 'groq':
                from groq import Groq
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                success = bool(response.choices[0].message.content)

            elif provider == 'deepseek':
                from openai import OpenAI
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com/v1"
                )
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                success = bool(response.choices[0].message.content)

            elif provider == 'openrouter':
                from openai import OpenAI
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                response = client.chat.completions.create(
                    model="anthropic/claude-3.5-sonnet",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                success = bool(response.choices[0].message.content)

            elif provider == 'cohere':
                import cohere
                client = cohere.Client(api_key)
                response = client.generate(prompt="test", max_tokens=10)
                success = bool(response.generations[0].text)

            elif provider == 'canvas':
                from canvasapi import Canvas
                # Extract Canvas URL from settings or use default
                canvas_url = "https://canvas.instructure.com"
                canvas = Canvas(canvas_url, api_key)
                user = canvas.get_current_user()
                success = bool(user.name)

            else:
                return {
                    'success': False,
                    'error': f'Verification not implemented for {provider}'
                }

            # Update verification status
            query = """
            UPDATE user_api_keys
            SET verification_status = ?,
                last_verified = CURRENT_TIMESTAMP
            WHERE user_id = ? AND provider = ?
            """
            self.db.execute_query(query, ('verified' if success else 'failed', self.user_id, provider))

            return {
                'success': success,
                'provider': provider,
                'message': 'API key verified successfully' if success else 'Verification failed'
            }

        except Exception as e:
            # Update as failed
            query = """
            UPDATE user_api_keys
            SET verification_status = 'failed',
                last_verified = CURRENT_TIMESTAMP
            WHERE user_id = ? AND provider = ?
            """
            self.db.execute_query(query, (self.user_id, provider))

            logger.error(f"Key verification failed for {provider}: {e}")
            return {
                'success': False,
                'provider': provider,
                'error': str(e)
            }

    def get_usage_today(self, provider: str) -> Dict[str, Any]:
        """
        Get usage stats for today for a provider.

        Args:
            provider: Provider name

        Returns:
            Usage statistics
        """
        record = self._get_key_record(provider)
        if not record:
            return {
                'requests_today': 0,
                'limit': 0,
                'remaining': 0
            }

        return {
            'requests_today': record['current_daily_requests'],
            'limit': record['daily_request_limit'],
            'remaining': record['daily_request_limit'] - record['current_daily_requests']
        }

    def increment_usage(self, provider: str) -> None:
        """
        Increment daily usage counter for provider.

        Args:
            provider: Provider name
        """
        query = """
        UPDATE user_api_keys
        SET current_daily_requests = current_daily_requests + 1
        WHERE user_id = ? AND provider = ?
        """
        self.db.execute_query(query, (self.user_id, provider))

    def reset_daily_counters(self) -> int:
        """
        Reset daily request counters (should run daily via scheduler).

        Returns:
            Number of counters reset
        """
        query = """
        UPDATE user_api_keys
        SET current_daily_requests = 0,
            last_reset_date = CURRENT_DATE
        WHERE user_id = ?
        AND last_reset_date < CURRENT_DATE
        """
        cursor = self.db.connection.cursor()
        cursor.execute(query, (self.user_id,))
        self.db.connection.commit()

        reset_count = cursor.rowcount
        if reset_count > 0:
            logger.info(f"Reset {reset_count} daily counters")
        return reset_count


if __name__ == "__main__":
    # Test API Key Manager
    print("Testing API Key Manager...")

    manager = APIKeyManager(user_id="test_user_123")

    # List all keys
    keys = manager.list_all_keys()
    print(f"Found {len(keys)} API keys")

    # Add test key
    result = manager.add_or_update_key(
        provider='gemini',
        api_key='test_key_12345',
        display_name='Test Gemini Key'
    )
    print(f"Add key result: {result}")

    # Enable/disable
    manager.enable_provider('gemini', enabled=True)
    print("Provider enabled")

    print("\nAPI Key Manager test completed!")
