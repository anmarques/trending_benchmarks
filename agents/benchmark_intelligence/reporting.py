"""
Report generation for Benchmark Intelligence System.

This module provides comprehensive reporting on benchmark trends,
model statistics, and insights over time.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
import json

from .tools.cache import CacheManager


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate comprehensive reports on benchmark intelligence data.

    Produces markdown reports with statistics, trends, and insights
    from the cached benchmark and model data.
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize report generator.

        Args:
            cache_manager: Cache manager instance for data access
        """
        self.cache = cache_manager

    def generate_report(self) -> str:
        """
        Generate comprehensive markdown report.

        Returns:
            Markdown formatted report string

        Report sections:
            - Executive Summary
            - Trending Models This Month
            - Most Common Benchmarks
            - Emerging Benchmarks
            - Benchmark Categories
            - Lab-Specific Insights
            - Temporal Trends
        """
        logger.info("Generating comprehensive report...")

        # Gather data
        stats = self.cache.get_stats()
        all_models = self.cache.get_all_models()
        all_benchmarks = self.cache.get_all_benchmarks()
        benchmark_trends = self.cache.get_benchmark_trends()

        # Build report sections
        report_sections = []

        # Header
        report_sections.append(self._generate_header())

        # Executive Summary
        report_sections.append(self._generate_executive_summary(stats, all_models))

        # Trending Models This Month
        report_sections.append(self._generate_trending_models(all_models))

        # Most Common Benchmarks
        report_sections.append(self._generate_most_common_benchmarks(benchmark_trends))

        # Emerging Benchmarks
        report_sections.append(self._generate_emerging_benchmarks(all_benchmarks))

        # Benchmark Categories
        report_sections.append(self._generate_category_distribution(all_benchmarks))

        # Lab-Specific Insights
        report_sections.append(self._generate_lab_insights(all_models))

        # Temporal Trends
        report_sections.append(self._generate_temporal_trends(benchmark_trends))

        # Footer
        report_sections.append(self._generate_footer())

        # Combine all sections
        report = "\n\n".join(report_sections)

        logger.info("Report generation complete")
        return report

    def _generate_header(self) -> str:
        """Generate report header."""
        now = datetime.utcnow()
        return f"""# Benchmark Intelligence Report

**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC

---"""

    def _generate_executive_summary(
        self,
        stats: Dict[str, Any],
        all_models: List[Dict[str, Any]]
    ) -> str:
        """Generate executive summary section."""
        total_models = stats.get("models", 0)
        total_benchmarks = stats.get("benchmarks", 0)
        total_labs = stats.get("labs", 0)
        total_links = stats.get("model_benchmark_links", 0)

        # Calculate time period
        if all_models:
            dates = [m["first_seen"] for m in all_models if m.get("first_seen")]
            if dates:
                earliest = min(dates)
                latest = max(dates)
                time_period = f"{earliest[:10]} to {latest[:10]}"
            else:
                time_period = "N/A"
        else:
            time_period = "N/A"

        return f"""## Executive Summary

- **Total Models Tracked:** {total_models}
- **Total Unique Benchmarks:** {total_benchmarks}
- **Labs/Organizations:** {total_labs}
- **Benchmark Measurements:** {total_links}
- **Time Period:** {time_period}

The Benchmark Intelligence system continuously tracks trending AI models from leading labs
and organizations, extracting and analyzing benchmark results to provide insights into
evaluation trends, emerging benchmarks, and lab-specific preferences."""

    def _generate_trending_models(self, all_models: List[Dict[str, Any]]) -> str:
        """Generate trending models section."""
        # Get models from last 30 days
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent_models = self.cache.get_trending_models(thirty_days_ago)

        if not recent_models:
            return """## Trending Models This Month

No new models discovered in the last 30 days."""

        # Sort by first_seen (most recent first)
        recent_models.sort(key=lambda m: m.get("first_seen", ""), reverse=True)

        # Limit to top 20
        top_models = recent_models[:20]

        lines = ["## Trending Models This Month", ""]
        lines.append(f"Discovered {len(recent_models)} new models in the last 30 days.")
        lines.append("")
        lines.append("| Model | Lab | Downloads | Likes | First Seen |")
        lines.append("|-------|-----|-----------|-------|------------|")

        for model in top_models:
            name = model.get("name", model.get("id", "Unknown"))
            lab = model.get("lab", "Unknown")
            downloads = self._format_number(model.get("downloads", 0))
            likes = self._format_number(model.get("likes", 0))
            first_seen = model.get("first_seen", "")[:10]

            lines.append(f"| {name} | {lab} | {downloads} | {likes} | {first_seen} |")

        return "\n".join(lines)

    def _generate_most_common_benchmarks(
        self,
        benchmark_trends: List[Dict[str, Any]]
    ) -> str:
        """Generate most common benchmarks section."""
        if not benchmark_trends:
            return """## Most Common Benchmarks

No benchmark data available."""

        # Sort by total_models (most popular first)
        all_time = sorted(
            benchmark_trends,
            key=lambda b: b.get("total_models", 0),
            reverse=True
        )[:20]

        # Get recent benchmarks (last 30 days)
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent = [
            b for b in benchmark_trends
            if b.get("last_recorded", "") >= thirty_days_ago
        ]
        recent = sorted(
            recent,
            key=lambda b: b.get("total_models", 0),
            reverse=True
        )[:20]

        lines = ["## Most Common Benchmarks", ""]

        # All-time top benchmarks
        lines.append("### All-Time Top 20")
        lines.append("")
        lines.append("| Benchmark | Models | Categories | First Seen |")
        lines.append("|-----------|--------|------------|------------|")

        for bench in all_time:
            name = bench.get("canonical_name", "Unknown")
            models = bench.get("total_models", 0)
            categories = ", ".join(bench.get("categories", [])[:3])
            if not categories:
                categories = "Uncategorized"
            first_seen = bench.get("first_seen", "")[:10]

            lines.append(f"| {name} | {models} | {categories} | {first_seen} |")

        # Recent benchmarks
        if recent:
            lines.append("")
            lines.append("### This Month's Top 20")
            lines.append("")
            lines.append("| Benchmark | Models | Categories | Last Recorded |")
            lines.append("|-----------|--------|------------|---------------|")

            for bench in recent:
                name = bench.get("canonical_name", "Unknown")
                models = bench.get("total_models", 0)
                categories = ", ".join(bench.get("categories", [])[:3])
                if not categories:
                    categories = "Uncategorized"
                last_recorded = bench.get("last_recorded", "")[:10]

                lines.append(f"| {name} | {models} | {categories} | {last_recorded} |")

        return "\n".join(lines)

    def _generate_emerging_benchmarks(
        self,
        all_benchmarks: List[Dict[str, Any]]
    ) -> str:
        """Generate emerging benchmarks section."""
        # Get benchmarks first seen in last 90 days
        ninety_days_ago = (datetime.utcnow() - timedelta(days=90)).isoformat()

        emerging = [
            b for b in all_benchmarks
            if b.get("first_seen", "") >= ninety_days_ago
        ]

        if not emerging:
            return """## Emerging Benchmarks

No new benchmarks discovered in the last 90 days."""

        # Sort by first_seen (most recent first)
        emerging.sort(key=lambda b: b.get("first_seen", ""), reverse=True)

        # Limit to top 15
        top_emerging = emerging[:15]

        lines = ["## Emerging Benchmarks", ""]
        lines.append(f"Discovered {len(emerging)} new benchmarks in the last 90 days.")
        lines.append("")
        lines.append("| Benchmark | Categories | First Seen |")
        lines.append("|-----------|------------|------------|")

        for bench in top_emerging:
            name = bench.get("canonical_name", "Unknown")
            categories = ", ".join(bench.get("categories", [])[:3])
            if not categories:
                categories = "Uncategorized"
            first_seen = bench.get("first_seen", "")[:10]

            lines.append(f"| {name} | {categories} | {first_seen} |")

        return "\n".join(lines)

    def _generate_category_distribution(
        self,
        all_benchmarks: List[Dict[str, Any]]
    ) -> str:
        """Generate benchmark category distribution section."""
        # Count categories
        category_counter = Counter()

        for bench in all_benchmarks:
            categories = bench.get("categories", [])
            for category in categories:
                category_counter[category] += 1

        if not category_counter:
            return """## Benchmark Categories

No category data available."""

        # Get top categories
        top_categories = category_counter.most_common(15)

        lines = ["## Benchmark Categories", ""]
        lines.append("Distribution of benchmarks across categories:")
        lines.append("")
        lines.append("| Category | Count | Percentage |")
        lines.append("|----------|-------|------------|")

        total = sum(category_counter.values())

        for category, count in top_categories:
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"| {category} | {count} | {percentage:.1f}% |")

        # Add pie chart data (for visualization)
        lines.append("")
        lines.append("### Category Distribution Data")
        lines.append("")
        lines.append("```json")
        chart_data = {
            "categories": [cat for cat, _ in top_categories],
            "counts": [count for _, count in top_categories],
        }
        lines.append(json.dumps(chart_data, indent=2))
        lines.append("```")

        return "\n".join(lines)

    def _generate_lab_insights(self, all_models: List[Dict[str, Any]]) -> str:
        """Generate lab-specific insights section."""
        # Group models by lab
        labs = defaultdict(list)
        for model in all_models:
            lab = model.get("lab")
            if lab:
                labs[lab].append(model)

        if not labs:
            return """## Lab-Specific Insights

No lab data available."""

        lines = ["## Lab-Specific Insights", ""]
        lines.append("### Models by Lab")
        lines.append("")
        lines.append("| Lab | Models | Avg Downloads | Avg Likes |")
        lines.append("|-----|--------|---------------|-----------|")

        # Sort labs by model count
        lab_stats = []
        for lab, models in labs.items():
            model_count = len(models)
            avg_downloads = sum(m.get("downloads", 0) for m in models) / model_count
            avg_likes = sum(m.get("likes", 0) for m in models) / model_count

            lab_stats.append({
                "lab": lab,
                "models": model_count,
                "avg_downloads": avg_downloads,
                "avg_likes": avg_likes,
            })

        lab_stats.sort(key=lambda x: x["models"], reverse=True)

        for stat in lab_stats[:20]:  # Top 20 labs
            lab = stat["lab"]
            models = stat["models"]
            avg_downloads = self._format_number(int(stat["avg_downloads"]))
            avg_likes = self._format_number(int(stat["avg_likes"]))

            lines.append(f"| {lab} | {models} | {avg_downloads} | {avg_likes} |")

        # Benchmark preferences by lab
        lines.append("")
        lines.append("### Benchmark Preferences by Lab")
        lines.append("")
        lines.append("Top benchmarks used by each lab (coming soon).")

        return "\n".join(lines)

    def _generate_temporal_trends(
        self,
        benchmark_trends: List[Dict[str, Any]]
    ) -> str:
        """Generate temporal trends section."""
        if not benchmark_trends:
            return """## Temporal Trends

No trend data available."""

        # Calculate growth metrics
        # This is simplified - in production would have more sophisticated analysis

        lines = ["## Temporal Trends", ""]
        lines.append("### Benchmark Popularity Over Time")
        lines.append("")
        lines.append("Tracking how benchmark usage evolves over time.")
        lines.append("")

        # Get benchmarks with activity
        active_benchmarks = [
            b for b in benchmark_trends
            if b.get("total_models", 0) > 0
        ]

        if active_benchmarks:
            # Sort by last_recorded
            active_benchmarks.sort(
                key=lambda b: b.get("last_recorded", ""),
                reverse=True
            )

            lines.append("| Benchmark | First Recorded | Last Recorded | Active Days | Total Models |")
            lines.append("|-----------|----------------|---------------|-------------|--------------|")

            for bench in active_benchmarks[:15]:
                name = bench.get("canonical_name", "Unknown")
                first = bench.get("first_recorded", "N/A")[:10]
                last = bench.get("last_recorded", "N/A")[:10]
                active_days = bench.get("active_days", 0)
                total_models = bench.get("total_models", 0)

                lines.append(f"| {name} | {first} | {last} | {active_days} | {total_models} |")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return f"""---

**Report Generation Details:**
- System: Benchmark Intelligence Agent
- Data Source: SQLite Cache Database
- Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

For more information, see the [project documentation](../../README.md)."""

    def _format_number(self, num: int) -> str:
        """Format number with thousands separators."""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return str(num)

    def update_readme(self, report_content: str) -> None:
        """
        Update the main README.md with the report.

        Args:
            report_content: Markdown report content
        """
        readme_path = Path(__file__).parent / "README.md"

        logger.info(f"Updating README at {readme_path}")

        try:
            with open(readme_path, "w") as f:
                f.write(report_content)

            logger.info("README updated successfully")

        except Exception as e:
            logger.error(f"Failed to update README: {e}")
            raise

    def save_snapshot(self, report_content: str) -> str:
        """
        Save historical snapshot of report.

        Args:
            report_content: Markdown report content

        Returns:
            Path to saved snapshot file
        """
        # Create reports directory if it doesn't exist
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_path = reports_dir / f"report_{timestamp}.md"

        logger.info(f"Saving report snapshot to {snapshot_path}")

        try:
            with open(snapshot_path, "w") as f:
                f.write(report_content)

            logger.info(f"Snapshot saved successfully: {snapshot_path}")
            return str(snapshot_path)

        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise

    def generate_json_summary(self) -> Dict[str, Any]:
        """
        Generate JSON summary of key metrics.

        Returns:
            Dictionary with key metrics and statistics
        """
        stats = self.cache.get_stats()
        all_models = self.cache.get_all_models()
        all_benchmarks = self.cache.get_all_benchmarks()
        benchmark_trends = self.cache.get_benchmark_trends()

        # Get recent models
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent_models = self.cache.get_trending_models(thirty_days_ago)

        # Top benchmarks
        top_benchmarks = sorted(
            benchmark_trends,
            key=lambda b: b.get("total_models", 0),
            reverse=True
        )[:10]

        # Category distribution
        category_counter = Counter()
        for bench in all_benchmarks:
            for category in bench.get("categories", []):
                category_counter[category] += 1

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_models": stats.get("models", 0),
                "total_benchmarks": stats.get("benchmarks", 0),
                "total_labs": stats.get("labs", 0),
                "models_this_month": len(recent_models),
            },
            "top_benchmarks": [
                {
                    "name": b.get("canonical_name"),
                    "models": b.get("total_models", 0),
                    "categories": b.get("categories", []),
                }
                for b in top_benchmarks
            ],
            "category_distribution": dict(category_counter.most_common(10)),
            "cache_stats": stats,
        }
