"""
AI-powered benchmark consolidation tool.

This module uses Claude to consolidate variations of benchmark names
into canonical forms, distinguishing between true variants and distinct benchmarks.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime

from ._claude_client import call_claude_json, is_anthropic_available

logger = logging.getLogger(__name__)


def consolidate_benchmarks(
    benchmark_names: List[str],
    claude_fn: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Consolidate benchmark name variations into canonical forms.

    Uses Claude to analyze benchmark names and create mappings from variations
    to canonical names, while identifying truly distinct benchmarks.

    Args:
        benchmark_names: List of benchmark names to consolidate
        claude_fn: Optional Claude API function for dependency injection.
                   Should accept (prompt, system_prompt) and return dict.

    Returns:
        Dictionary containing consolidation results:
            - consolidations: List of canonical names with their variations
            - distinct_benchmarks: List of benchmarks that are truly distinct
            - uncertain_mappings: List of ambiguous cases requiring review
            - metadata: Consolidation metadata

        See prompts/consolidate.md for full schema.

    Raises:
        ValueError: If benchmark_names is empty or invalid
        RuntimeError: If consolidation fails

    Example:
        >>> names = ["MMLU", "mmlu", "MMLU-Pro", "GSM8K", "GSM-8K"]
        >>> result = consolidate_benchmarks(names)
        >>> for cons in result['consolidations']:
        ...     print(f"{cons['canonical_name']}: {cons['variations']}")
    """
    try:
        if not benchmark_names or not isinstance(benchmark_names, list):
            raise ValueError("benchmark_names must be a non-empty list")

        if len(benchmark_names) == 0:
            raise ValueError("benchmark_names list is empty")

        # Remove duplicates while preserving order
        unique_names = list(dict.fromkeys(benchmark_names))

        logger.info(f"Consolidating {len(unique_names)} unique benchmark names")

        # Build consolidation prompt
        prompt = _build_consolidation_prompt(unique_names)

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
        if "consolidations" not in result:
            result["consolidations"] = []
        if "distinct_benchmarks" not in result:
            result["distinct_benchmarks"] = []
        if "uncertain_mappings" not in result:
            result["uncertain_mappings"] = []

        # Add metadata
        if "metadata" not in result:
            result["metadata"] = {}

        result["metadata"]["total_input_names"] = len(unique_names)
        result["metadata"]["total_canonical_names"] = len(result["consolidations"])
        result["metadata"]["consolidation_date"] = datetime.utcnow().isoformat()

        logger.info(
            f"Consolidated {len(unique_names)} names into "
            f"{len(result['consolidations'])} canonical names"
        )

        return result

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Benchmark consolidation failed: {e}")
        raise RuntimeError(f"Failed to consolidate benchmarks: {e}")


def _build_consolidation_prompt(benchmark_names: List[str]) -> str:
    """
    Build the prompt for benchmark consolidation.

    Loads the consolidation prompt template and fills in the benchmark names.

    Args:
        benchmark_names: List of benchmark names

    Returns:
        Complete prompt string
    """
    # Load prompt template
    prompt_path = Path(__file__).parent.parent / "prompts" / "consolidate.md"

    try:
        with open(prompt_path, "r") as f:
            template = f.read()
    except FileNotFoundError:
        logger.warning("Prompt template not found, using basic prompt")
        template = (
            "Consolidate the following benchmark names into canonical forms. "
            "Distinguish between variations of the same benchmark and truly distinct benchmarks."
        )

    # Build input JSON
    import json
    input_json = json.dumps({"benchmark_names": benchmark_names}, indent=2)

    # Build full prompt
    prompt = f"""{template}

## Benchmark Names to Consolidate

{input_json}

Analyze these benchmark names and return the consolidation results as JSON following the schema defined above.
"""

    return prompt


def create_name_mapping(
    consolidation_result: Dict[str, Any]
) -> Dict[str, str]:
    """
    Create a simple mapping from variation names to canonical names.

    Utility function to extract a direct name mapping dictionary.

    Args:
        consolidation_result: Result from consolidate_benchmarks()

    Returns:
        Dictionary mapping variation names to canonical names

    Example:
        >>> result = consolidate_benchmarks(names)
        >>> mapping = create_name_mapping(result)
        >>> print(mapping["mmlu"])  # "MMLU"
        >>> print(mapping["GSM-8K"])  # "GSM8K"
    """
    mapping = {}

    for consolidation in consolidation_result.get("consolidations", []):
        canonical = consolidation["canonical_name"]
        variations = consolidation.get("variations", [])

        for variation in variations:
            mapping[variation] = canonical

    return mapping


def apply_consolidation(
    benchmarks: List[Dict[str, Any]],
    consolidation_result: Dict[str, Any],
    add_canonical_field: bool = True,
) -> List[Dict[str, Any]]:
    """
    Apply consolidation mapping to benchmark data.

    Updates benchmark entries with canonical names based on consolidation results.

    Args:
        benchmarks: List of benchmark dictionaries (from extraction)
        consolidation_result: Result from consolidate_benchmarks()
        add_canonical_field: If True, adds "canonical_name" field.
                            If False, replaces "name" field.

    Returns:
        Updated benchmark list with canonical names

    Example:
        >>> benchmarks = [
        ...     {"name": "mmlu", "score": 82.5},
        ...     {"name": "GSM-8K", "score": 94.2}
        ... ]
        >>> result = consolidate_benchmarks(["mmlu", "MMLU", "GSM-8K", "GSM8K"])
        >>> updated = apply_consolidation(benchmarks, result)
        >>> print(updated[0]["canonical_name"])  # "MMLU"
    """
    # Create name mapping
    mapping = create_name_mapping(consolidation_result)

    # Apply mapping to benchmarks
    updated_benchmarks = []

    for benchmark in benchmarks:
        # Make a copy
        updated = benchmark.copy()

        original_name = benchmark.get("name")
        if original_name:
            canonical_name = mapping.get(original_name, original_name)

            if add_canonical_field:
                updated["canonical_name"] = canonical_name
            else:
                updated["name"] = canonical_name

        updated_benchmarks.append(updated)

    return updated_benchmarks


def extract_benchmark_names(
    benchmarks: List[Dict[str, Any]]
) -> List[str]:
    """
    Extract unique benchmark names from benchmark data.

    Utility function to get all unique benchmark names from extracted data.

    Args:
        benchmarks: List of benchmark dictionaries

    Returns:
        List of unique benchmark names

    Example:
        >>> benchmarks = [
        ...     {"name": "MMLU", "score": 82.5},
        ...     {"name": "mmlu", "score": 83.0},
        ...     {"name": "GSM8K", "score": 94.2}
        ... ]
        >>> names = extract_benchmark_names(benchmarks)
        >>> print(names)  # ["MMLU", "mmlu", "GSM8K"]
    """
    names: Set[str] = set()

    for benchmark in benchmarks:
        name = benchmark.get("name")
        if name:
            names.add(name)

    return list(names)
