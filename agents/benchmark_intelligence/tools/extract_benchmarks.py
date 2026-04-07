"""
AI-powered benchmark extraction from text documents.

This module uses Claude to extract structured benchmark data from
model cards, research papers, and technical documents.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from ._claude_client import call_claude_json, is_anthropic_available

logger = logging.getLogger(__name__)


def extract_benchmarks_from_text(
    text: str,
    source_type: str = "unknown",
    source_name: Optional[str] = None,
    claude_fn: Optional[callable] = None,
    detect_cooccurrence: bool = True,
) -> Dict[str, Any]:
    """
    Extract benchmarks from text using AI.

    Uses Claude to parse text content and extract structured benchmark data
    including scores, metrics, and evaluation contexts.

    Args:
        text: Text content to analyze (model card, paper, etc.)
        source_type: Type of source document ("model_card", "paper", "blog_post", etc.)
        source_name: Name/identifier of the source document
        claude_fn: Optional Claude API function for dependency injection.
                   Should accept (prompt, system_prompt) and return dict.
        detect_cooccurrence: If True, detect when benchmarks appear side-by-side
                           in the same document sections (e.g., same table/paragraph).

    Returns:
        Dictionary containing extracted benchmark data:
            - benchmarks: List of benchmark entries with scores and context
            - cooccurrences: List of benchmark pairs found side-by-side (if detect_cooccurrence=True)
            - metadata: Extraction metadata (source, date, count, etc.)

        See prompts/extract_benchmarks.md for full schema.

    Raises:
        ValueError: If text is empty or invalid
        RuntimeError: If extraction fails

    Example:
        >>> text = "Our model achieves 82.5% on MMLU and 94.2% on GSM8K (8-shot)."
        >>> result = extract_benchmarks_from_text(text, source_type="blog_post")
        >>> print(f"Found {result['metadata']['total_benchmarks']} benchmarks")
        >>> for bench in result['benchmarks']:
        ...     print(f"{bench['name']}: {bench['score']}")
    """
    try:
        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")

        if len(text.strip()) < 10:
            logger.warning("Text is very short, may not contain benchmarks")
            return {
                "benchmarks": [],
                "metadata": {
                    "document_source": source_name or "unknown",
                    "extraction_date": datetime.utcnow().isoformat(),
                    "total_benchmarks": 0,
                    "source_type": source_type,
                },
            }

        logger.info(f"Extracting benchmarks from {source_type} ({len(text)} chars)")

        # Load extraction prompt
        prompt = _build_extraction_prompt(text, source_type, source_name)

        # Call Claude (use injected function or default)
        if claude_fn is None:
            if not is_anthropic_available():
                raise RuntimeError(
                    "Anthropic API not available. Set ANTHROPIC_API_KEY environment "
                    "variable or install anthropic package (pip install anthropic)"
                )
            # Use 8192 tokens for benchmark extraction
            # (typical model card abstracts are 1-2K tokens, response ~2-4K)
            result = call_claude_json(prompt=prompt, max_tokens=8192)
        else:
            result = claude_fn(prompt=prompt)

        # Validate result structure
        if not isinstance(result, dict):
            raise RuntimeError("Invalid response format from Claude")

        if "benchmarks" not in result:
            logger.warning("No benchmarks key in response, creating empty result")
            result = {
                "benchmarks": [],
                "metadata": {
                    "document_source": source_name or "unknown",
                    "extraction_date": datetime.utcnow().isoformat(),
                    "total_benchmarks": 0,
                    "source_type": source_type,
                },
            }

        # Ensure metadata exists and has required fields
        if "metadata" not in result:
            result["metadata"] = {}

        result["metadata"]["document_source"] = source_name or "unknown"
        result["metadata"]["extraction_date"] = datetime.utcnow().isoformat()
        result["metadata"]["total_benchmarks"] = len(result["benchmarks"])
        result["metadata"]["source_type"] = source_type

        # Detect co-occurrences if enabled
        if detect_cooccurrence and result["benchmarks"]:
            cooccurrences = _detect_cooccurrences(result["benchmarks"])
            result["cooccurrences"] = cooccurrences
            logger.info(f"Detected {len(cooccurrences)} benchmark co-occurrences")
        else:
            result["cooccurrences"] = []

        logger.info(f"Extracted {len(result['benchmarks'])} benchmarks")

        return result

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Benchmark extraction failed: {e}")
        raise RuntimeError(f"Failed to extract benchmarks: {e}")


def _build_extraction_prompt(
    text: str,
    source_type: str,
    source_name: Optional[str] = None,
) -> str:
    """
    Build the prompt for benchmark extraction.

    Loads the extraction prompt template and fills in the text.

    Args:
        text: Text to extract from
        source_type: Type of source
        source_name: Name of source

    Returns:
        Complete prompt string
    """
    # Load prompt template
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract_benchmarks.md"

    try:
        with open(prompt_path, "r") as f:
            template = f.read()
    except FileNotFoundError:
        logger.warning("Prompt template not found, using basic prompt")
        template = (
            "Extract all benchmarks, scores, and evaluation contexts from the "
            "following text. Return structured JSON data."
        )

    # Build full prompt
    prompt = f"""{template}

## Text to Analyze

Source Type: {source_type}
Source Name: {source_name or "unknown"}

---

{text}

---

Extract all benchmarks from the above text and return as JSON following the schema defined above.
"""

    return prompt


def extract_benchmarks_from_multiple_sources(
    sources: List[Dict[str, Any]],
    claude_fn: Optional[callable] = None,
) -> List[Dict[str, Any]]:
    """
    Extract benchmarks from multiple text sources.

    Processes multiple documents and returns aggregated results.

    Args:
        sources: List of source dictionaries with keys:
                 - text: Text content
                 - source_type: Type of source
                 - source_name: Name/identifier
        claude_fn: Optional Claude function for injection

    Returns:
        List of extraction results (one per source)

    Example:
        >>> sources = [
        ...     {"text": card1, "source_type": "model_card", "source_name": "Model A"},
        ...     {"text": card2, "source_type": "model_card", "source_name": "Model B"},
        ... ]
        >>> results = extract_benchmarks_from_multiple_sources(sources)
    """
    results = []

    for i, source in enumerate(sources):
        try:
            logger.info(f"Processing source {i+1}/{len(sources)}")

            result = extract_benchmarks_from_text(
                text=source.get("text", ""),
                source_type=source.get("source_type", "unknown"),
                source_name=source.get("source_name"),
                claude_fn=claude_fn,
            )

            results.append(result)

        except Exception as e:
            logger.warning(f"Failed to extract from source {i+1}: {e}")
            # Add empty result
            results.append({
                "benchmarks": [],
                "metadata": {
                    "document_source": source.get("source_name", "unknown"),
                    "extraction_date": datetime.utcnow().isoformat(),
                    "total_benchmarks": 0,
                    "error": str(e),
                },
            })

    return results


def aggregate_benchmark_results(
    extraction_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate benchmark results from multiple extractions.

    Combines benchmarks from multiple sources into a single structure.

    Args:
        extraction_results: List of extraction result dictionaries

    Returns:
        Aggregated results with all benchmarks and combined metadata

    Example:
        >>> results = extract_benchmarks_from_multiple_sources(sources)
        >>> aggregated = aggregate_benchmark_results(results)
        >>> print(f"Total: {aggregated['metadata']['total_benchmarks']} benchmarks")
    """
    all_benchmarks = []
    sources = []

    for result in extraction_results:
        benchmarks = result.get("benchmarks", [])
        metadata = result.get("metadata", {})

        # Add source info to each benchmark
        source_name = metadata.get("document_source", "unknown")
        for bench in benchmarks:
            if "metadata" not in bench:
                bench["metadata"] = {}
            bench["metadata"]["extracted_from"] = source_name

        all_benchmarks.extend(benchmarks)
        sources.append(source_name)

    return {
        "benchmarks": all_benchmarks,
        "metadata": {
            "total_benchmarks": len(all_benchmarks),
            "sources": sources,
            "source_count": len(sources),
            "aggregation_date": datetime.utcnow().isoformat(),
        },
    }


def _detect_cooccurrences(benchmarks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect when benchmarks appear side-by-side in the same document section.

    Benchmarks that appear in the same table, paragraph, or list are considered
    to co-occur. This is used during consolidation to avoid merging benchmarks
    that are reported together (e.g., "MMLU" and "MMLU-Pro" in the same table
    are distinct benchmarks, not variants).

    Args:
        benchmarks: List of extracted benchmark dictionaries with source_location

    Returns:
        List of co-occurrence pairs: [{"benchmark_a": "MMLU", "benchmark_b": "MMLU-Pro", "location": "Table 1"}, ...]

    Example:
        >>> benchmarks = [
        ...     {"name": "MMLU", "source_location": "Table 1, Row 1"},
        ...     {"name": "MMLU-Pro", "source_location": "Table 1, Row 2"},
        ...     {"name": "GSM8K", "source_location": "Table 2, Row 1"}
        ... ]
        >>> cooccurrences = _detect_cooccurrences(benchmarks)
        >>> # Returns: [{"benchmark_a": "MMLU", "benchmark_b": "MMLU-Pro", "location": "Table 1"}]
    """
    cooccurrences = []

    # Group benchmarks by normalized source location (table/section level)
    # Normalize to remove row/item details for grouping
    location_groups: Dict[str, List[str]] = {}
    for benchmark in benchmarks:
        name = benchmark.get("name")
        location = benchmark.get("source_location", "unknown")

        if not name:
            continue

        # Normalize location to table/section level
        # "Table 1, Row 1" -> "Table 1"
        # "Section 3.2, paragraph 1" -> "Section 3.2"
        # "Performance highlights, item 1" -> "Performance highlights"
        normalized_location = _normalize_location(location)

        if normalized_location not in location_groups:
            location_groups[normalized_location] = []

        # Only add unique names to each location
        if name not in location_groups[normalized_location]:
            location_groups[normalized_location].append(name)

    # Find all pairs within each location
    for location, names in location_groups.items():
        if len(names) < 2:
            continue

        # Generate all pairs
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                name_a = names[i]
                name_b = names[j]

                # Only record if names are similar (potential variants)
                # e.g., "MMLU" and "MMLU-Pro", "GSM8K" and "GSM-8K"
                if _are_potentially_similar(name_a, name_b):
                    cooccurrences.append({
                        "benchmark_a": name_a,
                        "benchmark_b": name_b,
                        "location": location
                    })

    return cooccurrences


def _normalize_location(location: str) -> str:
    """
    Normalize source location to table/section level for co-occurrence detection.

    Removes row/item/paragraph details to group benchmarks from same table/section.

    Args:
        location: Original source location string

    Returns:
        Normalized location (table/section level)

    Example:
        >>> _normalize_location("Table 1, Row 1")
        'Table 1'
        >>> _normalize_location("Section 3.2, paragraph 1")
        'Section 3.2'
        >>> _normalize_location("Performance highlights, item 2")
        'Performance highlights'
    """
    # Common patterns to remove
    patterns_to_remove = [
        r',\s*Row\s+\d+',
        r',\s*row\s+\d+',
        r',\s*item\s+\d+',
        r',\s*Item\s+\d+',
        r',\s*paragraph\s+\d+',
        r',\s*Paragraph\s+\d+',
        r',\s*line\s+\d+',
        r',\s*Line\s+\d+',
    ]

    import re
    normalized = location
    for pattern in patterns_to_remove:
        normalized = re.sub(pattern, '', normalized)

    return normalized.strip()


def _are_potentially_similar(name_a: str, name_b: str) -> bool:
    """
    Check if two benchmark names are potentially similar (might be variants).

    This is a heuristic to identify benchmark pairs that might be considered
    for consolidation but should be kept separate when found together.

    Args:
        name_a: First benchmark name
        name_b: Second benchmark name

    Returns:
        True if names share significant overlap

    Example:
        >>> _are_potentially_similar("MMLU", "MMLU-Pro")
        True
        >>> _are_potentially_similar("MMLU", "GSM8K")
        False
        >>> _are_potentially_similar("GSM8K", "GSM-8K")
        True
    """
    # Normalize for comparison
    norm_a = name_a.lower().replace("-", "").replace("_", "").replace(" ", "")
    norm_b = name_b.lower().replace("-", "").replace("_", "").replace(" ", "")

    # If names are identical after normalization, they're similar
    if norm_a == norm_b:
        return True

    # If one name is a substring of the other (after normalization), they're similar
    # This catches cases like "MMLU" in "MMLU-Pro" or "MMLUPro"
    if norm_a in norm_b or norm_b in norm_a:
        return True

    # Calculate Levenshtein distance for more sophisticated comparison
    # Simple implementation: if they differ by only a few characters
    if len(norm_a) > 3 and len(norm_b) > 3:
        # Count matching prefix length
        prefix_len = 0
        for i in range(min(len(norm_a), len(norm_b))):
            if norm_a[i] == norm_b[i]:
                prefix_len += 1
            else:
                break

        # If they share >60% of the shorter name as prefix, they're similar
        min_len = min(len(norm_a), len(norm_b))
        if prefix_len / min_len > 0.6:
            return True

    return False
