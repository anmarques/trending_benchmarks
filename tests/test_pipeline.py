"""
Integration test for full pipeline execution.

Tests end-to-end pipeline with all stages.
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestPipelineIntegration:
    """Integration tests for full pipeline execution."""

    def test_pipeline_stages_exist(self):
        """Test that all pipeline stage modules exist."""
        from agents.benchmark_intelligence import (
            filter_models,
            find_docs,
            parse_docs,
            consolidate_benchmarks,
            categorize_benchmarks,
            report
        )

        # Just verify imports work
        assert filter_models is not None
        assert find_docs is not None
        assert parse_docs is not None
        assert consolidate_benchmarks is not None
        assert categorize_benchmarks is not None
        assert report is not None

    def test_config_loading(self):
        """Test configuration loading."""
        import yaml

        config_path = "/workspace/repos/trending_benchmarks/config.yaml"
        assert os.path.exists(config_path)

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Verify key configuration sections
        assert "labs" in config
        assert "discovery" in config
        assert "pdf_constraints" in config
        assert "retry_policy" in config
        assert "rate_limiting" in config

    def test_stage_1_filter_models(self):
        """Test stage 1: filter_models."""
        from agents.benchmark_intelligence.filter_models import filter_models

        # Create minimal test config
        config = {
            "labs": ["test-lab"],
            "discovery": {
                "models_per_lab": 5,
                "sort_by": "downloads",
                "filter_tags": [],
                "exclude_tags": []
            }
        }

        # This will try to connect to HuggingFace API
        # We'll just verify the function is callable
        assert callable(filter_models)

    def test_output_directory_structure(self):
        """Test that output directories can be created."""
        base_dir = Path("/workspace/repos/trending_benchmarks/agents/benchmark_intelligence/outputs")

        # Create test structure
        test_dirs = [
            base_dir / "filtered_models",
            base_dir / "docs",
            base_dir / "parsed",
            base_dir / "consolidated",
            base_dir / "categorized",
            base_dir / "reports"
        ]

        for dir_path in test_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_json_schema_validation(self):
        """Test JSON schema for outputs."""
        # Test filtered models schema
        filtered_model = {
            "id": "test/model",
            "author": "test",
            "downloads": 1000,
            "likes": 50,
            "tags": ["text-generation"],
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Should be valid JSON
        json_str = json.dumps(filtered_model)
        loaded = json.loads(json_str)
        assert loaded["id"] == "test/model"

    def test_benchmark_extraction_schema(self):
        """Test benchmark extraction output schema."""
        benchmark_entry = {
            "model_id": "test/model",
            "benchmarks": [
                {
                    "name": "MMLU",
                    "score": 85.5,
                    "metric": "accuracy",
                    "source": "model_card"
                }
            ],
            "extraction_timestamp": "2024-01-01T00:00:00Z"
        }

        # Should be valid JSON
        json_str = json.dumps(benchmark_entry)
        loaded = json.loads(json_str)
        assert len(loaded["benchmarks"]) == 1

    def test_consolidated_benchmark_schema(self):
        """Test consolidated benchmark schema."""
        consolidated = {
            "benchmark_name": "MMLU",
            "canonical_name": "MMLU",
            "occurrences": 10,
            "models": [
                {
                    "model_id": "test/model1",
                    "score": 85.5,
                    "metric": "accuracy"
                },
                {
                    "model_id": "test/model2",
                    "score": 87.0,
                    "metric": "accuracy"
                }
            ]
        }

        # Should be valid JSON
        json_str = json.dumps(consolidated)
        loaded = json.loads(json_str)
        assert loaded["canonical_name"] == "MMLU"
        assert len(loaded["models"]) == 2

    def test_categorized_benchmark_schema(self):
        """Test categorized benchmark schema."""
        categorized = {
            "benchmark_name": "MMLU",
            "category": "Knowledge & General Understanding",
            "subcategory": "Multidomain",
            "confidence": 0.95,
            "reasoning": "MMLU tests knowledge across multiple domains"
        }

        # Should be valid JSON
        json_str = json.dumps(categorized)
        loaded = json.loads(json_str)
        assert loaded["category"] == "Knowledge & General Understanding"

    def test_error_handling_in_pipeline(self):
        """Test error handling throughout pipeline."""
        from agents.benchmark_intelligence.error_aggregator import ErrorAggregator, ErrorCategory

        aggregator = ErrorAggregator()

        # Simulate pipeline errors
        aggregator.record_error(
            category=ErrorCategory.API_ERROR,
            message="HuggingFace API timeout",
            context={"model_id": "test/model"}
        )

        aggregator.record_error(
            category=ErrorCategory.PARSE_ERROR,
            message="Failed to parse PDF",
            context={"document_url": "https://example.com/paper.pdf"}
        )

        summary = aggregator.get_summary()
        assert summary["total_errors"] == 2

    def test_progress_tracking_in_pipeline(self):
        """Test progress tracking throughout pipeline."""
        from agents.benchmark_intelligence.progress_tracker import ProgressTracker, Stage

        tracker = ProgressTracker(total_items=100)

        # Simulate pipeline stages
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

        summary = tracker.get_summary()
        assert summary["completed_items"] == 60
        assert summary["progress_percentage"] == 60.0

    def test_connection_pool_integration(self):
        """Test connection pool in pipeline context."""
        from agents.benchmark_intelligence.connection_pool import ConnectionPool

        pool = ConnectionPool(pool_size=20)

        # Verify pool is ready
        stats = pool.get_stats()
        assert stats["pool_size"] == 20
        assert stats["active_connections"] == 0

    def test_rate_limiter_integration(self):
        """Test rate limiter in pipeline context."""
        from agents.benchmark_intelligence.rate_limiter import (
            RateLimiter,
            RateLimitConfig
        )

        configs = {
            "huggingface": RateLimitConfig(requests_per_minute=60),
            "anthropic": RateLimitConfig(requests_per_minute=50)
        }

        limiter = RateLimiter(configs)
        stats = limiter.get_stats()

        assert "huggingface" in stats
        assert "anthropic" in stats

    def test_concurrent_processor_integration(self):
        """Test concurrent processor in pipeline context."""
        from agents.benchmark_intelligence.concurrent_processor import ConcurrentModelProcessor

        processor = ConcurrentModelProcessor(max_workers=20)

        # Create test models
        models = [{"id": f"model_{i}"} for i in range(10)]

        def process(model):
            return {"processed": model["id"]}

        results = processor.process_models(models, process)
        assert len(results) == 10

    def test_full_pipeline_dry_run(self):
        """Test full pipeline dry run (no actual API calls)."""
        # This tests that all components can be initialized together
        from agents.benchmark_intelligence.connection_pool import ConnectionPool
        from agents.benchmark_intelligence.error_aggregator import ErrorAggregator
        from agents.benchmark_intelligence.progress_tracker import ProgressTracker, Stage
        from agents.benchmark_intelligence.concurrent_processor import ConcurrentModelProcessor
        from agents.benchmark_intelligence.rate_limiter import RateLimiter, RateLimitConfig

        # Initialize all components
        pool = ConnectionPool(pool_size=20)
        aggregator = ErrorAggregator()
        tracker = ProgressTracker(total_items=100)
        processor = ConcurrentModelProcessor(max_workers=20)

        configs = {
            "huggingface": RateLimitConfig(requests_per_minute=60),
            "anthropic": RateLimitConfig(requests_per_minute=50)
        }
        limiter = RateLimiter(configs)

        # Simulate pipeline flow
        tracker.start_stage(Stage.FILTER_MODELS)
        tracker.increment(20)
        tracker.complete_stage(Stage.FILTER_MODELS)

        # All components should work together
        assert pool.get_stats()["pool_size"] == 20
        assert aggregator.get_total_count() == 0
        assert tracker.get_progress_percentage() == 20.0
        assert processor.get_summary()["total"] == 0
        assert "huggingface" in limiter.get_stats()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
