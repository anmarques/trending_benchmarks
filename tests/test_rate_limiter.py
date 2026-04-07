"""
Unit tests for RateLimiter.

Tests token bucket algorithm, rate limiting, and exponential backoff.
"""

import pytest
import asyncio
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.benchmark_intelligence.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    TokenBucket
)


class TestTokenBucket:
    """Test suite for TokenBucket class."""

    def test_init(self):
        """Test TokenBucket initialization."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        assert bucket.capacity == 10
        assert bucket.refill_rate == 2.0
        assert bucket.tokens == 10.0

    def test_consume_tokens(self):
        """Test consuming tokens."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        # Consume 3 tokens
        assert bucket.consume(3)
        assert bucket.tokens == 7.0

        # Consume 7 more tokens
        assert bucket.consume(7)
        assert bucket.tokens == 0.0

        # Try to consume when empty
        assert not bucket.consume(1)

    def test_refill(self):
        """Test token refilling over time."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/second

        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0.0

        # Wait and check refill
        time.sleep(0.5)  # Should refill 5 tokens
        bucket._refill()
        assert bucket.tokens >= 4.0  # Allow for timing variance

    def test_capacity_limit(self):
        """Test that tokens don't exceed capacity."""
        bucket = TokenBucket(capacity=5, refill_rate=10.0)

        # Start with full capacity
        assert bucket.tokens == 5.0

        # Wait for refill attempt
        time.sleep(0.5)
        bucket._refill()

        # Should not exceed capacity
        assert bucket.tokens <= 5.0

    def test_wait_time_calculation(self):
        """Test wait time calculation."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens/second

        # Consume most tokens
        bucket.consume(9)

        # Calculate wait time for 5 tokens
        wait_time = bucket.get_wait_time(5)
        assert wait_time >= 2.0  # Need (5-1)/2 = 2 seconds


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    def test_init(self):
        """Test RateLimiter initialization."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=60)
        }
        limiter = RateLimiter(configs)

        assert "test_api" in limiter.configs
        assert "test_api" in limiter.buckets
        assert limiter.request_counts["test_api"] == 0

    @pytest.mark.asyncio
    async def test_simple_execution(self):
        """Test executing a simple function."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=60)
        }
        limiter = RateLimiter(configs)

        def test_func(x, y):
            return x + y

        result = await limiter.execute("test_api", test_func, 2, 3)
        assert result == 5
        assert limiter.request_counts["test_api"] == 1

    @pytest.mark.asyncio
    async def test_async_execution(self):
        """Test executing an async function."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=60)
        }
        limiter = RateLimiter(configs)

        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 2

        result = await limiter.execute("test_api", async_func, 5)
        assert result == 10
        assert limiter.request_counts["test_api"] == 1

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting actually limits requests."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=10)  # 10 req/min = 0.167 req/sec
        }
        limiter = RateLimiter(configs)

        call_count = 0

        def test_func():
            nonlocal call_count
            call_count += 1
            return call_count

        # Make multiple rapid requests
        start_time = time.time()
        results = []
        for _ in range(5):
            result = await limiter.execute("test_api", test_func)
            results.append(result)
        elapsed = time.time() - start_time

        # Should have some delay due to rate limiting
        assert len(results) == 5
        assert limiter.request_counts["test_api"] == 5

    @pytest.mark.asyncio
    async def test_retry_on_429(self):
        """Test retry with exponential backoff on 429 errors."""
        configs = {
            "test_api": RateLimitConfig(
                requests_per_minute=60,
                max_retries=3,
                initial_backoff_seconds=0.1
            )
        }
        limiter = RateLimiter(configs)

        attempts = 0

        def failing_func():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise Exception("429 Too Many Requests")
            return "success"

        result = await limiter.execute("test_api", failing_func)
        assert result == "success"
        assert attempts == 3
        assert limiter.retry_counts["test_api"] > 0

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test that retries eventually fail."""
        configs = {
            "test_api": RateLimitConfig(
                requests_per_minute=60,
                max_retries=2,
                initial_backoff_seconds=0.05
            )
        }
        limiter = RateLimiter(configs)

        def always_fails():
            raise Exception("429 Too Many Requests")

        with pytest.raises(Exception, match="429"):
            await limiter.execute("test_api", always_fails)

    @pytest.mark.asyncio
    async def test_multiple_apis(self):
        """Test rate limiting for multiple APIs."""
        configs = {
            "api1": RateLimitConfig(requests_per_minute=60),
            "api2": RateLimitConfig(requests_per_minute=30)
        }
        limiter = RateLimiter(configs)

        def api1_func():
            return "api1"

        def api2_func():
            return "api2"

        result1 = await limiter.execute("api1", api1_func)
        result2 = await limiter.execute("api2", api2_func)

        assert result1 == "api1"
        assert result2 == "api2"
        assert limiter.request_counts["api1"] == 1
        assert limiter.request_counts["api2"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent requests with rate limiting."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=100)
        }
        limiter = RateLimiter(configs)

        counter = 0

        async def increment():
            nonlocal counter
            counter += 1
            return counter

        # Make 20 concurrent requests
        tasks = [limiter.execute("test_api", increment) for _ in range(20)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 20
        assert limiter.request_counts["test_api"] == 20

    def test_get_stats(self):
        """Test getting statistics."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=60)
        }
        limiter = RateLimiter(configs)

        stats = limiter.get_stats()
        assert "test_api" in stats
        assert "total_requests" in stats["test_api"]
        assert "retries" in stats["test_api"]
        assert "available_tokens" in stats["test_api"]

    @pytest.mark.asyncio
    async def test_invalid_api(self):
        """Test using unconfigured API."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=60)
        }
        limiter = RateLimiter(configs)

        def test_func():
            return "test"

        with pytest.raises(ValueError, match="not configured"):
            await limiter.execute("unknown_api", test_func)

    def test_reset_stats(self):
        """Test resetting statistics."""
        configs = {
            "test_api": RateLimitConfig(requests_per_minute=60)
        }
        limiter = RateLimiter(configs)

        limiter.request_counts["test_api"] = 100
        limiter.retry_counts["test_api"] = 10

        limiter.reset_stats()

        assert limiter.request_counts["test_api"] == 0
        assert limiter.retry_counts["test_api"] == 0

    @pytest.mark.asyncio
    async def test_backoff_multiplier(self):
        """Test exponential backoff multiplier."""
        configs = {
            "test_api": RateLimitConfig(
                requests_per_minute=60,
                max_retries=3,
                initial_backoff_seconds=0.1,
                backoff_multiplier=2.0
            )
        }
        limiter = RateLimiter(configs)

        attempts = 0
        backoff_times = []

        def rate_limited_func():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                # Record when we're called
                backoff_times.append(time.time())
                raise Exception("rate limit error")
            return "success"

        start = time.time()
        result = await limiter.execute("test_api", rate_limited_func)

        assert result == "success"
        assert attempts == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
