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
from agents.benchmark_intelligence.tools.benchmark_validation import validate_benchmark_with_ai
from agents.benchmark_intelligence.tools._claude_client import is_anthropic_available


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def normalize_benchmark_name(name: str) -> str:
    """
    Normalize a benchmark name for grouping similar variants.

    Normalization strategy:
    - Convert Unicode superscripts/subscripts to ASCII digits
    - Lowercase
    - Remove hyphens, underscores, spaces
    - Remove noise qualifiers (shot count, zero-shot)
    - KEEP semantic qualifiers (Code, English, Multivariate, etc.)

    Args:
        name: Raw benchmark name

    Returns:
        Normalized name for grouping

    Example:
        >>> normalize_benchmark_name("MMLU (5-shot)")
        "mmlu"
        >>> normalize_benchmark_name("MTEB (Code)")
        "mteb(code)"
        >>> normalize_benchmark_name("MTEB (English, v2)")
        "mteb(english)"
        >>> normalize_benchmark_name("τ²-Bench")
        "τ2bench"
    """
    if not name:
        return ""

    # Convert Unicode superscripts and subscripts to regular digits
    # This ensures τ²-Bench and τ2-Bench normalize to the same string
    superscript_map = {
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
    }
    subscript_map = {
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'
    }

    normalized = name
    for super_char, digit in superscript_map.items():
        normalized = normalized.replace(super_char, digit)
    for sub_char, digit in subscript_map.items():
        normalized = normalized.replace(sub_char, digit)

    # Lowercase
    normalized = normalized.lower()

    # Remove noise qualifiers but KEEP semantic qualifiers
    # Noise: (5-shot), (zero-shot), (few-shot), version numbers
    import re

    # Remove shot-count qualifiers
    normalized = re.sub(r'\(\d+-shot\)', '', normalized)
    normalized = re.sub(r'\(zero-shot\)', '', normalized)
    normalized = re.sub(r'\(few-shot\)', '', normalized)
    normalized = re.sub(r'\(one-shot\)', '', normalized)

    # Remove standalone version indicators in parentheses: (v1), (v2), (version 2)
    # But keep when part of semantic qualifier like "(English, v2)" → keep as "(english)"
    normalized = re.sub(r'\s*,\s*v\d+', '', normalized)  # ", v2" within parentheses
    normalized = re.sub(r'\(v\d+\)', '', normalized)      # Standalone (v1)
    normalized = re.sub(r'\(version\s*\d+\)', '', normalized)

    # Remove bracket context (usually metadata)
    normalized = normalized.split('[')[0]

    # Remove separators (but preserve parentheses for semantic grouping)
    normalized = normalized.replace('-', '').replace('_', '').replace(' ', '')

    # Clean up any double parentheses or empty ones
    normalized = re.sub(r'\(\s*\)', '', normalized)

    normalized = normalized.strip()

    return normalized


def consolidate_benchmark_names(benchmarks: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Consolidate benchmark names from extraction results.

    Groups benchmark variants by normalized name and creates canonical
    name mappings. Applies benchmark aliases from config before normalization.

    Args:
        benchmarks: List of benchmark entries from Stage 3
        config: Optional configuration dict with consolidation settings

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
    # Load benchmark aliases from config
    benchmark_aliases = {}
    if config:
        consolidation_config = config.get("consolidation", {})
        benchmark_aliases = consolidation_config.get("benchmark_aliases", {})
        if benchmark_aliases:
            logger.info(f"Loaded {len(benchmark_aliases)} benchmark aliases from config")

    # Group by normalized name
    groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        'variants': set(),
        'models': set(),
        'mention_count': 0
    })

    alias_count = 0
    for bench in benchmarks:
        name = bench.get('name', '')
        if not name:
            continue

        # Apply alias resolution
        if name in benchmark_aliases:
            canonical = benchmark_aliases[name]
            logger.debug(f"Resolved alias: '{name}' → '{canonical}'")
            name = canonical
            alias_count += 1
        elif benchmark_aliases:
            # Check case-insensitive match
            name_lower = name.lower()
            for alias, canonical in benchmark_aliases.items():
                if alias.lower() == name_lower:
                    logger.debug(f"Resolved alias (case-insensitive): '{name}' → '{canonical}'")
                    name = canonical
                    alias_count += 1
                    break

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

    if alias_count > 0:
        logger.info(f"Resolved {alias_count} benchmark aliases")

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

        # Load configuration for advanced consolidation
        import yaml
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        config = {}
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.debug(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Could not load config.yaml: {e}, using defaults")

        # Perform consolidation with config
        output_data = consolidate_benchmark_names(all_benchmarks, config=config)

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

        # AI Validation: Validate unique canonical benchmark names
        logger.info("\n" + "=" * 70)
        logger.info("AI Validation of Consolidated Benchmarks")
        logger.info("=" * 70)

        # Collect all unique canonical names
        unique_names = [item['canonical_name'] for item in output_data]

        logger.info(f"Total consolidated benchmarks: {len(unique_names)}")
        logger.info(f"Running AI validation on {len(unique_names)} canonical names...")
        logger.info("")

        # Run AI validation if available and not explicitly disabled
        import os
        skip_ai_validation = os.environ.get('SKIP_AI_VALIDATION', '').lower() == 'true'
        if is_anthropic_available() and unique_names and not skip_ai_validation:
            rejected_names_set = set()
            validation_results = {
                'validated': 0,
                'accepted': 0,
                'rejected': 0,
                'errors': 0
            }

            for i, name in enumerate(unique_names, 1):
                try:
                    is_valid, confidence, reason = validate_benchmark_with_ai(name)

                    validation_results['validated'] += 1

                    if not is_valid or confidence < 70.0:
                        rejected_names_set.add(name)
                        validation_results['rejected'] += 1
                        logger.info(f"  ✗ Rejected: '{name}' (confidence: {confidence}%)")
                        logger.info(f"     Reason: {reason[:100]}...")
                    else:
                        validation_results['accepted'] += 1

                    # Progress reporting every 20 benchmarks
                    if i % 20 == 0:
                        logger.info(
                            f"  Progress: {i}/{len(unique_names)} "
                            f"(Accepted: {validation_results['accepted']}, "
                            f"Rejected: {validation_results['rejected']})"
                        )

                except Exception as e:
                    logger.warning(f"  Validation error for '{name}': {e}")
                    validation_results['errors'] += 1

            # Filter out rejected benchmarks from output_data
            logger.info("")
            logger.info("Filtering rejected benchmarks from results...")

            pre_filter_count = len(output_data)
            output_data = [
                item for item in output_data
                if item['canonical_name'] not in rejected_names_set
            ]
            post_filter_count = len(output_data)

            # Recalculate statistics after AI filtering
            unique_benchmarks = len(output_data)
            total_variants = sum(item['variant_count'] for item in output_data) if output_data else 0
            avg_variants = total_variants / unique_benchmarks if unique_benchmarks > 0 else 0

            logger.info("")
            logger.info("=" * 70)
            logger.info("AI Validation Summary:")
            logger.info("=" * 70)
            logger.info(f"  Benchmarks validated: {validation_results['validated']}")
            logger.info(f"  ✓ Accepted: {validation_results['accepted']}")
            logger.info(f"  ✗ Rejected: {validation_results['rejected']}")
            logger.info(f"  Errors: {validation_results['errors']}")
            logger.info(f"  Filtered from results: {pre_filter_count - post_filter_count}")
            logger.info("")
            logger.info("Final Consolidation Statistics:")
            logger.info(f"  Unique benchmarks: {unique_benchmarks}")
            logger.info(f"  Total variants: {total_variants}")
            logger.info(f"  Avg variants per benchmark: {avg_variants:.1f}")
            logger.info("=" * 70)

            # Add AI validation metadata
            ai_validation_metadata = {
                'ai_validation_performed': True,
                'benchmarks_validated': validation_results['validated'],
                'benchmarks_accepted': validation_results['accepted'],
                'benchmarks_rejected': validation_results['rejected'],
                'validation_errors': validation_results['errors'],
                'confidence_threshold': 70.0
            }
        else:
            if not is_anthropic_available():
                logger.warning("Claude API not available - skipping AI validation")
            ai_validation_metadata = {
                'ai_validation_performed': False,
                'reason': 'Claude API not available' if not is_anthropic_available() else 'No benchmarks to validate'
            }

    # Save standardized JSON output with preserved metadata
    metadata = {
        "models_without_benchmarks": models_without_benchmarks
    }

    # Add AI validation metadata if it was performed
    if output_data and 'ai_validation_metadata' in locals():
        metadata.update(ai_validation_metadata)

    output_path = save_stage_json(
        data=output_data,
        stage_name="consolidate_names",
        input_count=len(all_benchmarks),
        errors=[],
        metadata=metadata
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
