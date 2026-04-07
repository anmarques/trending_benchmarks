"""
Parallel document fetching utilities for benchmark extraction.

Fetches document content from multiple sources (HuggingFace model cards,
arXiv papers, GitHub repos, blog posts) in parallel using concurrent processing.
"""

import logging
import re
import requests
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .parse_model_card import parse_model_card
from ..clients.factory import get_hf_client


logger = logging.getLogger(__name__)


def detect_content_format(content: str, content_type: str = "text/html") -> str:
    """
    Detect the format of document content for routing to appropriate parser.

    Args:
        content: Document content to analyze
        content_type: HTTP Content-Type header (optional)

    Returns:
        Format identifier: "html_table", "markdown_table", "prose", or "pdf"

    Example:
        >>> html = "<table><tr><th>Benchmark</th></tr></table>"
        >>> detect_content_format(html)
        'html_table'
        >>> markdown = "| Benchmark | Score |\\n|-----------|-------|"
        >>> detect_content_format(markdown)
        'markdown_table'
    """
    # Check for PDF content type
    if "application/pdf" in content_type.lower():
        return "pdf"

    # Check for HTML tables (case-insensitive)
    # Look for <table> tag with optional attributes
    if re.search(r'<table[\s>]', content, re.IGNORECASE):
        return "html_table"

    # Check for markdown tables
    # Require header separator line with pipes and dashes: |---|---|
    if re.search(r'\|[-:\s]+\|[-:\s]+\|', content):
        return "markdown_table"

    # Default to prose (unstructured text)
    return "prose"


def fetch_document_content(
    url: str,
    doc_type: str,
    timeout: int = 30
) -> tuple[Optional[str], str]:
    """
    Fetch content from a single document URL.

    Args:
        url: Document URL to fetch
        doc_type: Type of document ("model_card", "arxiv_paper", "github", "blog")
        timeout: Request timeout in seconds

    Returns:
        Tuple of (content, content_type):
            - content: Document content as string, or None if fetch fails
            - content_type: MIME type (e.g., "text/html", "text/plain")

    Example:
        >>> content, ctype = fetch_document_content("https://arxiv.org/abs/2505.09388", "arxiv_paper")
    """
    try:
        if doc_type == "model_card":
            # Extract model_id from HuggingFace URL
            # Format: https://huggingface.co/Qwen/Qwen3-8B
            model_id = url.replace("https://huggingface.co/", "")
            hf_client = get_hf_client()
            card_data = parse_model_card(model_id, hf_client)
            return card_data.get("content", ""), "text/html"

        elif doc_type == "arxiv_paper":
            # Fetch arXiv abstract
            # Format: https://arxiv.org/abs/2505.09388
            arxiv_id = url.split("/abs/")[-1]
            # Try HTML abstract page first (easier to parse than PDF)
            abstract_url = f"https://export.arxiv.org/abs/{arxiv_id}"
            response = requests.get(abstract_url, timeout=timeout)
            response.raise_for_status()

            # Simple extraction of abstract from HTML
            # (Full PDF parsing would be in Phase 5 - multi-source extraction quality)
            html = response.text
            content_type = response.headers.get('content-type', 'text/html')

            # Extract abstract content between <blockquote> tags
            abstract_match = re.search(
                r'<blockquote[^>]*class="abstract mathjax"[^>]*>(.*?)</blockquote>',
                html,
                re.DOTALL
            )
            if abstract_match:
                abstract_text = abstract_match.group(1)
                # Remove HTML tags
                abstract_text = re.sub(r'<[^>]+>', '', abstract_text)
                # Clean whitespace
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                return abstract_text, content_type

            logger.warning(f"Could not extract abstract from {url}")
            return None, content_type

        elif doc_type == "github":
            # Fetch GitHub README
            # Format: https://github.com/QwenLM/Qwen3-8B
            # Convert to raw content URL
            parts = url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                # Try main branch first, then master
                for branch in ["main", "master"]:
                    readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
                    try:
                        response = requests.get(readme_url, timeout=timeout)
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', 'text/markdown')
                            return response.text, content_type
                    except Exception:
                        continue

            logger.warning(f"Could not fetch GitHub README from {url}")
            return None, "text/plain"

        elif doc_type in ("blog", "blog_post"):
            # Fetch blog post content (generic HTML fetch)
            # Note: This is basic - proper blog parsing would use BeautifulSoup
            # or dedicated scrapers (Phase 5 improvement)
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            content_type = response.headers.get('content-type', 'text/html')
            # Return raw HTML for now
            # (Phase 5 would add proper content extraction)
            return response.text, content_type

        else:
            logger.warning(f"Unknown document type: {doc_type}")
            return None, "text/plain"

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return None, "text/plain"
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None, "text/plain"
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return None, "text/plain"


def fetch_documents_for_model(
    model_id: str,
    documents: List[Dict[str, Any]],
    max_workers: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch content for all documents associated with a model.

    Fetches documents in parallel using ThreadPoolExecutor.

    Args:
        model_id: Model identifier
        documents: List of document specs from Stage 2 (find_docs)
                   Each has: type, url, found (boolean)
        max_workers: Maximum concurrent fetches per model

    Returns:
        List of document results with fetched content:
            - type: Document type
            - url: Document URL
            - content: Fetched content (or None if failed)
            - content_format: Format detected ("html_table", "markdown_table", "prose", "pdf")
            - success: Boolean indicating successful fetch

    Example:
        >>> docs = [
        ...     {"type": "model_card", "url": "https://huggingface.co/Qwen/Qwen3-8B", "found": True},
        ...     {"type": "arxiv_paper", "url": "https://arxiv.org/abs/2505.09388", "found": True}
        ... ]
        >>> results = fetch_documents_for_model("Qwen/Qwen3-8B", docs)
    """
    results = []

    # Filter to only documents marked as "found"
    docs_to_fetch = [doc for doc in documents if doc.get("found", False)]

    if not docs_to_fetch:
        logger.info(f"No documents to fetch for {model_id}")
        return results

    logger.info(f"Fetching {len(docs_to_fetch)} documents for {model_id}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all fetch tasks
        future_to_doc = {
            executor.submit(
                fetch_document_content,
                doc["url"],
                doc["type"]
            ): doc
            for doc in docs_to_fetch
        }

        # Collect results as they complete
        for future in as_completed(future_to_doc):
            doc = future_to_doc[future]
            try:
                content, content_type = future.result()
                success = content is not None

                # Detect content format for routing
                content_format = detect_content_format(content or "", content_type)

                results.append({
                    "type": doc["type"],
                    "url": doc["url"],
                    "content": content,
                    "content_format": content_format,
                    "success": success
                })

                if success:
                    logger.debug(
                        f"Fetched {doc['type']} for {model_id}: {len(content)} chars "
                        f"(format: {content_format})"
                    )
                else:
                    logger.warning(f"Failed to fetch {doc['type']} for {model_id}")

            except Exception as e:
                logger.error(f"Error fetching {doc['type']} for {model_id}: {e}")
                results.append({
                    "type": doc["type"],
                    "url": doc["url"],
                    "content": None,
                    "content_format": "prose",
                    "success": False
                })

    logger.info(
        f"Fetched {sum(1 for r in results if r['success'])}/{len(docs_to_fetch)} "
        f"documents for {model_id}"
    )

    return results


def fetch_documents_parallel(
    models: List[Dict[str, Any]],
    max_workers: int = 20,
    docs_per_model: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch documents for multiple models in parallel.

    Processes multiple models concurrently, with each model's documents
    also fetched in parallel.

    Args:
        models: List of model entries from Stage 2 output (find_docs)
                Each has: model_id, documents (list of doc specs)
        max_workers: Maximum concurrent models to process
        docs_per_model: Maximum concurrent documents per model

    Returns:
        List of results, one per model:
            - model_id: Model identifier
            - documents: List of fetched documents with content
            - success_count: Number of successfully fetched documents
            - total_count: Total documents attempted

    Example:
        >>> models = [
        ...     {
        ...         "model_id": "Qwen/Qwen3-8B",
        ...         "documents": [
        ...             {"type": "model_card", "url": "...", "found": True},
        ...             {"type": "arxiv_paper", "url": "...", "found": True}
        ...         ]
        ...     }
        ... ]
        >>> results = fetch_documents_parallel(models, max_workers=20)
    """
    logger.info(f"Fetching documents for {len(models)} models with {max_workers} workers")

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all model fetch tasks
        future_to_model = {
            executor.submit(
                fetch_documents_for_model,
                model["model_id"],
                model.get("documents", []),
                docs_per_model
            ): model
            for model in models
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_model):
            model = future_to_model[future]
            model_id = model["model_id"]

            try:
                documents = future.result()
                success_count = sum(1 for doc in documents if doc.get("success", False))

                results.append({
                    "model_id": model_id,
                    "documents": documents,
                    "success_count": success_count,
                    "total_count": len(documents)
                })

                completed += 1
                if completed % 10 == 0 or completed == len(models):
                    logger.info(f"Processed {completed}/{len(models)} models...")

            except Exception as e:
                logger.error(f"Error processing {model_id}: {e}")
                results.append({
                    "model_id": model_id,
                    "documents": [],
                    "success_count": 0,
                    "total_count": 0,
                    "error": str(e)
                })

    total_docs = sum(r.get("success_count", 0) for r in results)
    logger.info(f"Fetched {total_docs} total documents across {len(models)} models")

    return results


def prepare_document_specs_for_model(
    model: Dict[str, Any],
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Prepare document specifications for a single model.

    Extracts the documents list from a model entry and validates the structure.

    Args:
        model: Model entry with documents list
        **kwargs: Additional options (reserved for future use)

    Returns:
        List of document specifications ready for fetching

    Example:
        >>> model = {"model_id": "Qwen/Qwen3-8B", "documents": [...]}
        >>> docs = prepare_document_specs_for_model(model)
    """
    documents = model.get("documents", [])

    # Validate document structure
    valid_docs = []
    for doc in documents:
        if not isinstance(doc, dict):
            logger.warning(f"Invalid document spec (not a dict): {doc}")
            continue

        if "type" not in doc or "url" not in doc:
            logger.warning(f"Invalid document spec (missing type/url): {doc}")
            continue

        # Ensure 'found' field exists
        if "found" not in doc:
            doc["found"] = False

        valid_docs.append(doc)

    return valid_docs
