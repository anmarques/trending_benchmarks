"""
Unit tests for ErrorAggregator.

Tests error tracking, categorization, and reporting functionality.
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path
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
        """Test adding a single error."""
        aggregator = ErrorAggregator()

        aggregator.add_error(
            error_type="api_error",
            model_id="test_model",
            details={"url": "https://api.example.com", "error": "timeout"}
        )

        summary = aggregator.get_summary()
        assert summary["total"] == 1
        assert "api_error" in summary["by_type"]
        assert summary["by_type"]["api_error"]["count"] == 1

    def test_record_multiple_errors(self):
        """Test recording multiple errors."""
        aggregator = ErrorAggregator()

        for i in range(5):
            aggregator.record_error(
                category=ErrorCategory.PARSE_ERROR,
                message=f"Parse error {i}",
                context={"line": i}
            )

        assert aggregator.get_total_count() == 5
        errors = aggregator.get_errors_by_category(ErrorCategory.PARSE_ERROR)
        assert len(errors) == 5

    def test_error_categories(self):
        """Test different error categories."""
        aggregator = ErrorAggregator()

        aggregator.record_error(ErrorCategory.API_ERROR, "API failed")
        aggregator.record_error(ErrorCategory.PARSE_ERROR, "Parse failed")
        aggregator.record_error(ErrorCategory.VALIDATION_ERROR, "Invalid data")
        aggregator.record_error(ErrorCategory.NETWORK_ERROR, "Network timeout")

        assert aggregator.get_total_count() == 4
        assert len(aggregator.get_errors_by_category(ErrorCategory.API_ERROR)) == 1
        assert len(aggregator.get_errors_by_category(ErrorCategory.PARSE_ERROR)) == 1
        assert len(aggregator.get_errors_by_category(ErrorCategory.VALIDATION_ERROR)) == 1
        assert len(aggregator.get_errors_by_category(ErrorCategory.NETWORK_ERROR)) == 1

    def test_get_errors_by_category(self):
        """Test filtering errors by category."""
        aggregator = ErrorAggregator()

        aggregator.record_error(ErrorCategory.API_ERROR, "Error 1")
        aggregator.record_error(ErrorCategory.API_ERROR, "Error 2")
        aggregator.record_error(ErrorCategory.PARSE_ERROR, "Error 3")

        api_errors = aggregator.get_errors_by_category(ErrorCategory.API_ERROR)
        parse_errors = aggregator.get_errors_by_category(ErrorCategory.PARSE_ERROR)

        assert len(api_errors) == 2
        assert len(parse_errors) == 1

    def test_get_summary(self):
        """Test getting error summary statistics."""
        aggregator = ErrorAggregator()

        aggregator.record_error(ErrorCategory.API_ERROR, "Error 1")
        aggregator.record_error(ErrorCategory.API_ERROR, "Error 2")
        aggregator.record_error(ErrorCategory.PARSE_ERROR, "Error 3")

        summary = aggregator.get_summary()

        assert summary["total_errors"] == 3
        assert ErrorCategory.API_ERROR.value in summary["by_category"]
        assert summary["by_category"][ErrorCategory.API_ERROR.value] == 2
        assert summary["by_category"][ErrorCategory.PARSE_ERROR.value] == 1

    def test_get_recent_errors(self):
        """Test getting recent errors."""
        aggregator = ErrorAggregator()

        for i in range(10):
            aggregator.record_error(
                category=ErrorCategory.API_ERROR,
                message=f"Error {i}"
            )

        recent = aggregator.get_recent_errors(limit=5)
        assert len(recent) == 5

    def test_clear_errors(self):
        """Test clearing all errors."""
        aggregator = ErrorAggregator()

        aggregator.record_error(ErrorCategory.API_ERROR, "Error 1")
        aggregator.record_error(ErrorCategory.PARSE_ERROR, "Error 2")

        assert aggregator.get_total_count() == 2

        aggregator.clear()

        assert aggregator.get_total_count() == 0
        assert len(aggregator.errors) == 0

    def test_error_context(self):
        """Test error context storage."""
        aggregator = ErrorAggregator()

        context = {
            "model_id": "test/model",
            "url": "https://example.com",
            "attempt": 3
        }

        aggregator.record_error(
            category=ErrorCategory.API_ERROR,
            message="Request failed",
            context=context
        )

        errors = aggregator.get_errors_by_category(ErrorCategory.API_ERROR)
        assert errors[0].context == context

    def test_has_errors(self):
        """Test checking if errors exist."""
        aggregator = ErrorAggregator()

        assert not aggregator.has_errors()

        aggregator.record_error(ErrorCategory.API_ERROR, "Error")

        assert aggregator.has_errors()

    def test_error_timestamp(self):
        """Test that errors have timestamps."""
        aggregator = ErrorAggregator()

        before = datetime.now()
        aggregator.record_error(ErrorCategory.API_ERROR, "Error")
        after = datetime.now()

        errors = aggregator.get_errors_by_category(ErrorCategory.API_ERROR)
        assert before <= errors[0].timestamp <= after

    def test_concurrent_error_recording(self):
        """Test thread-safe error recording."""
        import threading

        aggregator = ErrorAggregator()

        def record_errors():
            for i in range(100):
                aggregator.record_error(
                    category=ErrorCategory.API_ERROR,
                    message=f"Error {i}"
                )

        threads = [threading.Thread(target=record_errors) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have all errors recorded
        assert aggregator.get_total_count() == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
