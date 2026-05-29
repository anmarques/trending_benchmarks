"""
AI-Powered Benchmark Validation (Post-Processing)

Runs after consolidation to validate unique benchmark names using Claude AI.
This is much more efficient than validating every mention during extraction.

Usage:
    python3 -m agents.benchmark_intelligence.validate_benchmarks_ai
    python3 -m agents.benchmark_intelligence.validate_benchmarks_ai --input consolidate_names_YYYYMMDD_HHMMSS.json
    python3 -m agents.benchmark_intelligence.validate_benchmarks_ai --confidence-threshold 80
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

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


def validate_benchmarks_batch(
    benchmark_names: List[str],
    confidence_threshold: float = 70.0,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Validate a list of unique benchmark names using AI.

    Args:
        benchmark_names: List of unique benchmark names to validate
        confidence_threshold: Minimum confidence to accept (0-100)
        batch_size: Report progress every N benchmarks

    Returns:
        Dictionary with validation results:
            - valid: List of validated benchmark names
            - rejected: List of rejected names with reasons
            - uncertain: List of low-confidence names
            - stats: Validation statistics
    """
    if not is_anthropic_available():
        raise RuntimeError(
            "Claude AI not available. Set ANTHROPIC_API_KEY environment variable."
        )

    valid = []
    rejected = []
    uncertain = []

    logger.info(f"Validating {len(benchmark_names)} unique benchmark names with AI...")
    logger.info(f"Confidence threshold: {confidence_threshold}%")
    logger.info(f"This will make {len(benchmark_names)} AI API calls.")
    logger.info("")

    for i, name in enumerate(benchmark_names, 1):
        try:
            is_valid, confidence, reason = validate_benchmark_with_ai(name)

            if is_valid and confidence >= confidence_threshold:
                valid.append({
                    "name": name,
                    "confidence": confidence,
                    "reason": reason
                })
            elif not is_valid:
                rejected.append({
                    "name": name,
                    "confidence": confidence,
                    "reason": reason
                })
            else:
                # Valid but low confidence
                uncertain.append({
                    "name": name,
                    "confidence": confidence,
                    "reason": reason
                })

            # Progress reporting
            if i % batch_size == 0 or i == len(benchmark_names):
                logger.info(
                    f"  Processed {i}/{len(benchmark_names)} "
                    f"(Valid: {len(valid)}, Rejected: {len(rejected)}, "
                    f"Uncertain: {len(uncertain)})"
                )

        except Exception as e:
            logger.warning(f"  Failed to validate '{name}': {e}")
            uncertain.append({
                "name": name,
                "confidence": 0,
                "reason": f"Validation error: {str(e)}"
            })

    stats = {
        "total_validated": len(benchmark_names),
        "valid_count": len(valid),
        "rejected_count": len(rejected),
        "uncertain_count": len(uncertain),
        "valid_percentage": len(valid) / len(benchmark_names) * 100 if benchmark_names else 0,
        "rejected_percentage": len(rejected) / len(benchmark_names) * 100 if benchmark_names else 0,
        "confidence_threshold": confidence_threshold
    }

    return {
        "valid": valid,
        "rejected": rejected,
        "uncertain": uncertain,
        "stats": stats
    }


def run(
    consolidate_json: Optional[str] = None,
    confidence_threshold: float = 70.0,
    output_report: bool = True
) -> str:
    """
    Execute AI validation on consolidated benchmark names.

    Args:
        consolidate_json: Path to consolidate_names JSON output (auto-finds if not specified)
        confidence_threshold: Minimum confidence to accept (0-100)
        output_report: Whether to generate a validation report

    Returns:
        Path to validation results JSON

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If validation fails
    """
    logger.info("=" * 70)
    logger.info("AI-Powered Benchmark Validation (Post-Processing)")
    logger.info("=" * 70)

    # Load input from consolidation stage
    if consolidate_json is None:
        consolidate_json = find_latest_stage_output("consolidate_names")
        if consolidate_json is None:
            raise FileNotFoundError(
                "No consolidate_names output found. Run Stage 4 first."
            )
        logger.info(f"Auto-discovered input: {Path(consolidate_json).name}")
    else:
        logger.info(f"Using input: {consolidate_json}")

    # Load consolidated benchmark names
    consolidate_data = load_stage_json(consolidate_json)
    benchmarks = consolidate_data['data']

    # Extract unique canonical names
    unique_names = [b['canonical_name'] for b in benchmarks]
    logger.info(f"Found {len(unique_names)} unique benchmark names to validate")
    logger.info("")

    # Validate with AI
    validation_results = validate_benchmarks_batch(
        unique_names,
        confidence_threshold=confidence_threshold
    )

    # Display summary
    stats = validation_results['stats']
    logger.info("")
    logger.info("=" * 70)
    logger.info("Validation Summary:")
    logger.info("=" * 70)
    logger.info(f"  Total validated: {stats['total_validated']}")
    logger.info(f"  ✓ Valid benchmarks: {stats['valid_count']} ({stats['valid_percentage']:.1f}%)")
    logger.info(f"  ✗ Rejected: {stats['rejected_count']} ({stats['rejected_percentage']:.1f}%)")
    logger.info(f"  ? Uncertain: {stats['uncertain_count']}")
    logger.info("")

    # Show top rejected benchmarks
    if validation_results['rejected']:
        logger.info("Top 20 Rejected Benchmarks:")
        for i, item in enumerate(validation_results['rejected'][:20], 1):
            logger.info(f"  {i}. {item['name']}")
            logger.info(f"     Reason: {item['reason'][:100]}...")
            logger.info("")

    # Show uncertain cases
    if validation_results['uncertain']:
        logger.info("Uncertain Cases (low confidence or errors):")
        for item in validation_results['uncertain'][:10]:
            logger.info(f"  - {item['name']} (confidence: {item['confidence']})")
        logger.info("")

    # Save validation results
    output_path = save_stage_json(
        data=validation_results,
        stage_name="ai_validation",
        input_count=len(unique_names),
        errors=[],
        metadata={
            "confidence_threshold": confidence_threshold,
            "validation_date": datetime.utcnow().isoformat()
        }
    )

    logger.info(f"✓ AI validation complete")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for AI validation."""
    parser = argparse.ArgumentParser(
        description="AI-Powered Benchmark Validation (Post-Processing)"
    )
    parser.add_argument(
        "--input",
        help="Path to consolidate_names JSON output (auto-finds if not specified)"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=70.0,
        help="Minimum confidence to accept (0-100, default: 70)"
    )

    args = parser.parse_args()

    try:
        output_path = run(
            consolidate_json=args.input,
            confidence_threshold=args.confidence_threshold
        )
        print(f"\n✓ Success! Output saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"AI validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
