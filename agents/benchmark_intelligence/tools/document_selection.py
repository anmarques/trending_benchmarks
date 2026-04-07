"""
AI-powered document selection and web-based discovery.

This module provides functionality to:
1. Discover multiple arXiv papers from various sources
2. Use AI to select the most relevant paper
3. Find GitHub repositories via web search (no hardcoded paths)
"""

import logging
import re
from typing import List, Dict, Any, Optional
import requests

from ._claude_client import call_claude, is_anthropic_available

logger = logging.getLogger(__name__)


def extract_all_arxiv_ids(
    model_card_content: str,
    tags: List[str]
) -> List[str]:
    """
    Extract all arXiv IDs from model card content and tags.

    Args:
        model_card_content: Full model card markdown content
        tags: List of model tags from HuggingFace

    Returns:
        List of unique arXiv IDs (e.g., ["2505.09388", "2407.21783"])

    Example:
        >>> tags = ["arxiv:2505.09388", "llm"]
        >>> content = "See our paper: https://arxiv.org/abs/2407.21783"
        >>> ids = extract_all_arxiv_ids(content, tags)
        >>> print(ids)
        ['2505.09388', '2407.21783']
    """
    arxiv_ids = set()

    # Extract from tags
    for tag in tags:
        if tag.startswith('arxiv:'):
            arxiv_id = tag.replace('arxiv:', '')
            arxiv_ids.add(arxiv_id)

    # Extract from content using regex patterns
    # Pattern 1: arxiv.org/abs/2407.21783
    # Pattern 2: arxiv.org/pdf/2407.21783.pdf
    # Pattern 3: arXiv:2407.21783
    patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)',
        r'arXiv[:\s]+(\d+\.\d+)',
        r'ar[xX]iv[:\s]+(\d+\.\d+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, model_card_content, re.IGNORECASE)
        arxiv_ids.update(matches)

    return sorted(list(arxiv_ids))


def fetch_arxiv_abstract(arxiv_id: str) -> Optional[Dict[str, str]]:
    """
    Fetch abstract and metadata for an arXiv paper.

    Args:
        arxiv_id: arXiv identifier (e.g., "2505.09388")

    Returns:
        Dictionary with title, abstract, arxiv_id, or None if fetch fails

    Example:
        >>> abstract = fetch_arxiv_abstract("2505.09388")
        >>> if abstract:
        ...     print(f"{abstract['title']}: {abstract['abstract'][:100]}")
    """
    try:
        # Fetch abstract page
        url = f"https://export.arxiv.org/abs/{arxiv_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        html = response.text

        # Extract title
        title_match = re.search(
            r'<meta name="citation_title" content="([^"]+)"',
            html
        )
        title = title_match.group(1) if title_match else "Unknown Title"

        # Extract abstract
        abstract_match = re.search(
            r'<blockquote[^>]*class="abstract[^"]*"[^>]*>(.*?)</blockquote>',
            html,
            re.DOTALL
        )

        if not abstract_match:
            logger.warning(f"Could not extract abstract from arXiv:{arxiv_id}")
            return None

        abstract_html = abstract_match.group(1)

        # Remove HTML tags
        abstract_text = re.sub(r'<[^>]+>', '', abstract_html)
        # Clean whitespace
        abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
        # Remove "Abstract:" prefix if present
        abstract_text = re.sub(r'^Abstract:\s*', '', abstract_text, flags=re.IGNORECASE)

        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract_text,
            "url": f"https://arxiv.org/abs/{arxiv_id}"
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch abstract for arXiv:{arxiv_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing abstract for arXiv:{arxiv_id}: {e}")
        return None


def search_arxiv_api(
    model_name: str,
    lab_name: str,
    max_results: int = 5
) -> List[str]:
    """
    Search arXiv API for papers about a model.

    Uses arXiv's official API to search for papers matching the model name
    and lab. This is more reliable than web scraping.

    Args:
        model_name: Name of the model (e.g., "Qwen3-8B")
        lab_name: Name of the lab/organization (e.g., "Qwen")
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of arXiv IDs found via API search

    Example:
        >>> ids = search_arxiv_api("Qwen3-8B", "Qwen", max_results=3)
        >>> print(ids)
        ['2505.09388', '2407.21783']
    """
    try:
        import xml.etree.ElementTree as ET
        from urllib.parse import quote

        # Build search query
        # Search for papers containing both model name and lab name
        # Clean model name for search (remove special chars)
        clean_model = re.sub(r'[^\w\s-]', ' ', model_name)
        clean_lab = re.sub(r'[^\w\s-]', ' ', lab_name)

        # arXiv API query format: all:term1+AND+term2
        query = f"all:{quote(clean_model)}+AND+{quote(clean_lab)}"
        url = f"http://export.arxiv.org/api/query?search_query={query}&max_results={max_results}"

        logger.debug(f"Searching arXiv API: {query}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse XML response
        # arXiv API returns Atom XML format
        root = ET.fromstring(response.content)

        # Extract arXiv IDs from entries
        # Namespace for Atom feed
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        arxiv_ids = []
        for entry in root.findall('atom:entry', ns):
            # Get the arXiv ID from the entry ID
            # Format: http://arxiv.org/abs/2505.09388v1
            id_elem = entry.find('atom:id', ns)
            if id_elem is not None:
                entry_id = id_elem.text
                # Extract arXiv ID from URL
                match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', entry_id)
                if match:
                    arxiv_id = match.group(1)
                    arxiv_ids.append(arxiv_id)

        if arxiv_ids:
            logger.info(f"Found {len(arxiv_ids)} papers via arXiv API for {model_name}: {arxiv_ids}")
        else:
            logger.debug(f"No papers found via arXiv API for {model_name}")

        return arxiv_ids

    except requests.exceptions.RequestException as e:
        logger.warning(f"arXiv API search failed for {model_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching arXiv API for {model_name}: {e}")
        return []


def select_best_arxiv_paper(
    abstracts: List[Dict[str, str]],
    model_name: str,
    lab_name: Optional[str] = None
) -> Optional[str]:
    """
    Use AI to select the most relevant arXiv paper from multiple candidates.

    Args:
        abstracts: List of abstract dictionaries from fetch_arxiv_abstract()
        model_name: Name of the model (e.g., "Qwen2.5-7B")
        lab_name: Optional lab/organization name for additional context

    Returns:
        Selected arXiv ID, or None if selection fails

    Example:
        >>> abstracts = [fetch_arxiv_abstract(id) for id in arxiv_ids]
        >>> best_id = select_best_arxiv_paper(abstracts, "Qwen2.5-7B", "Qwen")
    """
    if not abstracts:
        return None

    if len(abstracts) == 1:
        return abstracts[0]["arxiv_id"]

    # Filter out None values
    abstracts = [a for a in abstracts if a is not None]

    if not abstracts:
        return None

    if len(abstracts) == 1:
        return abstracts[0]["arxiv_id"]

    # Check if Claude API is available
    if not is_anthropic_available():
        logger.warning(
            "Anthropic API not available for paper selection, using first paper"
        )
        return abstracts[0]["arxiv_id"]

    # Build prompt for AI selection
    prompt = _build_paper_selection_prompt(abstracts, model_name, lab_name)

    try:
        # Call Claude to analyze and select
        from ._claude_client import call_claude_json

        result = call_claude_json(prompt=prompt, max_tokens=1024)

        selected_id = result.get("selected_arxiv_id")
        reason = result.get("reason", "No reason provided")

        if selected_id:
            logger.info(
                f"AI selected arXiv:{selected_id} from {len(abstracts)} candidates. "
                f"Reason: {reason}"
            )
            return selected_id
        else:
            logger.warning("AI did not return a selection, using first paper")
            return abstracts[0]["arxiv_id"]

    except Exception as e:
        logger.error(f"Failed to select paper with AI: {e}")
        # Fallback to first paper
        return abstracts[0]["arxiv_id"]


def _build_paper_selection_prompt(
    abstracts: List[Dict[str, str]],
    model_name: str,
    lab_name: Optional[str]
) -> str:
    """Build prompt for AI paper selection."""

    # Format abstracts for prompt
    abstracts_text = ""
    for i, abstract in enumerate(abstracts, 1):
        abstracts_text += f"""
Paper {i}:
arXiv ID: {abstract['arxiv_id']}
Title: {abstract['title']}
Abstract: {abstract['abstract']}

---
"""

    lab_context = f" from {lab_name}" if lab_name else ""

    prompt = f"""You are analyzing multiple arXiv papers to select the most relevant one for the model "{model_name}"{lab_context}.

Multiple arXiv papers were found. Your task is to select the PRIMARY technical paper that introduces or describes this specific model.

{abstracts_text}

Instructions:
- Select the paper that is MOST DIRECTLY about the model "{model_name}"
- Prefer papers that:
  1. Introduce/announce the model (not comparison papers)
  2. Have "{model_name}" in the title
  3. Are written by the lab that created the model{lab_context}
  4. Describe the model's architecture and training
- Avoid papers that:
  1. Just cite or compare against the model
  2. Are about different models in the same family
  3. Are general surveys or benchmarks

Return JSON:
{{
  "selected_arxiv_id": "the selected arXiv ID (e.g., '2505.09388')",
  "reason": "brief explanation (1-2 sentences) of why this paper was selected"
}}

IMPORTANT: Return ONLY the JSON, no other text.
"""

    return prompt


def search_github_repository(
    model_name: str,
    lab_name: str,
    max_results: int = 5
) -> Optional[str]:
    """
    Search for GitHub repository URL using web search (no hardcoded paths).

    Uses Google search to find the actual GitHub repository for a model.

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        max_results: Maximum search results to check

    Returns:
        GitHub repository URL if found, None otherwise

    Example:
        >>> url = search_github_repository("Qwen2.5", "Qwen")
        >>> print(url)  # e.g., "https://github.com/QwenLM/Qwen2.5"
    """
    try:
        # Import here to avoid circular dependency
        from .google_search import scrape_google_search

        # Build search query
        query = f"{lab_name} {model_name} github repository"

        logger.info(f"Searching for GitHub repo: {query}")

        results = scrape_google_search(query, max_results=max_results, delay=1.0)

        # Filter for GitHub URLs
        for result in results:
            url = result['url']

            # Check if URL is a GitHub repository
            # Pattern: github.com/org/repo
            match = re.match(r'https://github\.com/([^/]+)/([^/]+)/?', url)

            if match:
                org = match.group(1)
                repo = match.group(2)

                # Skip common false positives
                if repo in ['issues', 'pulls', 'actions', 'wiki', 'discussions']:
                    continue

                # Construct clean repository URL
                clean_url = f"https://github.com/{org}/{repo}"

                logger.info(f"Found GitHub repository: {clean_url}")
                return clean_url

        logger.info(f"No GitHub repository found for {model_name}")
        return None

    except Exception as e:
        logger.error(f"Error searching for GitHub repository: {e}")
        return None


def discover_arxiv_papers_via_search(
    model_name: str,
    lab_name: str,
    max_results: int = 3
) -> List[str]:
    """
    Discover arXiv papers via web search.

    Supplements tag/content extraction with web search to find papers
    that may not be mentioned in the model card.

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        max_results: Maximum number of papers to return

    Returns:
        List of arXiv IDs found via search

    Example:
        >>> ids = discover_arxiv_papers_via_search("Qwen2.5", "Qwen")
        >>> print(ids)  # ['2505.09388', '2407.21783']
    """
    try:
        from .google_search import scrape_google_search

        # Build search query
        query = f"{lab_name} {model_name} arxiv paper"

        logger.info(f"Searching for arXiv papers: {query}")

        results = scrape_google_search(query, max_results=max_results * 2, delay=1.0)

        arxiv_ids = []

        for result in results:
            url = result['url']

            # Extract arXiv ID from URL
            match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)', url)

            if match:
                arxiv_id = match.group(1)
                if arxiv_id not in arxiv_ids:
                    arxiv_ids.append(arxiv_id)

                if len(arxiv_ids) >= max_results:
                    break

        if arxiv_ids:
            logger.info(f"Found {len(arxiv_ids)} arXiv papers via search: {arxiv_ids}")
        else:
            logger.info(f"No arXiv papers found via search for {model_name}")

        return arxiv_ids

    except Exception as e:
        logger.error(f"Error searching for arXiv papers: {e}")
        return []
