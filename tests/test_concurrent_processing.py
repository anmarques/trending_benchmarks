"""
Integration test for concurrent processing with 20+ workers.

Tests the ConcurrentModelProcessor with high concurrency.
"""

import pytest
import asyncio
import sys
import os
import time
from unittest.mock import Mock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.benchmark_intelligence.concurrent_processor import (
    ConcurrentModelProcessor,
    TaskStatus
)


class TestConcurrentProcessing:
    """Integration tests for concurrent processing."""

    def test_high_concurrency_sync(self):
        """Test processing with 20+ workers (synchronous)."""
        processor = ConcurrentModelProcessor(max_workers=25)

        # Create test models
        models = [{"id": f"model_{i}", "data": i} for i in range(100)]

        # Simple processing function
        def process_model(model):
            time.sleep(0.01)  # Simulate work
            return {
                "model_id": model["id"],
                "result": model["data"] * 2
            }

        # Process models
        results = processor.process_models(models, process_model)

        # Verify results
        assert len(results) == 100
        assert processor.get_success_count() == 100
        assert processor.get_failure_count() == 0

    @pytest.mark.asyncio
    async def test_high_concurrency_async(self):
        """Test async processing with 20+ workers."""
        processor = ConcurrentModelProcessor(max_workers=30, use_async=True)

        # Create test models
        models = [{"id": f"model_{i}", "data": i} for i in range(100)]

        # Async processing function
        async def async_process_model(model):
            await asyncio.sleep(0.01)  # Simulate async work
            return {
                "model_id": model["id"],
                "result": model["data"] * 3
            }

        # Process models
        results = await processor.process_models_async(models, async_process_model)

        # Verify results
        assert len(results) == 100
        assert processor.get_success_count() == 100
        assert processor.get_failure_count() == 0

    def test_error_handling_concurrent(self):
        """Test error handling with concurrent processing."""
        processor = ConcurrentModelProcessor(max_workers=20)

        # Create test models
        models = [{"id": f"model_{i}", "data": i} for i in range(50)]

        # Processing function that fails for some models
        def process_with_errors(model):
            if model["data"] % 10 == 0:
                raise ValueError(f"Failed for model {model['id']}")
            return {
                "model_id": model["id"],
                "result": model["data"]
            }

        # Process models
        results = processor.process_models(models, process_with_errors)

        # Should have some failures
        assert len(results) == 50
        assert processor.get_failure_count() == 5  # 0, 10, 20, 30, 40
        assert processor.get_success_count() == 45

    def test_progress_callback(self):
        """Test progress callback during concurrent processing."""
        processor = ConcurrentModelProcessor(max_workers=20)

        # Create test models
        models = [{"id": f"model_{i}", "data": i} for i in range(50)]

        progress_updates = []

        def progress_callback(completed, total):
            progress_updates.append((completed, total))

        def process_model(model):
            return {"model_id": model["id"]}

        # Process with callback
        results = processor.process_models(
            models,
            process_model,
            progress_callback=progress_callback
        )

        # Verify progress updates
        assert len(progress_updates) == 50
        assert progress_updates[-1] == (50, 50)

    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling with concurrent processing."""
        processor = ConcurrentModelProcessor(max_workers=20, use_async=True)

        # Create test models
        models = [{"id": f"model_{i}", "data": i} for i in range(30)]

        async def async_process_with_errors(model):
            await asyncio.sleep(0.001)
            if model["data"] % 5 == 0:
                raise RuntimeError(f"Async failure for {model['id']}")
            return {"model_id": model["id"], "result": "ok"}

        # Process models
        results = await processor.process_models_async(
            models,
            async_process_with_errors
        )

        # Should have some failures (0, 5, 10, 15, 20, 25)
        assert len(results) == 30
        assert processor.get_failure_count() == 6

    def test_performance_scaling(self):
        """Test that more workers improve performance."""
        models = [{"id": f"model_{i}", "data": i} for i in range(100)]

        def process_model(model):
            time.sleep(0.01)
            return {"model_id": model["id"]}

        # Test with 10 workers
        processor_10 = ConcurrentModelProcessor(max_workers=10)
        start = time.time()
        processor_10.process_models(models, process_model)
        time_10 = time.time() - start

        # Test with 30 workers
        processor_30 = ConcurrentModelProcessor(max_workers=30)
        start = time.time()
        processor_30.process_models(models, process_model)
        time_30 = time.time() - start

        # 30 workers should be faster (allow some variance)
        assert time_30 < time_10 * 1.2  # At most 20% slower

    def test_get_summary(self):
        """Test getting processing summary."""
        processor = ConcurrentModelProcessor(max_workers=20)

        models = [{"id": f"model_{i}", "data": i} for i in range(50)]

        def process_model(model):
            if model["data"] == 25:
                raise ValueError("Test error")
            return {"model_id": model["id"]}

        processor.process_models(models, process_model)

        summary = processor.get_summary()

        assert summary["total"] == 50
        assert summary["completed"] == 49
        assert summary["failed"] == 1
        assert summary["pending"] == 0

    def test_failed_tasks_retrieval(self):
        """Test retrieving failed tasks."""
        processor = ConcurrentModelProcessor(max_workers=20)

        models = [{"id": f"model_{i}", "data": i} for i in range(30)]

        def process_model(model):
            if model["data"] % 10 == 0:
                raise ValueError(f"Error for {model['id']}")
            return {"model_id": model["id"]}

        processor.process_models(models, process_model)

        failed = processor.get_failed_tasks()

        assert len(failed) == 3  # 0, 10, 20
        assert all(task.status == TaskStatus.FAILED for task in failed)
        assert all(task.error is not None for task in failed)

    @pytest.mark.asyncio
    async def test_mixed_task_duration(self):
        """Test handling tasks with varying durations."""
        processor = ConcurrentModelProcessor(max_workers=25, use_async=True)

        models = [{"id": f"model_{i}", "duration": i * 0.001} for i in range(50)]

        async def variable_duration_task(model):
            await asyncio.sleep(model["duration"])
            return {"model_id": model["id"]}

        start = time.time()
        results = await processor.process_models_async(models, variable_duration_task)
        elapsed = time.time() - start

        # All tasks should complete
        assert len(results) == 50
        # Should complete in parallel (much faster than sequential)
        assert elapsed < 2.0  # Sum of all durations would be ~1.25s

    def test_empty_model_list(self):
        """Test handling empty model list."""
        processor = ConcurrentModelProcessor(max_workers=20)

        def process_model(model):
            return {"model_id": model["id"]}

        results = processor.process_models([], process_model)

        assert len(results) == 0
        assert processor.get_total_count() == 0

    @pytest.mark.asyncio
    async def test_stress_test(self):
        """Stress test with very high concurrency."""
        processor = ConcurrentModelProcessor(max_workers=50, use_async=True)

        # Create many models
        models = [{"id": f"model_{i}", "data": i} for i in range(200)]

        async def quick_process(model):
            await asyncio.sleep(0.001)
            return {"model_id": model["id"], "processed": True}

        start = time.time()
        results = await processor.process_models_async(models, quick_process)
        elapsed = time.time() - start

        # All should succeed
        assert len(results) == 200
        assert processor.get_success_count() == 200
        # Should be fast with high concurrency
        assert elapsed < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
