"""
Model card parser for extracting structured data from HuggingFace model cards.

This module provides functionality to fetch and parse model cards (README files)
from HuggingFace models.
"""

import logging
from typing import Dict, Any, Optional, List
import re

from ..clients.factory import get_hf_client
from ..clients.base import HFClientBase


logger = logging.getLogger(__name__)


def parse_model_card(
    model_id: str,
    hf_client: Optional[HFClientBase] = None,
) -> Dict[str, Any]:
    """
    Parse a model card from HuggingFace.

    Fetches the model card (README.md) and extracts structured information
    including metadata, sections, and raw content.

    Args:
        model_id: The model identifier (e.g., "meta-llama/Llama-2-7b")
        hf_client: HuggingFace client instance. If None, creates one using factory.

    Returns:
        Dictionary containing parsed model card data:
            - model_id: The model identifier
            - content: Full markdown content
            - sections: Dictionary mapping section titles to content
            - has_benchmarks: Boolean indicating if benchmark data was found
            - metadata: Additional metadata (word count, section count, etc.)

    Raises:
        ValueError: If model_id is invalid
        FileNotFoundError: If model card doesn't exist
        RuntimeError: If parsing fails

    Example:
        >>> card = parse_model_card("Qwen/Qwen2.5-7B")
        >>> print(f"Model card has {len(card['sections'])} sections")
        >>> if card['has_benchmarks']:
        ...     print("Benchmarks found in card")
    """
    try:
        if not model_id or not isinstance(model_id, str):
            raise ValueError("model_id must be a non-empty string")

        # Get HuggingFace client
        if hf_client is None:
            hf_client = get_hf_client()

        logger.info(f"Fetching model card for {model_id}")

        # Fetch the model card content
        content = hf_client.get_model_card(model_id)

        if not content:
            logger.warning(f"Model card for {model_id} is empty")
            return {
                "model_id": model_id,
                "content": "",
                "sections": {},
                "has_benchmarks": False,
                "metadata": {
                    "word_count": 0,
                    "section_count": 0,
                    "char_count": 0,
                },
            }

        # Parse sections from markdown
        sections = _extract_sections(content)

        # Detect if benchmarks are present
        has_benchmarks = _detect_benchmarks(content)

        # Calculate metadata
        word_count = len(content.split())
        char_count = len(content)
        section_count = len(sections)

        logger.info(
            f"Parsed model card for {model_id}: "
            f"{word_count} words, {section_count} sections, "
            f"benchmarks: {has_benchmarks}"
        )

        return {
            "model_id": model_id,
            "content": content,
            "sections": sections,
            "has_benchmarks": has_benchmarks,
            "metadata": {
                "word_count": word_count,
                "section_count": section_count,
                "char_count": char_count,
            },
        }

    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to parse model card for {model_id}: {e}")
        raise RuntimeError(f"Failed to parse model card: {e}")


def _extract_sections(content: str) -> Dict[str, str]:
    """
    Extract sections from markdown content.

    Parses markdown headers (# Header, ## Header, etc.) and extracts
    the content under each section.

    Args:
        content: Markdown content

    Returns:
        Dictionary mapping section titles to their content
    """
    sections = {}
    current_section = None
    current_content = []

    lines = content.split("\n")

    for line in lines:
        # Check if this is a header line
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if header_match:
            # Save previous section if exists
            if current_section is not None:
                sections[current_section] = "\n".join(current_content).strip()

            # Start new section
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            current_section = title
            current_content = []
        else:
            # Add to current section content
            if current_section is not None:
                current_content.append(line)

    # Save last section
    if current_section is not None:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _detect_benchmarks(content: str) -> bool:
    """
    Detect if benchmark data is present in the content.

    Uses heuristics to identify common benchmark patterns:
    - Tables with benchmark names
    - Lists of benchmark scores
    - Benchmark keywords (MMLU, GSM8K, HumanEval, etc.)

    Args:
        content: Text content to analyze

    Returns:
        True if benchmarks are likely present, False otherwise
    """
    # Common benchmark keywords
    benchmark_keywords = [
        "MMLU",
        "GSM8K",
        "HumanEval",
        "MBPP",
        "ARC-c",
        "HellaSwag",
        "TriviaQA",
        "accuracy",
        "pass@1",
        "benchmark",
        "evaluation",
        "performance",
    ]

    # Check for benchmark keywords
    content_lower = content.lower()
    keyword_count = sum(
        1 for keyword in benchmark_keywords if keyword.lower() in content_lower
    )

    # Check for table patterns (markdown tables often contain benchmarks)
    table_pattern = r"\|.*\|.*\|"
    has_tables = bool(re.search(table_pattern, content))

    # Check for score patterns (e.g., "82.5%", "Score: 85.2")
    score_pattern = r"\d+\.\d+\s*%|\d+\.\d+\s*\|\s*\d+"
    has_scores = bool(re.search(score_pattern, content))

    # Heuristic: likely has benchmarks if it has tables + scores + keywords
    has_benchmarks = (
        (has_tables and has_scores) or keyword_count >= 3
    )

    return has_benchmarks


def extract_tables_from_card(content: str) -> List[str]:
    """
    Extract markdown tables from model card content.

    Utility function to extract all markdown tables, which often
    contain benchmark results.

    Args:
        content: Markdown content

    Returns:
        List of table strings (markdown format)

    Example:
        >>> tables = extract_tables_from_card(card_content)
        >>> for table in tables:
        ...     print(table)
    """
    tables = []
    current_table = []
    in_table = False

    for line in content.split("\n"):
        # Check if line is part of a markdown table
        if "|" in line:
            current_table.append(line)
            in_table = True
        elif in_table:
            # End of table
            if current_table:
                tables.append("\n".join(current_table))
                current_table = []
            in_table = False

    # Add last table if exists
    if current_table:
        tables.append("\n".join(current_table))

    return tables
