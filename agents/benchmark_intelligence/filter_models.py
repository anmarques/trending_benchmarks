"""
Stage 1: Model Filtering

Discovers trending AI models from configured labs on HuggingFace and filters
them based on download count, date range, and task type criteria.

This is a standalone stage script with CLI entry point.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.tools.discover_models import discover_trending_models
from agents.benchmark_intelligence.stage_utils import save_stage_json
import yaml


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def run(config_path: str = "config.yaml") -> str:
    """
    Execute Stage 1: Model discovery and filtering.

    Reads configuration from config.yaml, queries HuggingFace for models from
    configured labs, applies filters, and outputs standardized JSON.

    Args:
        config_path: Path to configuration file (default: config.yaml)

    Returns:
        Path to generated JSON output file

    Raises:
        FileNotFoundError: If config file not found
        RuntimeError: If model discovery fails
    """
    logger.info("=" * 70)
    logger.info("Stage 1: Model Filtering")
    logger.info("=" * 70)

    # Load configuration
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    labs = config.get('labs', [])
    discovery_config = config.get('discovery', {})

    if not labs:
        raise ValueError("No labs configured in config.yaml")

    logger.info(f"Configuration loaded:")
    logger.info(f"  Labs: {len(labs)} configured")
    logger.info(f"  Models per lab: {discovery_config.get('models_per_lab', 15)}")
    logger.info(f"  Sort by: {discovery_config.get('sort_by', 'downloads')}")
    logger.info(f"  Min downloads: {discovery_config.get('min_downloads', 1000):,}")
    logger.info(f"  Date filter: {discovery_config.get('date_filter_months', 12)} months")

    # Estimate input count (models to be queried)
    input_count = len(labs) * discovery_config.get('models_per_lab', 15)

    logger.info(f"\nDiscovering models from {len(labs)} labs...")

    # Execute model discovery (wraps existing discover_trending_models)
    try:
        models = discover_trending_models(labs=labs, config=discovery_config)
        logger.info(f"✓ Discovered {len(models)} models after filtering")

    except Exception as e:
        logger.error(f"Model discovery failed: {e}")
        raise RuntimeError(f"Failed to discover models: {e}")

    # Prepare data for JSON output
    output_data = []
    for model in models:
        model_entry = {
            "model_id": model['id'],
            "author": model.get('author'),
            "lab": model.get('metadata', {}).get('discovered_from_lab'),
            "downloads": model.get('downloads', 0),
            "likes": model.get('likes', 0),
            "created_at": str(model.get('created_at', '')),
            "last_modified": str(model.get('last_modified', '')),
            "pipeline_tag": model.get('pipeline_tag'),
            "library_name": model.get('library_name'),
            "tags": model.get('tags', []),
            "private": model.get('private', False),
            "gated": model.get('gated', False),
        }
        output_data.append(model_entry)

    # Save standardized JSON output
    output_path = save_stage_json(
        data=output_data,
        stage_name="filter_models",
        input_count=input_count,
        errors=[]  # No errors in this run
    )

    logger.info(f"\n✓ Stage 1 complete")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Models: {len(models)} ({len(models)/len(labs):.1f} avg per lab)")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for Stage 1."""
    parser = argparse.ArgumentParser(
        description="Stage 1: Discover and filter AI models from HuggingFace"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )

    args = parser.parse_args()

    try:
        output_path = run(args.config)
        print(f"\n✓ Success! Output saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Stage 1 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
