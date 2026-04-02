"""
Web documentation fetcher for finding and downloading technical documents.

This module provides functionality to search for and fetch technical documentation
related to AI models, including technical reports, blog posts, and white papers.
"""

import logging
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Import fallback implementation
try:
    from .fetch_docs_fallback import search_and_fetch_simple
    HAS_FALLBACK = True
except ImportError:
    HAS_FALLBACK = False
    logger.warning("Fallback documentation fetcher not available")

# Import PDF parser
try:
    from . import pdf_parser
    HAS_PDF_PARSER = True
except ImportError:
    HAS_PDF_PARSER = False
    logger.warning("PDF parser not available - PDF documents will be skipped")


def fetch_documentation(
    model_name: str,
    labs_to_search: Optional[List[str]] = None,
    web_search_fn: Optional[callable] = None,
    web_fetch_fn: Optional[callable] = None,
    pdf_config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch documentation for a model from web sources.

    Searches for technical reports, blog posts, and white papers related to
    a specific model. Uses web search to find URLs and then fetches content.

    Args:
        model_name: Name of the model to search for (e.g., "Qwen2.5-7B", "Llama-3.1")
        labs_to_search: Optional list of organization names to prioritize in search
        web_search_fn: Optional web search function (for testing/injection).
                       Should accept query string and return list of results.
        web_fetch_fn: Optional web fetch function (for testing/injection).
                      Should accept URL and prompt, return content.
        pdf_config: PDF constraints configuration (max_file_size_mb,
                   download_timeout_seconds, max_extracted_chars)

    Returns:
        List of document dictionaries containing:
            - title: Document title
            - url: Source URL
            - content: Extracted text content
            - doc_type: Type of document (technical_report, blog_post, white_paper, etc.)
            - source: Source domain/organization
            - metadata: Additional metadata (fetch_date, word_count, etc.)

    Raises:
        ValueError: If model_name is invalid
        RuntimeError: If document fetching fails

    Example:
        >>> docs = fetch_documentation(
        ...     "Qwen2.5-7B",
        ...     labs_to_search=["Qwen", "Alibaba"]
        ... )
        >>> print(f"Found {len(docs)} documents")
        >>> for doc in docs:
        ...     print(f"{doc['title']}: {doc['url']}")
    """
    try:
        if not model_name or not isinstance(model_name, str):
            raise ValueError("model_name must be a non-empty string")

        logger.info(f"Searching for documentation for model: {model_name}")

        # Build search queries
        search_queries = _build_search_queries(model_name, labs_to_search)

        documents = []
        seen_urls = set()

        # Execute searches
        for query in search_queries:
            try:
                logger.debug(f"Searching: {query}")

                # Use injected function if provided, otherwise use fallback
                if web_search_fn is None:
                    logger.info("No web_search_fn provided, using fallback fetcher")
                    if HAS_FALLBACK:
                        return search_and_fetch_simple(
                            model_name=model_name,
                            labs_to_search=labs_to_search,
                            max_docs=5
                        )
                    else:
                        logger.warning("No fallback available, skipping documentation fetch")
                        return []

                results = web_search_fn(query)

                # Process search results
                for result in results:
                    url = result.get("url")
                    title = result.get("title", "Untitled")

                    # Skip duplicates
                    if url in seen_urls:
                        continue

                    # Filter URLs
                    if not _is_relevant_url(url, model_name):
                        continue

                    seen_urls.add(url)

                    # Check if URL is a PDF
                    if is_pdf_url(url):
                        logger.info(f"Detected PDF URL: {url}")
                        pdf_doc = fetch_pdf_document(url, pdf_config)
                        if pdf_doc:
                            documents.append(pdf_doc)
                            logger.info(f"Fetched PDF: {pdf_doc['title']} ({url})")
                        continue

                    # Fetch document content
                    try:
                        if web_fetch_fn is None:
                            logger.warning(
                                "No web_fetch_fn provided, cannot fetch content. "
                                "Pass web_fetch_fn parameter or use WebFetch tool."
                            )
                            # Add metadata without content
                            doc = {
                                "title": title,
                                "url": url,
                                "content": None,
                                "doc_type": _classify_document_type(url, title),
                                "source": _extract_source(url),
                                "metadata": {
                                    "fetch_date": datetime.utcnow().isoformat(),
                                    "search_query": query,
                                    "fetched": False,
                                },
                            }
                            documents.append(doc)
                            continue

                        content = web_fetch_fn(
                            url,
                            "Extract the main text content from this page. "
                            "Focus on technical details, benchmark results, and model descriptions."
                        )

                        if content:
                            doc = {
                                "title": title,
                                "url": url,
                                "content": content,
                                "doc_type": _classify_document_type(url, title),
                                "source": _extract_source(url),
                                "metadata": {
                                    "fetch_date": datetime.utcnow().isoformat(),
                                    "word_count": len(content.split()),
                                    "char_count": len(content),
                                    "search_query": query,
                                    "fetched": True,
                                },
                            }
                            documents.append(doc)
                            logger.info(f"Fetched: {title} ({url})")

                    except Exception as e:
                        logger.warning(f"Failed to fetch {url}: {e}")
                        continue

                    # Limit number of documents per query
                    if len(documents) >= 10:
                        break

            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue

        logger.info(f"Fetched {len(documents)} documents for {model_name}")

        return documents

    except Exception as e:
        logger.error(f"Failed to fetch documentation for {model_name}: {e}")
        raise RuntimeError(f"Failed to fetch documentation: {e}")


def _build_search_queries(
    model_name: str,
    labs_to_search: Optional[List[str]] = None
) -> List[str]:
    """
    Build search queries for finding model documentation.

    Args:
        model_name: Model name
        labs_to_search: Optional list of organization names

    Returns:
        List of search query strings
    """
    queries = []

    # Basic model search
    queries.append(f"{model_name} technical report")
    queries.append(f"{model_name} model card")
    queries.append(f"{model_name} benchmarks evaluation")

    # Lab-specific searches
    if labs_to_search:
        for lab in labs_to_search[:2]:  # Limit to top 2 labs
            queries.append(f"{lab} {model_name} announcement")
            queries.append(f"{lab} {model_name} blog post")

    # Research paper search
    queries.append(f"{model_name} arXiv paper")
    queries.append(f"{model_name} research paper")

    return queries


def _is_relevant_url(url: str, model_name: str) -> bool:
    """
    Check if a URL is relevant for the model.

    Filters out irrelevant domains and URLs.

    Args:
        url: URL to check
        model_name: Model name for context

    Returns:
        True if URL is relevant, False otherwise
    """
    if not url:
        return False

    url_lower = url.lower()

    # Preferred domains
    preferred_domains = [
        "huggingface.co",
        "arxiv.org",
        "github.com",
        "blog",
        "research",
        "papers",
    ]

    # Blocked domains
    blocked_domains = [
        "youtube.com",
        "twitter.com",
        "reddit.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com/posts",
    ]

    # Check blocked domains
    if any(domain in url_lower for domain in blocked_domains):
        return False

    # Prefer relevant domains
    has_preferred = any(domain in url_lower for domain in preferred_domains)

    # Check if model name appears in URL (good signal)
    model_name_clean = model_name.lower().replace(".", "").replace("-", "")
    url_clean = url_lower.replace(".", "").replace("-", "")
    has_model_name = model_name_clean in url_clean

    # Accept if has preferred domain or model name in URL
    return has_preferred or has_model_name


def _classify_document_type(url: str, title: str) -> str:
    """
    Classify the type of document based on URL and title.

    Args:
        url: Document URL
        title: Document title

    Returns:
        Document type classification
    """
    url_lower = url.lower()
    title_lower = title.lower()

    # Check URL patterns
    if "arxiv.org" in url_lower:
        return "research_paper"
    elif "github.com" in url_lower and "/blob/" in url_lower:
        return "technical_report"
    elif "blog" in url_lower or "medium.com" in url_lower:
        return "blog_post"
    elif "huggingface.co" in url_lower:
        return "model_card"

    # Check title patterns
    if any(word in title_lower for word in ["paper", "arxiv", "research"]):
        return "research_paper"
    elif any(word in title_lower for word in ["blog", "post", "announcement"]):
        return "blog_post"
    elif any(word in title_lower for word in ["documentation", "docs", "guide"]):
        return "documentation"
    elif "white paper" in title_lower or "whitepaper" in title_lower:
        return "white_paper"

    return "unknown"


def _extract_source(url: str) -> str:
    """
    Extract the source organization/domain from a URL.

    Args:
        url: Document URL

    Returns:
        Source identifier
    """
    # Extract domain
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if match:
        domain = match.group(1)

        # Map domains to organizations
        if "huggingface.co" in domain:
            return "HuggingFace"
        elif "arxiv.org" in domain:
            return "arXiv"
        elif "github.com" in domain:
            # Try to extract org from github.com/org/repo
            org_match = re.search(r"github\.com/([^/]+)", url)
            if org_match:
                return f"GitHub/{org_match.group(1)}"
            return "GitHub"
        elif "openai.com" in domain:
            return "OpenAI"
        elif "anthropic.com" in domain:
            return "Anthropic"
        elif "google" in domain:
            return "Google"
        elif "meta" in domain or "facebook" in domain:
            return "Meta"

        return domain

    return "unknown"


def filter_documents_by_type(
    documents: List[Dict[str, Any]],
    doc_types: List[str],
) -> List[Dict[str, Any]]:
    """
    Filter documents by type.

    Utility function to filter document lists by type.

    Args:
        documents: List of document dictionaries
        doc_types: List of document types to include

    Returns:
        Filtered list of documents

    Example:
        >>> papers = filter_documents_by_type(
        ...     docs,
        ...     ["research_paper", "technical_report"]
        ... )
    """
    return [doc for doc in documents if doc.get("doc_type") in doc_types]


def fetch_pdf_document(
    url: str,
    pdf_config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Download and extract content from a PDF document.

    Args:
        url: URL of the PDF document
        pdf_config: PDF constraints configuration (max_file_size_mb,
                   download_timeout_seconds, max_extracted_chars)

    Returns:
        Document dictionary with extracted content, or None if extraction fails

    Example:
        >>> doc = fetch_pdf_document(
        ...     "https://arxiv.org/pdf/2407.21783.pdf",
        ...     {"max_file_size_mb": 10, "download_timeout_seconds": 120}
        ... )
        >>> if doc:
        ...     print(f"Extracted {len(doc['content'])} characters")
    """
    if not HAS_PDF_PARSER:
        logger.warning("PDF parser not available, cannot fetch PDF documents")
        return None

    if not url:
        return None

    # Use default config if not provided
    if pdf_config is None:
        pdf_config = {
            "max_file_size_mb": 10,
            "download_timeout_seconds": 120,
            "max_extracted_chars": 50000
        }

    try:
        logger.info(f"Fetching PDF document: {url}")

        # Download PDF
        pdf_bytes = pdf_parser.download_pdf(
            url,
            max_size_mb=pdf_config.get("max_file_size_mb", 10),
            timeout=pdf_config.get("download_timeout_seconds", 120)
        )

        # Extract text and tables
        text, tables = pdf_parser.extract_text_from_pdf(pdf_bytes)

        # Check if PDF is readable
        if not pdf_parser.is_pdf_readable(text, min_chars=500):
            logger.warning(f"PDF is unreadable (<500 chars): {url}")
            return None

        # Format tables as text
        table_text = pdf_parser.format_tables_for_ai(tables)

        # Combine text and tables
        full_content = text
        if table_text:
            full_content += "\n\n=== EXTRACTED TABLES ===\n\n" + table_text

        # Truncate if needed
        max_chars = pdf_config.get("max_extracted_chars", 50000)
        full_content = pdf_parser.truncate_content(full_content, max_chars)

        # Compute content hash
        content_hash = pdf_parser.compute_content_hash(full_content)

        # Create document dictionary
        doc = {
            "title": _extract_title_from_url(url),
            "url": url,
            "content": full_content,
            "content_hash": content_hash,
            "doc_type": _classify_document_type(url, ""),
            "source": _extract_source(url),
            "metadata": {
                "fetch_date": datetime.utcnow().isoformat(),
                "char_count": len(full_content),
                "word_count": len(full_content.split()),
                "table_count": len(tables),
                "fetched": True,
                "is_pdf": True
            }
        }

        logger.info(
            f"Successfully extracted PDF: {len(full_content)} chars, "
            f"{len(tables)} tables from {url}"
        )

        return doc

    except ValueError as e:
        logger.warning(f"PDF extraction failed (unreadable/invalid): {url} - {e}")
        return None
    except TimeoutError as e:
        logger.warning(f"PDF download timed out: {url} - {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch PDF document {url}: {e}")
        return None


def _extract_title_from_url(url: str) -> str:
    """
    Extract a reasonable title from a URL.

    Args:
        url: Document URL

    Returns:
        Extracted title
    """
    # Try to get filename
    parts = url.split('/')
    if parts:
        filename = parts[-1]
        # Remove .pdf extension
        if filename.endswith('.pdf'):
            filename = filename[:-4]
        # Clean up the filename
        title = filename.replace('_', ' ').replace('-', ' ')
        return title

    return "Untitled Document"


def is_pdf_url(url: str) -> bool:
    """
    Check if a URL points to a PDF document.

    Args:
        url: URL to check

    Returns:
        True if URL appears to be a PDF, False otherwise

    Example:
        >>> is_pdf_url("https://arxiv.org/pdf/2407.21783.pdf")
        True
        >>> is_pdf_url("https://github.com/user/repo/blob/main/README.md")
        False
    """
    if not url:
        return False

    url_lower = url.lower()

    # Check for .pdf extension
    if url_lower.endswith('.pdf'):
        return True

    # Check for PDF in path (e.g., arxiv.org/pdf/)
    if '/pdf/' in url_lower:
        return True

    # Check for common PDF URL patterns
    pdf_patterns = [
        'arxiv.org/pdf',
        '/download/',
        '/releases/',
        'export=download'
    ]

    return any(pattern in url_lower for pattern in pdf_patterns)
