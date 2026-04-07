"""
Stage 3: Document Parsing and Benchmark Extraction

Fetches document content and extracts benchmark data using AI-powered analysis.
Processes multiple models in parallel with high concurrency support (20+ workers).

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
from agents.benchmark_intelligence.tools.parallel_fetcher import fetch_documents_parallel
from agents.benchmark_intelligence.tools.extract_benchmarks import extract_benchmarks_from_text
from agents.benchmark_intelligence.tools.parse_table import (
    parse_html_table,
    parse_markdown_table
)
from agents.benchmark_intelligence.concurrent_processor import ConcurrentModelProcessor
from agents.benchmark_intelligence.tools.cache import CacheManager


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def extract_benchmarks_from_model_docs(model_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single model: fetch documents and extract benchmarks.

    Args:
        model_entry: Model entry from Stage 2 with documents list

    Returns:
        Dictionary containing extracted benchmarks and metadata:
            - model_id: Model identifier
            - documents_processed: Number of documents successfully processed
            - benchmarks: List of extracted benchmark entries
            - errors: List of errors encountered
    """
    model_id = model_entry.get("model_id")
    documents = model_entry.get("documents", [])

    logger.debug(f"Processing {model_id}: {len(documents)} documents")

    # Fetch document content
    fetch_results = fetch_documents_parallel(
        models=[model_entry],
        max_workers=5,  # Fetch up to 5 docs per model in parallel
        docs_per_model=5
    )

    if not fetch_results:
        return {
            "model_id": model_id,
            "documents_processed": 0,
            "benchmarks": [],
            "errors": ["Failed to fetch documents"]
        }

    # Get fetched documents for this model
    model_docs = fetch_results[0].get("documents", [])
    successful_docs = [doc for doc in model_docs if doc.get("success", False)]

    all_benchmarks = []
    errors = []

    # Extract benchmarks from each successfully fetched document
    for doc in successful_docs:
        try:
            content = doc.get("content", "")
            if not content:
                continue

            content_format = doc.get("content_format", "prose")
            doc_type = doc.get("type", "unknown")
            url = doc.get("url")

            # Route to appropriate parser based on content format
            benchmarks = []

            if content_format == "html_table":
                # Use deterministic HTML table parser
                logger.debug(f"  {model_id}: Parsing HTML tables from {doc_type}")
                benchmarks = parse_html_table(content, model_id=model_id)

            elif content_format == "markdown_table":
                # Use deterministic Markdown table parser
                logger.debug(f"  {model_id}: Parsing Markdown tables from {doc_type}")
                benchmarks = parse_markdown_table(content, model_id=model_id)

            elif content_format == "prose":
                # Use AI-powered extraction for unstructured text
                logger.debug(f"  {model_id}: Using AI extraction for prose from {doc_type}")
                extraction_result = extract_benchmarks_from_text(
                    text=content,
                    source_type=doc_type,
                    source_name=url,
                    detect_cooccurrence=True
                )
                benchmarks = extraction_result.get("benchmarks", [])

            elif content_format == "pdf":
                # PDF extraction deferred to Phase 5
                logger.debug(f"  {model_id}: Skipping PDF extraction (Phase 5)")
                continue

            # Add source attribution to all benchmarks
            for bench in benchmarks:
                bench["model_id"] = model_id
                bench["source_url"] = url
                bench["source_type"] = doc_type

            all_benchmarks.extend(benchmarks)

            logger.debug(
                f"  {model_id}: Extracted {len(benchmarks)} benchmarks from {doc_type} "
                f"(format: {content_format})"
            )

        except Exception as e:
            error_msg = f"Failed to extract from {doc['type']}: {str(e)}"
            logger.warning(f"  {model_id}: {error_msg}")
            errors.append(error_msg)

    return {
        "model_id": model_id,
        "documents_processed": len(successful_docs),
        "benchmarks": all_benchmarks,
        "benchmark_count": len(all_benchmarks),
        "errors": errors
    }


def run(docs_json: Optional[str] = None, concurrency: int = 20) -> str:
    """
    Execute Stage 3: Document parsing and benchmark extraction.

    Reads document URLs from Stage 2 output, fetches content, extracts benchmarks
    using AI, and outputs standardized JSON.

    Args:
        docs_json: Path to find_documents JSON output (auto-finds if not specified)
        concurrency: Number of parallel workers (default: 20)

    Returns:
        Path to generated JSON output file

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If extraction fails
    """
    logger.info("=" * 70)
    logger.info("Stage 3: Document Parsing & Benchmark Extraction")
    logger.info("=" * 70)

    # Load input from Stage 2
    if docs_json is None:
        docs_json = find_latest_stage_output("find_documents")
        if docs_json is None:
            raise FileNotFoundError(
                "No find_documents output found. Run Stage 2 first."
            )
        logger.info(f"Auto-discovered input: {Path(docs_json).name}")
    else:
        logger.info(f"Using input: {docs_json}")

    # Load and validate Stage 2 output
    stage2_data = load_stage_json(docs_json)
    models = stage2_data['data']

    logger.info(f"Configuration:")
    logger.info(f"  Models to process: {len(models)}")
    logger.info(f"  Concurrency: {concurrency} workers")
    logger.info(f"  AI extraction: Enabled (Claude)")

    # Initialize concurrent processor
    processor = ConcurrentModelProcessor(max_workers=concurrency)

    # Progress callback
    def progress_callback(completed: int, total: int):
        if completed % 10 == 0 or completed == total:
            logger.info(f"  Progress: {completed}/{total} models processed")

    logger.info(f"\nProcessing {len(models)} models in parallel...")

    # Process all models concurrently
    results = processor.process_models(
        models=models,
        process_func=extract_benchmarks_from_model_docs,
        progress_callback=progress_callback
    )

    # Aggregate statistics
    output_data = []
    total_benchmarks = 0
    total_docs_processed = 0
    errors_list = []

    for result in results:
        model_id = result.get("model_id")
        benchmark_count = result.get("benchmark_count", 0)
        docs_processed = result.get("documents_processed", 0)
        errors = result.get("errors", [])

        total_benchmarks += benchmark_count
        total_docs_processed += docs_processed

        if errors:
            for error in errors:
                errors_list.append({
                    "model_id": model_id,
                    "error": error
                })

        # Prepare output entry
        output_entry = {
            "model_id": model_id,
            "documents_processed": docs_processed,
            "benchmark_count": benchmark_count,
            "benchmarks": result.get("benchmarks", [])
        }
        output_data.append(output_entry)

    # Calculate statistics
    models_with_benchmarks = sum(1 for r in results if r.get("benchmark_count", 0) > 0)
    avg_benchmarks_per_model = total_benchmarks / len(models) if models else 0

    logger.info(f"\n✓ Benchmark extraction complete:")
    logger.info(f"  Models processed: {len(models)}")
    logger.info(f"  Documents processed: {total_docs_processed}")
    logger.info(f"  Total benchmarks extracted: {total_benchmarks}")
    logger.info(f"  Models with benchmarks: {models_with_benchmarks} ({models_with_benchmarks/len(models)*100:.1f}%)")
    logger.info(f"  Avg benchmarks per model: {avg_benchmarks_per_model:.1f}")

    if errors_list:
        logger.warning(f"  Errors encountered: {len(errors_list)}")

    # Save standardized JSON output
    output_path = save_stage_json(
        data=output_data,
        stage_name="parse_documents",
        input_count=len(models),
        errors=errors_list
    )

    # Get processing summary
    summary = processor.get_summary()
    logger.info(f"\nProcessing summary:")
    logger.info(f"  Completed: {summary['completed']}")
    logger.info(f"  Failed: {summary['failed']}")

    logger.info(f"\n✓ Stage 3 complete")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for Stage 3."""
    parser = argparse.ArgumentParser(
        description="Stage 3: Parse documents and extract benchmarks"
    )
    parser.add_argument(
        "--input",
        help="Path to find_documents JSON output (auto-finds if not specified)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Number of parallel workers (default: 20)"
    )

    args = parser.parse_args()

    try:
        output_path = run(args.input, args.concurrency)
        print(f"\n✓ Success! Output saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Stage 3 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
