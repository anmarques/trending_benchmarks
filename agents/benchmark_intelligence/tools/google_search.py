"""
Google search scraping for document discovery.

This module provides functionality to scrape Google search results to find
documentation related to AI models (arXiv papers, GitHub reports, blogs).
"""

import logging
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def scrape_google_search(
    query: str,
    max_results: int = 10,
    delay: float = 2.0,
    user_agent: Optional[str] = None,
    max_retries: int = 3
) -> List[Dict[str, str]]:
    """
    Scrape Google search results for a given query.

    This function performs a Google search and extracts URLs, titles, and snippets
    from the search results page. It implements retry logic with exponential backoff
    to handle rate limiting and potential blocking.

    NOTE: Google heavily restricts scraping and may return JavaScript-required pages
    or CAPTCHAs. This implementation will skip and return empty results if blocked.
    For production use, consider using Google Custom Search API instead.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
        delay: Delay between searches in seconds (default: 2.0)
        user_agent: Custom User-Agent header (uses default if None)
        max_retries: Maximum number of retries on block/CAPTCHA (default: 3)

    Returns:
        List of dictionaries containing:
            - url: Result URL
            - title: Result title
            - snippet: Result description/snippet

    Example:
        >>> results = scrape_google_search(
        ...     "Qwen2.5 arxiv paper",
        ...     max_results=5
        ... )
        >>> for result in results:
        ...     print(f"{result['title']}: {result['url']}")

    Raises:
        RuntimeError: If all retry attempts fail due to blocking/CAPTCHA
    """
    if not query:
        raise ValueError("Query cannot be empty")

    # Default User-Agent (Mozilla/5.0)
    if user_agent is None:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Build Google search URL
    encoded_query = quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}&num={max_results}"

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    results = []

    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            # Add delay before request (except first attempt)
            if attempt > 0:
                backoff_delay = delay * (2 ** attempt)
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}, waiting {backoff_delay:.1f}s")
                time.sleep(backoff_delay)
            elif delay > 0:
                time.sleep(delay)

            # Make request
            logger.debug(f"Fetching Google search results for: {query}")
            response = requests.get(search_url, headers=headers, timeout=30)

            # Check for blocking/CAPTCHA
            if response.status_code == 429:
                logger.warning(f"Rate limited (429) on attempt {attempt + 1}/{max_retries}")
                continue

            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} on attempt {attempt + 1}/{max_retries}")
                continue

            # Check for CAPTCHA or JavaScript requirement in response
            if "detected unusual traffic" in response.text.lower() or "captcha" in response.text.lower():
                logger.warning(f"CAPTCHA detected on attempt {attempt + 1}/{max_retries}")
                continue

            if "<noscript>" in response.text and "enablejs" in response.text:
                logger.warning(f"JavaScript required (anti-scraping) on attempt {attempt + 1}/{max_retries}")
                continue

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract search results
            # Google search results are in divs with specific classes
            # Note: Google's HTML structure changes, so we try multiple selectors
            search_results = _extract_search_results(soup)

            if not search_results:
                logger.warning(f"No results found for query: {query}")
                return []

            results = search_results[:max_results]
            logger.info(f"Successfully scraped {len(results)} results for query: {query}")
            return results

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
            continue

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed on attempt {attempt + 1}/{max_retries}: {e}")
            continue

        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            if attempt == max_retries - 1:
                raise
            continue

    # All retries failed
    logger.error(f"Failed to scrape Google search after {max_retries} attempts (blocked/CAPTCHA)")
    # Per spec: skip if blocked after retries
    return []


def _extract_search_results(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extract search results from Google search page HTML.

    Tries multiple selectors to handle Google's changing HTML structure.

    Args:
        soup: BeautifulSoup object of search results page

    Returns:
        List of result dictionaries
    """
    results = []

    # Try different selectors for Google search results
    # Modern Google uses div elements with various classes

    # Strategy 1: Look for search result divs (most common)
    search_divs = soup.find_all('div', class_='g')

    if not search_divs:
        # Strategy 2: Try alternative class names
        search_divs = soup.find_all('div', attrs={'data-sokoban-container': True})

    if not search_divs:
        # Strategy 3: Look for any div containing a link with cite element
        search_divs = soup.find_all('div', recursive=True)
        search_divs = [div for div in search_divs if div.find('a') and div.find('cite')]

    for div in search_divs:
        try:
            # Extract link
            link_elem = div.find('a', href=True)
            if not link_elem:
                continue

            url = link_elem.get('href', '')

            # Filter out non-http URLs (internal Google links, etc.)
            if not url.startswith('http'):
                continue

            # Skip Google's internal links
            if 'google.com' in url and '/search?' in url:
                continue

            # Extract title
            # Title is usually in an h3 element
            title_elem = div.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else ''

            # If no h3, try getting text from the link
            if not title:
                title = link_elem.get_text(strip=True)

            # Extract snippet/description
            # Usually in a div with specific classes or data attributes
            snippet = ''

            # Try multiple snippet selectors
            snippet_selectors = [
                {'class_': 'VwiC3b'},  # Common snippet class
                {'class_': 'st'},       # Older snippet class
                {'attrs': {'data-content-feature': '1'}},  # Data attribute
                {'class_': 'IsZvec'},   # Another variant
            ]

            for selector in snippet_selectors:
                snippet_elem = div.find('div', **selector) if 'class_' in selector else div.find('div', **selector)
                if snippet_elem:
                    snippet = snippet_elem.get_text(strip=True)
                    break

            # If still no snippet, try getting any div text that's not the title
            if not snippet:
                text_divs = div.find_all('div')
                for text_div in text_divs:
                    text = text_div.get_text(strip=True)
                    if text and text != title and len(text) > 20:
                        snippet = text
                        break

            # Only add if we have at least a URL and title
            if url and title:
                results.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet or ''
                })

        except Exception as e:
            logger.debug(f"Error extracting result from div: {e}")
            continue

    return results


def search_arxiv_paper(
    model_name: str,
    lab_name: str,
    max_results: int = 5,
    delay: float = 2.0
) -> Optional[str]:
    """
    Search for arXiv paper URL for a specific model.

    Uses Google search to find arXiv papers related to the model.
    Filters results to arxiv.org URLs only.

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        max_results: Maximum search results to check
        delay: Delay between searches in seconds

    Returns:
        arXiv PDF URL if found, None otherwise

    Example:
        >>> url = search_arxiv_paper("Llama-3.1", "meta-llama")
        >>> if url:
        ...     print(f"Found paper: {url}")
    """
    query = f'"{model_name}" {lab_name} arxiv pdf'

    try:
        results = scrape_google_search(query, max_results=max_results, delay=delay)

        # Filter for arxiv.org URLs
        for result in results:
            url = result['url']
            if 'arxiv.org' in url.lower():
                # Convert to PDF URL if it's an abstract page
                if '/abs/' in url:
                    url = url.replace('/abs/', '/pdf/') + '.pdf'
                elif '/pdf/' not in url:
                    # Try to construct PDF URL
                    arxiv_id = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)', url)
                    if arxiv_id:
                        url = f"https://arxiv.org/pdf/{arxiv_id.group(1)}.pdf"

                logger.info(f"Found arXiv paper for {model_name}: {url}")
                return url

        logger.info(f"No arXiv paper found for {model_name}")
        return None

    except Exception as e:
        logger.error(f"Error searching for arXiv paper: {e}")
        return None


def search_github_pdf(
    model_name: str,
    lab_name: str,
    github_org: Optional[str] = None,
    max_results: int = 5,
    delay: float = 2.0
) -> Optional[str]:
    """
    Search for GitHub-hosted PDF technical reports.

    Searches for PDF files in GitHub repositories related to the model.

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        github_org: GitHub organization name (if different from lab_name)
        max_results: Maximum search results to check
        delay: Delay between searches in seconds

    Returns:
        GitHub PDF URL if found, None otherwise

    Example:
        >>> url = search_github_pdf("Llama-3", "meta-llama")
        >>> if url:
        ...     print(f"Found report: {url}")
    """
    org = github_org or lab_name
    query = f'"{model_name}" {org} github technical report pdf'

    try:
        results = scrape_google_search(query, max_results=max_results, delay=delay)

        # Filter for GitHub PDF URLs
        for result in results:
            url = result['url']
            if 'github.com' in url.lower() and url.lower().endswith('.pdf'):
                logger.info(f"Found GitHub PDF for {model_name}: {url}")
                return url

        logger.info(f"No GitHub PDF found for {model_name}")
        return None

    except Exception as e:
        logger.error(f"Error searching for GitHub PDF: {e}")
        return None


def search_blog_posts(
    model_name: str,
    lab_name: str,
    max_results: int = 5,
    delay: float = 2.0
) -> List[Dict[str, str]]:
    """
    Search for official blog posts and announcements about a model.

    Uses Google search to find blog posts from any domain.
    Does not restrict to specific lab domains.

    Args:
        model_name: Name of the model
        lab_name: Name of the lab/organization
        max_results: Maximum number of results to return
        delay: Delay between searches in seconds

    Returns:
        List of blog post dictionaries with url, title, snippet

    Example:
        >>> posts = search_blog_posts("Qwen2.5", "Qwen")
        >>> for post in posts:
        ...     print(f"{post['title']}: {post['url']}")
    """
    query = f'"{lab_name}" "{model_name}" announcement'

    try:
        results = scrape_google_search(query, max_results=max_results, delay=delay)

        # Filter out non-blog URLs (documentation, GitHub, etc.)
        blog_results = []
        for result in results:
            url = result['url'].lower()
            # Skip technical documentation sites
            if any(skip in url for skip in ['github.com', 'arxiv.org', 'huggingface.co/docs']):
                continue
            blog_results.append(result)

        logger.info(f"Found {len(blog_results)} blog posts for {model_name}")
        return blog_results

    except Exception as e:
        logger.error(f"Error searching for blog posts: {e}")
        return []


def get_arxiv_metadata(arxiv_url: str) -> Optional[Dict[str, any]]:
    """
    Fetch metadata for an arXiv paper including authors.

    This function fetches the arXiv abstract page to extract author information,
    which can be used to verify that the paper is from the correct lab.

    Args:
        arxiv_url: arXiv URL (abstract or PDF)

    Returns:
        Dictionary with metadata including:
            - title: Paper title
            - authors: List of author names
            - abstract: Paper abstract
            - arxiv_id: arXiv identifier
        Returns None if metadata cannot be fetched

    Example:
        >>> metadata = get_arxiv_metadata("https://arxiv.org/abs/2407.21783")
        >>> if metadata:
        ...     print(f"Authors: {', '.join(metadata['authors'])}")
    """
    try:
        # Convert PDF URL to abstract URL
        if '/pdf/' in arxiv_url:
            abstract_url = arxiv_url.replace('/pdf/', '/abs/').replace('.pdf', '')
        else:
            abstract_url = arxiv_url

        # Extract arXiv ID
        arxiv_id_match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)', abstract_url)
        if not arxiv_id_match:
            logger.warning(f"Could not extract arXiv ID from URL: {arxiv_url}")
            return None

        arxiv_id = arxiv_id_match.group(1)

        # Fetch abstract page
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(abstract_url, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.warning(f"Failed to fetch arXiv metadata: HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title_elem = soup.find('h1', class_='title')
        title = title_elem.get_text(strip=True).replace('Title:', '').strip() if title_elem else ''

        # Extract authors
        authors = []
        authors_div = soup.find('div', class_='authors')
        if authors_div:
            author_links = authors_div.find_all('a')
            authors = [link.get_text(strip=True) for link in author_links]

        # Extract abstract
        abstract_elem = soup.find('blockquote', class_='abstract')
        abstract = abstract_elem.get_text(strip=True).replace('Abstract:', '').strip() if abstract_elem else ''

        metadata = {
            'arxiv_id': arxiv_id,
            'title': title,
            'authors': authors,
            'abstract': abstract
        }

        logger.info(f"Fetched metadata for arXiv:{arxiv_id}, {len(authors)} authors")
        return metadata

    except Exception as e:
        logger.error(f"Error fetching arXiv metadata: {e}")
        return None


def filter_arxiv_by_authors(
    arxiv_urls: List[str],
    lab_name: str
) -> Optional[str]:
    """
    Filter arXiv papers by checking if authors include lab members.

    Given multiple arXiv URLs, fetches metadata for each and returns
    the URL of the paper whose authors include the lab name.

    Args:
        arxiv_urls: List of arXiv URLs to check
        lab_name: Lab name to search for in author affiliations

    Returns:
        URL of the paper with matching authors, or first URL if none match

    Example:
        >>> urls = ["https://arxiv.org/abs/2407.21783", "https://arxiv.org/abs/1234.5678"]
        >>> url = filter_arxiv_by_authors(urls, "meta")
    """
    if not arxiv_urls:
        return None

    if len(arxiv_urls) == 1:
        return arxiv_urls[0]

    lab_name_lower = lab_name.lower()

    for url in arxiv_urls:
        metadata = get_arxiv_metadata(url)
        if not metadata or not metadata.get('authors'):
            continue

        # Check if any author name contains the lab name
        for author in metadata['authors']:
            if lab_name_lower in author.lower():
                logger.info(f"Selected arXiv paper with author matching '{lab_name}': {url}")
                return url

    # No author match found, return first URL
    logger.info(f"No author match found for '{lab_name}', using first result")
    return arxiv_urls[0]
