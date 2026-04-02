"""
Enhanced documentation fetcher with Google search integration.

This module extends fetch_docs.py with Google search-based document discovery
for arXiv papers, GitHub PDFs, and blog posts.
"""

import logging
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Import Google search functionality
try:
    from .google_search import (
        search_arxiv_paper,
        search_github_pdf,
        search_blog_posts,
        filter_arxiv_by_authors,
        get_arxiv_metadata
    )
    HAS_GOOGLE_SEARCH = True
except ImportError:
    HAS_GOOGLE_SEARCH = False
    logger.warning("Google search not available")


def fetch_model_card(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch model card from HuggingFace.

    Args:
        model_id: Full model ID (e.g., "Qwen/Qwen2.5-7B")

    Returns:
        Document dictionary or None if not found
    """
    url = f"https://huggingface.co/{model_id}/raw/main/README.md"

    try:
        logger.debug(f"Fetching model card: {url}")
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            logger.warning(f"Model card not found (HTTP {response.status_code})")
            return None

        content = response.text

        # Check for arXiv URLs in model card
        arxiv_urls = _extract_arxiv_urls(content)

        doc = {
            "title": f"{model_id} - Model Card",
            "url": url,
            "content": content,
            "doc_type": "model_card",
            "source": "HuggingFace",
            "metadata": {
                "fetch_date": datetime.utcnow().isoformat(),
                "word_count": len(content.split()),
                "char_count": len(content),
                "fetched": True,
                "arxiv_urls_found": arxiv_urls
            }
        }

        logger.info(f"Fetched model card for {model_id}")
        return doc

    except Exception as e:
        logger.error(f"Failed to fetch model card: {e}")
        return None


def fetch_arxiv_paper(
    model_name: str,
    lab_name: str,
    model_card_doc: Optional[Dict[str, Any]] = None,
    config: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch arXiv paper for a model.

    Strategy:
    1. Check model card for arxiv.org URLs first
    2. If found, use that URL directly (use only first paper)
    3. If not found, use Google search
    4. If multiple papers found, filter by authors matching lab name

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        model_card_doc: Optional model card document (to extract URLs)
        config: Optional configuration dict with google_search settings

    Returns:
        Document dictionary or None if not found
    """
    if not HAS_GOOGLE_SEARCH:
        logger.warning("Google search not available, cannot fetch arXiv papers")
        return None

    arxiv_url = None

    # Step 1: Check model card for arXiv URLs
    if model_card_doc and model_card_doc.get("metadata", {}).get("arxiv_urls_found"):
        arxiv_urls = model_card_doc["metadata"]["arxiv_urls_found"]
        if arxiv_urls:
            arxiv_url = arxiv_urls[0]  # Use first URL found
            logger.info(f"Found arXiv URL in model card: {arxiv_url}")

    # Step 2: If not found in model card, use Google search
    if not arxiv_url:
        logger.info(f"Searching Google for arXiv paper: {model_name}")

        # Get config settings
        delay = 2.0
        max_results = 5
        if config and "google_search" in config:
            delay = config["google_search"].get("delay_between_searches", 2.0)
            max_results = config["google_search"].get("max_results_per_query", 10)

        arxiv_url = search_arxiv_paper(
            model_name=model_name,
            lab_name=lab_name,
            max_results=max_results,
            delay=delay
        )

    if not arxiv_url:
        logger.info(f"No arXiv paper found for {model_name}")
        return None

    # Step 3: Download and return document metadata
    # Note: Actual PDF parsing happens later in the pipeline
    doc = {
        "title": f"{model_name} - arXiv Paper",
        "url": arxiv_url,
        "content": None,  # PDF content extracted later
        "doc_type": "arxiv_paper",
        "source": "arXiv",
        "metadata": {
            "fetch_date": datetime.utcnow().isoformat(),
            "fetched": False,  # PDF parsing happens in separate step
            "requires_pdf_parsing": True
        }
    }

    logger.info(f"Found arXiv paper for {model_name}: {arxiv_url}")
    return doc


def fetch_github_pdf(
    model_name: str,
    lab_name: str,
    model_card_doc: Optional[Dict[str, Any]] = None,
    config: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch GitHub-hosted PDF technical reports.

    Strategy:
    1. Check model card for GitHub repo links
    2. Try known URL patterns (releases, docs folders)
    3. If not found, use Google search

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        model_card_doc: Optional model card document
        config: Optional configuration dict

    Returns:
        Document dictionary or None if not found
    """
    if not HAS_GOOGLE_SEARCH:
        logger.warning("Google search not available, cannot fetch GitHub PDFs")
        return None

    # Try known patterns first
    github_org = _get_github_org(lab_name)
    known_patterns = [
        f"https://github.com/{github_org}/{model_name}/releases/download/v1.0/{model_name}_report.pdf",
        f"https://github.com/{github_org}/{model_name}/blob/main/docs/technical_report.pdf",
        f"https://github.com/{github_org}/{model_name}/blob/main/report.pdf",
    ]

    for url in known_patterns:
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                logger.info(f"Found GitHub PDF at known pattern: {url}")
                return {
                    "title": f"{model_name} - GitHub Technical Report",
                    "url": url,
                    "content": None,
                    "doc_type": "github_pdf",
                    "source": f"GitHub/{github_org}",
                    "metadata": {
                        "fetch_date": datetime.utcnow().isoformat(),
                        "fetched": False,
                        "requires_pdf_parsing": True
                    }
                }
        except:
            continue

    # Use Google search as fallback
    logger.info(f"Searching Google for GitHub PDF: {model_name}")

    delay = 2.0
    max_results = 5
    if config and "google_search" in config:
        delay = config["google_search"].get("delay_between_searches", 2.0)
        max_results = config["google_search"].get("max_results_per_query", 10)

    pdf_url = search_github_pdf(
        model_name=model_name,
        lab_name=lab_name,
        github_org=github_org,
        max_results=max_results,
        delay=delay
    )

    if not pdf_url:
        logger.info(f"No GitHub PDF found for {model_name}")
        return None

    doc = {
        "title": f"{model_name} - GitHub Technical Report",
        "url": pdf_url,
        "content": None,
        "doc_type": "github_pdf",
        "source": f"GitHub/{github_org}",
        "metadata": {
            "fetch_date": datetime.utcnow().isoformat(),
            "fetched": False,
            "requires_pdf_parsing": True
        }
    }

    logger.info(f"Found GitHub PDF for {model_name}: {pdf_url}")
    return doc


def fetch_blog_posts(
    model_name: str,
    lab_name: str,
    config: Optional[Dict] = None,
    max_posts: int = 3
) -> List[Dict[str, Any]]:
    """
    Fetch official blog posts and announcements.

    Uses Google search only (no domain restrictions).

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        config: Optional configuration dict
        max_posts: Maximum number of posts to fetch

    Returns:
        List of blog post documents
    """
    if not HAS_GOOGLE_SEARCH:
        logger.warning("Google search not available, cannot fetch blog posts")
        return []

    logger.info(f"Searching Google for blog posts: {model_name}")

    delay = 2.0
    max_results = 5
    if config and "google_search" in config:
        delay = config["google_search"].get("delay_between_searches", 2.0)
        max_results = config["google_search"].get("max_results_per_query", 10)

    search_results = search_blog_posts(
        model_name=model_name,
        lab_name=lab_name,
        max_results=max_results,
        delay=delay
    )

    documents = []
    for result in search_results[:max_posts]:
        # Fetch content
        content = _fetch_html_content(result['url'])

        doc = {
            "title": result.get("title", "Blog Post"),
            "url": result["url"],
            "content": content,
            "doc_type": "blog_post",
            "source": _extract_domain(result["url"]),
            "metadata": {
                "fetch_date": datetime.utcnow().isoformat(),
                "snippet": result.get("snippet", ""),
                "word_count": len(content.split()) if content else 0,
                "fetched": content is not None
            }
        }

        documents.append(doc)
        logger.info(f"Fetched blog post: {result['url']}")

    return documents


def fetch_all_documentation(
    model_id: str,
    model_name: str,
    lab_name: str,
    config: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Fetch all available documentation for a model.

    This is the main entry point that orchestrates fetching from all sources:
    1. Model card (HuggingFace) - always fetch
    2. arXiv paper - check model card first, else Google search
    3. GitHub PDF - try known patterns, else Google search
    4. Blog posts - Google search only

    Args:
        model_id: Full model ID (e.g., "Qwen/Qwen2.5-7B")
        model_name: Model name (e.g., "Qwen2.5-7B")
        lab_name: Lab/organization name
        config: Optional configuration dict

    Returns:
        List of all fetched documents
    """
    documents = []

    # 1. Fetch model card (always)
    logger.info(f"Fetching documentation for {model_id}")
    model_card = fetch_model_card(model_id)
    if model_card:
        documents.append(model_card)

    # 2. Fetch arXiv paper (if available)
    arxiv_doc = fetch_arxiv_paper(
        model_name=model_name,
        lab_name=lab_name,
        model_card_doc=model_card,
        config=config
    )
    if arxiv_doc:
        documents.append(arxiv_doc)

    # 3. Fetch GitHub PDF (if available)
    github_doc = fetch_github_pdf(
        model_name=model_name,
        lab_name=lab_name,
        model_card_doc=model_card,
        config=config
    )
    if github_doc:
        documents.append(github_doc)

    # 4. Fetch blog posts
    blog_docs = fetch_blog_posts(
        model_name=model_name,
        lab_name=lab_name,
        config=config,
        max_posts=3
    )
    documents.extend(blog_docs)

    logger.info(f"Fetched {len(documents)} documents for {model_id}")
    return documents


# Helper functions

def _extract_arxiv_urls(content: str) -> List[str]:
    """Extract arXiv URLs from text content."""
    urls = []

    # Pattern for arXiv URLs
    patterns = [
        r'https?://arxiv\.org/(?:abs|pdf)/(\d+\.\d+)',
        r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            arxiv_id = match.group(1)
            url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            if url not in urls:
                urls.append(url)

    return urls


def _get_github_org(lab_name: str) -> str:
    """Map lab name to GitHub organization name."""
    mapping = {
        "Qwen": "QwenLM",
        "meta-llama": "meta-llama",
        "mistralai": "mistralai",
        "google": "google-research",
        "microsoft": "microsoft",
        "deepseek-ai": "deepseek-ai",
        "OpenGVLab": "OpenGVLab",
        "THUDM": "THUDM",
        "01-ai": "01-ai",
        "internlm": "InternLM",
    }

    return mapping.get(lab_name, lab_name)


def _fetch_html_content(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch and extract text content from HTML page."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=timeout)

        if response.status_code != 200:
            logger.warning(f"Failed to fetch HTML (HTTP {response.status_code}): {url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script, style, nav, header, footer
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        # Get text
        text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        # Limit size
        if len(text) > 50000:
            logger.warning(f"Content too large ({len(text)} chars), truncating to 50K")
            text = text[:50000]

        return text

    except Exception as e:
        logger.error(f"Error fetching HTML content: {e}")
        return None


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if match:
        domain = match.group(1)

        # Map to friendly names
        if "huggingface.co" in domain:
            return "HuggingFace"
        elif "arxiv.org" in domain:
            return "arXiv"
        elif "github.com" in domain:
            org_match = re.search(r'github\.com/([^/]+)', url)
            if org_match:
                return f"GitHub/{org_match.group(1)}"
            return "GitHub"

        return domain

    return "unknown"
