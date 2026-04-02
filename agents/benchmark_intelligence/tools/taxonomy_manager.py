"""
Adaptive taxonomy evolution for benchmark categorization.

This module manages the benchmark taxonomy lifecycle:
- Loading current taxonomy from benchmark_taxonomy.md
- Analyzing benchmark fit against taxonomy
- Proposing new categories based on poor-fit benchmarks
- Evolving taxonomy with new categories
- Archiving taxonomy versions when changes occur
"""

import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from ._claude_client import call_claude_json, is_anthropic_available

logger = logging.getLogger(__name__)


def load_current_taxonomy(path: str) -> Dict[str, Any]:
    """
    Load current taxonomy from benchmark_taxonomy.md file.

    Parses the markdown file to extract category definitions and structure.

    Args:
        path: Path to benchmark_taxonomy.md file

    Returns:
        Dictionary containing:
            - categories: List of category dicts with name, description, examples
            - metadata: File metadata (last_updated, version, etc.)
            - raw_content: Original file content for archiving

    Example:
        >>> taxonomy = load_current_taxonomy("benchmark_taxonomy.md")
        >>> print(taxonomy["categories"][0]["name"])
        'Knowledge & General Understanding'
    """
    try:
        taxonomy_path = Path(path)

        if not taxonomy_path.exists():
            logger.warning(f"Taxonomy file not found at {path}, creating default")
            return _create_default_taxonomy()

        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse markdown to extract categories
        categories = _parse_taxonomy_from_markdown(content)

        # Extract metadata
        metadata = {
            "last_updated": datetime.utcnow().isoformat(),
            "source_file": str(taxonomy_path),
            "category_count": len(categories),
        }

        taxonomy = {
            "categories": categories,
            "metadata": metadata,
            "raw_content": content,
        }

        logger.info(f"Loaded taxonomy with {len(categories)} categories from {path}")
        return taxonomy

    except Exception as e:
        logger.error(f"Failed to load taxonomy from {path}: {e}")
        raise RuntimeError(f"Taxonomy loading failed: {e}")


def _parse_taxonomy_from_markdown(content: str) -> List[Dict[str, Any]]:
    """
    Parse taxonomy categories from markdown content.

    Extracts category sections (e.g., "### 2.1 Knowledge & General Understanding")
    and their benchmark examples.

    Args:
        content: Markdown file content

    Returns:
        List of category dictionaries
    """
    categories = []

    # Pattern to match category headers like "### 2.1 Knowledge & General Understanding"
    # or "## 2. Top 30+ Common Benchmarks by Category" followed by "### 2.1 ..."
    category_pattern = r'###\s+\d+\.\d+\s+(.+?)(?=###|\Z)'

    matches = re.finditer(category_pattern, content, re.DOTALL)

    for match in matches:
        category_name = match.group(1).split('\n')[0].strip()
        section_content = match.group(1)

        # Extract benchmark examples from the table
        benchmarks = _extract_benchmarks_from_section(section_content)

        categories.append({
            "name": category_name,
            "description": _extract_description(section_content),
            "examples": benchmarks,
        })

    # If no categories found with the pattern, extract from section headers
    if not categories:
        categories = _extract_categories_fallback(content)

    logger.debug(f"Parsed {len(categories)} categories from taxonomy")
    return categories


def _extract_benchmarks_from_section(section_content: str) -> List[str]:
    """Extract benchmark names from a category section."""
    benchmarks = []

    # Look for table rows with benchmark names (e.g., "| **MMLU** | ...")
    benchmark_pattern = r'\|\s*\*\*([^*]+?)\*\*\s*\|'
    matches = re.findall(benchmark_pattern, section_content)

    for match in matches:
        benchmark = match.strip()
        if benchmark and benchmark not in ['Benchmark', 'Pattern', 'Examples']:
            benchmarks.append(benchmark)

    return benchmarks


def _extract_description(section_content: str) -> str:
    """Extract description from section content."""
    # Get first paragraph after the header
    lines = section_content.split('\n')
    for line in lines[1:]:
        line = line.strip()
        if line and not line.startswith('|') and not line.startswith('#'):
            return line
    return ""


def _extract_categories_fallback(content: str) -> List[Dict[str, Any]]:
    """Fallback parser for taxonomy categories."""
    # Extract major section headers
    categories = []

    # Common category names to look for
    common_categories = [
        "Knowledge & General Understanding",
        "Reasoning & Commonsense",
        "Mathematical Reasoning",
        "Code Generation & Software Engineering",
        "Vision & Multimodal",
        "Long Context",
        "Instruction Following",
        "Safety & Ethics",
        "Multilingual",
        "Agent & Tool Use",
    ]

    for cat_name in common_categories:
        if cat_name.lower() in content.lower():
            categories.append({
                "name": cat_name,
                "description": f"Benchmarks for {cat_name.lower()}",
                "examples": [],
            })

    return categories


def _create_default_taxonomy() -> Dict[str, Any]:
    """Create a default taxonomy when file doesn't exist."""
    default_categories = [
        {
            "name": "Knowledge & General Understanding",
            "description": "Benchmarks evaluating factual knowledge and general understanding",
            "examples": ["MMLU", "C-Eval", "CMMLU"],
        },
        {
            "name": "Reasoning & Commonsense",
            "description": "Benchmarks evaluating logical reasoning and commonsense",
            "examples": ["ARC", "HellaSwag", "PIQA"],
        },
        {
            "name": "Mathematical Reasoning",
            "description": "Benchmarks evaluating mathematical problem solving",
            "examples": ["GSM8K", "MATH", "AIME"],
        },
        {
            "name": "Code Generation & Software Engineering",
            "description": "Benchmarks evaluating coding and software development",
            "examples": ["HumanEval", "MBPP", "SWE-bench"],
        },
    ]

    return {
        "categories": default_categories,
        "metadata": {
            "last_updated": datetime.utcnow().isoformat(),
            "category_count": len(default_categories),
            "is_default": True,
        },
        "raw_content": "",
    }


def analyze_benchmark_fit(
    benchmarks: List[str],
    taxonomy: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze how well benchmarks fit into current taxonomy.

    Uses Claude AI to determine which benchmarks are well-categorized
    and which are poor fits for existing categories.

    Args:
        benchmarks: List of benchmark names to analyze
        taxonomy: Current taxonomy structure

    Returns:
        Dictionary with:
            - well_categorized: List of benchmarks that fit well
            - poor_fit: List of benchmarks that don't fit existing categories
            - analysis: Detailed analysis from AI

    Example:
        >>> analysis = analyze_benchmark_fit(
        ...     ["MMLU", "GSM8K", "NewBenchmarkX"],
        ...     taxonomy
        ... )
        >>> print(analysis["poor_fit"])
        ['NewBenchmarkX']
    """
    try:
        if not benchmarks:
            logger.info("No benchmarks to analyze")
            return {
                "well_categorized": [],
                "poor_fit": [],
                "analysis": "No benchmarks provided",
            }

        logger.info(f"Analyzing fit for {len(benchmarks)} benchmarks")

        # Build category summary
        category_names = [cat["name"] for cat in taxonomy.get("categories", [])]

        # Build prompt for Claude
        prompt = f"""Analyze how well these benchmarks fit into the existing taxonomy categories.

EXISTING CATEGORIES:
{json.dumps(category_names, indent=2)}

BENCHMARKS TO ANALYZE:
{json.dumps(benchmarks[:50], indent=2)}  # Limit to 50 for prompt size

For each benchmark, determine if it fits well into one of the existing categories or if it represents a new type that doesn't fit well.

Return JSON with this structure:
{{
  "well_categorized": ["benchmark1", "benchmark2", ...],  // Benchmarks that fit existing categories
  "poor_fit": ["benchmark3", "benchmark4", ...],  // Benchmarks that don't fit well
  "analysis": "Brief explanation of findings"
}}

Consider a benchmark "well categorized" if it clearly belongs to an existing category.
Consider it a "poor fit" if:
- It represents a new evaluation type not covered by existing categories
- It's a hybrid that spans multiple categories in a novel way
- It's domain-specific in a way not captured by current taxonomy
"""

        if not is_anthropic_available():
            logger.warning("Anthropic API not available, using heuristic analysis")
            return _analyze_fit_heuristic(benchmarks, taxonomy)

        result = call_claude_json(prompt=prompt)

        # Validate result
        if not isinstance(result, dict):
            raise ValueError("Invalid response format")

        # Ensure required keys
        well_categorized = result.get("well_categorized", [])
        poor_fit = result.get("poor_fit", [])

        logger.info(
            f"Analysis complete: {len(well_categorized)} well-categorized, "
            f"{len(poor_fit)} poor fit"
        )

        return {
            "well_categorized": well_categorized,
            "poor_fit": poor_fit,
            "analysis": result.get("analysis", ""),
        }

    except Exception as e:
        logger.error(f"Benchmark fit analysis failed: {e}")
        # Return safe default
        return {
            "well_categorized": benchmarks,
            "poor_fit": [],
            "analysis": f"Analysis failed: {e}",
        }


def _analyze_fit_heuristic(
    benchmarks: List[str],
    taxonomy: Dict[str, Any],
) -> Dict[str, Any]:
    """Heuristic fallback for analyzing benchmark fit without AI."""
    # Simple heuristic: Check if benchmark name appears in examples
    all_examples = []
    for cat in taxonomy.get("categories", []):
        all_examples.extend(cat.get("examples", []))

    well_categorized = []
    poor_fit = []

    for bench in benchmarks:
        # Check if benchmark or similar name is in examples
        if any(bench.lower() in ex.lower() or ex.lower() in bench.lower()
               for ex in all_examples):
            well_categorized.append(bench)
        else:
            poor_fit.append(bench)

    return {
        "well_categorized": well_categorized,
        "poor_fit": poor_fit,
        "analysis": "Heuristic analysis (AI not available)",
    }


def propose_new_categories(
    poor_fit_benchmarks: List[str],
    taxonomy: Dict[str, Any],
) -> List[str]:
    """
    Propose new taxonomy categories for poorly-fitting benchmarks.

    Uses Claude AI to analyze benchmarks that don't fit well and suggest
    new categories to add to the taxonomy.

    Args:
        poor_fit_benchmarks: List of benchmark names that don't fit current taxonomy
        taxonomy: Current taxonomy structure

    Returns:
        List of new category names to add

    Example:
        >>> new_cats = propose_new_categories(
        ...     ["AudioBench", "SpeechQA", "VoiceEval"],
        ...     taxonomy
        ... )
        >>> print(new_cats)
        ['Audio & Speech Processing']
    """
    try:
        if not poor_fit_benchmarks:
            logger.info("No poorly-fitting benchmarks, no new categories needed")
            return []

        logger.info(f"Proposing new categories for {len(poor_fit_benchmarks)} benchmarks")

        # Get existing category names
        existing_categories = [cat["name"] for cat in taxonomy.get("categories", [])]

        # Build prompt
        prompt = f"""Analyze these benchmarks that don't fit well into existing taxonomy categories and propose new categories.

EXISTING CATEGORIES:
{json.dumps(existing_categories, indent=2)}

POORLY-FITTING BENCHMARKS:
{json.dumps(poor_fit_benchmarks[:30], indent=2)}  # Limit to 30

Propose new category names that would better organize these benchmarks.

Guidelines:
- Only propose categories if there's a clear pattern (3+ related benchmarks)
- Category names should be descriptive and parallel to existing categories
- Don't propose categories that overlap significantly with existing ones
- Focus on evaluation types, not specific domains

Return JSON with this structure:
{{
  "proposed_categories": [
    {{
      "name": "Category Name",
      "rationale": "Why this category is needed",
      "example_benchmarks": ["bench1", "bench2"]
    }}
  ]
}}

If no new categories are needed (e.g., benchmarks are too diverse or few), return empty list.
"""

        if not is_anthropic_available():
            logger.warning("Anthropic API not available, skipping category proposal")
            return []

        result = call_claude_json(prompt=prompt)

        # Extract category names
        proposed = result.get("proposed_categories", [])
        new_category_names = [cat["name"] for cat in proposed if isinstance(cat, dict)]

        logger.info(f"Proposed {len(new_category_names)} new categories")
        for cat in proposed:
            if isinstance(cat, dict):
                logger.debug(f"  - {cat.get('name')}: {cat.get('rationale', '')}")

        return new_category_names

    except Exception as e:
        logger.error(f"Category proposal failed: {e}")
        return []


def evolve_taxonomy(
    current: Dict[str, Any],
    proposed_categories: List[str],
) -> Dict[str, Any]:
    """
    Evolve taxonomy by merging in new categories.

    Args:
        current: Current taxonomy structure
        proposed_categories: List of new category names to add

    Returns:
        Updated taxonomy structure with new categories

    Example:
        >>> evolved = evolve_taxonomy(
        ...     current_taxonomy,
        ...     ["Audio & Speech Processing", "Time Series Forecasting"]
        ... )
    """
    try:
        if not proposed_categories:
            logger.info("No new categories to add")
            return current

        logger.info(f"Evolving taxonomy with {len(proposed_categories)} new categories")

        # Make a copy of current taxonomy
        evolved = {
            "categories": current.get("categories", []).copy(),
            "metadata": current.get("metadata", {}).copy(),
            "raw_content": current.get("raw_content", ""),
        }

        # Add new categories
        for cat_name in proposed_categories:
            # Check if category already exists
            existing_names = [cat["name"] for cat in evolved["categories"]]
            if cat_name not in existing_names:
                evolved["categories"].append({
                    "name": cat_name,
                    "description": f"Benchmarks for {cat_name.lower()}",
                    "examples": [],
                })
                logger.info(f"Added new category: {cat_name}")

        # Update metadata
        evolved["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        evolved["metadata"]["category_count"] = len(evolved["categories"])

        return evolved

    except Exception as e:
        logger.error(f"Taxonomy evolution failed: {e}")
        return current


def archive_taxonomy_if_changed(
    old: Dict[str, Any],
    new: Dict[str, Any],
    timestamp: str,
) -> Optional[Path]:
    """
    Archive old taxonomy if it differs from new taxonomy.

    Compares old and new taxonomies and creates an archive copy if different.

    Args:
        old: Old taxonomy structure
        new: New taxonomy structure
        timestamp: Timestamp string for archive filename (format: YYYYMMDD)

    Returns:
        Path to archived file if created, None if unchanged

    Example:
        >>> archive_path = archive_taxonomy_if_changed(
        ...     old_taxonomy,
        ...     new_taxonomy,
        ...     "20260402"
        ... )
    """
    try:
        # Compare category structures
        old_categories = sorted([cat["name"] for cat in old.get("categories", [])])
        new_categories = sorted([cat["name"] for cat in new.get("categories", [])])

        if old_categories == new_categories:
            logger.info("Taxonomy unchanged, no archive created")
            return None

        logger.info("Taxonomy changed, creating archive")

        # Create archive directory
        archive_dir = Path(__file__).parent.parent.parent / "archive"
        archive_dir.mkdir(exist_ok=True)

        # Create archive filename
        archive_filename = f"benchmark_taxonomy_{timestamp}.md"
        archive_path = archive_dir / archive_filename

        # Save old taxonomy content
        old_content = old.get("raw_content", "")
        if old_content:
            with open(archive_path, 'w', encoding='utf-8') as f:
                f.write(old_content)
            logger.info(f"Archived taxonomy to {archive_path}")
            return archive_path
        else:
            logger.warning("Old taxonomy has no content to archive")
            return None

    except Exception as e:
        logger.error(f"Taxonomy archiving failed: {e}")
        return None


def update_taxonomy_file(
    taxonomy: Dict[str, Any],
    path: str,
) -> None:
    """
    Update benchmark_taxonomy.md file with new taxonomy.

    Writes updated taxonomy to the markdown file, preserving format
    and adding new categories.

    Args:
        taxonomy: Updated taxonomy structure
        path: Path to benchmark_taxonomy.md file

    Example:
        >>> update_taxonomy_file(evolved_taxonomy, "benchmark_taxonomy.md")
    """
    try:
        taxonomy_path = Path(path)

        # Read current content
        if taxonomy_path.exists():
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        else:
            current_content = ""

        # Build updated content
        updated_content = _build_taxonomy_markdown(taxonomy, current_content)

        # Write updated content
        with open(taxonomy_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        logger.info(f"Updated taxonomy file at {path}")

    except Exception as e:
        logger.error(f"Failed to update taxonomy file: {e}")
        raise RuntimeError(f"Taxonomy file update failed: {e}")


def _build_taxonomy_markdown(
    taxonomy: Dict[str, Any],
    current_content: str,
) -> str:
    """
    Build markdown content for taxonomy file.

    If current_content exists, append new categories.
    Otherwise, create new content.
    """
    categories = taxonomy.get("categories", [])

    if current_content:
        # Append new categories to existing content
        # Find the end of the category sections
        new_sections = []

        for cat in categories:
            cat_name = cat["name"]
            # Check if this category already exists in content
            if cat_name not in current_content:
                # Add new category section
                section = f"""
### {cat_name}

{cat.get("description", "")}

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
"""
                new_sections.append(section)

        if new_sections:
            # Append to current content
            updated = current_content.rstrip() + "\n\n" + "\n".join(new_sections)
            return updated
        else:
            return current_content
    else:
        # Create new content from scratch
        content_parts = [
            "# LLM/VLM/Audio-Language Model Benchmark Taxonomy",
            "",
            f"**Last Updated:** {datetime.utcnow().strftime('%B %Y')}",
            "**Purpose:** Inform AI prompts for extraction and classification of benchmarks from model cards",
            "",
            "---",
            "",
            "## Categories",
            "",
        ]

        for i, cat in enumerate(categories, 1):
            content_parts.extend([
                f"### {i}. {cat['name']}",
                "",
                cat.get("description", ""),
                "",
                "| Benchmark | Description | Typical Metrics |",
                "|-----------|-------------|-----------------|",
                "",
            ])

        return "\n".join(content_parts)
