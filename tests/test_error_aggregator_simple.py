"""
Simple unit tests for ErrorAggregator.

Tests error tracking and aggregation functionality.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.benchmark_intelligence.error_aggregator import ErrorAggregator


class TestErrorAggregator:
    """Test suite for ErrorAggregator class."""

    def test_init(self):
        """Test ErrorAggregator initialization."""
        aggregator = ErrorAggregator()
        summary = aggregator.get_summary()
        assert summary["total"] == 0

    def test_add_error(self):
        """Test adding errors."""
        aggregator = ErrorAggregator()

        aggregator.add_error("api_error", "model1", {"error": "timeout"})

        summary = aggregator.get_summary()
        assert summary["total"] == 1

    def test_multiple_errors(self):
        """Test adding multiple errors."""
        aggregator = ErrorAggregator()

        for i in range(5):
            aggregator.add_error("parse_error", f"model{i}", {"line": i})

        summary = aggregator.get_summary()
        assert summary["total"] == 5

    def test_error_types(self):
        """Test different error types."""
        aggregator = ErrorAggregator()

        aggregator.add_error("api_error", "model1", {})
        aggregator.add_error("parse_error", "model2", {})
        aggregator.add_error("validation_error", "model3", {})

        summary = aggregator.get_summary()
        assert summary["total"] == 3

    def test_clear_errors(self):
        """Test clearing errors."""
        aggregator = ErrorAggregator()

        aggregator.add_error("api_error", "model1", {})
        aggregator.add_error("api_error", "model2", {})

        assert aggregator.get_summary()["total"] == 2

        aggregator.clear()

        assert aggregator.get_summary()["total"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
