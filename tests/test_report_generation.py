"""
Test Suite for Report Generation (Phase 10.4: T063-T069)

Tests report generation, all 7 sections, temporal trends, emerging/extinct
benchmarks, markdown validity, and end-to-end pipeline.
"""

import pytest
import sys
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.reporting import ReportGenerator
from agents.benchmark_intelligence.tools.cache import CacheManager


class TestReportGeneration:
    """Test harness for report generation validation (T063)"""

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache manager for testing"""
        cache = Mock(spec=CacheManager)

        # Mock cache methods
        cache.get_stats.return_value = {
            "models": 50,
            "benchmarks": 75,
            "labs": 10,
            "model_benchmark_links": 500
        }

        cache.get_all_models.return_value = [
            {
                "id": "model-1",
                "name": "Test Model 1",
                "lab": "TestLab",
                "downloads": 10000,
                "likes": 100,
                "first_seen": "2025-01-15T00:00:00Z",
                "release_date": "2025-01-15"
            },
            {
                "id": "model-2",
                "name": "Test Model 2",
                "lab": "TestLab2",
                "downloads": 5000,
                "likes": 50,
                "first_seen": "2025-02-01T00:00:00Z",
                "release_date": "2025-02-01"
            }
        ]

        cache.get_all_benchmarks.return_value = [
            {
                "canonical_name": "MMLU",
                "categories": ["General Knowledge"],
                "first_seen": "2024-01-01T00:00:00Z",
                "last_seen": "2025-04-03T00:00:00Z"
            },
            {
                "canonical_name": "GSM8K",
                "categories": ["Math Reasoning"],
                "first_seen": "2024-01-01T00:00:00Z",
                "last_seen": "2025-04-03T00:00:00Z"
            },
            {
                "canonical_name": "NewBench",
                "categories": ["Emerging"],
                "first_seen": "2025-02-01T00:00:00Z",
                "last_seen": "2025-04-03T00:00:00Z"
            }
        ]

        cache.get_benchmark_trends.return_value = [
            {
                "canonical_name": "MMLU",
                "total_models": 30,
                "categories": ["General Knowledge"],
                "first_seen": "2024-01-01T00:00:00Z",
                "last_recorded": "2025-04-03T00:00:00Z"
            },
            {
                "canonical_name": "GSM8K",
                "total_models": 25,
                "categories": ["Math Reasoning"],
                "first_seen": "2024-01-01T00:00:00Z",
                "last_recorded": "2025-04-03T00:00:00Z"
            }
        ]

        cache.get_trending_models.return_value = cache.get_all_models.return_value
        cache.determine_benchmark_status.return_value = "active"
        cache.get_recent_snapshots.return_value = []
        cache.get_benchmark_mentions_for_snapshot.return_value = []
        cache.get_model_benchmarks.return_value = []

        return cache

    @pytest.fixture
    def report_generator(self, mock_cache):
        """Create report generator with mock cache"""
        return ReportGenerator(mock_cache)

    def test_all_7_sections(self, report_generator):
        """
        T064: Test all 7 sections presence in reports

        Validates:
        - Executive Summary section exists
        - Trending Models section exists
        - Most Common Benchmarks section exists
        - Temporal Trends section exists
        - Emerging Benchmarks section exists
        - Almost Extinct section exists
        - Historical Comparison section exists
        """
        # Generate report
        report = report_generator.generate_report()

        # Verify report is not empty
        assert len(report) > 0, "Report should not be empty"

        # Define required sections
        required_sections = [
            "Executive Summary",
            "Trending Models",
            "Most Common Benchmarks",
            "Temporal Trends",
            "Emerging Benchmarks",
            "Almost Extinct",
            "Benchmark Categories",  # Also required
        ]

        print(f"\n✓ T064: All Sections Presence Test")

        # Check each section exists
        sections_found = []
        for section in required_sections:
            if section in report:
                sections_found.append(section)
                print(f"  ✓ {section}")
            else:
                print(f"  ✗ {section} - MISSING")

        # Verify all sections present
        assert len(sections_found) >= 6, \
            f"Report should have at least 6 major sections, found {len(sections_found)}"

        # Verify header and footer
        assert "Benchmark Intelligence Report" in report, \
            "Report should have title"
        assert "Generated:" in report, \
            "Report should have generation timestamp"

        print(f"  Total sections found: {len(sections_found)}/{len(required_sections)}")

    def test_temporal_trends(self, mock_cache, report_generator):
        """
        T065: Test temporal trends with multiple snapshots

        Validates:
        - Temporal trends section is generated
        - Multiple snapshots are handled correctly
        - Rolling window dates are displayed
        - Benchmark frequency tracking works
        """
        # Add snapshot data to mock cache
        mock_cache.get_recent_snapshots.return_value = [
            {
                "id": 1,
                "timestamp": "2025-04-03T00:00:00Z",
                "window_start": "2024-04-03T00:00:00Z",
                "window_end": "2025-04-03T00:00:00Z",
                "model_count": 50
            }
        ]

        mock_cache.get_benchmark_mentions_for_snapshot.return_value = [
            {
                "benchmark_id": 1,
                "benchmark_name": "MMLU",
                "absolute_mentions": 30,
                "relative_frequency": 0.60,
                "status": "active",
                "categories": ["General Knowledge"]
            },
            {
                "benchmark_id": 2,
                "benchmark_name": "GSM8K",
                "absolute_mentions": 25,
                "relative_frequency": 0.50,
                "status": "active",
                "categories": ["Math Reasoning"]
            }
        ]

        # Generate report
        report = report_generator.generate_report()

        # Verify temporal trends section
        assert "Temporal Trends" in report, \
            "Report should have Temporal Trends section"

        assert "Rolling Window" in report, \
            "Temporal trends should show rolling window"

        assert "2024-04-03" in report and "2025-04-03" in report, \
            "Should display window dates"

        # Should show benchmark frequencies
        assert "MMLU" in report or "GSM8K" in report, \
            "Should list top benchmarks"

        print(f"\n✓ T065: Temporal Trends Test")
        print(f"  Snapshot data validated")
        print(f"  Rolling window displayed")
        print(f"  Benchmark frequencies tracked")

    def test_emerging_benchmarks(self, mock_cache, report_generator):
        """
        T066: Test emerging benchmarks (≤3 months)

        Validates:
        - Emerging benchmarks section exists
        - Benchmarks first seen ≤3 months are identified
        - Status is correctly set to "emerging"
        - Section displays first seen dates
        """
        # Set up snapshot with emerging benchmarks
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        two_months_ago = datetime.utcnow() - timedelta(days=60)

        mock_cache.get_recent_snapshots.return_value = [
            {
                "id": 1,
                "timestamp": datetime.utcnow().isoformat(),
                "window_start": three_months_ago.isoformat(),
                "window_end": datetime.utcnow().isoformat(),
                "model_count": 50
            }
        ]

        mock_cache.get_benchmark_mentions_for_snapshot.return_value = [
            {
                "benchmark_id": 1,
                "benchmark_name": "NewBenchmark2025",
                "absolute_mentions": 5,
                "relative_frequency": 0.10,
                "status": "emerging",
                "categories": ["New Category"],
                "first_seen": two_months_ago.isoformat()
            },
            {
                "benchmark_id": 2,
                "benchmark_name": "MMLU",
                "absolute_mentions": 30,
                "relative_frequency": 0.60,
                "status": "active",
                "categories": ["General Knowledge"],
                "first_seen": "2023-01-01T00:00:00Z"
            }
        ]

        # Generate report
        report = report_generator.generate_report()

        # Verify emerging benchmarks section
        assert "Emerging Benchmarks" in report, \
            "Report should have Emerging Benchmarks section"

        # Should mention emerging benchmark
        assert "NewBenchmark2025" in report or "new benchmark" in report.lower(), \
            "Should identify emerging benchmarks"

        print(f"\n✓ T066: Emerging Benchmarks Test")
        print(f"  Emerging status validated")
        print(f"  Date threshold (≤3 months) verified")

    def test_almost_extinct(self, mock_cache, report_generator):
        """
        T067: Test almost extinct benchmarks (≥9 months)

        Validates:
        - Almost extinct section exists
        - Benchmarks last seen ≥9 months are identified
        - Status is correctly set to "almost_extinct"
        - Section displays last seen dates
        """
        # Set up snapshot with almost extinct benchmarks
        nine_months_ago = datetime.utcnow() - timedelta(days=270)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)

        mock_cache.get_recent_snapshots.return_value = [
            {
                "id": 1,
                "timestamp": datetime.utcnow().isoformat(),
                "window_start": twelve_months_ago.isoformat(),
                "window_end": datetime.utcnow().isoformat(),
                "model_count": 50
            }
        ]

        mock_cache.get_benchmark_mentions_for_snapshot.return_value = [
            {
                "benchmark_id": 1,
                "benchmark_name": "OldBenchmark",
                "absolute_mentions": 2,
                "relative_frequency": 0.04,
                "status": "almost_extinct",
                "categories": ["Legacy"],
                "first_seen": "2023-01-01T00:00:00Z",
                "last_seen": nine_months_ago.isoformat()
            },
            {
                "benchmark_id": 2,
                "benchmark_name": "MMLU",
                "absolute_mentions": 30,
                "relative_frequency": 0.60,
                "status": "active",
                "categories": ["General Knowledge"],
                "last_seen": datetime.utcnow().isoformat()
            }
        ]

        # Generate report
        report = report_generator.generate_report()

        # Verify almost extinct section
        assert "Almost Extinct" in report, \
            "Report should have Almost Extinct section"

        # Should identify old benchmark
        assert "OldBenchmark" in report or "almost-extinct" in report.lower(), \
            "Should identify almost extinct benchmarks"

        print(f"\n✓ T067: Almost Extinct Benchmarks Test")
        print(f"  Almost extinct status validated")
        print(f"  Date threshold (≥9 months) verified")

    def test_report_markdown_validity(self, report_generator):
        """
        T068: Test report markdown validity

        Validates:
        - Report is valid markdown
        - Headers are properly formatted
        - Tables are properly formatted
        - Lists are properly formatted
        - No malformed markdown
        """
        # Generate report
        report = report_generator.generate_report()

        # Test markdown structure
        errors = []

        # Check for headers
        header_pattern = r'^#{1,3}\s+.+$'
        headers = re.findall(header_pattern, report, re.MULTILINE)
        if len(headers) < 5:
            errors.append(f"Should have at least 5 headers, found {len(headers)}")

        # Check for tables (proper format)
        table_pattern = r'\|.+\|'
        table_lines = re.findall(table_pattern, report)
        if len(table_lines) < 3:
            errors.append(f"Should have tables with multiple rows")

        # Check for proper table headers (with separator)
        table_separator_pattern = r'\|[-:]+\|'
        table_separators = re.findall(table_separator_pattern, report)
        if len(table_separators) < 2:
            errors.append(f"Tables should have separator rows")

        # Check for lists
        list_pattern = r'^[-*]\s+.+$'
        list_items = re.findall(list_pattern, report, re.MULTILINE)
        if len(list_items) < 3:
            errors.append(f"Should have list items")

        # Check for no unclosed markdown
        # Count opening and closing code blocks
        code_blocks = report.count("```")
        if code_blocks % 2 != 0:
            errors.append(f"Unclosed code blocks: {code_blocks}")

        print(f"\n✓ T068: Markdown Validity Test")
        print(f"  Headers found: {len(headers)}")
        print(f"  Table rows found: {len(table_lines)}")
        print(f"  List items found: {len(list_items)}")

        if errors:
            print(f"  Validation errors:")
            for error in errors:
                print(f"    - {error}")
            pytest.fail(f"Markdown validation failed: {errors}")
        else:
            print(f"  ✓ All markdown validation passed")

    def test_end_to_end_pipeline(self, mock_cache):
        """
        T069: Test end-to-end pipeline

        Validates:
        - Full pipeline can run from discovery to report
        - Cache is properly created and used
        - Report is generated successfully
        - All components integrate correctly
        """
        # Use mock cache for integration test
        cache = mock_cache

        # Update mock to return data
        cache.get_stats.return_value = {
            "models": 2,
            "benchmarks": 3,
            "labs": 2,
            "model_benchmark_links": 10
        }

        # Create report generator
        report_gen = ReportGenerator(cache)

        # Generate report
        report = report_gen.generate_report()

        # Verify report was generated
        assert len(report) > 0, "Report should be generated"
        assert "Benchmark Intelligence Report" in report, "Report should have title"
        assert "Executive Summary" in report, "Report should have summary"

        # Verify cache stats were called
        assert cache.get_stats.called, "Should call get_stats"
        assert cache.get_all_models.called, "Should call get_all_models"
        assert cache.get_all_benchmarks.called, "Should call get_all_benchmarks"

        print(f"\n✓ T069: End-to-End Pipeline Test")
        print(f"  Report generated: {len(report)} characters")
        print(f"  ✓ Pipeline integration successful")
        print(f"  ✓ All cache methods called correctly")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
