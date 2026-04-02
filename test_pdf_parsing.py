#!/usr/bin/env python3
"""
Test script for PDF parsing functionality.
Tests downloading and extracting content from a sample arXiv PDF.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.benchmark_intelligence.tools import pdf_parser
from agents.benchmark_intelligence.tools.fetch_docs import fetch_pdf_document, is_pdf_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pdf_url_detection():
    """Test PDF URL detection."""
    print("\n=== Testing PDF URL Detection ===")

    test_urls = [
        ("https://arxiv.org/pdf/2407.21783.pdf", True),
        ("https://arxiv.org/pdf/2407.21783", True),
        ("https://github.com/user/repo/blob/main/README.md", False),
        ("https://example.com/document.pdf", True),
        ("https://huggingface.co/model/card", False),
    ]

    for url, expected in test_urls:
        result = is_pdf_url(url)
        status = "✓" if result == expected else "✗"
        print(f"{status} {url}: {result} (expected {expected})")


def test_pdf_download_and_extraction():
    """Test downloading and extracting a real arXiv PDF."""
    print("\n=== Testing PDF Download and Extraction ===")

    # Use a well-known arXiv paper (Llama 3.1)
    test_url = "https://arxiv.org/pdf/2407.21783.pdf"

    print(f"Testing with: {test_url}")

    try:
        # Download PDF
        print("Downloading PDF...")
        pdf_bytes = pdf_parser.download_pdf(
            test_url,
            max_size_mb=10,
            timeout=120
        )
        print(f"✓ Downloaded {len(pdf_bytes)} bytes")

        # Extract text and tables
        print("Extracting text and tables...")
        text, tables = pdf_parser.extract_text_from_pdf(pdf_bytes)
        print(f"✓ Extracted {len(text)} characters")
        print(f"✓ Found {len(tables)} tables")

        # Check readability
        is_readable = pdf_parser.is_pdf_readable(text)
        print(f"✓ PDF is {'readable' if is_readable else 'unreadable'}")

        # Show sample of extracted text
        print("\nFirst 500 characters of extracted text:")
        print("-" * 60)
        print(text[:500])
        print("-" * 60)

        # Compute hash
        content_hash = pdf_parser.compute_content_hash(text)
        print(f"\nContent hash: {content_hash}")

        # Test truncation
        truncated = pdf_parser.truncate_content(text, max_chars=1000)
        print(f"\nTruncated to {len(truncated)} characters (from {len(text)})")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fetch_pdf_document():
    """Test the integrated fetch_pdf_document function."""
    print("\n=== Testing Integrated PDF Fetching ===")

    test_url = "https://arxiv.org/pdf/2407.21783.pdf"

    pdf_config = {
        "max_file_size_mb": 10,
        "download_timeout_seconds": 120,
        "max_extracted_chars": 50000
    }

    try:
        doc = fetch_pdf_document(test_url, pdf_config)

        if doc:
            print("✓ Successfully fetched PDF document")
            print(f"  Title: {doc['title']}")
            print(f"  URL: {doc['url']}")
            print(f"  Type: {doc['doc_type']}")
            print(f"  Source: {doc['source']}")
            print(f"  Content length: {len(doc['content'])} chars")
            print(f"  Content hash: {doc['content_hash']}")
            print(f"  Tables: {doc['metadata']['table_count']}")
            print(f"  Word count: {doc['metadata']['word_count']}")

            # Show a sample of content
            print("\nFirst 300 characters of content:")
            print("-" * 60)
            print(doc['content'][:300])
            print("-" * 60)

            return True
        else:
            print("✗ Failed to fetch PDF document")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("PDF Parsing Test Suite")
    print("=" * 70)

    results = []

    # Test 1: URL detection
    test_pdf_url_detection()

    # Test 2: Download and extraction
    print("\nNote: This test will download a real PDF from arXiv.")
    print("This may take a few seconds...")
    result1 = test_pdf_download_and_extraction()
    results.append(("PDF download and extraction", result1))

    # Test 3: Integrated function
    result2 = test_fetch_pdf_document()
    results.append(("Integrated PDF fetching", result2))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
