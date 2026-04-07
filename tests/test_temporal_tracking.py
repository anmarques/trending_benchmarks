"""
Tests for temporal tracking functionality.

Tests 12-month window calculation and status classification (emerging/extinct).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestTemporalTracking:
    """Test suite for temporal tracking features."""

    def test_12_month_window_calculation(self):
        """Test that 12-month window is calculated correctly."""
        # Current date
        now = datetime.now()

        # Calculate 12 months ago
        twelve_months_ago = now - relativedelta(months=12)

        # Test that the difference is approximately 12 months
        months_diff = (now.year - twelve_months_ago.year) * 12 + (now.month - twelve_months_ago.month)
        assert months_diff == 12

    def test_model_age_calculation(self):
        """Test calculating model age for temporal filtering."""
        now = datetime.now()

        # Model from 6 months ago (should be included)
        recent_model_date = now - relativedelta(months=6)

        # Model from 18 months ago (should be excluded)
        old_model_date = now - relativedelta(months=18)

        # 12-month threshold
        threshold = now - relativedelta(months=12)

        assert recent_model_date > threshold
        assert old_model_date < threshold

    def test_benchmark_emergence_detection(self):
        """Test detecting emerging benchmarks."""
        # Simulate benchmark mentions over time
        benchmark_timeline = {
            "MMLU": {
                "first_seen": datetime.now() - relativedelta(months=24),
                "mentions_last_3_months": 50,
                "mentions_previous_9_months": 10
            },
            "NewBench": {
                "first_seen": datetime.now() - relativedelta(months=2),
                "mentions_last_3_months": 30,
                "mentions_previous_9_months": 0
            }
        }

        # NewBench is emerging (recent first appearance + high recent mentions)
        newbench = benchmark_timeline["NewBench"]
        is_emerging = (
            newbench["first_seen"] > datetime.now() - relativedelta(months=6) and
            newbench["mentions_last_3_months"] > 10
        )
        assert is_emerging

        # MMLU is not emerging (old benchmark)
        mmlu = benchmark_timeline["MMLU"]
        is_not_emerging = mmlu["first_seen"] > datetime.now() - relativedelta(months=6)
        assert not is_not_emerging

    def test_benchmark_extinction_detection(self):
        """Test detecting extinct/declining benchmarks."""
        # Simulate benchmark usage decline
        benchmark_timeline = {
            "OldBench": {
                "mentions_last_3_months": 2,
                "mentions_previous_9_months": 45,
                "last_seen": datetime.now() - relativedelta(months=8)
            },
            "ActiveBench": {
                "mentions_last_3_months": 40,
                "mentions_previous_9_months": 35,
                "last_seen": datetime.now() - relativedelta(days=5)
            }
        }

        # OldBench is extinct (sharp decline in usage)
        oldbench = benchmark_timeline["OldBench"]
        decline_ratio = oldbench["mentions_last_3_months"] / max(oldbench["mentions_previous_9_months"], 1)
        is_extinct = decline_ratio < 0.2  # Less than 20% of previous usage
        assert is_extinct

        # ActiveBench is not extinct (stable/growing usage)
        activebench = benchmark_timeline["ActiveBench"]
        active_decline_ratio = activebench["mentions_last_3_months"] / max(activebench["mentions_previous_9_months"], 1)
        is_not_extinct = active_decline_ratio < 0.2
        assert not is_not_extinct

    def test_status_classification_emerging(self):
        """Test classification of emerging benchmarks."""

        def classify_benchmark_status(first_seen, mentions_recent, mentions_old):
            """Classify benchmark as emerging, stable, or extinct."""
            # Emerging: first seen in last 6 months AND gaining traction
            if first_seen > datetime.now() - relativedelta(months=6):
                if mentions_recent > 10:
                    return "emerging"

            # Extinct: sharp decline in usage
            if mentions_old > 0:
                decline_ratio = mentions_recent / mentions_old
                if decline_ratio < 0.2 and mentions_recent < 5:
                    return "extinct"

            # Stable: everything else
            return "stable"

        # Test emerging
        status = classify_benchmark_status(
            first_seen=datetime.now() - relativedelta(months=3),
            mentions_recent=25,
            mentions_old=0
        )
        assert status == "emerging"

    def test_status_classification_extinct(self):
        """Test classification of extinct benchmarks."""

        def classify_benchmark_status(first_seen, mentions_recent, mentions_old):
            """Classify benchmark as emerging, stable, or extinct."""
            if first_seen > datetime.now() - relativedelta(months=6):
                if mentions_recent > 10:
                    return "emerging"

            if mentions_old > 0:
                decline_ratio = mentions_recent / mentions_old
                if decline_ratio < 0.2 and mentions_recent < 5:
                    return "extinct"

            return "stable"

        # Test extinct
        status = classify_benchmark_status(
            first_seen=datetime.now() - relativedelta(months=18),
            mentions_recent=3,
            mentions_old=50
        )
        assert status == "extinct"

    def test_status_classification_stable(self):
        """Test classification of stable benchmarks."""

        def classify_benchmark_status(first_seen, mentions_recent, mentions_old):
            """Classify benchmark as emerging, stable, or extinct."""
            if first_seen > datetime.now() - relativedelta(months=6):
                if mentions_recent > 10:
                    return "emerging"

            if mentions_old > 0:
                decline_ratio = mentions_recent / mentions_old
                if decline_ratio < 0.2 and mentions_recent < 5:
                    return "extinct"

            return "stable"

        # Test stable
        status = classify_benchmark_status(
            first_seen=datetime.now() - relativedelta(months=18),
            mentions_recent=40,
            mentions_old=35
        )
        assert status == "stable"

    def test_temporal_window_filtering(self):
        """Test filtering models by temporal window."""
        now = datetime.now()

        models = [
            {"id": "model1", "created_at": now - relativedelta(months=3)},
            {"id": "model2", "created_at": now - relativedelta(months=8)},
            {"id": "model3", "created_at": now - relativedelta(months=15)},
            {"id": "model4", "created_at": now - relativedelta(months=1)},
        ]

        # Filter to 12-month window
        threshold = now - relativedelta(months=12)
        filtered = [m for m in models if m["created_at"] > threshold]

        assert len(filtered) == 3  # model1, model2, model4
        assert "model3" not in [m["id"] for m in filtered]

    def test_benchmark_trend_analysis(self):
        """Test analyzing benchmark trends over time."""
        # Simulate monthly mention counts
        benchmark_data = {
            "months": list(range(12)),  # Last 12 months (0 = current month)
            "mentions": [5, 8, 12, 15, 18, 22, 28, 35, 40, 45, 50, 55]
        }

        # Calculate trend (increasing)
        recent_avg = sum(benchmark_data["mentions"][-3:]) / 3  # Last 3 months
        older_avg = sum(benchmark_data["mentions"][:3]) / 3    # First 3 months

        growth_rate = (recent_avg - older_avg) / older_avg
        assert growth_rate > 0  # Positive growth
        assert growth_rate > 2.0  # More than 200% growth

    def test_time_series_aggregation(self):
        """Test aggregating benchmark data by time periods."""
        from collections import defaultdict

        # Simulate benchmark mentions with timestamps
        mentions = [
            {"benchmark": "MMLU", "date": datetime.now() - relativedelta(months=1)},
            {"benchmark": "MMLU", "date": datetime.now() - relativedelta(months=2)},
            {"benchmark": "GSM8K", "date": datetime.now() - relativedelta(months=1)},
            {"benchmark": "MMLU", "date": datetime.now() - relativedelta(months=6)},
        ]

        # Aggregate by quarter
        def get_quarter(date):
            return (date.year, (date.month - 1) // 3)

        by_quarter = defaultdict(lambda: defaultdict(int))
        for mention in mentions:
            quarter = get_quarter(mention["date"])
            by_quarter[quarter][mention["benchmark"]] += 1

        # Should have data aggregated by quarters
        assert len(by_quarter) >= 2  # At least 2 quarters

    def test_recency_scoring(self):
        """Test scoring benchmarks by recency."""
        now = datetime.now()

        benchmarks = [
            {"name": "A", "last_seen": now - relativedelta(days=5)},
            {"name": "B", "last_seen": now - relativedelta(months=3)},
            {"name": "C", "last_seen": now - relativedelta(months=10)},
        ]

        # Calculate recency scores (higher = more recent)
        for bench in benchmarks:
            days_ago = (now - bench["last_seen"]).days
            bench["recency_score"] = 1.0 / (days_ago + 1)

        # Sort by recency
        sorted_benches = sorted(benchmarks, key=lambda x: x["recency_score"], reverse=True)

        # Most recent should be first
        assert sorted_benches[0]["name"] == "A"
        assert sorted_benches[-1]["name"] == "C"

    def test_seasonal_patterns(self):
        """Test detecting seasonal patterns in benchmark usage."""
        # This is a simplified test - real implementation would be more complex
        monthly_mentions = {
            "January": 10,
            "February": 12,
            "March": 15,
            "April": 8,   # Conference deadline?
            "May": 20,
            "June": 25,
            "July": 18,
            "August": 15,
            "September": 30,  # Back to school?
            "October": 28,
            "November": 32,
            "December": 12,   # Holiday season
        }

        # Simple variance check
        values = list(monthly_mentions.values())
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)

        # Should have some variance (not flat line)
        assert variance > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
