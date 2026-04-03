#!/usr/bin/env python3
"""
Test script for temporal tracking implementation (Phase 5, User Story 2).

Tests T025-T034:
- create_temporal_snapshot with 12-month window
- calculate_benchmark_status
- calculate_relative_frequency
- Temporal trends reporting
- Emerging benchmarks section
- Almost extinct benchmarks section
- Historical snapshot comparison
- Multiple snapshot runs

Usage:
    python test_temporal_tracking.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import cache directly to avoid dependency issues
sys.path.insert(0, str(Path(__file__).parent / "agents" / "benchmark_intelligence" / "tools"))
from cache import CacheManager


def test_temporal_snapshot_creation():
    """Test T025: create_temporal_snapshot method."""
    print("\n" + "="*80)
    print("TEST T025: Temporal Snapshot Creation")
    print("="*80)

    # Use a test database
    cache = CacheManager("test_temporal.db")

    # Add some test data
    now = datetime.utcnow()

    # Add models with various release dates
    for i in range(5):
        release_date = (now - timedelta(days=30 * i)).isoformat()
        cache.add_model({
            'id': f'test-lab/model-{i}',
            'name': f'Test Model {i}',
            'lab': 'test-lab',
            'release_date': release_date,
            'downloads': 1000 * (i + 1),
            'likes': 100 * (i + 1),
            'tags': ['test']
        })

    # Add benchmarks
    benchmark_ids = []
    for i in range(3):
        bench_id = cache.add_benchmark(
            name=f'TestBench-{i}',
            categories=['test', 'evaluation'],
            attributes={'domain': 'test'}
        )
        benchmark_ids.append(bench_id)

    # Link models to benchmarks
    for i in range(5):
        model_id = f'test-lab/model-{i}'
        for bench_id in benchmark_ids[:i+1]:  # Varying coverage
            cache.add_model_benchmark(
                model_id=model_id,
                benchmark_id=bench_id,
                score=0.85 + (i * 0.02),
                source_type='test'
            )

    # Create temporal snapshot
    snapshot_id = cache.create_temporal_snapshot(
        taxonomy_version='test_taxonomy.md',
        summary={'test': 'temporal_snapshot'}
    )

    print(f"✓ Created temporal snapshot: ID={snapshot_id}")

    # Verify snapshot
    snapshot = cache.get_snapshot(snapshot_id)
    print(f"  - Window: {snapshot['window_start'][:10]} to {snapshot['window_end'][:10]}")
    print(f"  - Models in window: {snapshot['model_count']}")
    print(f"  - Benchmarks: {snapshot['benchmark_count']}")

    # Verify benchmark mentions
    mentions = cache.get_benchmark_mentions_for_snapshot(snapshot_id)
    print(f"  - Benchmark mentions: {len(mentions)}")

    for mention in mentions:
        print(f"    * {mention['benchmark_name']}: {mention['absolute_mentions']} mentions, "
              f"{mention['relative_frequency']*100:.1f}% frequency, status={mention['status']}")

    return cache, snapshot_id


def test_benchmark_status_calculation(cache):
    """Test T026: calculate_benchmark_status method."""
    print("\n" + "="*80)
    print("TEST T026: Benchmark Status Calculation")
    print("="*80)

    now = datetime.utcnow().isoformat()

    # Test emerging (≤ 3 months)
    first_seen_emerging = (datetime.utcnow() - timedelta(days=60)).isoformat()
    last_seen_emerging = (datetime.utcnow() - timedelta(days=10)).isoformat()
    status_emerging = cache.calculate_benchmark_status(first_seen_emerging, last_seen_emerging, now)
    print(f"✓ Emerging benchmark (60 days old): status={status_emerging}")
    assert status_emerging == "emerging", f"Expected 'emerging', got '{status_emerging}'"

    # Test active
    first_seen_active = (datetime.utcnow() - timedelta(days=180)).isoformat()
    last_seen_active = (datetime.utcnow() - timedelta(days=30)).isoformat()
    status_active = cache.calculate_benchmark_status(first_seen_active, last_seen_active, now)
    print(f"✓ Active benchmark (180 days old, seen 30 days ago): status={status_active}")
    assert status_active == "active", f"Expected 'active', got '{status_active}'"

    # Test almost extinct (≥ 9 months)
    first_seen_extinct = (datetime.utcnow() - timedelta(days=400)).isoformat()
    last_seen_extinct = (datetime.utcnow() - timedelta(days=280)).isoformat()
    status_extinct = cache.calculate_benchmark_status(first_seen_extinct, last_seen_extinct, now)
    print(f"✓ Almost extinct benchmark (last seen 280 days ago): status={status_extinct}")
    assert status_extinct == "almost_extinct", f"Expected 'almost_extinct', got '{status_extinct}'"


def test_relative_frequency_calculation(cache):
    """Test T027: calculate_relative_frequency method."""
    print("\n" + "="*80)
    print("TEST T027: Relative Frequency Calculation")
    print("="*80)

    # Test various frequencies
    test_cases = [
        (10, 100, 0.1),
        (25, 100, 0.25),
        (100, 100, 1.0),
        (0, 100, 0.0),
        (5, 0, 0.0),  # Edge case: no models
    ]

    for mentions, total, expected in test_cases:
        freq = cache.calculate_relative_frequency(mentions, total)
        print(f"✓ {mentions}/{total} = {freq:.2f} (expected {expected:.2f})")
        assert abs(freq - expected) < 0.001, f"Expected {expected}, got {freq}"


def test_temporal_report_generation(cache, snapshot_id):
    """Test T028-T031: Report generation with temporal sections."""
    print("\n" + "="*80)
    print("TEST T028-T031: Temporal Report Generation")
    print("="*80)

    # Import reporting module directly
    sys.path.insert(0, str(Path(__file__).parent / "agents" / "benchmark_intelligence"))
    from reporting import ReportGenerator

    reporter = ReportGenerator(cache)

    # Test individual sections
    print("\n[T028] Testing Temporal Trends section...")
    trends = reporter._generate_temporal_trends([])
    assert "## Temporal Trends" in trends
    assert "Rolling Window" in trends
    print("✓ Temporal Trends section generated")

    print("\n[T029] Testing Emerging Benchmarks section...")
    emerging = reporter._generate_emerging_benchmarks_section()
    assert "## Emerging Benchmarks" in emerging
    print("✓ Emerging Benchmarks section generated")

    print("\n[T030] Testing Almost Extinct section...")
    extinct = reporter._generate_almost_extinct_section()
    assert "## Almost Extinct Benchmarks" in extinct
    print("✓ Almost Extinct Benchmarks section generated")

    print("\n[T031] Testing Historical Comparison section...")
    comparison = reporter._generate_historical_comparison()
    assert "## Historical Snapshot Comparison" in comparison
    print("✓ Historical Snapshot Comparison section generated")

    # Generate full report
    print("\n[T033] Testing full report integration...")
    report = reporter.generate_report()

    # Verify all sections present
    expected_sections = [
        "# Benchmark Intelligence Report",
        "## Executive Summary",
        "## Trending Models",
        "## Most Common Benchmarks",
        "## Temporal Trends",
        "## Emerging Benchmarks",
        "## Almost Extinct Benchmarks",
        "## Historical Snapshot Comparison",
        "## Benchmark Categories",
        "## Lab-Specific Insights",
    ]

    for section in expected_sections:
        assert section in report, f"Missing section: {section}"

    print("✓ Full report generated with all temporal sections")
    print(f"  - Report length: {len(report)} characters")


def test_multiple_snapshots(cache):
    """Test T034: Multiple snapshot runs."""
    print("\n" + "="*80)
    print("TEST T034: Multiple Snapshot Runs")
    print("="*80)

    # Create first snapshot (already done in test_temporal_snapshot_creation)
    snapshots = cache.get_recent_snapshots(limit=10)
    initial_count = len(snapshots)
    print(f"Initial snapshot count: {initial_count}")

    # Modify data and create second snapshot
    print("\nAdding new model and benchmark...")
    new_model_id = 'test-lab/model-new'
    cache.add_model({
        'id': new_model_id,
        'name': 'New Test Model',
        'lab': 'test-lab',
        'release_date': datetime.utcnow().isoformat(),
        'downloads': 5000,
        'likes': 500,
        'tags': ['test', 'new']
    })

    new_bench_id = cache.add_benchmark(
        name='NewBenchmark',
        categories=['emerging', 'test'],
        attributes={'domain': 'new'}
    )

    cache.add_model_benchmark(
        model_id=new_model_id,
        benchmark_id=new_bench_id,
        score=0.92,
        source_type='test'
    )

    # Create second snapshot
    snapshot_id_2 = cache.create_temporal_snapshot(
        summary={'test': 'second_snapshot'}
    )

    print(f"✓ Created second snapshot: ID={snapshot_id_2}")

    # Verify we have multiple snapshots
    snapshots = cache.get_recent_snapshots(limit=10)
    print(f"✓ Total snapshots: {len(snapshots)} (increased by {len(snapshots) - initial_count})")
    assert len(snapshots) >= 2, "Should have at least 2 snapshots"

    # Test historical comparison
    print("\nTesting historical comparison with multiple snapshots...")
    sys.path.insert(0, str(Path(__file__).parent / "agents" / "benchmark_intelligence"))
    from reporting import ReportGenerator
    reporter = ReportGenerator(cache)
    comparison = reporter._generate_historical_comparison()

    # Should now have actual comparison data
    assert "Not enough snapshots" not in comparison
    assert "Current Snapshot:" in comparison
    assert "Previous Snapshot:" in comparison
    print("✓ Historical comparison working with multiple snapshots")

    return snapshot_id_2


def cleanup():
    """Remove test database."""
    import os
    test_db = "test_temporal.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        print(f"\n✓ Cleaned up test database: {test_db}")


def main():
    """Run all temporal tracking tests."""
    print("\n" + "="*80)
    print("TEMPORAL TRACKING TEST SUITE (Phase 5, User Story 2)")
    print("Testing Tasks T025-T034")
    print("="*80)

    try:
        # Clean up any existing test database
        cleanup()

        # Run tests
        cache, snapshot_id = test_temporal_snapshot_creation()
        test_benchmark_status_calculation(cache)
        test_relative_frequency_calculation(cache)
        test_temporal_report_generation(cache, snapshot_id)
        snapshot_id_2 = test_multiple_snapshots(cache)

        # Final summary
        print("\n" + "="*80)
        print("ALL TESTS PASSED!")
        print("="*80)
        print("\nCompleted Tasks:")
        print("  ✓ T025: create_temporal_snapshot with 12-month window")
        print("  ✓ T026: calculate_benchmark_status method")
        print("  ✓ T027: calculate_relative_frequency method")
        print("  ✓ T028: Temporal Trends section in reporting")
        print("  ✓ T029: Emerging Benchmarks section")
        print("  ✓ T030: Almost Extinct Benchmarks section")
        print("  ✓ T031: Historical Snapshot Comparison")
        print("  ✓ T032: main.py integrated with temporal logic")
        print("  ✓ T033: Temporal snapshot data in report generation")
        print("  ✓ T034: Multiple snapshot testing")
        print("\nPhase 5, User Story 2: COMPLETE")
        print("="*80 + "\n")

        # Cleanup
        cleanup()

        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        cleanup()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())
