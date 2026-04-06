"""
PDF parsing utilities for extracting text and tables from PDF documents.

This module provides functionality to download and parse PDF files from URLs,
using pdfplumber as the primary library with PyPDF2 as a fallback.
"""

import logging
import hashlib
from typing import Tuple, List, Optional
import io
import requests

logger = logging.getLogger(__name__)

# Try importing PDF libraries
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.warning("pdfplumber not installed - PDF parsing limited to PyPDF2")

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    logger.warning("PyPDF2 not installed - PDF parsing disabled")


def download_pdf(
    url: str,
    max_size_mb: int = 10,
    timeout: int = 120
) -> bytes:
    """
    Download a PDF file from a URL with size and timeout constraints.

    Args:
        url: URL of the PDF file to download
        max_size_mb: Maximum file size in megabytes (default: 10)
        timeout: Download timeout in seconds (default: 120)

    Returns:
        PDF file content as bytes

    Raises:
        ValueError: If URL is invalid or file is too large
        requests.RequestException: If download fails
        TimeoutError: If download exceeds timeout

    Example:
        >>> pdf_bytes = download_pdf("https://arxiv.org/pdf/2407.21783.pdf")
        >>> print(f"Downloaded {len(pdf_bytes)} bytes")
    """
    if not url or not isinstance(url, str):
        raise ValueError("url must be a non-empty string")

    if not url.lower().endswith('.pdf') and 'pdf' not in url.lower():
        logger.warning(f"URL may not be a PDF: {url}")

    logger.info(f"Downloading PDF from: {url}")

    try:
        # Make HEAD request first to check file size
        head_response = requests.head(url, timeout=30, allow_redirects=True)
        head_response.raise_for_status()

        content_length = head_response.headers.get('Content-Length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > max_size_mb:
                raise ValueError(
                    f"PDF file too large: {size_mb:.2f}MB exceeds {max_size_mb}MB limit"
                )
            logger.debug(f"PDF size: {size_mb:.2f}MB")

        # Download the PDF file
        response = requests.get(
            url,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            stream=True
        )
        response.raise_for_status()

        # Check actual size during download
        pdf_bytes = b''
        max_bytes = max_size_mb * 1024 * 1024

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                pdf_bytes += chunk
                if len(pdf_bytes) > max_bytes:
                    raise ValueError(
                        f"PDF file exceeds {max_size_mb}MB limit during download"
                    )

        logger.info(f"Downloaded {len(pdf_bytes)} bytes from {url}")
        return pdf_bytes

    except requests.Timeout:
        raise TimeoutError(f"PDF download timed out after {timeout} seconds: {url}")
    except requests.RequestException as e:
        logger.error(f"Failed to download PDF from {url}: {e}")
        raise


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, List]:
    """
    Extract text and tables from a PDF file.

    Tries pdfplumber first (better table extraction), falls back to PyPDF2
    if pdfplumber fails or is not available.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Tuple of (extracted_text, tables):
            - extracted_text: Full text content as string
            - tables: List of tables (each table is a list of lists)

    Raises:
        ValueError: If PDF cannot be parsed by either library
        RuntimeError: If no PDF parsing libraries are available

    Example:
        >>> text, tables = extract_text_from_pdf(pdf_bytes)
        >>> print(f"Extracted {len(text)} characters and {len(tables)} tables")
    """
    if not HAS_PDFPLUMBER and not HAS_PYPDF2:
        raise RuntimeError(
            "No PDF parsing libraries available. "
            "Install pdfplumber or PyPDF2: pip install pdfplumber PyPDF2"
        )

    if not pdf_bytes:
        raise ValueError("pdf_bytes cannot be empty")

    # Try pdfplumber first (better table extraction)
    if HAS_PDFPLUMBER:
        try:
            logger.debug("Attempting PDF extraction with pdfplumber")
            return _extract_with_pdfplumber(pdf_bytes)
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            if HAS_PYPDF2:
                logger.info("Falling back to PyPDF2")
            else:
                raise ValueError(f"Failed to extract PDF with pdfplumber: {e}")

    # Fallback to PyPDF2
    if HAS_PYPDF2:
        try:
            logger.debug("Attempting PDF extraction with PyPDF2")
            return _extract_with_pypdf2(pdf_bytes)
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            raise ValueError(f"Failed to extract PDF with PyPDF2: {e}")

    raise RuntimeError("No PDF extraction succeeded")


def _extract_with_pdfplumber(pdf_bytes: bytes) -> Tuple[str, List]:
    """
    Extract text and tables using pdfplumber.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Tuple of (text, tables)
    """
    text_parts = []
    all_tables = []

    pdf_file = io.BytesIO(pdf_bytes)

    with pdfplumber.open(pdf_file) as pdf:
        logger.debug(f"PDF has {len(pdf.pages)} pages")

        for page_num, page in enumerate(pdf.pages, 1):
            # Extract text from page
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

            # Extract tables from page
            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)
                logger.debug(f"Page {page_num}: extracted {len(tables)} tables")

    full_text = '\n'.join(text_parts)
    logger.info(
        f"pdfplumber extracted {len(full_text)} characters "
        f"and {len(all_tables)} tables"
    )

    return full_text, all_tables


def _extract_with_pypdf2(pdf_bytes: bytes) -> Tuple[str, List]:
    """
    Extract text using PyPDF2 (no table extraction).

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Tuple of (text, empty_tables_list)
    """
    text_parts = []

    pdf_file = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)

    logger.debug(f"PDF has {len(reader.pages)} pages")

    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    full_text = '\n'.join(text_parts)
    logger.info(f"PyPDF2 extracted {len(full_text)} characters (no table support)")

    # PyPDF2 doesn't support table extraction
    return full_text, []


def truncate_content(text: str, max_chars: int = 50000) -> str:
    """
    Truncate text content to maximum character limit.

    Args:
        text: Text content to truncate
        max_chars: Maximum number of Unicode characters (default: 50000)

    Returns:
        Truncated text (or original if under limit)

    Example:
        >>> truncated = truncate_content(long_text, max_chars=10000)
        >>> print(f"Text length: {len(truncated)} chars")
    """
    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    logger.info(f"Truncating text from {len(text)} to {max_chars} characters")
    truncated = text[:max_chars]

    # Add truncation marker
    truncated += "\n\n[... content truncated ...]"

    return truncated


def compute_content_hash(text: str) -> str:
    """
    Compute SHA256 hash of text content for change detection.

    Args:
        text: Text content to hash

    Returns:
        Hexadecimal hash string

    Example:
        >>> hash_value = compute_content_hash(extracted_text)
        >>> print(f"Content hash: {hash_value}")
    """
    if not text:
        return hashlib.sha256(b'').hexdigest()

    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def is_pdf_readable(text: str, min_chars: int = 500) -> bool:
    """
    Check if extracted PDF text is readable (not image-only or corrupted).

    Args:
        text: Extracted text content
        min_chars: Minimum character threshold for readability (default: 500)

    Returns:
        True if text is readable, False otherwise

    Example:
        >>> if is_pdf_readable(extracted_text):
        ...     process_content(extracted_text)
        ... else:
        ...     logger.warning("PDF is unreadable")
    """
    if not text:
        return False

    return len(text.strip()) >= min_chars


def format_tables_for_ai(tables: List) -> str:
    """
    Format extracted tables as text for AI processing.

    Converts table data structures to a readable text format that can be
    sent to AI models for analysis.

    Args:
        tables: List of tables (each table is a list of lists)

    Returns:
        Formatted table text

    Example:
        >>> table_text = format_tables_for_ai(tables)
        >>> combined = extracted_text + "\\n\\n" + table_text
    """
    if not tables:
        return ""

    formatted_parts = []

    for table_num, table in enumerate(tables, 1):
        if not table:
            continue

        formatted_parts.append(f"\n--- Table {table_num} ---")

        for row in table:
            if row:
                # Join cells with | separator
                row_text = " | ".join(str(cell or "").strip() for cell in row)
                formatted_parts.append(row_text)

        formatted_parts.append("")  # Empty line after table

    return '\n'.join(formatted_parts)
