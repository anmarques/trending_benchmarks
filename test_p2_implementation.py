#!/usr/bin/env python3
"""
Test script for P2-3 and P2-4 implementation.
Tests source_type tracking and deprecated benchmark detection.
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.benchmark_intelligence.tools.cache import CacheManager

def test_source_type_tracking():
    """Test P2-3: Track source type in model_benchmarks"""
    print("Testing P2-3: Source type tracking...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        cache = CacheManager(db_path)

        # Add a model
        cache.add_model({
            "id": "test/model1",
            "name": "Test Model 1",
            "lab": "TestLab",
        })

        # Add a benchmark
        benchmark_id = cache.add_benchmark(
            name="MMLU",
            categories=["reasoning", "knowledge"],
        )

        # Add model-benchmark link with source_type
        link_id = cache.add_model_benchmark(
            model_id="test/model1",
            benchmark_id=benchmark_id,
            score=85.5,
            context={"shot_count": 5},
            source_url="https://example.com/card",
            source_type="model_card",
        )

        # Verify source_type was stored
        benchmarks = cache.get_model_benchmarks("test/model1")
        assert len(benchmarks) == 1, f"Expected 1 benchmark, got {len(benchmarks)}"

        # Check if source_type exists in the result
        # Note: We need to query the database directly since get_model_benchmarks
        # might not return source_type in the current implementation
        with cache._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source_type FROM model_benchmarks WHERE id = ?
            """, (link_id,))
            row = cursor.fetchone()
            assert row is not None, "Link not found"
            assert row['source_type'] == "model_card", f"Expected source_type='model_card', got '{row['source_type']}'"

        print("✓ Source type is tracked correctly")

        # Test with different source types
        for source_type in ["arxiv_paper", "blog_post", "github_pdf"]:
            cache.add_model_benchmark(
                model_id="test/model1",
                benchmark_id=benchmark_id,
                score=86.0,
                context={"shot_count": 3},  # Different context to avoid conflict
                source_url=f"https://example.com/{source_type}",
                source_type=source_type,
            )

        print("✓ Multiple source types can be stored")

    finally:
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

def test_last_seen_tracking():
    """Test P2-4: Track last_seen for benchmarks"""
    print("\nTesting P2-4: Last seen tracking...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        cache = CacheManager(db_path)

        # Add a benchmark
        benchmark_id = cache.add_benchmark(
            name="GSM8K",
            categories=["math"],
        )

        # Verify last_seen was set
        with cache._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_seen FROM benchmarks WHERE id = ?", (benchmark_id,))
            row = cursor.fetchone()
            assert row is not None, "Benchmark not found"
            assert row['last_seen'] is not None, "last_seen should be set on creation"
            first_seen = row['last_seen']

        print("✓ last_seen is set on benchmark creation")

        # Update the benchmark (simulating a new mention)
        import time
        time.sleep(0.1)  # Small delay to ensure timestamp changes
        cache.add_benchmark(
            name="GSM8K",
            categories=["math", "reasoning"],  # Updated categories
        )

        # Verify last_seen was updated
        with cache._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_seen FROM benchmarks WHERE id = ?", (benchmark_id,))
            row = cursor.fetchone()
            assert row is not None, "Benchmark not found"
            assert row['last_seen'] > first_seen, "last_seen should be updated"

        print("✓ last_seen is updated on benchmark mention")

    finally:
        Path(db_path).unlink(missing_ok=True)

def test_deprecated_benchmarks():
    """Test P2-4: Deprecated benchmark detection"""
    print("\nTesting P2-4: Deprecated benchmark detection...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        cache = CacheManager(db_path)

        # Add some benchmarks with different last_seen dates
        now = datetime.utcnow().isoformat()
        seven_months_ago = (datetime.utcnow() - timedelta(days=7*30)).isoformat()
        three_months_ago = (datetime.utcnow() - timedelta(days=3*30)).isoformat()

        # Recent benchmark
        recent_id = cache.add_benchmark(name="MMLU", categories=["reasoning"])

        # Old benchmark (manually set last_seen to 7 months ago)
        old_id = cache.add_benchmark(name="SuperGLUE", categories=["nlp"])
        with cache._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE benchmarks SET last_seen = ? WHERE id = ?
            """, (seven_months_ago, old_id))
            conn.commit()

        # Medium-old benchmark (3 months ago - should not be deprecated)
        medium_id = cache.add_benchmark(name="HellaSwag", categories=["reasoning"])
        with cache._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE benchmarks SET last_seen = ? WHERE id = ?
            """, (three_months_ago, medium_id))
            conn.commit()

        # Get deprecated benchmarks (not seen in 6 months)
        deprecated = cache.get_deprecated_benchmarks(months=6)

        # Verify only the 7-month-old benchmark is deprecated
        deprecated_names = [b['canonical_name'] for b in deprecated]
        assert "SuperGLUE" in deprecated_names, "SuperGLUE should be deprecated"
        assert "MMLU" not in deprecated_names, "MMLU should not be deprecated"
        assert "HellaSwag" not in deprecated_names, "HellaSwag should not be deprecated"

        print(f"✓ Deprecated benchmarks detected: {deprecated_names}")

        # Verify the deprecated benchmark has correct data
        superglu = next(b for b in deprecated if b['canonical_name'] == "SuperGLUE")
        assert superglu['last_seen'] == seven_months_ago, "Last seen date should match"
        assert superglu['categories'] == ["nlp"], "Categories should be preserved"

        print("✓ Deprecated benchmark data is correct")

    finally:
        Path(db_path).unlink(missing_ok=True)

def test_model_benchmark_last_seen():
    """Test P2-4: Track last_seen in model_benchmarks"""
    print("\nTesting P2-4: Model-benchmark last_seen tracking...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        cache = CacheManager(db_path)

        # Add model and benchmark
        cache.add_model({
            "id": "test/model1",
            "name": "Test Model",
        })
        benchmark_id = cache.add_benchmark(name="MMLU")

        # Add model-benchmark link
        link_id = cache.add_model_benchmark(
            model_id="test/model1",
            benchmark_id=benchmark_id,
            score=85.0,
        )

        # Verify last_seen was set
        with cache._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_seen FROM model_benchmarks WHERE id = ?", (link_id,))
            row = cursor.fetchone()
            assert row is not None, "Link not found"
            assert row['last_seen'] is not None, "last_seen should be set"
            first_seen = row['last_seen']

        print("✓ last_seen is set on model-benchmark link creation")

        # Update the link (same model, benchmark, context)
        import time
        time.sleep(0.1)
        cache.add_model_benchmark(
            model_id="test/model1",
            benchmark_id=benchmark_id,
            score=86.0,  # Updated score
        )

        # Verify last_seen was updated
        with cache._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_seen FROM model_benchmarks WHERE id = ?", (link_id,))
            row = cursor.fetchone()
            assert row is not None, "Link not found"
            assert row['last_seen'] > first_seen, "last_seen should be updated"

        print("✓ last_seen is updated on model-benchmark update")

    finally:
        Path(db_path).unlink(missing_ok=True)

if __name__ == "__main__":
    print("=" * 80)
    print("Testing P2-3 & P2-4 Implementation")
    print("=" * 80)

    try:
        test_source_type_tracking()
        test_last_seen_tracking()
        test_deprecated_benchmarks()
        test_model_benchmark_last_seen()

        print("\n" + "=" * 80)
        print("✓ All tests passed!")
        print("=" * 80)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
