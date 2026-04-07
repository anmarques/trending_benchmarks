"""
Stage 5: Benchmark Categorization

Categorizes benchmarks into taxonomy categories. This MVP version uses
simple rule-based categorization. Full taxonomy evolution with AI-powered
classification is deferred to Phase 6 (User Story 4).

This is a standalone stage script with CLI entry point.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.stage_utils import (
    load_stage_json,
    save_stage_json,
    find_latest_stage_output
)
from agents.benchmark_intelligence.tools.taxonomy_manager import (
    load_taxonomy_json,
    apply_category_overrides
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# MVP taxonomy (simple rule-based categories)
TAXONOMY_RULES = {
    'coding': [
        'humaneval', 'mbpp', 'codegen', 'apps', 'codeforce', 'leetcode',
        'swench', 'swebench', 'codecontests'
    ],
    'math': [
        'gsm8k', 'gsm', 'math', 'aime', 'mathqa', 'mawps', 'svamp',
        'asdiv', 'minerva'
    ],
    'knowledge': [
        'mmlu', 'arc', 'hellaswag', 'winogrande', 'piqa', 'siqa',
        'commonsenseqa', 'csqa', 'openbookqa', 'triviaqa', 'naturalquestions',
        'nq', 'squad', 'webqa', 'truthfulqa'
    ],
    'reasoning': [
        'bbh', 'bigbenchhard', 'logiqa', 'reclor', 'strategyqa',
        'clutrr', 'drop', 'quoref'
    ],
    'vision': [
        'videomme', 'mme', 'mmbench', 'seed', 'pope', 'vqav2',
        'vizwiz', 'textvqa', 'docvqa', 'chartqa', 'infovqa',
        'ocrbench', 'refcoco'
    ],
    'audio': [
        'librispeech', 'commonvoice', 'fleurs', 'voxceleb',
        'tedlium', 'switchboard'
    ],
    'multilingual': [
        'ceval', 'cmmlu', 'flores', 'xtreme', 'xnli', 'pawsx',
        'mlqa', 'tydiqa', 'indicglue'
    ],
    'agent': [
        'webarena', 'osworld', 'mint', 'alfworld', 'scienceworld',
        'babyai', 'textcraft'
    ],
    'comparison': [
        'alpacaeval', 'arenahard', 'mtbench', 'chatbotarena',
        'lmsys', 'bfcl'
    ],
    'safety': [
        'harmfulqa', 'toxicgen', 'realtoxicityprompts', 'saferbench',
        'trustllm', 'decodingtrust'
    ],
}


def categorize_benchmark(benchmark_name: str) -> List[str]:
    """
    Categorize a benchmark using simple rule-based matching.

    Args:
        benchmark_name: Canonical benchmark name (normalized)

    Returns:
        List of category names (can be multiple categories)

    Example:
        >>> categorize_benchmark("MMLU")
        ['knowledge']
        >>> categorize_benchmark("HumanEval")
        ['coding']
    """
    if not benchmark_name:
        return ['uncategorized']

    # Normalize for matching
    name_lower = benchmark_name.lower().replace('-', '').replace('_', '').replace(' ', '')

    categories = []

    # Check each taxonomy category
    for category, keywords in TAXONOMY_RULES.items():
        for keyword in keywords:
            if keyword in name_lower:
                if category not in categories:
                    categories.append(category)
                break

    # If no category matched, mark as uncategorized
    if not categories:
        categories = ['uncategorized']

    return categories


def run(input_json: Optional[str] = None) -> str:
    """
    Execute Stage 5: Benchmark categorization.

    Reads consolidated benchmarks from Stage 4 output, applies taxonomy
    categorization, and outputs standardized JSON.

    Args:
        input_json: Path to consolidate_names JSON output (auto-finds if not specified)

    Returns:
        Path to generated JSON output file

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If categorization fails
    """
    logger.info("=" * 70)
    logger.info("Stage 5: Benchmark Categorization")
    logger.info("=" * 70)

    # Load input from Stage 4
    if input_json is None:
        input_json = find_latest_stage_output("consolidate_names")
        if input_json is None:
            raise FileNotFoundError(
                "No consolidate_names output found. Run Stage 4 first."
            )
        logger.info(f"Auto-discovered input: {Path(input_json).name}")
    else:
        logger.info(f"Using input: {input_json}")

    # Load and validate Stage 4 output
    stage4_data = load_stage_json(input_json)
    benchmarks = stage4_data['data']

    # Preserve metadata from Stage 4
    stage4_metadata = stage4_data.get('metadata', {})
    models_without_benchmarks = stage4_metadata.get('models_without_benchmarks', 0)

    logger.info(f"Configuration:")
    logger.info(f"  Benchmarks to categorize: {len(benchmarks)}")
    logger.info(f"  Taxonomy version: MVP-v1 (rule-based)")
    logger.info(f"  Available categories: {len(TAXONOMY_RULES)}")
    if models_without_benchmarks > 0:
        logger.info(f"  Models without benchmarks: {models_without_benchmarks}")

    if not benchmarks:
        logger.warning("No benchmarks found in input - output will be empty")
        output_data = []
    else:
        logger.info(f"\nCategorizing benchmarks...")

        # T087: Load current taxonomy to track changes
        try:
            taxonomy = load_taxonomy_json()
            taxonomy_version = taxonomy.get("version", "MVP-v1")
            existing_categories = set()
            for domain in taxonomy.get("domains", []):
                existing_categories.update(domain.get("categories", []))
            logger.info(f"  Loaded taxonomy version: {taxonomy_version}")
        except Exception as e:
            logger.warning(f"Failed to load taxonomy.json: {e}, using MVP taxonomy")
            taxonomy_version = "MVP-v1"
            existing_categories = set(TAXONOMY_RULES.keys())

        # Categorize each benchmark
        output_data = []
        category_counts = {}
        new_categories = set()  # T087: Track newly created categories

        for benchmark in benchmarks:
            canonical_name = benchmark.get('canonical_name', '')

            # Get categories
            categories = categorize_benchmark(canonical_name)

            # T087: Check if any category is newly created
            newly_created = False
            for cat in categories:
                if cat not in existing_categories and cat != 'uncategorized':
                    new_categories.add(cat)
                    newly_created = True

            # Track category distribution
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # Create output entry
            output_entry = {
                'canonical_name': canonical_name,
                'categories': categories,
                'primary_category': categories[0] if categories else 'uncategorized',
                'taxonomy_version': taxonomy_version,
                'newly_created_category': newly_created,
                # Preserve metadata from Stage 4
                'mention_count': benchmark.get('mention_count', 0),
                'model_count': benchmark.get('model_count', 0),
                'variant_count': benchmark.get('variant_count', 0),
            }
            output_data.append(output_entry)

        # T088: Apply manual category overrides from config.yaml
        logger.info(f"\nApplying category overrides...")
        output_data = apply_category_overrides(output_data)

        # Statistics
        logger.info(f"\n✓ Categorization complete:")
        logger.info(f"  Benchmarks categorized: {len(output_data)}")
        logger.info(f"\n  Distribution by category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {category}: {count} benchmarks")

        # T087: Report taxonomy changes
        if new_categories:
            logger.info(f"\n  New categories created: {len(new_categories)}")
            for cat in sorted(new_categories):
                logger.info(f"    - {cat}")

    # T087: Build taxonomy_changes section
    taxonomy_changes = {
        "new_categories": list(new_categories) if 'new_categories' in locals() else [],
        "categories_modified": [],  # Future enhancement: track category definition changes
        "taxonomy_version": taxonomy_version if 'taxonomy_version' in locals() else "MVP-v1"
    }

    # Save standardized JSON output with preserved metadata
    output_path = save_stage_json(
        data=output_data,
        stage_name="categorize_benchmarks",
        input_count=len(benchmarks),
        errors=[],
        metadata={
            "models_without_benchmarks": models_without_benchmarks,
            "taxonomy_changes": taxonomy_changes  # T087: Add taxonomy changes to output
        }
    )

    logger.info(f"\n✓ Stage 5 complete")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for Stage 5."""
    parser = argparse.ArgumentParser(
        description="Stage 5: Categorize benchmarks into taxonomy"
    )
    parser.add_argument(
        "--input",
        help="Path to consolidate_names JSON output (auto-finds if not specified)"
    )

    args = parser.parse_args()

    try:
        output_path = run(args.input)
        print(f"\n✓ Success! Output saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Stage 5 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
