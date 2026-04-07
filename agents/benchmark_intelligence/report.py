"""
Stage 6: Report Generation

Generates Markdown reports from categorized benchmark data. This MVP version
creates a simple popularity-based report. Full temporal trending analysis
(emerging/active/almost-extinct) is deferred to Phase 4 (User Story 2).

This is a standalone stage script with CLI entry point.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.stage_utils import (
    load_stage_json,
    save_stage_json,
    find_latest_stage_output
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def generate_report_markdown(
    categorized_benchmarks: List[Dict[str, Any]],
    snapshot_id: Optional[int] = None,
    models_without_benchmarks: int = 0
) -> str:
    """
    Generate Markdown report from categorized benchmarks.

    Args:
        categorized_benchmarks: List of categorized benchmarks from Stage 5
        snapshot_id: Optional snapshot ID for report metadata
        models_without_benchmarks: Count of models with no benchmarks found

    Returns:
        Markdown report content

    Example:
        >>> benchmarks = [{"canonical_name": "MMLU", "categories": ["knowledge"], ...}]
        >>> report = generate_report_markdown(benchmarks)
    """
    timestamp = datetime.utcnow().isoformat()

    # Group by primary category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for bench in categorized_benchmarks:
        primary = bench.get('primary_category', 'uncategorized')
        if primary not in by_category:
            by_category[primary] = []
        by_category[primary].append(bench)

    # Sort benchmarks within each category by mention count
    for category in by_category:
        by_category[category].sort(
            key=lambda x: x.get('mention_count', 0),
            reverse=True
        )

    # Generate report
    lines = []
    lines.append("# Trending AI Benchmarks Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    if snapshot_id:
        lines.append(f"**Snapshot ID:** {snapshot_id}")
    lines.append(f"**Total Benchmarks:** {len(categorized_benchmarks)}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"This report analyzes {len(categorized_benchmarks)} unique benchmarks "
                 f"mentioned across multiple AI models.")
    if models_without_benchmarks > 0:
        lines.append("")
        lines.append(f"**Note:** {models_without_benchmarks} models had no benchmarks extracted. "
                     f"This may be due to missing documentation, extraction failures, or "
                     f"models without published benchmark results.")
    lines.append("")

    # Category Distribution
    lines.append("### Distribution by Category")
    lines.append("")
    lines.append("| Category | Count | Percentage |")
    lines.append("|----------|-------|------------|")
    total = len(categorized_benchmarks)
    for category in sorted(by_category.keys()):
        count = len(by_category[category])
        pct = (count / total * 100) if total > 0 else 0
        lines.append(f"| {category.capitalize()} | {count} | {pct:.1f}% |")
    lines.append("")

    # Top 20 Most Popular Benchmarks (Overall)
    lines.append("## Top 20 Most Popular Benchmarks")
    lines.append("")
    lines.append("Ranked by total mentions across all models:")
    lines.append("")
    lines.append("| Rank | Benchmark | Category | Mentions | Models | Variants |")
    lines.append("|------|-----------|----------|----------|--------|----------|")

    # Sort all benchmarks by mention count
    sorted_benchmarks = sorted(
        categorized_benchmarks,
        key=lambda x: x.get('mention_count', 0),
        reverse=True
    )

    for i, bench in enumerate(sorted_benchmarks[:20], 1):
        name = bench.get('canonical_name', 'Unknown')
        category = bench.get('primary_category', 'uncategorized')
        mentions = bench.get('mention_count', 0)
        models = bench.get('model_count', 0)
        variants = bench.get('variant_count', 0)

        lines.append(f"| {i} | {name} | {category} | {mentions} | {models} | {variants} |")

    lines.append("")

    # Benchmarks by Category
    lines.append("## Benchmarks by Category")
    lines.append("")

    for category in sorted(by_category.keys()):
        benchmarks = by_category[category]
        lines.append(f"### {category.capitalize()}")
        lines.append("")
        lines.append("| Benchmark | Mentions | Models | Variants |")
        lines.append("|-----------|----------|--------|----------|")

        for bench in benchmarks[:10]:  # Top 10 per category
            name = bench.get('canonical_name', 'Unknown')
            mentions = bench.get('mention_count', 0)
            models = bench.get('model_count', 0)
            variants = bench.get('variant_count', 0)

            lines.append(f"| {name} | {mentions} | {models} | {variants} |")

        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated by Benchmark Intelligence System (MVP)*")
    lines.append("")

    return "\n".join(lines)


def run(input_json: Optional[str] = None, snapshot_id: Optional[int] = None) -> str:
    """
    Execute Stage 6: Report generation.

    Reads categorized benchmarks from Stage 5 output, generates Markdown report,
    and outputs both the report file and JSON metadata.

    Args:
        input_json: Path to categorize_benchmarks JSON output (auto-finds if not specified)
        snapshot_id: Optional snapshot ID for report metadata

    Returns:
        Path to generated JSON metadata file

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If report generation fails
    """
    logger.info("=" * 70)
    logger.info("Stage 6: Report Generation")
    logger.info("=" * 70)

    # Load input from Stage 5
    if input_json is None:
        input_json = find_latest_stage_output("categorize_benchmarks")
        if input_json is None:
            raise FileNotFoundError(
                "No categorize_benchmarks output found. Run Stage 5 first."
            )
        logger.info(f"Auto-discovered input: {Path(input_json).name}")
    else:
        logger.info(f"Using input: {input_json}")

    # Load and validate Stage 5 output
    stage5_data = load_stage_json(input_json)
    benchmarks = stage5_data['data']

    # Check for models with no benchmarks in metadata
    models_without_benchmarks = 0
    if 'metadata' in stage5_data and 'models_without_benchmarks' in stage5_data['metadata']:
        models_without_benchmarks = stage5_data['metadata']['models_without_benchmarks']

    logger.info(f"Configuration:")
    logger.info(f"  Benchmarks to report: {len(benchmarks)}")
    if models_without_benchmarks > 0:
        logger.info(f"  Models with no benchmarks: {models_without_benchmarks}")
    if snapshot_id:
        logger.info(f"  Snapshot ID: {snapshot_id}")

    if not benchmarks:
        logger.warning("No benchmarks found in input - generating empty report")

    logger.info(f"\nGenerating Markdown report...")

    # Generate report content
    report_content = generate_report_markdown(
        benchmarks,
        snapshot_id,
        models_without_benchmarks
    )

    # Create reports directory
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Save report to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_filename = f"trending_benchmarks_{timestamp}.md"
    report_path = reports_dir / report_filename

    with open(report_path, 'w') as f:
        f.write(report_content)

    logger.info(f"✓ Report saved to: {report_path}")

    # Count sections
    sections_generated = report_content.count('##')

    # Create metadata output
    metadata = {
        'snapshot_id': snapshot_id,
        'report_path': str(report_path),
        'sections_generated': sections_generated,
        'benchmark_count': len(benchmarks),
    }

    # Save metadata JSON
    output_path = save_stage_json(
        data=[metadata],
        stage_name="report_metadata",
        input_count=len(benchmarks),
        errors=[]
    )

    logger.info(f"\n✓ Stage 6 complete")
    logger.info(f"  Report: {report_path}")
    logger.info(f"  Metadata: {output_path}")
    logger.info(f"  Sections: {sections_generated}")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for Stage 6."""
    parser = argparse.ArgumentParser(
        description="Stage 6: Generate trending benchmarks report"
    )
    parser.add_argument(
        "--input",
        help="Path to categorize_benchmarks JSON output (auto-finds if not specified)"
    )
    parser.add_argument(
        "--snapshot-id",
        type=int,
        help="Optional snapshot ID for report metadata"
    )

    args = parser.parse_args()

    try:
        output_path = run(args.input, args.snapshot_id)
        print(f"\n✓ Success! Metadata saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Stage 6 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
