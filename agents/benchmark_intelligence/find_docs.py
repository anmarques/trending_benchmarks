"""
Stage 2: Document Finding

Finds documentation sources for filtered models including model cards,
arXiv papers, blog posts, and GitHub documentation.

This is a standalone stage script with CLI entry point.
"""

import sys
import argparse
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.stage_utils import (
    load_stage_json,
    save_stage_json,
    find_latest_stage_output
)
from agents.benchmark_intelligence.tools.cache import CacheManager
from agents.benchmark_intelligence.error_aggregator import ErrorAggregator
from agents.benchmark_intelligence.tools.document_selection import (
    extract_all_arxiv_ids,
    fetch_arxiv_abstract,
    select_best_arxiv_paper,
    search_arxiv_api
)
from agents.benchmark_intelligence.tools.parse_model_card import parse_model_card


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def construct_document_urls(model_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Construct documentation URLs for a model from model card content only.

    Strategy:
    1. Always include HuggingFace model card
    2. Extract ALL arXiv papers from model card (tags + content)
    3. Use AI to select best paper if multiple found

    Args:
        model_data: Model information dictionary

    Returns:
        List of document specifications with URLs
    """
    model_id = model_data['model_id']
    tags = model_data.get('tags', [])
    author = model_data.get('author', '')
    model_name = model_id.split('/')[-1]
    documents = []

    # 1. HuggingFace Model Card (always available)
    documents.append({
        'type': 'model_card',
        'url': f'https://huggingface.co/{model_id}',
        'found': True
    })

    # 2. arXiv Papers - Extract from model card, fallback to arXiv API search
    try:
        # Fetch model card to search for arXiv references
        logger.debug(f"Fetching model card for {model_id} to find arXiv papers")
        from agents.benchmark_intelligence.clients.factory import get_hf_client
        hf_client = get_hf_client()
        model_card = parse_model_card(model_id, hf_client)
        model_card_content = model_card.get('content', '')

        # Extract arXiv IDs from tags and content
        arxiv_ids = extract_all_arxiv_ids(model_card_content, tags)

        # If no papers found in model card, search arXiv API
        if not arxiv_ids:
            logger.info(f"No arXiv papers in model card for {model_id}, searching arXiv API")
            arxiv_ids = search_arxiv_api(model_name, author, max_results=5)

        if arxiv_ids:
            logger.info(
                f"Found {len(arxiv_ids)} arXiv papers for {model_id}: {arxiv_ids}"
            )

            if len(arxiv_ids) == 1:
                # Only one paper, use it
                selected_id = arxiv_ids[0]
                logger.info(f"Using single arXiv paper: {selected_id}")
            else:
                # Multiple papers - fetch abstracts and use AI to select best one
                logger.info(f"Multiple arXiv papers found, fetching abstracts...")
                abstracts = []
                for arxiv_id in arxiv_ids:
                    abstract = fetch_arxiv_abstract(arxiv_id)
                    if abstract:
                        abstracts.append(abstract)

                # Use AI to select the best paper
                selected_id = select_best_arxiv_paper(abstracts, model_name, author)

            if selected_id:
                documents.append({
                    'type': 'arxiv_paper',
                    'url': f'https://arxiv.org/abs/{selected_id}',
                    'found': True,
                    'metadata': {
                        'total_candidates': len(arxiv_ids),
                        'ai_selected': len(arxiv_ids) > 1
                    }
                })

    except Exception as e:
        logger.warning(f"Failed to discover arXiv papers for {model_id}: {e}")

    return documents


def run(models_json: Optional[str] = None) -> str:
    """
    Execute Stage 2: Document URL discovery.

    Reads models from Stage 1 output, constructs documentation URLs for each model,
    and outputs standardized JSON.

    Args:
        models_json: Path to filter_models JSON output (auto-finds if not specified)

    Returns:
        Path to generated JSON output file

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If document finding fails
    """
    logger.info("=" * 70)
    logger.info("Stage 2: Document Finding")
    logger.info("=" * 70)

    # Load input from Stage 1
    if models_json is None:
        models_json = find_latest_stage_output("filter_models")
        if models_json is None:
            raise FileNotFoundError(
                "No filter_models output found. Run Stage 1 first."
            )
        logger.info(f"Auto-discovered input: {Path(models_json).name}")
    else:
        logger.info(f"Using input: {models_json}")

    # Load and validate Stage 1 output
    stage1_data = load_stage_json(models_json)
    models = stage1_data['data']

    logger.info(f"Processing {len(models)} models...")

    # Initialize cache for document hash tracking
    cache = CacheManager(use_pool=False)  # Simple mode for this stage

    # Initialize error aggregator
    error_aggregator = ErrorAggregator(max_samples_per_type=5)

    output_data = []
    total_docs_found = 0

    # Process each model
    for i, model in enumerate(models, 1):
        model_id = model['model_id']

        try:
            # Construct document URLs
            documents = construct_document_urls(model)

            # Count found documents
            found_count = sum(1 for doc in documents if doc.get('found', False))
            total_docs_found += found_count

            output_entry = {
                'model_id': model_id,
                'documents': documents,
                'doc_count': len(documents),
                'found_count': found_count
            }
            output_data.append(output_entry)

        except Exception as e:
            error_msg = f"Failed to construct URLs: {str(e)}"
            logger.warning(f"  {model_id}: {error_msg}")

            error_aggregator.add_error(
                "url_construction_failure",
                model_id,
                {"error": str(e)}
            )

            # Add entry with error
            output_entry = {
                'model_id': model_id,
                'documents': [],
                'doc_count': 0,
                'found_count': 0,
                'error': error_msg
            }
            output_data.append(output_entry)

        if (i % 50 == 0) or (i == len(models)):
            logger.info(f"  Processed {i}/{len(models)} models...")

    # Calculate statistics
    avg_docs_per_model = len(output_data) / len(models) if models else 0

    logger.info(f"\n✓ Document finding complete:")
    logger.info(f"  Models processed: {len(models)}")
    logger.info(f"  Total document URLs: {total_docs_found}")
    logger.info(f"  Avg docs per model: {avg_docs_per_model:.1f}")

    # Display error summary if any errors occurred
    if error_aggregator.has_errors():
        logger.info(f"\n{error_aggregator.format_summary_text()}")

    # Get error summary for JSON output
    error_summary = error_aggregator.get_summary()

    # Save standardized JSON output with error summary
    output_path = save_stage_json(
        data=output_data,
        stage_name="find_documents",
        input_count=len(models),
        errors=[],
        metadata={"error_summary": error_summary} if error_summary else None
    )

    logger.info(f"\n✓ Stage 2 complete")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for Stage 2."""
    parser = argparse.ArgumentParser(
        description="Stage 2: Find documentation URLs for filtered models"
    )
    parser.add_argument(
        "--input",
        help="Path to filter_models JSON output (auto-finds if not specified)"
    )

    args = parser.parse_args()

    try:
        output_path = run(args.input)
        print(f"\n✓ Success! Output saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Stage 2 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
