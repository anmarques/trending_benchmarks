"""
AI-powered benchmark classification tool.

This module uses Claude to classify benchmarks into categories and attributes
using a comprehensive taxonomy.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from ._claude_client import call_claude_json, is_anthropic_available

logger = logging.getLogger(__name__)


def classify_benchmark(
    benchmark_name: str,
    description: Optional[str] = None,
    claude_fn: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Classify a benchmark into categories and attributes.

    Uses Claude to analyze a benchmark and assign it to multi-label categories
    with confidence scores, based on a comprehensive taxonomy.

    Args:
        benchmark_name: Name of the benchmark (e.g., "MMLU", "GSM8K")
        description: Optional description or context about the benchmark
        claude_fn: Optional Claude API function for dependency injection.
                   Should accept (prompt, system_prompt) and return dict.

    Returns:
        Dictionary containing classification results:
            - benchmark_name: The benchmark name
            - primary_categories: List of primary categories with confidence
            - secondary_attributes: List of secondary attributes with confidence
            - modality: List of modalities (text, vision, audio, multimodal)
            - domain: Specific domain if applicable
            - difficulty_level: Difficulty classification
            - metadata: Classification metadata

        See prompts/classify.md for full schema.

    Raises:
        ValueError: If benchmark_name is empty or invalid
        RuntimeError: If classification fails

    Example:
        >>> result = classify_benchmark(
        ...     "MMLU",
        ...     description="57 academic subjects covering knowledge"
        ... )
        >>> for cat in result['primary_categories']:
        ...     print(f"{cat['category']}: {cat['confidence']}")
    """
    try:
        if not benchmark_name or not isinstance(benchmark_name, str):
            raise ValueError("benchmark_name must be a non-empty string")

        logger.info(f"Classifying benchmark: {benchmark_name}")

        # Build classification prompt
        prompt = _build_classification_prompt(benchmark_name, description)

        # Call Claude (use injected function or default)
        if claude_fn is None:
            if not is_anthropic_available():
                raise RuntimeError(
                    "Anthropic API not available. Set ANTHROPIC_API_KEY environment "
                    "variable or install anthropic package (pip install anthropic)"
                )
            result = call_claude_json(prompt=prompt)
        else:
            result = claude_fn(prompt=prompt)

        # Validate result structure
        if not isinstance(result, dict):
            raise RuntimeError("Invalid response format from Claude")

        # Ensure required keys exist
        if "benchmark_name" not in result:
            result["benchmark_name"] = benchmark_name
        if "primary_categories" not in result:
            result["primary_categories"] = []
        if "secondary_attributes" not in result:
            result["secondary_attributes"] = []
        if "modality" not in result:
            result["modality"] = ["text"]  # Default to text
        if "metadata" not in result:
            result["metadata"] = {}

        # Add classification metadata
        result["metadata"]["classification_date"] = datetime.utcnow().isoformat()

        # Calculate overall confidence if not present
        if "confidence_overall" not in result["metadata"]:
            if result["primary_categories"]:
                avg_confidence = sum(
                    cat.get("confidence", 0.5)
                    for cat in result["primary_categories"]
                ) / len(result["primary_categories"])
                result["metadata"]["confidence_overall"] = avg_confidence
            else:
                result["metadata"]["confidence_overall"] = 0.0

        logger.info(
            f"Classified {benchmark_name}: "
            f"{len(result['primary_categories'])} categories, "
            f"confidence: {result['metadata']['confidence_overall']:.2f}"
        )

        return result

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Benchmark classification failed: {e}")
        raise RuntimeError(f"Failed to classify benchmark: {e}")


def _load_taxonomy_categories() -> Optional[str]:
    """
    Load taxonomy categories from benchmark_taxonomy.md file.

    Returns:
        String with category information or None if not available
    """
    try:
        # Try to load from project root
        taxonomy_path = Path(__file__).parent.parent.parent.parent / "benchmark_taxonomy.md"

        if not taxonomy_path.exists():
            logger.debug("Taxonomy file not found, using prompt default")
            return None

        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract category sections (sections 2.x)
        # This will provide category names and examples to the classifier
        logger.debug(f"Loaded taxonomy from {taxonomy_path}")
        return content

    except Exception as e:
        logger.warning(f"Failed to load taxonomy: {e}")
        return None


def _build_classification_prompt(
    benchmark_name: str,
    description: Optional[str] = None,
) -> str:
    """
    Build the prompt for benchmark classification.

    Loads the classification prompt template and fills in the benchmark info.
    Also loads current taxonomy from benchmark_taxonomy.md if available.

    Args:
        benchmark_name: Benchmark name
        description: Optional description

    Returns:
        Complete prompt string
    """
    # Load prompt template
    prompt_path = Path(__file__).parent.parent / "prompts" / "classify.md"

    try:
        with open(prompt_path, "r") as f:
            template = f.read()
    except FileNotFoundError:
        logger.warning("Prompt template not found, using basic prompt")
        template = (
            "Classify the following benchmark into categories and attributes. "
            "Use the comprehensive taxonomy to assign multi-label categories."
        )

    # Try to load current taxonomy
    taxonomy_content = _load_taxonomy_categories()
    if taxonomy_content:
        # Append taxonomy reference to prompt
        template = template + "\n\n## Current Taxonomy Reference\n\n" + taxonomy_content[:5000]  # Limit size

    # Build input JSON
    import json
    input_data = {
        "benchmark_name": benchmark_name,
        "description": description,
    }
    input_json = json.dumps(input_data, indent=2)

    # Build full prompt
    prompt = f"""{template}

## Benchmark to Classify

{input_json}

Classify this benchmark and return the results as JSON following the schema defined above.
"""

    return prompt


def classify_benchmarks_batch(
    benchmarks: List[Dict[str, str]],
    claude_fn: Optional[callable] = None,
) -> List[Dict[str, Any]]:
    """
    Classify multiple benchmarks.

    Processes a list of benchmarks and returns classification results for each.

    Args:
        benchmarks: List of dictionaries with keys:
                    - name: Benchmark name
                    - description: Optional description
        claude_fn: Optional Claude function for injection

    Returns:
        List of classification results (one per benchmark)

    Example:
        >>> benchmarks = [
        ...     {"name": "MMLU", "description": "57 academic subjects"},
        ...     {"name": "GSM8K", "description": "Grade school math"},
        ... ]
        >>> results = classify_benchmarks_batch(benchmarks)
    """
    results = []

    for i, benchmark in enumerate(benchmarks):
        try:
            logger.info(f"Classifying benchmark {i+1}/{len(benchmarks)}")

            result = classify_benchmark(
                benchmark_name=benchmark.get("name", ""),
                description=benchmark.get("description"),
                claude_fn=claude_fn,
            )

            results.append(result)

        except Exception as e:
            logger.warning(f"Failed to classify {benchmark.get('name')}: {e}")
            # Add error result
            results.append({
                "benchmark_name": benchmark.get("name", "unknown"),
                "primary_categories": [],
                "secondary_attributes": [],
                "modality": ["text"],
                "domain": None,
                "difficulty_level": None,
                "metadata": {
                    "classification_date": datetime.utcnow().isoformat(),
                    "confidence_overall": 0.0,
                    "error": str(e),
                },
            })

    return results


def filter_by_category(
    classifications: List[Dict[str, Any]],
    category: str,
    min_confidence: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Filter classifications by category.

    Returns classifications that have the specified category with
    sufficient confidence.

    Args:
        classifications: List of classification results
        category: Category name to filter by (e.g., "Math", "Code")
        min_confidence: Minimum confidence threshold (0.0-1.0)

    Returns:
        Filtered list of classifications

    Example:
        >>> results = classify_benchmarks_batch(benchmarks)
        >>> math_benchmarks = filter_by_category(results, "Math", min_confidence=0.8)
    """
    filtered = []

    for classification in classifications:
        # Check primary categories
        for cat in classification.get("primary_categories", []):
            if (
                cat.get("category") == category
                and cat.get("confidence", 0.0) >= min_confidence
            ):
                filtered.append(classification)
                break

    return filtered


def get_category_summary(
    classifications: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Get summary of category distribution.

    Counts how many benchmarks fall into each category.

    Args:
        classifications: List of classification results

    Returns:
        Dictionary mapping category names to counts

    Example:
        >>> results = classify_benchmarks_batch(benchmarks)
        >>> summary = get_category_summary(results)
        >>> print(f"Math: {summary.get('Math', 0)} benchmarks")
    """
    category_counts: Dict[str, int] = {}

    for classification in classifications:
        for cat in classification.get("primary_categories", []):
            category_name = cat.get("category")
            if category_name:
                category_counts[category_name] = (
                    category_counts.get(category_name, 0) + 1
                )

    return category_counts


def enrich_benchmarks_with_classification(
    benchmarks: List[Dict[str, Any]],
    classifications: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Enrich benchmark data with classification information.

    Merges classification results into benchmark data.

    Args:
        benchmarks: List of benchmark dictionaries
        classifications: List of classification results

    Returns:
        Enriched benchmark list with classification data

    Example:
        >>> benchmarks = [{"name": "MMLU", "score": 82.5}]
        >>> classifications = classify_benchmarks_batch([{"name": "MMLU"}])
        >>> enriched = enrich_benchmarks_with_classification(benchmarks, classifications)
        >>> print(enriched[0]["categories"])
    """
    # Create lookup by name
    classification_map = {
        c["benchmark_name"]: c for c in classifications
    }

    enriched = []

    for benchmark in benchmarks:
        # Make a copy
        enriched_bench = benchmark.copy()

        # Get classification for this benchmark
        bench_name = benchmark.get("name") or benchmark.get("canonical_name")
        if bench_name and bench_name in classification_map:
            classification = classification_map[bench_name]

            # Add classification fields
            enriched_bench["categories"] = [
                cat["category"]
                for cat in classification.get("primary_categories", [])
            ]
            enriched_bench["modality"] = classification.get("modality", ["text"])
            enriched_bench["domain"] = classification.get("domain")
            enriched_bench["difficulty_level"] = classification.get("difficulty_level")

        enriched.append(enriched_bench)

    return enriched
