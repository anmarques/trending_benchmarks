"""
Stage 4: Benchmark Name Consolidation

Consolidates benchmark name variants into canonical names. This MVP version
uses simple string normalization and grouping. Advanced similarity detection
and web search validation are deferred to Phase 4.

This is a standalone stage script with CLI entry point.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.stage_utils import (
    load_stage_json,
    save_stage_json,
    find_latest_stage_output
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def normalize_benchmark_name(name: str) -> str:
    """
    Normalize a benchmark name for grouping similar variants.

    Simple normalization for MVP:
    - Lowercase
    - Remove hyphens, underscores, spaces
    - Remove version suffixes

    Args:
        name: Raw benchmark name

    Returns:
        Normalized name for grouping

    Example:
        >>> normalize_benchmark_name("MMLU (5-shot)")
        "mmlu"
        >>> normalize_benchmark_name("GSM-8K")
        "gsm8k"
    """
    if not name:
        return ""

    # Lowercase
    normalized = name.lower()

    # Remove common noise patterns
    normalized = normalized.split('(')[0]  # Remove parenthetical context
    normalized = normalized.split('[')[0]  # Remove bracket context

    # Remove separators
    normalized = normalized.replace('-', '').replace('_', '').replace(' ', '')

    # Remove trailing numbers that might be versions
    # (Keep embedded numbers like "gsm8k")
    normalized = normalized.strip()

    return normalized


def consolidate_benchmark_names(benchmarks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Consolidate benchmark names from extraction results.

    Groups benchmark variants by normalized name and creates canonical
    name mappings. This is a simple MVP implementation.

    Args:
        benchmarks: List of benchmark entries from Stage 3

    Returns:
        List of consolidated benchmark groups:
            - canonical_name: The most common variant (used as canonical)
            - variants: List of all seen variants
            - mention_count: Total mentions across all models
            - model_count: Number of unique models mentioning this benchmark

    Example:
        >>> benchmarks = [
        ...     {"name": "MMLU", "model_id": "model1"},
        ...     {"name": "MMLU (5-shot)", "model_id": "model2"},
        ...     {"name": "GSM8K", "model_id": "model1"}
        ... ]
        >>> result = consolidate_benchmark_names(benchmarks)
        # Returns groups for "MMLU" and "GSM8K"
    """
    # Group by normalized name
    groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        'variants': set(),
        'models': set(),
        'mention_count': 0
    })

    for bench in benchmarks:
        name = bench.get('name', '')
        if not name:
            continue

        model_id = bench.get('model_id', '')
        normalized = normalize_benchmark_name(name)

        if not normalized:
            continue

        # Add variant name
        groups[normalized]['variants'].add(name)

        # Track model
        if model_id:
            groups[normalized]['models'].add(model_id)

        # Increment mention count
        groups[normalized]['mention_count'] += 1

    # Convert to output format
    consolidated = []
    for normalized_name, data in groups.items():
        variants = sorted(list(data['variants']))

        # Choose canonical name (most common variant)
        # For MVP, just use the first alphabetically (could improve with frequency count)
        canonical_name = variants[0] if variants else normalized_name

        consolidated.append({
            'canonical_name': canonical_name,
            'normalized': normalized_name,
            'variants': variants,
            'variant_count': len(variants),
            'mention_count': data['mention_count'],
            'model_count': len(data['models']),
            'similarity_scores': [],  # Deferred to Phase 4
            'web_search_used': False  # Deferred to Phase 4
        })

    # Sort by mention count (most popular first)
    consolidated.sort(key=lambda x: x['mention_count'], reverse=True)

    return consolidated


def run(input_json: Optional[str] = None) -> str:
    """
    Execute Stage 4: Benchmark name consolidation.

    Reads benchmark extractions from Stage 3 output, consolidates variant names,
    and outputs standardized JSON with canonical names.

    Args:
        input_json: Path to parse_documents JSON output (auto-finds if not specified)

    Returns:
        Path to generated JSON output file

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If consolidation fails
    """
    logger.info("=" * 70)
    logger.info("Stage 4: Benchmark Name Consolidation")
    logger.info("=" * 70)

    # Load input from Stage 3
    if input_json is None:
        input_json = find_latest_stage_output("parse_documents")
        if input_json is None:
            raise FileNotFoundError(
                "No parse_documents output found. Run Stage 3 first."
            )
        logger.info(f"Auto-discovered input: {Path(input_json).name}")
    else:
        logger.info(f"Using input: {input_json}")

    # Load and validate Stage 3 output
    stage3_data = load_stage_json(input_json)
    models = stage3_data['data']

    # Preserve metadata from Stage 3
    stage3_metadata = stage3_data.get('metadata', {})
    models_without_benchmarks = stage3_metadata.get('models_without_benchmarks', 0)

    # Collect all benchmarks from all models
    all_benchmarks = []
    for model in models:
        benchmarks = model.get('benchmarks', [])
        all_benchmarks.extend(benchmarks)

    logger.info(f"Configuration:")
    logger.info(f"  Models processed: {len(models)}")
    logger.info(f"  Total benchmark mentions: {len(all_benchmarks)}")
    if models_without_benchmarks > 0:
        logger.info(f"  Models without benchmarks: {models_without_benchmarks}")

    if not all_benchmarks:
        logger.warning("No benchmarks found in input - output will be empty")
        output_data = []
    else:
        logger.info(f"\nConsolidating benchmark names...")

        # Perform consolidation
        output_data = consolidate_benchmark_names(all_benchmarks)

        # Statistics
        unique_benchmarks = len(output_data)
        total_variants = sum(item['variant_count'] for item in output_data)
        avg_variants = total_variants / unique_benchmarks if unique_benchmarks > 0 else 0

        logger.info(f"\n✓ Name consolidation complete:")
        logger.info(f"  Unique benchmarks: {unique_benchmarks}")
        logger.info(f"  Total variants: {total_variants}")
        logger.info(f"  Avg variants per benchmark: {avg_variants:.1f}")

        # Show top 10 most mentioned
        if output_data:
            logger.info(f"\n  Top 10 most mentioned benchmarks:")
            for i, item in enumerate(output_data[:10], 1):
                logger.info(
                    f"    {i}. {item['canonical_name']}: "
                    f"{item['mention_count']} mentions, "
                    f"{item['variant_count']} variants"
                )

    # Save standardized JSON output with preserved metadata
    output_path = save_stage_json(
        data=output_data,
        stage_name="consolidate_names",
        input_count=len(all_benchmarks),
        errors=[],
        metadata={
            "models_without_benchmarks": models_without_benchmarks
        }
    )

    logger.info(f"\n✓ Stage 4 complete")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for Stage 4."""
    parser = argparse.ArgumentParser(
        description="Stage 4: Consolidate benchmark name variants"
    )
    parser.add_argument(
        "--input",
        help="Path to parse_documents JSON output (auto-finds if not specified)"
    )

    args = parser.parse_args()

    try:
        output_path = run(args.input)
        print(f"\n✓ Success! Output saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Stage 4 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
