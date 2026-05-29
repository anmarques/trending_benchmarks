"""
Rate limiting functionality using token bucket algorithm.

Implements rate limiting for API requests with exponential backoff on 429 errors.
Supports per-API rate limits with configurable request quotas.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """Token bucket implementation for rate limiting."""

    capacity: int  # Maximum tokens (requests) allowed
    refill_rate: float  # Tokens added per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.time()

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Calculate wait time until requested tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Wait time in seconds
        """
        self._refill()

        if self.tokens >= tokens:
            return 0.0

        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


@dataclass
class RateLimitConfig:
    """Configuration for a rate-limited API."""

    requests_per_minute: int
    max_retries: int = 5
    initial_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0


class RateLimiter:
    """
    Manages rate limiting for multiple APIs using token bucket algorithm.

    Features:
    - Per-API rate limiting with token bucket algorithm
    - Request queuing with automatic retry
    - Exponential backoff on 429 errors
    - Concurrent request handling
    """

    def __init__(self, api_configs: Dict[str, RateLimitConfig]):
        """
        Initialize rate limiter with API configurations.

        Args:
            api_configs: Dictionary mapping API names to their rate limit configs
        """
        self.configs = api_configs
        self.buckets: Dict[str, TokenBucket] = {}
        self.locks: Dict[str, asyncio.Lock] = {}

        # Initialize token buckets for each API
        for api_name, config in api_configs.items():
            capacity = config.requests_per_minute
            refill_rate = config.requests_per_minute / 60.0  # tokens per second

            self.buckets[api_name] = TokenBucket(
                capacity=capacity,
                refill_rate=refill_rate
            )
            self.locks[api_name] = asyncio.Lock()

        # Statistics
        self.request_counts: Dict[str, int] = {api: 0 for api in api_configs}
        self.retry_counts: Dict[str, int] = {api: 0 for api in api_configs}
        self.backoff_counts: Dict[str, int] = {api: 0 for api in api_configs}

    async def execute(
        self,
        api_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with rate limiting and automatic retry.

        Args:
            api_name: Name of the API (must be in api_configs)
            func: Function to execute (can be sync or async)
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            ValueError: If api_name is not configured
            Exception: If all retries are exhausted
        """
        if api_name not in self.configs:
            raise ValueError(f"API '{api_name}' not configured in rate limiter")

        config = self.configs[api_name]
        bucket = self.buckets[api_name]
        lock = self.locks[api_name]

        retry_count = 0
        backoff_time = config.initial_backoff_seconds

        while retry_count <= config.max_retries:
            # Wait for token availability
            async with lock:
                wait_time = bucket.get_wait_time(tokens=1)
                if wait_time > 0:
                    logger.debug(f"Rate limit wait for {api_name}: {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)

                # Consume token
                while not bucket.consume(tokens=1):
                    await asyncio.sleep(0.1)

                self.request_counts[api_name] += 1

            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                return result

            except Exception as e:
                error_msg = str(e)
                is_rate_limit_error = (
                    "429" in error_msg or
                    "rate limit" in error_msg.lower() or
                    "too many requests" in error_msg.lower()
                )

                if is_rate_limit_error and retry_count < config.max_retries:
                    self.retry_counts[api_name] += 1
                    self.backoff_counts[api_name] += 1

                    logger.warning(
                        f"Rate limit hit for {api_name} (retry {retry_count + 1}/{config.max_retries}). "
                        f"Backing off for {backoff_time:.2f}s"
                    )

                    await asyncio.sleep(backoff_time)
                    backoff_time = min(
                        backoff_time * config.backoff_multiplier,
                        config.max_backoff_seconds
                    )
                    retry_count += 1
                else:
                    # Non-rate-limit error or retries exhausted
                    raise

        # Should not reach here, but just in case
        raise Exception(f"Rate limit retries exhausted for {api_name}")

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all APIs.

        Returns:
            Dictionary with stats per API
        """
        stats = {}
        for api_name in self.configs:
            bucket = self.buckets[api_name]
            stats[api_name] = {
                "total_requests": self.request_counts[api_name],
                "retries": self.retry_counts[api_name],
                "backoffs": self.backoff_counts[api_name],
                "available_tokens": int(bucket.tokens),
                "capacity": bucket.capacity
            }
        return stats

    def reset_stats(self):
        """Reset all statistics counters."""
        for api_name in self.configs:
            self.request_counts[api_name] = 0
            self.retry_counts[api_name] = 0
            self.backoff_counts[api_name] = 0


def create_default_rate_limiter() -> RateLimiter:
    """
    Create a rate limiter with default API configurations.

    Returns:
        Configured RateLimiter instance
    """
    api_configs = {
        "huggingface": RateLimitConfig(
            requests_per_minute=60,  # Conservative default
            max_retries=5,
            initial_backoff_seconds=2.0,
            max_backoff_seconds=60.0
        ),
        "anthropic": RateLimitConfig(
            requests_per_minute=50,  # API tier dependent
            max_retries=5,
            initial_backoff_seconds=2.0,
            max_backoff_seconds=120.0
        ),
        "arxiv": RateLimitConfig(
            requests_per_minute=30,  # Be nice to arXiv
            max_retries=3,
            initial_backoff_seconds=1.0,
            max_backoff_seconds=30.0
        )
    }

    return RateLimiter(api_configs)
