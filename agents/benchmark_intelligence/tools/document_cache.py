"""
Document-level caching for parse_docs stage.

Ensures each unique document URL is fetched and parsed only once,
even if referenced by multiple models.
"""

import logging
import hashlib
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .parallel_fetcher import fetch_document_content
from .extract_benchmarks import extract_benchmarks_from_text
from .parse_table import parse_html_table, parse_markdown_table
from .extract_benchmarks_vision import extract_benchmarks_from_pdf
from .benchmark_validation import filter_benchmarks

logger = logging.getLogger(__name__)


class DocumentCache:
    """
    Cache for document fetching and parsing.

    Deduplicates documents by URL to avoid fetching and parsing the same
    document multiple times when it's referenced by multiple models.
    """

    def __init__(self):
        """Initialize the document cache."""
        self._url_to_content = {}  # url -> fetched content
        self._url_to_benchmarks = {}  # url -> extracted benchmarks
        self._url_to_models = defaultdict(list)  # url -> list of model_ids

    def build_url_index(self, models: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Build an index mapping URLs to models that reference them.

        Args:
            models: List of model entries from Stage 2

        Returns:
            Dictionary mapping URL to list of model IDs
        """
        url_to_models = defaultdict(list)

        for model in models:
            model_id = model['model_id']
            for doc in model.get('documents', []):
                url = doc.get('url')
                if url and doc.get('found', False):
                    url_to_models[url].append(model_id)

        self._url_to_models = url_to_models

        # Log deduplication stats
        total_refs = sum(len(models) for models in url_to_models.values())
        unique_urls = len(url_to_models)

        logger.info(f"Document deduplication:")
        logger.info(f"  Total document references: {total_refs}")
        logger.info(f"  Unique URLs: {unique_urls}")
        logger.info(f"  Deduplication savings: {total_refs - unique_urls} fetches avoided")

        # Show top duplicates
        duplicates = [(url, models) for url, models in url_to_models.items() if len(models) > 1]
        if duplicates:
            duplicates.sort(key=lambda x: len(x[1]), reverse=True)
            logger.info(f"  Top duplicate URLs:")
            for url, models in duplicates[:5]:
                logger.info(f"    {len(models)} models: {url[:80]}...")

        return dict(url_to_models)

    def fetch_and_parse_all(
        self,
        models: List[Dict[str, Any]],
        max_workers: int = 10
    ) -> None:
        """
        Fetch and parse all unique documents.

        Args:
            models: List of model entries from Stage 2
            max_workers: Maximum concurrent fetches
        """
        # Build URL index first
        self.build_url_index(models)

        # Create a map of url -> doc metadata (type, etc.)
        url_to_doc_info = {}
        for model in models:
            for doc in model.get('documents', []):
                url = doc.get('url')
                if url and doc.get('found', False) and url not in url_to_doc_info:
                    url_to_doc_info[url] = {
                        'type': doc.get('type'),
                        'url': url
                    }

        logger.info(f"\nFetching and parsing {len(url_to_doc_info)} unique documents...")

        # Process each unique URL
        processed = 0
        for url, doc_info in url_to_doc_info.items():
            try:
                # Fetch content
                content, content_type = fetch_document_content(
                    url=url,
                    doc_type=doc_info['type']
                )

                if not content:
                    logger.warning(f"Failed to fetch: {url[:80]}...")
                    self._url_to_benchmarks[url] = []
                    continue

                # Determine content format
                from .parallel_fetcher import detect_content_format
                content_format = detect_content_format(content, content_type)

                # Store content
                self._url_to_content[url] = {
                    'content': content,
                    'content_format': content_format,
                    'type': doc_info['type']
                }

                # Extract benchmarks
                benchmarks = self._extract_benchmarks(
                    content=content,
                    content_format=content_format,
                    doc_type=doc_info['type'],
                    url=url
                )

                self._url_to_benchmarks[url] = benchmarks

                processed += 1
                if processed % 10 == 0:
                    logger.info(f"  Processed {processed}/{len(url_to_doc_info)} documents...")

                logger.debug(
                    f"  {url[:80]}... -> {len(benchmarks)} benchmarks "
                    f"(format: {content_format}, shared by {len(self._url_to_models[url])} models)"
                )

            except Exception as e:
                logger.warning(f"Failed to process {url[:80]}...: {e}")
                self._url_to_benchmarks[url] = []

        logger.info(f"✓ Fetched and parsed {processed} unique documents")

    def _extract_benchmarks(
        self,
        content: Any,
        content_format: str,
        doc_type: str,
        url: str
    ) -> List[Dict[str, Any]]:
        """
        Extract benchmarks from document content.

        Args:
            content: Document content (str or bytes)
            content_format: Format detected (html_table, markdown_table, pdf, prose)
            doc_type: Document type (model_card, arxiv_paper, blog, etc.)
            url: Document URL

        Returns:
            List of benchmark dictionaries
        """
        benchmarks = []

        try:
            if content_format == "html_table":
                benchmarks = parse_html_table(content, model_id=None)

            elif content_format == "markdown_table":
                benchmarks = parse_markdown_table(content, model_id=None)

            elif content_format == "pdf":
                extraction_result = extract_benchmarks_from_pdf(
                    pdf_content=content,
                    source_name=url
                )
                benchmarks = extraction_result.get("benchmarks", [])

            elif content_format == "prose":
                extraction_result = extract_benchmarks_from_text(
                    text=content,
                    source_type=doc_type,
                    source_name=url,
                    detect_cooccurrence=True
                )
                benchmarks = extraction_result.get("benchmarks", [])

        except Exception as e:
            logger.error(f"Extraction failed for {url[:80]}...: {e}")
            benchmarks = []

        # Apply validation filters to remove false positives
        if benchmarks:
            pre_filter_count = len(benchmarks)
            benchmarks = filter_benchmarks(
                benchmarks,
                use_ai_validation=False  # AI validation disabled by default
            )
            if len(benchmarks) < pre_filter_count:
                logger.debug(
                    f"Filtered {pre_filter_count - len(benchmarks)} "
                    f"false positives from {url[:80]}..."
                )

        return benchmarks

    def get_benchmarks_for_model(
        self,
        model_id: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get extracted benchmarks for a model from the cache.

        Args:
            model_id: Model identifier
            documents: List of document specs for this model

        Returns:
            Dictionary with benchmarks and metadata
        """
        all_benchmarks = []
        docs_processed = 0

        for doc in documents:
            url = doc.get('url')
            if not url or not doc.get('found', False):
                continue

            # Get cached benchmarks for this URL
            benchmarks = self._url_to_benchmarks.get(url, [])

            if benchmarks:
                docs_processed += 1

                # Add model-specific attribution
                for bench in benchmarks:
                    bench_copy = bench.copy()
                    bench_copy["model_id"] = model_id
                    bench_copy["source_url"] = url
                    bench_copy["source_type"] = doc.get('type')
                    all_benchmarks.append(bench_copy)

        return {
            "model_id": model_id,
            "documents_processed": docs_processed,
            "benchmarks": all_benchmarks,
            "benchmark_count": len(all_benchmarks),
            "errors": []
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_urls = len(self._url_to_models)
        total_refs = sum(len(models) for models in self._url_to_models.values())
        fetched = len(self._url_to_content)
        parsed = len(self._url_to_benchmarks)

        total_benchmarks = sum(len(b) for b in self._url_to_benchmarks.values())

        return {
            "unique_urls": total_urls,
            "total_references": total_refs,
            "deduplication_savings": total_refs - total_urls,
            "documents_fetched": fetched,
            "documents_parsed": parsed,
            "total_benchmarks_extracted": total_benchmarks
        }
