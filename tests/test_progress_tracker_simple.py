"""
Simple unit tests for ProgressTracker.

Tests progress tracking functionality.
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.benchmark_intelligence.progress_tracker import ProgressTracker


class TestProgressTracker:
    """Test suite for ProgressTracker class."""

    def test_init(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(total_models=100, enable_console_updates=False)
        stats = tracker.get_stats()
        assert stats["models_processed"] == 0
        assert stats["benchmarks_extracted"] == 0

    def test_increment_models(self):
        """Test incrementing model counter."""
        tracker = ProgressTracker(total_models=100, enable_console_updates=False)

        tracker.increment_models_processed()
        tracker.increment_models_processed()

        stats = tracker.get_stats()
        assert stats["models_processed"] == 2

    def test_increment_benchmarks(self):
        """Test incrementing benchmark counter."""
        tracker = ProgressTracker(total_models=100, enable_console_updates=False)

        tracker.increment_benchmarks_extracted(5)
        tracker.increment_benchmarks_extracted(10)

        stats = tracker.get_stats()
        assert stats["benchmarks_extracted"] == 15

    def test_errors(self):
        """Test error tracking."""
        tracker = ProgressTracker(total_models=100, enable_console_updates=False)

        tracker.increment_errors_encountered()
        tracker.increment_errors_encountered()

        stats = tracker.get_stats()
        assert stats["errors_encountered"] == 2

    def test_elapsed_time(self):
        """Test elapsed time tracking."""
        tracker = ProgressTracker(total_models=100, enable_console_updates=False)
        tracker.start()

        time.sleep(0.1)

        stats = tracker.get_stats()
        assert stats["elapsed_time"] > 0

        tracker.stop()

    def test_start_stop(self):
        """Test start and stop functionality."""
        tracker = ProgressTracker(total_models=100, enable_console_updates=False)

        tracker.start()
        assert tracker.is_running()

        tracker.stop()
        # Give it time to stop
        time.sleep(0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
