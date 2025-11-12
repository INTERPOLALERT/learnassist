"""
Academic Command Center - AI Router
Routes AI tasks to optimal providers, prevents simultaneous calls,
handles caching, fallbacks, and cost tracking.

CRITICAL: Only ONE API call per provider at any time!
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from threading import Lock, Thread
from queue import Queue, Empty
import logging

# AI API clients will be imported dynamically
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
import cohere
import anthropic

from .database import DatabaseManager, DatabaseHelper
from .encryption import EncryptionService

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AIRouter:
    """
    Central AI request router with queueing to prevent simultaneous calls.

    Features:
    - Request queueing (ONE call per provider at a time)
    - Response caching
    - Automatic fallback on failure
    - Cost tracking
    - Provider selection based on task type
    """

    def __init__(
        self,
        user_id: str,
        db_manager: Optional[DatabaseManager] = None,
        encryption: Optional[EncryptionService] = None
    ):
        """
        Initialize AI Router.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
            encryption: Encryption service instance
        """
        self.user_id = user_id

        # Initialize services
        self.db = db_manager or DatabaseManager()
        self.db_helper = DatabaseHelper(self.db)
        self.encryption = encryption or EncryptionService()

        # Request queues (one per provider)
        self.queues: Dict[str, Queue] = {
            'gemini': Queue(),
            'groq': Queue(),
            'deepseek': Queue(),
            'openrouter': Queue(),
            'cohere': Queue()
        }

        # Locks to ensure only one request processing per provider
        self.locks: Dict[str, Lock] = {
            provider: Lock() for provider in self.queues.keys()
        }

        # Track active requests
        self.active_requests: Dict[str, bool] = {
            provider: False for provider in self.queues.keys()
        }

        # Start queue workers
        self.workers: Dict[str, Thread] = {}
        self._start_workers()

        # Load API keys
        self.api_keys = self._load_api_keys()

        # Initialize API clients
        self.clients = self._initialize_clients()

        # Task type routing configuration
        self.task_routing = self._configure_task_routing()

        # Cost tracking (per 1K tokens in USD)
        self.cost_rates = {
            'gemini': 0.00025,
            'groq': 0.0001,
            'deepseek': 0.00014,
            'openrouter_claude': 0.003,
            'cohere': 0.0002
        }

    def _load_api_keys(self) -> Dict[str, str]:
        """
        Load and decrypt user's API keys from database.

        Returns:
            Dictionary of provider -> API key
        """
        query = """
        SELECT provider, api_key_encrypted, api_key_iv
        FROM user_api_keys
        WHERE user_id = ? AND is_enabled = 1
        """

        rows = self.db.execute_query(query, (self.user_id,), fetch_all=True)

        api_keys = {}
        for row in rows:
            provider = row['provider']

            # Skip Canvas (not AI provider)
            if provider == 'canvas':
                continue

            try:
                # Decrypt API key
                encrypted_hex = row['api_key_encrypted']
                iv_hex = row['api_key_iv']
                decrypted_key = self.encryption.decrypt_from_hex(encrypted_hex, iv_hex)

                api_keys[provider] = decrypted_key
                logger.debug(f"Loaded API key for {provider}")

            except Exception as e:
                logger.error(f"Failed to decrypt {provider} key: {e}")

        return api_keys

    def _initialize_clients(self) -> Dict[str, Any]:
        """
        Initialize API clients for each provider.

        Returns:
            Dictionary of provider -> client instance
        """
        clients = {}

        # Gemini
        if 'gemini' in self.api_keys:
            genai.configure(api_key=self.api_keys['gemini'])
            clients['gemini'] = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini client initialized")

        # Groq
        if 'groq' in self.api_keys:
            clients['groq'] = Groq(api_key=self.api_keys['groq'])
            logger.info("Groq client initialized")

        # DeepSeek (OpenAI-compatible)
        if 'deepseek' in self.api_keys:
            clients['deepseek'] = OpenAI(
                api_key=self.api_keys['deepseek'],
                base_url="https://api.deepseek.com/v1"
            )
            logger.info("DeepSeek client initialized")

        # OpenRouter (for Claude)
        if 'openrouter' in self.api_keys:
            clients['openrouter'] = OpenAI(
                api_key=self.api_keys['openrouter'],
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("OpenRouter client initialized")

        # Cohere
        if 'cohere' in self.api_keys:
            clients['cohere'] = cohere.Client(self.api_keys['cohere'])
            logger.info("Cohere client initialized")

        return clients

    def _configure_task_routing(self) -> Dict[str, Dict[str, Any]]:
        """
        Configure which provider to use for each task type.

        Returns:
            Task routing configuration
        """
        return {
            'parse_essay_instructions': {
                'primary': 'gemini',
                'fallback': 'groq',
                'cache_hours': 168  # 7 days
            },
            'generate_subtasks': {
                'primary': 'groq',
                'fallback': 'deepseek',
                'cache_hours': 24
            },
            'analyze_material_content': {
                'primary': 'gemini',
                'fallback': 'groq',
                'cache_hours': -1  # Cache forever (content doesn't change)
            },
            'semantic_search': {
                'primary': 'cohere',
                'fallback': 'gemini',
                'cache_hours': -1
            },
            'check_grammar': {
                'primary': 'deepseek',
                'fallback': 'groq',
                'cache_hours': 0  # Never cache
            },
            'rubric_analysis': {
                'primary': 'openrouter',  # Claude for best reasoning
                'fallback': 'gemini',
                'cache_hours': 168
            },
            'expand_idea': {
                'primary': 'gemini',
                'fallback': 'groq',
                'cache_hours': 0
            },
            'paraphrase': {
                'primary': 'deepseek',
                'fallback': 'groq',
                'cache_hours': 0
            },
            'find_evidence': {
                'primary': 'gemini',
                'fallback': 'groq',
                'cache_hours': 24
            }
        }

    def _start_workers(self) -> None:
        """Start background worker threads for each provider queue."""
        for provider in self.queues.keys():
            worker = Thread(
                target=self._queue_worker,
                args=(provider,),
                daemon=True,
                name=f"AI-Worker-{provider}"
            )
            worker.start()
            self.workers[provider] = worker
            logger.debug(f"Started worker thread for {provider}")

    def _queue_worker(self, provider: str) -> None:
        """
        Background worker that processes queued requests.

        Args:
            provider: Provider name (gemini, groq, etc.)
        """
        queue = self.queues[provider]
        lock = self.locks[provider]

        while True:
            try:
                # Get next request from queue (blocking)
                request_data = queue.get(timeout=1)

                # Process with lock to ensure only one at a time
                with lock:
                    self.active_requests[provider] = True
                    logger.debug(f"[{provider}] Processing request...")

                    try:
                        # Execute the actual API call
                        result = self._execute_provider_request(
                            provider,
                            request_data
                        )

                        # Put result in response callback
                        if 'callback' in request_data:
                            request_data['callback'](result)

                    except Exception as e:
                        logger.error(f"[{provider}] Request failed: {e}")
                        if 'callback' in request_data:
                            request_data['callback']({
                                'success': False,
                                'error': str(e)
                            })

                    finally:
                        self.active_requests[provider] = False
                        queue.task_done()

            except Empty:
                # No requests in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Worker error for {provider}: {e}")

    def _execute_provider_request(
        self,
        provider: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute actual API request to provider.

        Args:
            provider: Provider name
            request_data: Request parameters

        Returns:
            Response dictionary
        """
        start_time = time.time()

        try:
            client = self.clients.get(provider)
            if not client:
                raise ValueError(f"No client for provider: {provider}")

            prompt = request_data['prompt']
            temperature = request_data.get('temperature', 0.7)
            max_tokens = request_data.get('max_tokens', 2000)

            response_text = None
            tokens_used = 0

            # Call appropriate provider
            if provider == 'gemini':
                response = client.generate_content(
                    prompt,
                    generation_config={
                        'temperature': temperature,
                        'max_output_tokens': max_tokens
                    }
                )
                response_text = response.text
                # Estimate tokens (Gemini doesn't always return token count)
                tokens_used = len(response_text.split()) * 1.3  # Rough estimate

            elif provider == 'groq':
                response = client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                response_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens

            elif provider == 'deepseek':
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                response_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens

            elif provider == 'openrouter':
                response = client.chat.completions.create(
                    model="anthropic/claude-3.5-sonnet",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                response_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens

            elif provider == 'cohere':
                response = client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                response_text = response.generations[0].text
                tokens_used = response.meta.billed_units.output_tokens

            else:
                raise ValueError(f"Unknown provider: {provider}")

            # Calculate cost
            cost = (tokens_used / 1000) * self.cost_rates.get(provider, 0.001)
            response_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"[{provider}] Success: {tokens_used} tokens, "
                f"${cost:.4f}, {response_time_ms}ms"
            )

            return {
                'success': True,
                'provider': provider,
                'response': response_text,
                'tokens_used': tokens_used,
                'cost_usd': cost,
                'response_time_ms': response_time_ms
            }

        except Exception as e:
            logger.error(f"[{provider}] API call failed: {e}")
            return {
                'success': False,
                'provider': provider,
                'error': str(e)
            }

    def execute_task(
        self,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an AI task with automatic routing, caching, and fallback.

        Args:
            task_data: {
                'task_type': str,
                'payload': {
                    'prompt': str,
                    'temperature': float,
                    'max_tokens': int
                },
                'cache_key': Optional[str],
                'cache_duration_hours': Optional[int]
            }

        Returns:
            {
                'success': bool,
                'data': str (if success),
                'error': str (if failure),
                'provider': str,
                'cached': bool,
                'cost_usd': float
            }
        """
        task_type = task_data['task_type']
        payload = task_data['payload']
        custom_cache_key = task_data.get('cache_key')

        # Get routing config
        routing = self.task_routing.get(task_type)
        if not routing:
            return {
                'success': False,
                'error': f'Unknown task type: {task_type}'
            }

        # Generate cache key
        if custom_cache_key:
            cache_key = custom_cache_key
        else:
            cache_key = self.encryption.generate_cache_key(
                task_type,
                self.user_id,
                payload['prompt']
            )

        # Check cache
        cached_response = self._check_cache(cache_key)
        if cached_response:
            logger.info(f"[CACHE HIT] {task_type}")
            return {
                'success': True,
                'data': cached_response,
                'cached': True,
                'cost_usd': 0.0
            }

        # Determine provider
        primary_provider = routing['primary']
        fallback_provider = routing['fallback']

        # Try primary provider
        result = self._enqueue_request(primary_provider, payload)

        # If primary fails, try fallback
        if not result['success'] and fallback_provider:
            logger.warning(f"Primary ({primary_provider}) failed, trying fallback ({fallback_provider})")
            result = self._enqueue_request(fallback_provider, payload)

        # If successful, cache the response
        if result['success']:
            cache_hours = task_data.get('cache_duration_hours', routing['cache_hours'])
            if cache_hours != 0:  # 0 means never cache
                self._cache_response(
                    task_type=task_type,
                    provider=result['provider'],
                    prompt=payload['prompt'],
                    response=result['response'],
                    cache_key=cache_key,
                    cache_hours=cache_hours,
                    tokens_used=result['tokens_used'],
                    cost_usd=result['cost_usd'],
                    response_time_ms=result['response_time_ms']
                )

            return {
                'success': True,
                'data': result['response'],
                'provider': result['provider'],
                'cached': False,
                'cost_usd': result['cost_usd'],
                'tokens_used': result['tokens_used'],
                'response_time_ms': result['response_time_ms']
            }
        else:
            return {
                'success': False,
                'error': result['error'],
                'provider': result.get('provider', 'unknown')
            }

    def _enqueue_request(
        self,
        provider: str,
        payload: Dict[str, Any],
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Enqueue request and wait for response.

        Args:
            provider: Provider to use
            payload: Request payload
            timeout: Timeout in seconds

        Returns:
            Response dictionary
        """
        if provider not in self.clients:
            return {
                'success': False,
                'error': f'Provider not available: {provider}'
            }

        # Create response container
        response_container = {'result': None}

        def callback(result):
            response_container['result'] = result

        # Add to queue
        request = {
            'prompt': payload['prompt'],
            'temperature': payload.get('temperature', 0.7),
            'max_tokens': payload.get('max_tokens', 2000),
            'callback': callback
        }

        self.queues[provider].put(request)
        logger.debug(f"Enqueued request to {provider}")

        # Wait for response (with timeout)
        start_wait = time.time()
        while response_container['result'] is None:
            if time.time() - start_wait > timeout:
                return {
                    'success': False,
                    'error': f'Request timeout after {timeout}s'
                }
            time.sleep(0.1)

        return response_container['result']

    def _check_cache(self, cache_key: str) -> Optional[str]:
        """
        Check if cached response exists and is not expired.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Cached response text or None
        """
        return self.db_helper.get_cached_ai_response(cache_key)

    def _cache_response(
        self,
        task_type: str,
        provider: str,
        prompt: str,
        response: str,
        cache_key: str,
        cache_hours: int,
        tokens_used: int,
        cost_usd: float,
        response_time_ms: int
    ) -> None:
        """
        Cache AI response in database.

        Args:
            task_type: Task type
            provider: Provider used
            prompt: Original prompt
            response: AI response
            cache_key: Cache key
            cache_hours: How long to cache (-1 = forever)
            tokens_used: Tokens used
            cost_usd: Cost in USD
            response_time_ms: Response time
        """
        if cache_hours == -1:
            # Cache forever (set expiry to 100 years from now)
            expires_at = datetime.now() + timedelta(days=36500)
        else:
            expires_at = datetime.now() + timedelta(hours=cache_hours)

        self.db_helper.log_ai_interaction(
            user_id=self.user_id,
            task_type=task_type,
            provider=provider,
            prompt=prompt,
            response=response,
            cache_key=cache_key,
            cache_duration_hours=cache_hours
        )

        logger.debug(f"Cached response with key: {cache_key}")

    def get_usage_stats(self, time_period: str = 'today') -> Dict[str, Any]:
        """
        Get AI API usage statistics.

        Args:
            time_period: 'today', 'week', 'month', 'all'

        Returns:
            Usage statistics
        """
        # Determine time filter
        if time_period == 'today':
            time_filter = "DATE(created_at) = DATE('now')"
        elif time_period == 'week':
            time_filter = "created_at >= DATE('now', '-7 days')"
        elif time_period == 'month':
            time_filter = "created_at >= DATE('now', '-30 days')"
        else:
            time_filter = "1=1"

        query = f"""
        SELECT
            provider,
            COUNT(*) as request_count,
            SUM(tokens_used) as total_tokens,
            SUM(estimated_cost_usd) as total_cost,
            AVG(response_time_ms) as avg_response_time,
            SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as cache_hits
        FROM ai_interactions
        WHERE user_id = ? AND {time_filter}
        GROUP BY provider
        """

        stats = self.db.execute_query(query, (self.user_id,), fetch_all=True)

        # Calculate totals
        total_cost = sum(s['total_cost'] or 0 for s in stats)
        total_requests = sum(s['request_count'] for s in stats)
        total_cache_hits = sum(s['cache_hits'] for s in stats)

        # Calculate savings from caching
        cache_savings = self._calculate_cache_savings(time_period)

        return {
            'period': time_period,
            'by_provider': stats,
            'total_cost': round(total_cost, 4),
            'total_requests': total_requests,
            'total_cache_hits': total_cache_hits,
            'cache_hit_rate': round(total_cache_hits / total_requests * 100, 1) if total_requests > 0 else 0,
            'cache_savings_usd': cache_savings
        }

    def _calculate_cache_savings(self, time_period: str) -> float:
        """Calculate how much money was saved by caching."""
        # This would require tracking what the cost would have been without cache
        # For now, estimate based on cache hits
        stats = self.get_usage_stats(time_period)
        cache_hits = stats['total_cache_hits']

        # Average cost per request (very rough estimate)
        avg_cost = 0.002  # $0.002 per request on average

        return round(cache_hits * avg_cost, 4)

    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cached AI responses.

        Args:
            older_than_days: Only clear cache older than X days (None = clear all)

        Returns:
            Number of entries cleared
        """
        if older_than_days:
            query = """
            DELETE FROM ai_interactions
            WHERE user_id = ?
            AND cache_expires_at < DATE('now', ? || ' days')
            """
            params = (self.user_id, -older_than_days)
        else:
            query = "DELETE FROM ai_interactions WHERE user_id = ?"
            params = (self.user_id,)

        cursor = self.db.connection.cursor()
        cursor.execute(query, params)
        self.db.connection.commit()

        cleared = cursor.rowcount
        logger.info(f"Cleared {cleared} cached AI responses")
        return cleared


if __name__ == "__main__":
    # Test AI Router
    print("Testing AI Router...")

    # This would require actual API keys to test fully
    # For now, just test initialization
    try:
        router = AIRouter(user_id="test_user_123")
        print(f"AI Router initialized")
        print(f"Available providers: {list(router.clients.keys())}")
        print(f"Active requests: {router.active_requests}")

        print("\nAI Router test completed!")
    except Exception as e:
        print(f"Test failed (expected without real API keys): {e}")
