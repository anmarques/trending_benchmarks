"""
Orchestrator for 6-Stage Benchmark Intelligence Pipeline

Runs all stages sequentially:
1. filter_models - Discover and filter AI models
2. find_docs - Find documentation URLs
3. parse_docs - Extract benchmarks from documents
4. consolidate_benchmarks - Consolidate name variants
5. categorize_benchmarks - Categorize into taxonomy
6. report - Generate trending benchmarks report

This is the main entry point for generating a complete benchmark intelligence report.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all stage modules
from agents.benchmark_intelligence import filter_models
from agents.benchmark_intelligence import find_docs
from agents.benchmark_intelligence import parse_docs
from agents.benchmark_intelligence import consolidate_benchmarks
from agents.benchmark_intelligence import categorize_benchmarks
from agents.benchmark_intelligence import report


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def run_pipeline(
    config_path: str = "config.yaml",
    concurrency: int = 20,
    snapshot_id: Optional[int] = None
) -> dict:
    """
    Execute the complete 6-stage benchmark intelligence pipeline.

    Runs all stages in sequence, passing output from each stage to the next.

    Args:
        config_path: Path to configuration file for Stage 1
        concurrency: Number of parallel workers for Stage 3
        snapshot_id: Optional snapshot ID for database integration

    Returns:
        Dictionary with paths to all stage outputs and final report

    Raises:
        RuntimeError: If any stage fails
    """
    logger.info("=" * 80)
    logger.info("BENCHMARK INTELLIGENCE PIPELINE - FULL EXECUTION")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.utcnow().isoformat()}")
    logger.info(f"Configuration: {config_path}")
    logger.info(f"Concurrency: {concurrency} workers")
    logger.info("=" * 80)

    results = {}
    start_time = datetime.utcnow()

    try:
        # Stage 1: Model Filtering
        logger.info("\n" + ">" * 40)
        logger.info("STAGE 1/6: Model Filtering")
        logger.info(">" * 40)
        stage1_output = filter_models.run(config_path)
        results['stage1_models'] = stage1_output
        logger.info(f"✓ Stage 1 complete: {stage1_output}")

        # Stage 2: Document Finding
        logger.info("\n" + ">" * 40)
        logger.info("STAGE 2/6: Document Finding")
        logger.info(">" * 40)
        stage2_output = find_docs.run(stage1_output)
        results['stage2_documents'] = stage2_output
        logger.info(f"✓ Stage 2 complete: {stage2_output}")

        # Stage 3: Document Parsing & Benchmark Extraction
        logger.info("\n" + ">" * 40)
        logger.info("STAGE 3/6: Document Parsing & Benchmark Extraction")
        logger.info(">" * 40)
        stage3_output = parse_docs.run(stage2_output, concurrency)
        results['stage3_benchmarks'] = stage3_output
        logger.info(f"✓ Stage 3 complete: {stage3_output}")

        # Stage 4: Benchmark Name Consolidation
        logger.info("\n" + ">" * 40)
        logger.info("STAGE 4/6: Benchmark Name Consolidation")
        logger.info(">" * 40)
        stage4_output = consolidate_benchmarks.run(stage3_output)
        results['stage4_consolidated'] = stage4_output
        logger.info(f"✓ Stage 4 complete: {stage4_output}")

        # Stage 5: Benchmark Categorization
        logger.info("\n" + ">" * 40)
        logger.info("STAGE 5/6: Benchmark Categorization")
        logger.info(">" * 40)
        stage5_output = categorize_benchmarks.run(stage4_output)
        results['stage5_categorized'] = stage5_output
        logger.info(f"✓ Stage 5 complete: {stage5_output}")

        # Stage 6: Report Generation
        logger.info("\n" + ">" * 40)
        logger.info("STAGE 6/6: Report Generation")
        logger.info(">" * 40)
        stage6_output = report.run(stage5_output, snapshot_id)
        results['stage6_report'] = stage6_output
        logger.info(f"✓ Stage 6 complete: {stage6_output}")

        # Calculate total time
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE EXECUTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"End time: {end_time.isoformat()}")
        logger.info("\nOutput files:")
        for stage_name, path in results.items():
            logger.info(f"  {stage_name}: {path}")

        # Extract report path from metadata
        import json
        with open(stage6_output, 'r') as f:
            metadata = json.load(f)
            report_path = metadata['data'][0]['report_path']

        logger.info(f"\n📊 FINAL REPORT: {report_path}")
        logger.info("=" * 80)

        results['total_duration'] = duration
        results['final_report'] = report_path

        return results

    except Exception as e:
        logger.error(f"\n❌ PIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Pipeline execution failed at stage: {e}")


def main():
    """CLI entry point for pipeline orchestrator."""
    parser = argparse.ArgumentParser(
        description="Run complete 6-stage benchmark intelligence pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with default config
  python -m agents.benchmark_intelligence.generate

  # Run with custom config and higher concurrency
  python -m agents.benchmark_intelligence.generate --config my_config.yaml --concurrency 30

  # Run with snapshot ID for database integration
  python -m agents.benchmark_intelligence.generate --snapshot-id 123

Stages:
  1. filter_models      - Discover trending AI models from HuggingFace
  2. find_docs          - Find documentation URLs (model cards, papers, blogs)
  3. parse_docs         - Extract benchmarks using AI (Claude)
  4. consolidate        - Consolidate benchmark name variants
  5. categorize         - Categorize benchmarks into taxonomy
  6. report             - Generate Markdown report

Output:
  - JSON files in outputs/ directory (one per stage)
  - Final report in reports/ directory
        """
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Number of parallel workers for Stage 3 extraction (default: 20)"
    )
    parser.add_argument(
        "--snapshot-id",
        type=int,
        help="Optional snapshot ID for database integration"
    )

    args = parser.parse_args()

    try:
        results = run_pipeline(
            config_path=args.config,
            concurrency=args.concurrency,
            snapshot_id=args.snapshot_id
        )

        print(f"\n✅ SUCCESS! Pipeline complete.")
        print(f"📊 View report: {results['final_report']}")
        print(f"⏱️  Total time: {results['total_duration']:.1f}s")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
