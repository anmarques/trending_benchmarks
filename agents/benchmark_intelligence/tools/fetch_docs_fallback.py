"""
Fallback web fetching using requests library (no MCP tools required).

This provides a simple implementation for fetching documentation
when WebSearch/WebFetch MCP tools are not available.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)


def search_and_fetch_simple(
    model_name: str,
    labs_to_search: List[str] = None,
    max_docs: int = 5
) -> List[Dict[str, Any]]:
    """
    Simple documentation fetcher using known URL patterns.
    
    Instead of web search, constructs URLs for known documentation sources:
    - GitHub repositories
    - ArXiv papers
    - HuggingFace model pages
    - Official blogs
    
    Args:
        model_name: Model name
        labs_to_search: List of lab names
        max_docs: Maximum documents to fetch
        
    Returns:
        List of document dictionaries
    """
    documents = []
    
    # Construct potential URLs based on known patterns
    urls_to_try = _build_known_urls(model_name, labs_to_search)
    
    for url, doc_type in urls_to_try:
        if len(documents) >= max_docs:
            break
            
        try:
            logger.debug(f"Trying URL: {url}")
            
            content = _fetch_url_content(url)
            if content and len(content) > 500:  # Minimum content threshold
                doc = {
                    "title": _extract_title(content, url),
                    "url": url,
                    "content": content,
                    "doc_type": doc_type,
                    "source": _extract_domain(url),
                    "metadata": {
                        "fetch_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "word_count": len(content.split()),
                        "fetched": True
                    }
                }
                documents.append(doc)
                logger.info(f"Fetched: {url}")
                
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            continue
    
    return documents


def _build_known_urls(model_name: str, labs: List[str] = None) -> List[tuple]:
    """
    Build list of (URL, doc_type) tuples for known documentation sources.
    """
    urls = []
    
    # Clean model name
    model_clean = model_name.replace(" ", "-").replace("_", "-")
    
    # HuggingFace raw README (better than model page)
    if labs:
        for lab in labs[:1]:  # Primary lab only
            urls.append((
                f"https://huggingface.co/{lab}/{model_clean}/raw/main/README.md",
                "model_card"
            ))
    
    # GitHub README (often has more details than HF)
    if labs:
        for lab in labs[:1]:
            github_orgs = {
                "Qwen": ["QwenLM", "Qwen"],
                "meta-llama": ["meta-llama", "facebookresearch"],
                "mistralai": ["mistralai"],
                "google": ["google-research", "google-deepmind"],
                "microsoft": ["microsoft"],
                "deepseek-ai": ["deepseek-ai"],
                "OpenGVLab": ["OpenGVLab"],
            }
            
            for github_org in github_orgs.get(lab, [lab]):
                urls.append((
                    f"https://raw.githubusercontent.com/{github_org}/{model_clean}/main/README.md",
                    "technical_report"
                ))
    
    # Note: Skipping arXiv search for now - search results pages are too large
    # and require parsing. Will add proper paper search later.
    
    return urls


def _fetch_url_content(url: str, timeout: int = 10) -> str:
    """
    Fetch and extract text content from a URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; BenchmarkIntelligence/1.0)"
    }
    
    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # Get text
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = '\n'.join(lines)
    
    # Limit size to avoid overwhelming Claude (max ~50K chars)
    if len(text) > 50000:
        logger.warning(f"Content too large ({len(text)} chars), truncating to 50K")
        text = text[:50000] + "\n\n[Content truncated due to length]"
    
    return text


def _extract_title(content: str, url: str) -> str:
    """Extract title from content or URL."""
    lines = content.split('\n')
    for line in lines[:20]:  # Check first 20 lines
        if line and len(line) < 200:  # Reasonable title length
            return line
    return url.split('/')[-1]


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    import re
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return match.group(1) if match else "unknown"
