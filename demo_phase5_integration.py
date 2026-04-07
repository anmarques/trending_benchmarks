#!/usr/bin/env python3
"""
Demo script showing Phase 5 User Story 3 integration in action.

Simulates a small pipeline run to demonstrate:
- Error aggregation during processing
- Real-time progress tracking
- Multi-source extraction verification
- Handling models with no benchmarks
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.benchmark_intelligence.error_aggregator import ErrorAggregator
from agents.benchmark_intelligence.progress_tracker import ProgressTracker


def simulate_model_processing():
    """Simulate processing multiple models with errors and progress tracking."""

    print("=" * 80)
    print("PHASE 5 USER STORY 3 - INTEGRATION DEMO")
    print("=" * 80)
    print("\nSimulating processing of 25 models with multi-source extraction...")
    print()

    # Initialize components
    error_aggregator = ErrorAggregator(max_samples_per_type=5)
    progress_tracker = ProgressTracker(total_models=25, update_interval=2.0)

    # Start progress tracking
    progress_tracker.start()

    # Simulate processing models
    models = [
        ("meta-llama/Llama-3.1-8B", 24, ["model_card", "arxiv", "github"]),
        ("Qwen/Qwen2.5-7B-Instruct", 18, ["model_card", "arxiv", "blog", "github"]),
        ("mistralai/Mistral-7B-v0.1", 15, ["model_card", "blog"]),
        ("google/gemma-2-9b", 0, []),  # No benchmarks found
        ("deepseek-ai/DeepSeek-V2", 22, ["model_card", "arxiv"]),
        ("microsoft/Phi-3-mini", 12, ["model_card"]),
        ("nvidia/Llama-3.1-Nemotron-70B", 0, []),  # No benchmarks found
        ("01-ai/Yi-34B", 19, ["model_card", "github"]),
        ("alibaba-pai/Qwen1.5-110B", 16, ["model_card", "blog"]),
        ("THUDM/ChatGLM3-6B", 14, ["model_card", "github"]),
    ]

    total_benchmarks = 0
    models_without_benchmarks = 0

    for i, (model_id, benchmark_count, sources) in enumerate(models, 1):
        # Simulate processing time
        time.sleep(0.3)

        # Process model
        if benchmark_count > 0:
            total_benchmarks += benchmark_count
            progress_tracker.increment_benchmarks_extracted(benchmark_count)

            # Simulate occasional extraction errors
            if i % 4 == 0:
                error_type = "extraction_arxiv"
                error_aggregator.add_error(
                    error_type,
                    model_id,
                    {"error": "JSON truncation", "tokens": 16000}
                )
                progress_tracker.increment_errors_encountered()
        else:
            models_without_benchmarks += 1
            error_aggregator.add_error(
                "no_benchmarks_found",
                model_id,
                {"sources_checked": ["model_card", "arxiv", "blog", "github"]}
            )

        # Simulate fetch errors
        if i % 5 == 0:
            error_aggregator.add_error(
                "arxiv_fetch_failure",
                model_id,
                {"url": f"https://arxiv.org/abs/...", "status_code": 404}
            )
            progress_tracker.increment_errors_encountered()

        progress_tracker.increment_models_processed()

    # Process remaining models (simulated batch)
    print("\n  Processing remaining models in batch...")
    for i in range(15):
        time.sleep(0.2)

        benchmarks = 10 if i % 3 != 0 else 0

        if benchmarks > 0:
            total_benchmarks += benchmarks
            progress_tracker.increment_benchmarks_extracted(benchmarks)
        else:
            models_without_benchmarks += 1

        if i % 6 == 0:
            error_aggregator.add_error(
                "github_fetch_failure",
                f"org/model-{i}",
                {"error": "404 Not Found"}
            )
            progress_tracker.increment_errors_encountered()

        progress_tracker.increment_models_processed()

    # Stop progress tracking
    progress_tracker.stop()

    # Display results
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE - RESULTS SUMMARY")
    print("=" * 80)

    stats = progress_tracker.get_stats()
    print(f"\n📊 Processing Statistics:")
    print(f"  Models processed: {stats['models_processed']}")
    print(f"  Benchmarks extracted: {stats['benchmarks_extracted']:,}")
    print(f"  Total errors: {stats['errors_encountered']}")
    print(f"  Models without benchmarks: {models_without_benchmarks}")
    print(f"  Success rate: {(stats['models_processed'] - models_without_benchmarks) / stats['models_processed'] * 100:.1f}%")
    print(f"  Total time: {stats['elapsed_seconds']:.1f}s")

    # Display error summary
    if error_aggregator.has_errors():
        print(f"\n⚠️  {error_aggregator.format_summary_text()}")

    # Show sample errors
    print("\n📋 Sample Error Details:")
    summary = error_aggregator.get_summary()
    for error_type, stats in list(summary.items())[:3]:  # Show first 3 types
        print(f"\n  {error_type}:")
        print(f"    Total: {stats['count']} errors")
        print(f"    Models affected: {stats['models_affected']}")
        if stats['samples']:
            sample = stats['samples'][0]
            print(f"    Example: {sample['model_id']}")
            if 'details' in sample:
                for key, value in list(sample['details'].items())[:2]:
                    print(f"      - {key}: {value}")

    print("\n" + "=" * 80)
    print("PHASE 5 FEATURES DEMONSTRATED")
    print("=" * 80)
    print("\n✓ Real-time progress tracking (updates every 2 seconds)")
    print("✓ Error aggregation by type with samples")
    print("✓ Models without benchmarks tracked and reported")
    print("✓ Multi-source extraction (model_card, arxiv, blog, github)")
    print("✓ Thread-safe concurrent processing")
    print("✓ Comprehensive statistics and reporting")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        simulate_model_processing()
        print("\n✅ Demo completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
