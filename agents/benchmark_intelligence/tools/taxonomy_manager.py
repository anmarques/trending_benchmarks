"""
Adaptive taxonomy evolution for benchmark categorization.

This module manages the benchmark taxonomy lifecycle:
- Loading current taxonomy from benchmark_taxonomy.md
- Analyzing benchmark fit against taxonomy
- Proposing new categories based on poor-fit benchmarks
- Evolving taxonomy with new categories
- Archiving taxonomy versions when changes occur
- Managing taxonomy.json with domain classification
- Supporting manual category overrides from config.yaml
"""

import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
import yaml

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

    Compares old and new taxonomies using content hash and creates an archive copy if different.

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
        # Compare category structures using hash for accurate change detection
        old_categories = sorted([cat["name"] for cat in old.get("categories", [])])
        new_categories = sorted([cat["name"] for cat in new.get("categories", [])])

        # Compute hashes of category lists
        old_hash = hashlib.sha256(str(old_categories).encode('utf-8')).hexdigest()
        new_hash = hashlib.sha256(str(new_categories).encode('utf-8')).hexdigest()

        if old_hash == new_hash:
            logger.info("Taxonomy unchanged (hash match), no archive created")
            return None

        logger.info(f"Taxonomy changed (hash mismatch: {old_hash[:8]} -> {new_hash[:8]}), creating archive")

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


def load_taxonomy_json(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load taxonomy from taxonomy.json file.

    T085: Supports dynamic category addition with domain classification.

    Args:
        path: Path to taxonomy.json file (defaults to tools/taxonomy.json)

    Returns:
        Dictionary containing:
            - version: Taxonomy version string
            - last_updated: ISO timestamp
            - domains: List of domain definitions
            - benchmarks: List of benchmark entries with domain, is_emerging, is_almost_extinct
            - category_overrides: Manual overrides from config

    Example:
        >>> taxonomy = load_taxonomy_json()
        >>> print(taxonomy["version"])
        '1.0.0'
    """
    if path is None:
        path = str(Path(__file__).parent / "taxonomy.json")

    taxonomy_path = Path(path)

    if not taxonomy_path.exists():
        logger.warning(f"Taxonomy JSON not found at {path}, creating default")
        return _create_default_taxonomy_json()

    try:
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            taxonomy = json.load(f)

        logger.info(f"Loaded taxonomy version {taxonomy.get('version')} from {path}")
        return taxonomy

    except Exception as e:
        logger.error(f"Failed to load taxonomy JSON from {path}: {e}")
        return _create_default_taxonomy_json()


def _create_default_taxonomy_json() -> Dict[str, Any]:
    """Create default taxonomy.json structure."""
    return {
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat(),
        "domains": [
            {
                "name": "language",
                "description": "Language understanding and generation benchmarks",
                "categories": ["Knowledge & General Understanding", "Reasoning & Commonsense"]
            },
            {
                "name": "multimodal",
                "description": "Multimodal benchmarks combining text, vision, audio",
                "categories": ["Vision & Multimodal", "Audio & Speech Processing"]
            },
            {
                "name": "coding",
                "description": "Code generation and software engineering benchmarks",
                "categories": ["Code Generation & Software Engineering"]
            },
            {
                "name": "math",
                "description": "Mathematical problem solving benchmarks",
                "categories": ["Mathematical Reasoning"]
            }
        ],
        "benchmarks": [],
        "category_overrides": {}
    }


def add_benchmark_to_taxonomy(
    canonical_name: str,
    domain: str,
    is_emerging: bool = False,
    is_almost_extinct: bool = False,
    taxonomy_path: Optional[str] = None
) -> None:
    """
    Add a benchmark to the taxonomy.json file.

    T085: Implements dynamic benchmark addition to taxonomy with domain classification.

    Args:
        canonical_name: Canonical benchmark name
        domain: Domain classification (language, multimodal, vision, reasoning, coding, math, knowledge)
        is_emerging: Whether benchmark is emerging (recently introduced)
        is_almost_extinct: Whether benchmark is almost extinct (rarely used)
        taxonomy_path: Path to taxonomy.json file (defaults to tools/taxonomy.json)

    Example:
        >>> add_benchmark_to_taxonomy("NewBenchmark", "reasoning", is_emerging=True)
    """
    if taxonomy_path is None:
        taxonomy_path = str(Path(__file__).parent / "taxonomy.json")

    # Load current taxonomy
    taxonomy = load_taxonomy_json(taxonomy_path)

    # Check if benchmark already exists
    existing_benchmarks = {b["canonical_name"]: b for b in taxonomy.get("benchmarks", [])}

    if canonical_name in existing_benchmarks:
        # Update existing benchmark
        existing_benchmarks[canonical_name]["domain"] = domain
        existing_benchmarks[canonical_name]["is_emerging"] = is_emerging
        existing_benchmarks[canonical_name]["is_almost_extinct"] = is_almost_extinct
        existing_benchmarks[canonical_name]["last_seen"] = datetime.utcnow().isoformat()
        logger.info(f"Updated benchmark '{canonical_name}' in taxonomy")
    else:
        # Add new benchmark
        new_benchmark = {
            "canonical_name": canonical_name,
            "domain": domain,
            "is_emerging": is_emerging,
            "is_almost_extinct": is_almost_extinct,
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat()
        }
        taxonomy["benchmarks"].append(new_benchmark)
        logger.info(f"Added new benchmark '{canonical_name}' to taxonomy (domain: {domain})")

    # Update version and timestamp
    taxonomy["last_updated"] = datetime.utcnow().isoformat()

    # Save updated taxonomy
    _save_taxonomy_json(taxonomy, taxonomy_path)


def _save_taxonomy_json(taxonomy: Dict[str, Any], path: str) -> None:
    """Save taxonomy to JSON file."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(taxonomy, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved taxonomy to {path}")
    except Exception as e:
        logger.error(f"Failed to save taxonomy JSON: {e}")
        raise


def populate_taxonomy_from_mentions(
    benchmark_mentions: List[Dict[str, Any]],
    taxonomy_path: Optional[str] = None
) -> None:
    """
    Auto-populate taxonomy from benchmark_mentions table status.

    T085: Automatically populates is_emerging and is_almost_extinct flags
    from benchmark_mentions table status field.

    Args:
        benchmark_mentions: List of benchmark mention records with status field
                           (status: 'emerging', 'active', 'almost_extinct')
        taxonomy_path: Path to taxonomy.json file

    Example:
        >>> mentions = [
        ...     {"canonical_name": "MMLU", "status": "active"},
        ...     {"canonical_name": "NewBench", "status": "emerging"}
        ... ]
        >>> populate_taxonomy_from_mentions(mentions)
    """
    if taxonomy_path is None:
        taxonomy_path = str(Path(__file__).parent / "taxonomy.json")

    taxonomy = load_taxonomy_json(taxonomy_path)

    for mention in benchmark_mentions:
        canonical_name = mention.get("canonical_name")
        status = mention.get("status", "active")

        if not canonical_name:
            continue

        # Determine flags from status
        is_emerging = (status == "emerging")
        is_almost_extinct = (status == "almost_extinct")

        # Classify domain (use AI or heuristic)
        domain = _classify_benchmark_domain(canonical_name, taxonomy)

        # Add/update benchmark
        add_benchmark_to_taxonomy(
            canonical_name=canonical_name,
            domain=domain,
            is_emerging=is_emerging,
            is_almost_extinct=is_almost_extinct,
            taxonomy_path=taxonomy_path
        )


def _classify_benchmark_domain(
    benchmark_name: str,
    taxonomy: Dict[str, Any]
) -> str:
    """
    Classify benchmark into a domain using heuristics.

    Falls back to 'knowledge' domain if classification is uncertain.

    Args:
        benchmark_name: Benchmark name to classify
        taxonomy: Current taxonomy structure

    Returns:
        Domain name (language, multimodal, vision, reasoning, coding, math, knowledge)
    """
    name_lower = benchmark_name.lower()

    # Heuristic classification based on name patterns
    if any(kw in name_lower for kw in ["code", "humaneval", "mbpp", "swe", "programming"]):
        return "coding"
    elif any(kw in name_lower for kw in ["math", "gsm", "aime", "olympiad"]):
        return "math"
    elif any(kw in name_lower for kw in ["vision", "image", "vqa", "coco", "imagenet"]):
        return "vision"
    elif any(kw in name_lower for kw in ["multimodal", "vlm", "audio", "video", "speech"]):
        return "multimodal"
    elif any(kw in name_lower for kw in ["reason", "logic", "arc", "hellaswag", "piqa"]):
        return "reasoning"
    elif any(kw in name_lower for kw in ["mmlu", "knowledge", "qa", "trivia"]):
        return "knowledge"
    else:
        # Default to knowledge domain
        return "knowledge"


def load_category_overrides(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load manual category overrides from config.yaml.

    T088: Supports manual category overrides via config.yaml.

    Args:
        config_path: Path to config.yaml file (defaults to repo root)

    Returns:
        Dictionary mapping benchmark names to category overrides

    Example:
        >>> overrides = load_category_overrides()
        >>> print(overrides.get("MMLU"))  # "Knowledge & General Understanding"
    """
    if config_path is None:
        # Try to find config.yaml in repo root
        config_path = str(Path(__file__).parent.parent.parent.parent / "config.yaml")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        overrides = config.get("taxonomy", {}).get("category_overrides", {})
        logger.info(f"Loaded {len(overrides)} category overrides from config")
        return overrides

    except FileNotFoundError:
        logger.debug(f"Config file not found at {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load category overrides from config: {e}")
        return {}


def apply_category_overrides(
    benchmarks: List[Dict[str, Any]],
    config_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Apply manual category overrides to benchmark categorization results.

    T088: Manual overrides from config.yaml take precedence over AI classification.

    Args:
        benchmarks: List of benchmark categorization results
        config_path: Path to config.yaml file

    Returns:
        Updated benchmarks list with overrides applied

    Example:
        >>> benchmarks = [{"name": "MMLU", "category": "Knowledge"}]
        >>> updated = apply_category_overrides(benchmarks)
    """
    overrides = load_category_overrides(config_path)

    if not overrides:
        return benchmarks

    updated_benchmarks = []
    override_count = 0

    for benchmark in benchmarks:
        benchmark_name = benchmark.get("name") or benchmark.get("canonical_name")
        if not benchmark_name:
            updated_benchmarks.append(benchmark)
            continue

        # Check for override
        if benchmark_name in overrides:
            override_category = overrides[benchmark_name]
            original_category = benchmark.get("category")

            benchmark["category"] = override_category
            benchmark["category_source"] = "manual_override"

            if original_category != override_category:
                logger.info(
                    f"Override applied: '{benchmark_name}' category changed from "
                    f"'{original_category}' to '{override_category}'"
                )
                override_count += 1

        updated_benchmarks.append(benchmark)

    if override_count > 0:
        logger.info(f"Applied {override_count} category overrides")

    return updated_benchmarks
