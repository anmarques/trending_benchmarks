"""
Report generation for Benchmark Intelligence System.

This module provides comprehensive reporting on benchmark trends,
model statistics, and insights over time.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
import json

from .tools.cache import CacheManager
from .tools.retry_utils import retry_with_exponential_backoff


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate comprehensive reports on benchmark intelligence data.

    Produces markdown reports with statistics, trends, and insights
    from the cached benchmark and model data.
    """

    def __init__(self, cache_manager: CacheManager, retry_config: Optional[Dict[str, Any]] = None):
        """
        Initialize report generator.

        Args:
            cache_manager: Cache manager instance for data access
            retry_config: Optional retry configuration for report generation
        """
        self.cache = cache_manager
        self.retry_config = retry_config or {
            "max_attempts": 3,
            "initial_delay_seconds": 1,
            "backoff_multiplier": 2,
            "max_delay_seconds": 60,
        }

    def generate_report(self) -> str:
        """
        Generate comprehensive markdown report with retry logic.

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
        logger.info("Generating comprehensive report with retry logic...")

        # Use retry wrapper for report generation
        return retry_with_exponential_backoff(
            self._generate_report_internal,
            self.retry_config
        )

    def _generate_report_internal(self) -> str:
        """
        Internal report generation logic (wrapped by retry).

        Returns:
            Markdown formatted report string

        T033: Integrate temporal snapshot data into report generation
        """
        logger.info("Executing report generation...")

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

        # Temporal Trends (T028 - updated with snapshot-based tracking)
        report_sections.append(self._generate_temporal_trends(benchmark_trends))

        # Emerging Benchmarks (T029 - from temporal snapshot)
        report_sections.append(self._generate_emerging_benchmarks_section())

        # Almost Extinct Benchmarks (T030 - from temporal snapshot)
        report_sections.append(self._generate_almost_extinct_section())

        # Historical Snapshot Comparison (T031)
        report_sections.append(self._generate_historical_comparison())

        # Benchmark Categories
        report_sections.append(self._generate_category_distribution(all_benchmarks))

        # Lab-Specific Insights
        report_sections.append(self._generate_lab_insights(all_models))

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

        # Calculate variant statistics
        all_benchmarks = self.cache.get_all_benchmarks()
        variant_count = 0
        for model in all_models:
            benchmarks = self.cache.get_model_benchmarks(model.get("id"))
            for bench in benchmarks:
                context = bench.get("context", {})
                # Count variants based on context (shots, subset, etc.)
                if context:
                    variant_count += 1

        # Calculate benchmark status distribution
        status_distribution = {"emerging": 0, "active": 0, "almost_extinct": 0}
        three_months_ago = (datetime.utcnow() - timedelta(days=90)).isoformat()
        nine_months_ago = (datetime.utcnow() - timedelta(days=270)).isoformat()

        for bench in all_benchmarks:
            first_seen = bench.get("first_seen", "")
            last_seen = bench.get("last_seen", "")
            status = self.cache.determine_benchmark_status(first_seen, last_seen)
            status_distribution[status] = status_distribution.get(status, 0) + 1

        return f"""## Executive Summary

- **Total Models Tracked:** {total_models}
- **Total Unique Benchmarks:** {total_benchmarks}
- **Benchmark Variants:** {variant_count}
- **Labs/Organizations:** {total_labs}
- **Benchmark Measurements:** {total_links}
- **Time Period:** {time_period}

**Benchmark Status Distribution:**
- **Emerging** (first seen ≤ 3 months): {status_distribution['emerging']}
- **Active** (stable activity): {status_distribution['active']}
- **Almost Extinct** (not seen ≥ 9 months): {status_distribution['almost_extinct']}

The Benchmark Intelligence system continuously tracks trending AI models from leading labs
and organizations, extracting and analyzing benchmark results to provide insights into
evaluation trends, emerging benchmarks, and lab-specific preferences."""

    def _generate_trending_models(self, all_models: List[Dict[str, Any]]) -> str:
        """Generate trending models section."""
        # Get models from last 12 months (to match discovery config)
        twelve_months_ago = (datetime.utcnow() - timedelta(days=365)).isoformat()
        recent_models = self.cache.get_trending_models(twelve_months_ago)

        if not recent_models:
            return """## Trending Models (Last 12 Months)

No new models discovered in the last 12 months."""

        # Sort by downloads (most popular first), then by release date
        recent_models.sort(
            key=lambda m: (m.get("downloads", 0), m.get("first_seen", "")),
            reverse=True
        )

        # Show ALL models (no arbitrary limit)
        lines = ["## Trending Models (Last 12 Months)", ""]
        lines.append(f"Discovered {len(recent_models)} models from major labs in the last year.")
        lines.append("")
        lines.append("| Model | Lab | Downloads | Likes | Release Date |")
        lines.append("|-------|-----|-----------|-------|--------------|")

        for model in recent_models:
            name = model.get("name", model.get("id", "Unknown"))
            lab = model.get("lab", "Unknown")
            downloads = self._format_number(model.get("downloads", 0))
            likes = self._format_number(model.get("likes", 0))
            # Use release_date if available, otherwise first_seen
            release_date = model.get("release_date", model.get("first_seen", ""))[:10]

            lines.append(f"| {name} | {lab} | {downloads} | {likes} | {release_date} |")

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
        lines.append("| Benchmark | Models | Categories | Status | First Seen |")
        lines.append("|-----------|--------|------------|--------|------------|")

        for bench in all_time:
            name = bench.get("canonical_name", "Unknown")
            models = bench.get("total_models", 0)
            categories = ", ".join(bench.get("categories", [])[:3])
            if not categories:
                categories = "Uncategorized"
            first_seen = bench.get("first_seen", "")
            last_seen = bench.get("last_recorded", bench.get("last_seen", ""))

            # Determine status
            status = self.cache.determine_benchmark_status(first_seen, last_seen)
            status_icon = {"emerging": "🆕", "active": "✅", "almost_extinct": "⚠️"}.get(status, "")
            status_label = f"{status_icon} {status.replace('_', ' ').title()}"

            first_seen_date = first_seen[:10]

            lines.append(f"| {name} | {models} | {categories} | {status_label} | {first_seen_date} |")

        # Recent benchmarks
        if recent:
            lines.append("")
            lines.append("### This Month's Top 20")
            lines.append("")
            lines.append("| Benchmark | Models | Categories | Status | Last Recorded |")
            lines.append("|-----------|--------|------------|--------|---------------|")

            for bench in recent:
                name = bench.get("canonical_name", "Unknown")
                models = bench.get("total_models", 0)
                categories = ", ".join(bench.get("categories", [])[:3])
                if not categories:
                    categories = "Uncategorized"
                first_seen = bench.get("first_seen", "")
                last_recorded = bench.get("last_recorded", "")

                # Determine status
                status = self.cache.determine_benchmark_status(first_seen, last_recorded)
                status_icon = {"emerging": "🆕", "active": "✅", "almost_extinct": "⚠️"}.get(status, "")
                status_label = f"{status_icon} {status.replace('_', ' ').title()}"

                last_recorded_date = last_recorded[:10]

                lines.append(f"| {name} | {models} | {categories} | {status_label} | {last_recorded_date} |")

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

        # Get taxonomy version info from latest snapshot
        recent_snapshots = self.cache.get_recent_snapshots(limit=1)
        taxonomy_info = ""
        if recent_snapshots:
            snapshot = recent_snapshots[0]
            taxonomy_version = snapshot.get("taxonomy_version")
            if taxonomy_version:
                taxonomy_info = f"\n**Taxonomy Version:** {taxonomy_version}"
                lines.append(f"_Current taxonomy version: {taxonomy_version}_")
                lines.append("")

        lines.append("| Category | Count | Percentage |")
        lines.append("|----------|-------|------------|")

        total = sum(category_counter.values())

        for category, count in top_categories:
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"| {category} | {count} | {percentage:.1f}% |")

        # Add taxonomy change notes
        lines.append("")
        lines.append("### Taxonomy Evolution Notes")
        lines.append("")
        lines.append("The benchmark taxonomy is automatically evolved and refined over time as new benchmarks are discovered.")
        lines.append("Categories are generated based on benchmark names, descriptions, and usage patterns across models.")
        lines.append("")
        lines.append("**Key Features:**")
        lines.append("- **Automatic Evolution**: New categories emerge as new benchmarks are discovered")
        lines.append("- **Versioned History**: All taxonomy changes are archived for historical tracking")
        lines.append("- **Multi-Label Support**: Benchmarks can belong to multiple categories")
        lines.append("- **Manual Overrides**: Categories can be manually refined via `categories.yaml`")

        # Check if there are multiple snapshots to show taxonomy changes
        all_snapshots = self.cache.get_recent_snapshots(limit=5)
        if len(all_snapshots) > 1:
            lines.append("")
            lines.append("**Recent Taxonomy Updates:**")
            lines.append("")
            lines.append("| Snapshot Date | Taxonomy Version | Notes |")
            lines.append("|---------------|------------------|-------|")
            for snap in all_snapshots:
                snap_date = snap.get("timestamp", "")[:10]
                tax_ver = snap.get("taxonomy_version", "N/A")
                # Extract summary if available
                summary = snap.get("summary", {})
                notes = summary.get("taxonomy_notes", "Standard taxonomy")
                lines.append(f"| {snap_date} | {tax_ver} | {notes} |")

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
        """
        Generate temporal trends section with snapshot-based tracking.

        T028: Temporal Trends Section
        """
        lines = ["## Temporal Trends", ""]

        # Get latest snapshot
        snapshots = self.cache.get_recent_snapshots(limit=1)
        if not snapshots:
            lines.append("No temporal snapshot data available yet.")
            lines.append("")
            lines.append("_Run the pipeline in snapshot or full mode to generate temporal data._")
            return "\n".join(lines)

        latest_snapshot = snapshots[0]
        snapshot_id = latest_snapshot['id']
        window_start = latest_snapshot['window_start'][:10]
        window_end = latest_snapshot['window_end'][:10]

        lines.append(f"**Rolling Window:** {window_start} to {window_end} (12 months)")
        lines.append("")

        # Get benchmark mentions for this snapshot
        mentions = self.cache.get_benchmark_mentions_for_snapshot(snapshot_id)

        if not mentions:
            lines.append("No benchmark mentions in current snapshot.")
            return "\n".join(lines)

        # Sort by relative frequency
        mentions.sort(key=lambda m: m['relative_frequency'], reverse=True)

        lines.append("### Top Benchmarks by Frequency")
        lines.append("")
        lines.append("| Benchmark | Mentions | Frequency | Status | Categories |")
        lines.append("|-----------|----------|-----------|--------|------------|")

        for mention in mentions[:20]:
            name = mention.get('benchmark_name', 'Unknown')
            abs_mentions = mention.get('absolute_mentions', 0)
            rel_freq = mention.get('relative_frequency', 0.0)
            status = mention.get('status', 'active')
            categories = ", ".join(mention.get('categories', [])[:2])
            if not categories:
                categories = "Uncategorized"

            # Format frequency as percentage
            freq_pct = f"{rel_freq * 100:.1f}%"

            lines.append(f"| {name} | {abs_mentions} | {freq_pct} | {status} | {categories} |")

        return "\n".join(lines)

    def _generate_emerging_benchmarks_section(self) -> str:
        """
        Generate Emerging Benchmarks section from temporal snapshot.

        Shows benchmarks first seen ≤ 3 months ago.

        T029: Emerging Benchmarks Section
        """
        lines = ["## Emerging Benchmarks", ""]

        # Get latest snapshot
        snapshots = self.cache.get_recent_snapshots(limit=1)
        if not snapshots:
            lines.append("No temporal snapshot data available yet.")
            return "\n".join(lines)

        latest_snapshot = snapshots[0]
        snapshot_id = latest_snapshot['id']

        # Get benchmark mentions with "emerging" status
        mentions = self.cache.get_benchmark_mentions_for_snapshot(snapshot_id)
        emerging = [m for m in mentions if m.get('status') == 'emerging']

        if not emerging:
            lines.append("No emerging benchmarks detected in the current snapshot.")
            lines.append("")
            lines.append("_Emerging benchmarks are those first seen within the last 3 months._")
            return "\n".join(lines)

        # Sort by first_seen (most recent first)
        emerging.sort(key=lambda m: m.get('first_seen', ''), reverse=True)

        lines.append(f"Discovered **{len(emerging)}** new benchmarks in the last 3 months.")
        lines.append("")
        lines.append("| Benchmark | First Seen | Mentions | Frequency | Categories |")
        lines.append("|-----------|------------|----------|-----------|------------|")

        for bench in emerging:
            name = bench.get('benchmark_name', 'Unknown')
            first_seen = bench.get('first_seen', '')[:10]
            mentions = bench.get('absolute_mentions', 0)
            rel_freq = bench.get('relative_frequency', 0.0)
            categories = ", ".join(bench.get('categories', [])[:2])
            if not categories:
                categories = "Uncategorized"

            freq_pct = f"{rel_freq * 100:.1f}%"

            lines.append(f"| {name} | {first_seen} | {mentions} | {freq_pct} | {categories} |")

        return "\n".join(lines)

    def _generate_almost_extinct_section(self) -> str:
        """
        Generate Almost Extinct Benchmarks section from temporal snapshot.

        Shows benchmarks last seen ≥ 9 months ago.

        T030: Almost Extinct Benchmarks Section
        """
        lines = ["## Almost Extinct Benchmarks", ""]

        # Get latest snapshot
        snapshots = self.cache.get_recent_snapshots(limit=1)
        if not snapshots:
            lines.append("No temporal snapshot data available yet.")
            return "\n".join(lines)

        latest_snapshot = snapshots[0]
        snapshot_id = latest_snapshot['id']

        # Get benchmark mentions with "almost_extinct" status
        mentions = self.cache.get_benchmark_mentions_for_snapshot(snapshot_id)
        almost_extinct = [m for m in mentions if m.get('status') == 'almost_extinct']

        if not almost_extinct:
            lines.append("No almost-extinct benchmarks detected in the current snapshot.")
            lines.append("")
            lines.append("_Almost-extinct benchmarks are those last seen ≥ 9 months ago._")
            return "\n".join(lines)

        # Sort by last_seen (oldest first)
        almost_extinct.sort(key=lambda m: m.get('last_seen', ''))

        lines.append(f"Identified **{len(almost_extinct)}** benchmarks nearing extinction.")
        lines.append("")
        lines.append("| Benchmark | Last Seen | Mentions | Categories |")
        lines.append("|-----------|-----------|----------|------------|")

        for bench in almost_extinct:
            name = bench.get('benchmark_name', 'Unknown')
            last_seen = bench.get('last_seen', '')[:10]
            mentions = bench.get('absolute_mentions', 0)
            categories = ", ".join(bench.get('categories', [])[:2])
            if not categories:
                categories = "Uncategorized"

            lines.append(f"| {name} | {last_seen} | {mentions} | {categories} |")

        return "\n".join(lines)

    def _generate_historical_comparison(self) -> str:
        """
        Generate Historical Snapshot Comparison section.

        Compares current snapshot with previous snapshot to show trends.

        T031: Historical Snapshot Comparison
        """
        lines = ["## Historical Snapshot Comparison", ""]

        # Get last 2 snapshots
        snapshots = self.cache.get_recent_snapshots(limit=2)
        if len(snapshots) < 2:
            lines.append("Not enough snapshots for historical comparison.")
            lines.append("")
            lines.append("_At least 2 snapshots are required. Run the pipeline multiple times._")
            return "\n".join(lines)

        current_snapshot = snapshots[0]
        previous_snapshot = snapshots[1]

        current_id = current_snapshot['id']
        previous_id = previous_snapshot['id']

        current_date = current_snapshot['timestamp'][:10]
        previous_date = previous_snapshot['timestamp'][:10]

        lines.append(f"**Current Snapshot:** {current_date}")
        lines.append(f"**Previous Snapshot:** {previous_date}")
        lines.append("")

        # Get mentions for both snapshots
        current_mentions = self.cache.get_benchmark_mentions_for_snapshot(current_id)
        previous_mentions = self.cache.get_benchmark_mentions_for_snapshot(previous_id)

        # Create lookup dictionaries
        current_dict = {m['benchmark_id']: m for m in current_mentions}
        previous_dict = {m['benchmark_id']: m for m in previous_mentions}

        # Calculate changes
        changes = []
        all_benchmark_ids = set(current_dict.keys()) | set(previous_dict.keys())

        for benchmark_id in all_benchmark_ids:
            current = current_dict.get(benchmark_id)
            previous = previous_dict.get(benchmark_id)

            if current and previous:
                # Benchmark in both snapshots
                freq_change = current['relative_frequency'] - previous['relative_frequency']
                mention_change = current['absolute_mentions'] - previous['absolute_mentions']
                changes.append({
                    'benchmark_name': current['benchmark_name'],
                    'status': 'changed',
                    'current_freq': current['relative_frequency'],
                    'previous_freq': previous['relative_frequency'],
                    'freq_change': freq_change,
                    'mention_change': mention_change,
                    'categories': current.get('categories', [])
                })
            elif current:
                # New benchmark
                changes.append({
                    'benchmark_name': current['benchmark_name'],
                    'status': 'new',
                    'current_freq': current['relative_frequency'],
                    'previous_freq': 0.0,
                    'freq_change': current['relative_frequency'],
                    'mention_change': current['absolute_mentions'],
                    'categories': current.get('categories', [])
                })
            else:
                # Disappeared benchmark
                changes.append({
                    'benchmark_name': previous['benchmark_name'],
                    'status': 'disappeared',
                    'current_freq': 0.0,
                    'previous_freq': previous['relative_frequency'],
                    'freq_change': -previous['relative_frequency'],
                    'mention_change': -previous['absolute_mentions'],
                    'categories': previous.get('categories', [])
                })

        # Sort by absolute frequency change
        changes.sort(key=lambda c: abs(c['freq_change']), reverse=True)

        # Show top gainers
        gainers = [c for c in changes if c['freq_change'] > 0][:10]
        if gainers:
            lines.append("### Top Gainers")
            lines.append("")
            lines.append("| Benchmark | Previous | Current | Change |")
            lines.append("|-----------|----------|---------|--------|")

            for change in gainers:
                name = change['benchmark_name']
                prev = f"{change['previous_freq'] * 100:.1f}%"
                curr = f"{change['current_freq'] * 100:.1f}%"
                delta = f"+{change['freq_change'] * 100:.1f}%"

                lines.append(f"| {name} | {prev} | {curr} | {delta} |")

            lines.append("")

        # Show top decliners
        decliners = [c for c in changes if c['freq_change'] < 0][:10]
        if decliners:
            lines.append("### Top Decliners")
            lines.append("")
            lines.append("| Benchmark | Previous | Current | Change |")
            lines.append("|-----------|----------|---------|--------|")

            for change in decliners:
                name = change['benchmark_name']
                prev = f"{change['previous_freq'] * 100:.1f}%"
                curr = f"{change['current_freq'] * 100:.1f}%"
                delta = f"{change['freq_change'] * 100:.1f}%"

                lines.append(f"| {name} | {prev} | {curr} | {delta} |")

            lines.append("")

        # Summary stats
        new_count = len([c for c in changes if c['status'] == 'new'])
        disappeared_count = len([c for c in changes if c['status'] == 'disappeared'])

        lines.append("### Summary")
        lines.append("")
        lines.append(f"- **New benchmarks:** {new_count}")
        lines.append(f"- **Disappeared benchmarks:** {disappeared_count}")
        lines.append(f"- **Model count change:** {current_snapshot['model_count']} vs {previous_snapshot['model_count']}")

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

    def update_readme(self, report_path: str) -> None:
        """
        Update the root README.md with latest report information.

        Args:
            report_path: Path to the latest report file
        """
        # Root README path
        root_readme = Path("/workspace/repos/trending_benchmarks/README.md")

        logger.info(f"Updating root README at {root_readme}")

        try:
            # Read current README
            with open(root_readme, "r") as f:
                readme_content = f.read()

            # Get stats for the latest report section
            stats = self.cache.get_stats()
            all_models = self.cache.get_all_models()

            # Get models from last 12 months for accurate count
            twelve_months_ago = (datetime.utcnow() - timedelta(days=365)).isoformat()
            recent_models = self.cache.get_trending_models(twelve_months_ago)
            models_analyzed = len(recent_models)

            # Total unique benchmarks
            benchmarks_count = stats.get("benchmarks", 0)

            # Format report date
            report_date = datetime.utcnow().strftime("%B %d, %Y")

            # Get relative path to report from root
            report_rel_path = Path(report_path).relative_to("/workspace/repos/trending_benchmarks")
            report_filename = Path(report_path).name

            # Format date for display in link (YYYY-MM-DD)
            report_date_short = datetime.utcnow().strftime("%Y-%m-%d")

            # Build new Latest Report section
            new_section = f"""## 📊 Latest Report

**[View Latest Benchmark Report →]({report_rel_path})**

**Key Findings** ({report_date_short}):
- **{benchmarks_count} unique benchmarks** discovered
- **{models_analyzed} models** analyzed from major labs
- **Report Date:** {report_date}"""

            # Find and replace the "## 📊 Latest Report" section
            # Pattern: from "## 📊 Latest Report" to the next "---" or "##"
            pattern = r'## 📊 Latest Report.*?(?=\n---|\n##|$)'

            if re.search(pattern, readme_content, re.DOTALL):
                # Replace existing section
                updated_content = re.sub(
                    pattern,
                    new_section,
                    readme_content,
                    flags=re.DOTALL
                )
            else:
                # Section not found - insert after header
                # Find first --- after header
                lines = readme_content.split('\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.strip() == '---':
                        insert_pos = i + 1
                        break

                if insert_pos > 0:
                    lines.insert(insert_pos, '')
                    lines.insert(insert_pos + 1, new_section)
                    lines.insert(insert_pos + 2, '')
                    updated_content = '\n'.join(lines)
                else:
                    # Fallback: prepend to content
                    updated_content = new_section + '\n\n' + readme_content

            # Write updated README
            with open(root_readme, "w") as f:
                f.write(updated_content)

            logger.info("Root README updated successfully")

        except Exception as e:
            logger.error(f"Failed to update root README: {e}")
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
