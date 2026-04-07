"""
Unit tests for ConnectionPool.

Tests the connection pooling functionality for managing HTTP connections.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.benchmark_intelligence.connection_pool import ConnectionPool


class TestConnectionPool:
    """Test suite for ConnectionPool class."""

    def test_init_default_size(self):
        """Test ConnectionPool initialization with default size."""
        pool = ConnectionPool()
        assert pool.pool_size == 10
        assert pool.timeout == 30
        assert len(pool.connections) == 0

    def test_init_custom_size(self):
        """Test ConnectionPool initialization with custom size."""
        pool = ConnectionPool(pool_size=20, timeout=60)
        assert pool.pool_size == 20
        assert pool.timeout == 60

    @pytest.mark.asyncio
    async def test_connection_acquisition(self):
        """Test acquiring a connection from the pool."""
        pool = ConnectionPool(pool_size=5)

        # Acquire a connection
        async with pool.acquire() as conn:
            assert conn is not None

    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """Test that connections are reused from the pool."""
        pool = ConnectionPool(pool_size=3)

        # Acquire and release multiple connections
        connections_acquired = []
        for _ in range(5):
            async with pool.acquire() as conn:
                connections_acquired.append(id(conn))

        # Should have reused connections (pool size is 3)
        assert len(set(connections_acquired)) <= 3

    @pytest.mark.asyncio
    async def test_concurrent_acquisitions(self):
        """Test concurrent connection acquisitions."""
        pool = ConnectionPool(pool_size=5)
        results = []

        async def acquire_connection():
            async with pool.acquire() as conn:
                results.append(conn)
                await asyncio.sleep(0.01)

        # Create multiple concurrent tasks
        tasks = [acquire_connection() for _ in range(10)]
        await asyncio.gather(*tasks)

        # All acquisitions should succeed
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_pool_exhaustion(self):
        """Test behavior when pool is exhausted."""
        pool = ConnectionPool(pool_size=2)
        acquired = []

        async def hold_connection():
            async with pool.acquire() as conn:
                acquired.append(conn)
                await asyncio.sleep(0.1)

        # Start tasks that will hold connections
        tasks = [hold_connection() for _ in range(4)]
        await asyncio.gather(*tasks)

        # Should still complete all tasks (with queuing)
        assert len(acquired) == 4

    def test_get_stats(self):
        """Test statistics collection."""
        pool = ConnectionPool(pool_size=5)
        stats = pool.get_stats()

        assert "pool_size" in stats
        assert "active_connections" in stats
        assert "available_connections" in stats
        assert stats["pool_size"] == 5

    @pytest.mark.asyncio
    async def test_close_pool(self):
        """Test closing the connection pool."""
        pool = ConnectionPool(pool_size=3)

        # Acquire some connections
        async with pool.acquire() as conn:
            assert conn is not None

        # Close the pool
        await pool.close()

        stats = pool.get_stats()
        assert stats["active_connections"] == 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout configuration."""
        pool = ConnectionPool(pool_size=2, timeout=5)
        assert pool.timeout == 5

        # Ensure timeout is respected
        async with pool.acquire() as conn:
            assert conn is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
