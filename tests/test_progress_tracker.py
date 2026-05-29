"""
Unit tests for ProgressTracker.

Tests progress tracking, milestone tracking, and reporting functionality.
"""

import pytest
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.benchmark_intelligence.progress_tracker import (
    ProgressTracker,
    Stage,
    StageProgress
)


class TestProgressTracker:
    """Test suite for ProgressTracker class."""

    def test_init(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(total_items=100)
        assert tracker.total_items == 100
        assert tracker.completed_items == 0
        assert tracker.get_progress_percentage() == 0.0

    def test_increment_progress(self):
        """Test incrementing progress."""
        tracker = ProgressTracker(total_items=100)

        tracker.increment(10)
        assert tracker.completed_items == 10
        assert tracker.get_progress_percentage() == 10.0

        tracker.increment(15)
        assert tracker.completed_items == 25
        assert tracker.get_progress_percentage() == 25.0

    def test_set_progress(self):
        """Test setting progress directly."""
        tracker = ProgressTracker(total_items=100)

        tracker.set_progress(50)
        assert tracker.completed_items == 50
        assert tracker.get_progress_percentage() == 50.0

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        tracker = ProgressTracker(total_items=200)

        tracker.increment(50)
        assert tracker.get_progress_percentage() == 25.0

        tracker.increment(50)
        assert tracker.get_progress_percentage() == 50.0

        tracker.increment(100)
        assert tracker.get_progress_percentage() == 100.0

    def test_stage_tracking(self):
        """Test stage-based progress tracking."""
        tracker = ProgressTracker(total_items=100)

        tracker.start_stage(Stage.FILTER_MODELS)
        assert tracker.current_stage == Stage.FILTER_MODELS

        tracker.increment(20)
        tracker.complete_stage(Stage.FILTER_MODELS)

        stage_progress = tracker.get_stage_progress(Stage.FILTER_MODELS)
        assert stage_progress.completed

    def test_multiple_stages(self):
        """Test tracking multiple stages."""
        tracker = ProgressTracker(total_items=100)

        # Stage 1
        tracker.start_stage(Stage.FILTER_MODELS)
        tracker.increment(20)
        tracker.complete_stage(Stage.FILTER_MODELS)

        # Stage 2
        tracker.start_stage(Stage.FIND_DOCS)
        tracker.increment(30)
        tracker.complete_stage(Stage.FIND_DOCS)

        assert tracker.get_stage_progress(Stage.FILTER_MODELS).completed
        assert tracker.get_stage_progress(Stage.FIND_DOCS).completed

    def test_elapsed_time(self):
        """Test elapsed time tracking."""
        tracker = ProgressTracker(total_items=100)

        time.sleep(0.1)  # Small delay

        elapsed = tracker.get_elapsed_time()
        assert elapsed > 0.0
        assert elapsed >= 0.1

    def test_estimated_remaining_time(self):
        """Test estimated remaining time calculation."""
        tracker = ProgressTracker(total_items=100)

        tracker.increment(50)
        time.sleep(0.1)

        remaining = tracker.get_estimated_remaining_time()
        assert remaining >= 0.0

    def test_get_summary(self):
        """Test getting progress summary."""
        tracker = ProgressTracker(total_items=100)

        tracker.start_stage(Stage.FILTER_MODELS)
        tracker.increment(25)

        summary = tracker.get_summary()

        assert summary["total_items"] == 100
        assert summary["completed_items"] == 25
        assert summary["progress_percentage"] == 25.0
        assert "elapsed_time" in summary
        assert "current_stage" in summary

    def test_reset_progress(self):
        """Test resetting progress."""
        tracker = ProgressTracker(total_items=100)

        tracker.increment(50)
        assert tracker.completed_items == 50

        tracker.reset()
        assert tracker.completed_items == 0
        assert tracker.get_progress_percentage() == 0.0

    def test_completion_detection(self):
        """Test detecting completion."""
        tracker = ProgressTracker(total_items=100)

        assert not tracker.is_complete()

        tracker.increment(100)
        assert tracker.is_complete()

    def test_overflow_protection(self):
        """Test that progress doesn't exceed total."""
        tracker = ProgressTracker(total_items=100)

        tracker.increment(120)  # Try to exceed
        assert tracker.completed_items <= 100
        assert tracker.get_progress_percentage() <= 100.0

    def test_stage_duration(self):
        """Test stage duration tracking."""
        tracker = ProgressTracker(total_items=100)

        tracker.start_stage(Stage.FILTER_MODELS)
        time.sleep(0.1)
        tracker.complete_stage(Stage.FILTER_MODELS)

        stage_progress = tracker.get_stage_progress(Stage.FILTER_MODELS)
        assert stage_progress.duration > 0.0
        assert stage_progress.duration >= 0.1

    def test_all_stages(self):
        """Test all pipeline stages."""
        tracker = ProgressTracker(total_items=100)

        stages = [
            Stage.FILTER_MODELS,
            Stage.FIND_DOCS,
            Stage.PARSE_DOCS,
            Stage.CONSOLIDATE,
            Stage.CATEGORIZE,
            Stage.REPORT
        ]

        for stage in stages:
            tracker.start_stage(stage)
            tracker.increment(10)
            tracker.complete_stage(stage)

        # All stages should be completed
        for stage in stages:
            assert tracker.get_stage_progress(stage).completed

    def test_concurrent_increments(self):
        """Test thread-safe progress increments."""
        import threading

        tracker = ProgressTracker(total_items=1000)

        def increment_progress():
            for _ in range(100):
                tracker.increment(1)

        threads = [threading.Thread(target=increment_progress) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have all increments
        assert tracker.completed_items == 1000
        assert tracker.is_complete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
