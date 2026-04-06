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


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def extract_arxiv_id(tags: List[str]) -> Optional[str]:
    """
    Extract arXiv ID from model tags.

    Args:
        tags: List of model tags

    Returns:
        arXiv ID if found (e.g., "2505.09388"), None otherwise
    """
    for tag in tags:
        if tag.startswith('arxiv:'):
            return tag.replace('arxiv:', '')
    return None


def construct_document_urls(model_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Construct documentation URLs for a model.

    Args:
        model_data: Model information dictionary

    Returns:
        List of document specifications with URLs
    """
    model_id = model_data['model_id']
    tags = model_data.get('tags', [])
    documents = []

    # 1. HuggingFace Model Card (always available)
    documents.append({
        'type': 'model_card',
        'url': f'https://huggingface.co/{model_id}',
        'found': True
    })

    # 2. arXiv Paper (if referenced in tags)
    arxiv_id = extract_arxiv_id(tags)
    if arxiv_id:
        documents.append({
            'type': 'arxiv_paper',
            'url': f'https://arxiv.org/abs/{arxiv_id}',
            'found': True
        })

    # 3. GitHub Repository (construct from model_id)
    # Format: github.com/org/repo
    # Some labs have predictable GitHub patterns
    author = model_data.get('author', '')
    github_orgs = {
        'Qwen': 'QwenLM',
        'meta-llama': 'meta-llama',
        'mistralai': 'mistralai',
        'google': 'google-research',
        'microsoft': 'microsoft',
        'deepseek-ai': 'deepseek-ai',
        'nvidia': 'NVIDIA',
        'openai': 'openai',
        'moonshotai': 'moonshotai',
        'zai-org': 'THUDM',
        'ibm-granite': 'ibm-granite'
    }

    github_org = github_orgs.get(author)
    if github_org:
        # Extract model name from model_id
        model_name = model_id.split('/')[-1]
        documents.append({
            'type': 'github',
            'url': f'https://github.com/{github_org}/{model_name}',
            'found': False  # Will be validated in future if needed
        })

    # 4. Official Blog Posts (for major models)
    # Add predictable blog URLs for major labs
    blog_urls = {
        'Qwen': 'https://qwenlm.github.io/blog/',
        'meta-llama': 'https://ai.meta.com/blog/',
        'mistralai': 'https://mistral.ai/news/',
        'google': 'https://blog.research.google/',
        'deepseek-ai': 'https://www.deepseek.com/blog/',
    }

    if author in blog_urls:
        documents.append({
            'type': 'blog',
            'url': blog_urls[author],
            'found': False  # Generic blog URL, not model-specific
        })

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

    output_data = []
    total_docs_found = 0

    # Process each model
    for i, model in enumerate(models, 1):
        model_id = model['model_id']

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

        if (i % 50 == 0) or (i == len(models)):
            logger.info(f"  Processed {i}/{len(models)} models...")

    # Calculate statistics
    avg_docs_per_model = len(output_data) / len(models) if models else 0

    logger.info(f"\n✓ Document finding complete:")
    logger.info(f"  Models processed: {len(models)}")
    logger.info(f"  Total document URLs: {total_docs_found}")
    logger.info(f"  Avg docs per model: {avg_docs_per_model:.1f}")

    # Save standardized JSON output
    output_path = save_stage_json(
        data=output_data,
        stage_name="find_documents",
        input_count=len(models),
        errors=[]  # No errors in this simple implementation
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
