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
    cooccurrences: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Consolidate benchmark name variations into canonical forms.

    Uses Claude to analyze benchmark names and create mappings from variations
    to canonical names, while identifying truly distinct benchmarks.

    Args:
        benchmark_names: List of benchmark names to consolidate
        claude_fn: Optional Claude API function for dependency injection.
                   Should accept (prompt, system_prompt) and return dict.
        cooccurrences: Optional list of benchmark pairs that appear side-by-side
                      in the same document sections. These pairs will NOT be merged
                      during consolidation (e.g., "MMLU" and "MMLU-Pro" in same table).

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

        # Apply side-by-side disambiguation
        if cooccurrences:
            result = _apply_cooccurrence_disambiguation(result, cooccurrences)
            logger.info(f"Applied {len(cooccurrences)} co-occurrence constraints")

        # Add metadata
        if "metadata" not in result:
            result["metadata"] = {}

        result["metadata"]["total_input_names"] = len(unique_names)
        result["metadata"]["total_canonical_names"] = len(result["consolidations"])
        result["metadata"]["consolidation_date"] = datetime.utcnow().isoformat()
        result["metadata"]["cooccurrence_constraints"] = len(cooccurrences) if cooccurrences else 0

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


def _apply_most_common_nomenclature(
    consolidation_result: Dict[str, Any],
    usage_counts: Dict[str, int]
) -> Dict[str, Any]:
    """
    Apply "most common nomenclature" rule to select canonical names.

    For each group of consolidated variants, selects the variant used by
    the most models as the canonical name. Implements tie-breaking rules
    from SPECIFICATIONS.md Section 4.3.

    Tie-breaking rules (if counts are equal):
    1. Prefer uppercase > lowercase > mixed case
    2. Examples: "MMLU" > "mmlu" > "Mmlu"

    Args:
        consolidation_result: Result from Claude consolidation
        usage_counts: Dict mapping benchmark names to usage counts

    Returns:
        Updated consolidation result with canonical names adjusted

    Example:
        >>> result = {"consolidations": [{"canonical_name": "mmlu", "variations": ["MMLU", "mmlu"]}]}
        >>> usage = {"MMLU": 10, "mmlu": 3}
        >>> updated = _apply_most_common_nomenclature(result, usage)
        >>> print(updated["consolidations"][0]["canonical_name"])  # "MMLU"
    """
    for consolidation in consolidation_result.get("consolidations", []):
        variations = consolidation.get("variations", [])
        current_canonical = consolidation.get("canonical_name")

        if not variations or len(variations) <= 1:
            continue

        # Count usage for each variation
        variant_counts = {}
        for variant in variations:
            variant_counts[variant] = usage_counts.get(variant, 0)

        # Find max usage count
        max_count = max(variant_counts.values()) if variant_counts else 0

        # Get all variants with max count (for tie-breaking)
        top_variants = [v for v, c in variant_counts.items() if c == max_count]

        if len(top_variants) == 0:
            # No usage data, keep AI's choice
            logger.debug(f"No usage data for {current_canonical}, keeping AI choice")
            continue
        elif len(top_variants) == 1:
            # Clear winner
            selected = top_variants[0]
            if selected != current_canonical:
                logger.info(
                    f"Most common nomenclature: '{selected}' (used by {max_count} models) "
                    f"selected over '{current_canonical}'"
                )
                consolidation["canonical_name"] = selected
                consolidation["notes"] = (
                    f"{consolidation.get('notes', '')} "
                    f"Canonical name selected based on usage: {max_count} models use '{selected}'."
                ).strip()
        else:
            # Tie - apply tie-breaking rules
            selected = _tie_break_canonical_name(top_variants, max_count)
            if selected != current_canonical:
                logger.info(
                    f"Tie-breaking: '{selected}' selected from {top_variants} "
                    f"(all used by {max_count} models)"
                )
                consolidation["canonical_name"] = selected
                consolidation["notes"] = (
                    f"{consolidation.get('notes', '')} "
                    f"Tie-breaking applied: {len(top_variants)} variants tied at {max_count} models. "
                    f"Selected '{selected}' (uppercase > lowercase > mixed case)."
                ).strip()

    return consolidation_result


def _apply_cooccurrence_disambiguation(
    consolidation_result: Dict[str, Any],
    cooccurrences: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Apply side-by-side benchmark disambiguation.

    When two benchmarks appear together in the same document section (same table,
    same paragraph), they should be treated as distinct benchmarks, not merged.

    This function splits any consolidation groups where members co-occur.

    Args:
        consolidation_result: Result from Claude consolidation
        cooccurrences: List of benchmark pairs found side-by-side
                      [{"benchmark_a": "MMLU", "benchmark_b": "MMLU-Pro", "location": "Table 1"}, ...]

    Returns:
        Updated consolidation result with co-occurring benchmarks separated

    Example:
        Before: consolidations = [{"canonical_name": "MMLU", "variations": ["MMLU", "mmlu", "MMLU-Pro"]}]
        After (with MMLU+MMLU-Pro cooccurrence):
              consolidations = [
                  {"canonical_name": "MMLU", "variations": ["MMLU", "mmlu"]},
                  {"canonical_name": "MMLU-Pro", "variations": ["MMLU-Pro"]}
              ]
    """
    from typing import Tuple

    # Build set of co-occurring pairs (both directions for easy lookup)
    cooccurring_pairs: Set[Tuple[str, str]] = set()
    for cooccur in cooccurrences:
        a = cooccur["benchmark_a"]
        b = cooccur["benchmark_b"]
        cooccurring_pairs.add((a, b))
        cooccurring_pairs.add((b, a))  # Symmetric

    # Process each consolidation group
    new_consolidations = []
    split_count = 0

    for consolidation in consolidation_result.get("consolidations", []):
        variations = consolidation.get("variations", [])

        if len(variations) <= 1:
            # No variations to split
            new_consolidations.append(consolidation)
            continue

        # Check if any variations co-occur
        needs_split = False
        for i in range(len(variations)):
            for j in range(i + 1, len(variations)):
                if (variations[i], variations[j]) in cooccurring_pairs:
                    needs_split = True
                    break
            if needs_split:
                break

        if not needs_split:
            # No co-occurrences, keep as-is
            new_consolidations.append(consolidation)
            continue

        # Split the group: separate co-occurring benchmarks
        # Strategy: Create separate consolidations for each unique variation
        # that co-occurs with another in this group
        separated_variations = set()
        for i in range(len(variations)):
            for j in range(i + 1, len(variations)):
                if (variations[i], variations[j]) in cooccurring_pairs:
                    separated_variations.add(variations[i])
                    separated_variations.add(variations[j])

        # If some variations need separation, split them out
        if separated_variations:
            # Keep non-separated variations together
            kept_variations = [v for v in variations if v not in separated_variations]

            if kept_variations:
                # Create consolidation for non-separated variations
                new_consolidations.append({
                    "canonical_name": kept_variations[0],
                    "variations": kept_variations,
                    "benchmark_type": consolidation.get("benchmark_type", "same"),
                    "confidence": consolidation.get("confidence", 1.0),
                    "notes": f"{consolidation.get('notes', '')} (Split from original group due to co-occurrence)".strip()
                })

            # Create individual consolidations for separated variations
            for var in sorted(separated_variations):
                new_consolidations.append({
                    "canonical_name": var,
                    "variations": [var],
                    "benchmark_type": "distinct",
                    "confidence": 1.0,
                    "notes": f"Separated due to side-by-side appearance with similar benchmark name"
                })

            split_count += 1
        else:
            new_consolidations.append(consolidation)

    consolidation_result["consolidations"] = new_consolidations

    if split_count > 0:
        logger.info(f"Split {split_count} consolidation groups due to co-occurrence")

    return consolidation_result


def _tie_break_canonical_name(variants: List[str], count: int) -> str:
    """
    Apply tie-breaking rules when multiple variants have equal usage.

    Tie-breaking order:
    1. Uppercase (all characters uppercase)
    2. Lowercase (all characters lowercase)
    3. Mixed case

    Args:
        variants: List of variant names with equal usage counts
        count: The tied usage count

    Returns:
        Selected canonical name

    Example:
        >>> _tie_break_canonical_name(["MMLU", "mmlu", "Mmlu"], 5)
        'MMLU'
        >>> _tie_break_canonical_name(["mmlu", "Mmlu"], 5)
        'mmlu'
    """
    # Categorize variants
    uppercase = []
    lowercase = []
    mixed_case = []

    for variant in variants:
        # Only consider alphabetic characters for case classification
        alpha_chars = ''.join(c for c in variant if c.isalpha())
        if not alpha_chars:
            # No alphabetic characters, treat as mixed
            mixed_case.append(variant)
        elif alpha_chars.isupper():
            uppercase.append(variant)
        elif alpha_chars.islower():
            lowercase.append(variant)
        else:
            mixed_case.append(variant)

    # Apply preference: uppercase > lowercase > mixed
    if uppercase:
        selected = uppercase[0]
        logger.debug(f"Tie-break: Selected uppercase variant '{selected}'")
        return selected
    elif lowercase:
        selected = lowercase[0]
        logger.debug(f"Tie-break: Selected lowercase variant '{selected}'")
        return selected
    else:
        selected = mixed_case[0] if mixed_case else variants[0]
        logger.debug(f"Tie-break: Selected mixed-case variant '{selected}'")
        return selected
