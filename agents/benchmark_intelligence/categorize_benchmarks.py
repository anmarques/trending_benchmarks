"""
Stage 5: Benchmark Categorization

Categorizes benchmarks into taxonomy categories. This MVP version uses
simple rule-based categorization. Full taxonomy evolution with AI-powered
classification is deferred to Phase 6 (User Story 4).

This is a standalone stage script with CLI entry point.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.stage_utils import (
    load_stage_json,
    save_stage_json,
    find_latest_stage_output
)
from agents.benchmark_intelligence.tools.taxonomy_manager import (
    load_taxonomy_json,
    apply_category_overrides
)
from agents.benchmark_intelligence.tools._claude_client import call_claude_json, is_anthropic_available


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# Taxonomy (rule-based keywords for common benchmarks)
TAXONOMY_RULES = {
    'knowledge': [
        'arc', 'boolq', 'cmmlu', 'commonsense', 'naturalquestions',
        'obqa', 'openbookqa', 'piqa', 'race', 'simpleqa', 'squad',
        'triviaqa', 'truthfulqa', 'webquest', 'wikitext'
    ],
    'reasoning': [
        'bbh', 'bigbench', 'drop', 'gpqa', 'hellaswag', 'lsat',
        'logiqa', 'musr', 'siqa', 'socialiq', 'winogrande', 'zebralogic'
    ],
    'math': [
        'aime', 'amc', 'cmath', 'deepmindmath', 'gsm', 'imo',
        'math', 'mathvista', 'mgsm', 'minif2f', 'olympiad', 'sat'
    ],
    'coding': [
        'bigcodebench', 'codeforces', 'crux', 'design2code', 'humaneval',
        'livecode', 'mbpp', 'multiple', 'ojbench', 'repoqa', 'swebench'
    ],
    'instruction': [
        'followir', 'ifeval', 'ifbench', 'instructionfollowing'
    ],
    'alignment': [
        'alpacaeval', 'alignbench', 'arenahard', 'hhem', 'livebench',
        'mtbench', 'writingbench'
    ],
    'agent': [
        'acebench', 'androidworld', 'apibank', 'apibench', 'bfcl',
        'ccbench', 'muirbench', 'osworld', 'screenspot', 'taubench',
        'tirbench', 'windowsagent', 'zerobench', 'τ2bench', 'τ²bench'
    ],
    'longcontext': [
        'infinitebench', 'longbench', 'longcode', 'longvideo',
        'mmlongbench', 'quality', 'ruler', 'squality'
    ],
    'vision': [
        '7scenes', 'activitynet', 'ai2d', 'blink', 'charades', 'chartqa',
        'countbench', 'cvbench', 'dl3dv', 'docvqa', 'dtu', 'embspatial',
        'gotbenchmark', 'hallusion', 'ibims', 'infovqa', 'lvbench',
        'medxpert', 'mhalu', 'mlvu', 'mmbench', 'mmmu', 'mmstar', 'mmvet',
        'mmvu', 'motionbench', 'mtvqa', 'mvbench', 'next', 'nyuv2',
        'ocrbench', 'odinw', 'okvqa', 'omnidocbench', 'perception',
        'pmcvqa', 'realworldqa', 'refcoco', 'refspatial', 'rtvlm',
        'simplevqa', 'slake', 'sunrgbd', 'textvqa', 'tvqa', 'videomme',
        'videomu', 'vitabench', 'vizwiz', 'vlmsareblind', 'vqav2',
        'vsibench', 'websrc'
    ],
    'retrieval': [
        'climatefever', 'cmteb', 'frames', 'mldr', 'mmteb', 'mteb',
        'nanoscifact', 'paws', 'sickr', 'stsbenchmark', 'treccovid',
        'twittersemeval'
    ],
    'multilingual': [
        'ceval', 'fleurs', 'flores', 'mmmlu', 'multilingualmmlu', 'wmt'
    ],
    'audio': [
        'aishell', 'alimeeting', 'chime', 'covost', 'fleurs',
        'librispeech', 'spgispeech', 'switchboard'
    ],
    'safety': [
        'jbbq', 'safetybench', 'saladbench', 'vlguard'
    ],
    'timeseries': [
        'smd', 'tsbad', 'uea'
    ],
}


def categorize_benchmark(benchmark_name: str) -> List[str]:
    """
    Categorize a benchmark using simple rule-based matching.

    Args:
        benchmark_name: Canonical benchmark name (normalized)

    Returns:
        List of category names (can be multiple categories)

    Example:
        >>> categorize_benchmark("MMLU")
        ['knowledge']
        >>> categorize_benchmark("HumanEval")
        ['coding']
    """
    if not benchmark_name:
        return ['uncategorized']

    # Normalize for matching
    name_lower = benchmark_name.lower().replace('-', '').replace('_', '').replace(' ', '')

    categories = []

    # Check each taxonomy category
    for category, keywords in TAXONOMY_RULES.items():
        for keyword in keywords:
            if keyword in name_lower:
                if category not in categories:
                    categories.append(category)
                break

    # If no category matched, mark as uncategorized
    if not categories:
        categories = ['uncategorized']

    return categories


def review_categorization_with_ai(benchmarks_with_categories: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Single AI call to review and correct categorization for ALL benchmarks.

    More efficient and provides better context than per-benchmark categorization.
    AI can see patterns across all benchmarks and ensure consistency.

    Args:
        benchmarks_with_categories: List of dicts with 'name' and 'current_category'

    Returns:
        Dict mapping benchmark_name -> corrected_category

    Example:
        >>> review_categorization_with_ai([
        ...     {"name": "GPQA Diamond", "current_category": "uncategorized"},
        ...     {"name": "MMLU", "current_category": "knowledge"}
        ... ])
        {"GPQA Diamond": "knowledge", "MMLU": "knowledge"}
    """
    if not is_anthropic_available():
        logger.warning("AI categorization unavailable, keeping current categories")
        return {}

    # Available categories with descriptions
    categories_desc = {
        "knowledge": "General knowledge, QA, facts (ARC, TriviaQA, SimpleQA, BoolQ, RACE)",
        "reasoning": "Logical reasoning, inference (BIG-Bench Hard, GPQA, DROP, HellaSwag, WinoGrande)",
        "math": "Mathematical reasoning, problem solving (GSM8K, MATH, AIME, OlympiadBench)",
        "coding": "Programming, code generation, software engineering (HumanEval, MBPP, SWE-Bench, LiveCodeBench)",
        "instruction": "Following instructions precisely (IF-Eval, IFBench, FollowIR)",
        "alignment": "Model comparison, human preference, dialogue quality (AlpacaEval, Arena-Hard, MT-Bench, LiveBench)",
        "agent": "Interactive agents, tool use, function calling (OSWorld, TauBench, API-Bench, BFCL)",
        "longcontext": "Long document/context understanding (RULER, LongBench, InfiniteBench, QuALITY)",
        "vision": "Visual understanding, VQA, OCR, multimodal (MMMU, DocVQA, VideoMME, ChartQA)",
        "retrieval": "Embedding, retrieval, semantic similarity (MTEB, MLDR, FRAMES, STSBenchmark)",
        "multilingual": "Cross-lingual, translation (FLORES, C-EVAL, MMMLU, WMT)",
        "audio": "Speech recognition, audio processing (LibriSpeech, FLEURS, AISHELL)",
        "safety": "Safety, toxicity, bias, fairness (SafetyBench, JBBQ, VLGuard)",
        "timeseries": "Time series analysis, forecasting (TSB-AD, UEA, SMD)"
    }

    categories_list = "\n".join([f"- **{cat}**: {desc}" for cat, desc in categories_desc.items()])

    # Format benchmark list
    benchmark_list = []
    for b in benchmarks_with_categories:
        name = b['name']
        current_cat = b['current_category']
        benchmark_list.append(f"  - {name}: {current_cat}")

    benchmarks_str = "\n".join(benchmark_list[:250])  # Limit to fit in context
    if len(benchmark_list) > 250:
        benchmarks_str += f"\n  ... and {len(benchmark_list) - 250} more"

    prompt = f"""
Review and correct the categorization of {len(benchmarks_with_categories)} AI evaluation benchmarks.

**Available Categories**:
{categories_list}

**Current Categorization** (name: current_category):
{benchmarks_str}

**Your Task**:
1. Review each benchmark's current category
2. For "uncategorized" benchmarks: assign the best category based on the benchmark name
3. For already categorized benchmarks: verify correctness, suggest corrections if needed
4. Ensure similar benchmarks get consistent categories (e.g., GPQA and GPQA Diamond)
5. Consider the full context - seeing all benchmarks together helps spot patterns

**Important Guidelines**:
- **knowledge** vs **reasoning**: GPQA is reasoning (knowledge-intensive reasoning), not knowledge
- **instruction** vs **reasoning**: IF-Eval, IFBench are instruction, not reasoning
- **longcontext** vs **reasoning/vision**: RULER, LongBench, InfiniteBench are longcontext
- **alignment**: AlpacaEval, Arena-Hard, MT-Bench, LiveBench are alignment (human preference/dialogue)
- **retrieval** vs **multilingual**: MTEB is retrieval (embedding/semantic similarity), not multilingual
- **agent** includes tool use, function calling (API-Bench, BFCL, ZeroBench, OSWorld)
- **vision**: Design2Code can be vision or coding depending on context
- Ensure variant consistency: GPQA ≈ GPQA Diamond, MMMU ≈ MMMU Pro, AIME ≈ AIME 2024 ≈ AIME 2025

**Output JSON**:
{{
  "corrections": {{
    "GPQA Diamond": "knowledge",
    "LiveCodeBench": "coding",
    "IF-Eval": "comparison",
    ... only include benchmarks that need categorization or correction
  }},
  "summary": "Brief summary of changes (1-2 sentences)"
}}

**Important**:
- Only include benchmarks in "corrections" that need changes (uncategorized → category, or wrong category → correct category)
- Do NOT include benchmarks that are already correctly categorized
- Use lowercase category names
"""

    try:
        result = call_claude_json(prompt=prompt, max_tokens=4096)
        corrections = result.get('corrections', {})
        summary = result.get('summary', 'No summary provided')

        # Validate all categories
        valid_categories = set(categories_desc.keys()) | {'uncategorized'}
        validated_corrections = {}

        for name, category in corrections.items():
            if category.lower() in valid_categories:
                validated_corrections[name] = category.lower()
            else:
                logger.warning(f"AI returned invalid category '{category}' for '{name}', ignoring")

        logger.info(f"  AI Summary: {summary}")
        logger.info(f"  Corrections: {len(validated_corrections)} benchmarks")

        return validated_corrections

    except Exception as e:
        logger.error(f"AI categorization review failed: {e}")
        return {}


def run(input_json: Optional[str] = None, use_ai: bool = True) -> str:
    """
    Execute Stage 5: Benchmark categorization.

    Reads consolidated benchmarks from Stage 4 output, applies taxonomy
    categorization, and outputs standardized JSON.

    Args:
        input_json: Path to consolidate_names JSON output (auto-finds if not specified)

    Returns:
        Path to generated JSON output file

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If categorization fails
    """
    logger.info("=" * 70)
    logger.info("Stage 5: Benchmark Categorization")
    logger.info("=" * 70)

    # Load input from Stage 4
    if input_json is None:
        input_json = find_latest_stage_output("consolidate_names")
        if input_json is None:
            raise FileNotFoundError(
                "No consolidate_names output found. Run Stage 4 first."
            )
        logger.info(f"Auto-discovered input: {Path(input_json).name}")
    else:
        logger.info(f"Using input: {input_json}")

    # Load and validate Stage 4 output
    stage4_data = load_stage_json(input_json)
    benchmarks = stage4_data['data']

    # Preserve metadata from Stage 4
    stage4_metadata = stage4_data.get('metadata', {})
    models_without_benchmarks = stage4_metadata.get('models_without_benchmarks', 0)

    logger.info(f"Configuration:")
    logger.info(f"  Benchmarks to categorize: {len(benchmarks)}")
    logger.info(f"  Taxonomy version: MVP-v1 (rule-based)")
    logger.info(f"  Available categories: {len(TAXONOMY_RULES)}")
    if models_without_benchmarks > 0:
        logger.info(f"  Models without benchmarks: {models_without_benchmarks}")

    if not benchmarks:
        logger.warning("No benchmarks found in input - output will be empty")
        output_data = []
    else:
        logger.info(f"\nCategorizing benchmarks...")

        # T087: Load current taxonomy to track changes
        try:
            taxonomy = load_taxonomy_json()
            taxonomy_version = taxonomy.get("version", "MVP-v1")
            existing_categories = set()
            for domain in taxonomy.get("domains", []):
                existing_categories.update(domain.get("categories", []))
            logger.info(f"  Loaded taxonomy version: {taxonomy_version}")
        except Exception as e:
            logger.warning(f"Failed to load taxonomy.json: {e}, using MVP taxonomy")
            taxonomy_version = "MVP-v1"
            existing_categories = set(TAXONOMY_RULES.keys())

        # Categorize each benchmark
        output_data = []
        category_counts = {}
        new_categories = set()  # T087: Track newly created categories

        # First pass: Rule-based categorization
        for benchmark in benchmarks:
            canonical_name = benchmark.get('canonical_name', '')
            categories = categorize_benchmark(canonical_name)
            benchmark['_categories'] = categories  # Temporary storage

        # Second pass: Single AI call to review all categorizations
        if use_ai and is_anthropic_available():
            # Prepare data for AI review
            benchmarks_for_review = [
                {
                    'name': b.get('canonical_name', ''),
                    'current_category': b['_categories'][0]
                }
                for b in benchmarks
            ]

            uncategorized_count = sum(1 for b in benchmarks if b['_categories'] == ['uncategorized'])

            logger.info(f"\nAI Categorization Review:")
            logger.info(f"  Rule-based categorized: {len(benchmarks) - uncategorized_count}")
            logger.info(f"  Uncategorized: {uncategorized_count}")
            logger.info(f"  Sending all {len(benchmarks)} benchmarks to AI for review...")
            logger.info("")

            # Single AI call reviews all benchmarks
            corrections = review_categorization_with_ai(benchmarks_for_review)

            # Apply corrections
            ai_corrected = 0
            for benchmark in benchmarks:
                canonical_name = benchmark.get('canonical_name', '')
                if canonical_name in corrections:
                    new_category = corrections[canonical_name]
                    old_category = benchmark['_categories'][0]
                    benchmark['_categories'] = [new_category]
                    benchmark['_ai_categorized'] = True
                    ai_corrected += 1

                    if old_category == 'uncategorized':
                        logger.info(f"  {canonical_name}: uncategorized → {new_category}")
                    else:
                        logger.info(f"  {canonical_name}: {old_category} → {new_category} (corrected)")

            logger.info(f"\n✓ AI review complete:")
            logger.info(f"  Corrections applied: {ai_corrected}")

        # Build final output
        for benchmark in benchmarks:
            canonical_name = benchmark.get('canonical_name', '')
            categories = benchmark.get('_categories', ['uncategorized'])

            # T087: Check if any category is newly created
            newly_created = False
            for cat in categories:
                if cat not in existing_categories and cat != 'uncategorized':
                    new_categories.add(cat)
                    newly_created = True

            # Track category distribution
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # Create output entry
            output_entry = {
                'canonical_name': canonical_name,
                'categories': categories,
                'primary_category': categories[0] if categories else 'uncategorized',
                'taxonomy_version': taxonomy_version,
                'newly_created_category': newly_created,
                'ai_categorized': benchmark.get('_ai_categorized', False),
                # Preserve metadata from Stage 4
                'mention_count': benchmark.get('mention_count', 0),
                'model_count': benchmark.get('model_count', 0),
                'variant_count': benchmark.get('variant_count', 0),
            }
            output_data.append(output_entry)

        # T088: Apply manual category overrides from config.yaml
        logger.info(f"\nApplying category overrides...")
        output_data = apply_category_overrides(output_data)

        # Statistics
        logger.info(f"\n✓ Categorization complete:")
        logger.info(f"  Benchmarks categorized: {len(output_data)}")
        logger.info(f"\n  Distribution by category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {category}: {count} benchmarks")

        # T087: Report taxonomy changes
        if new_categories:
            logger.info(f"\n  New categories created: {len(new_categories)}")
            for cat in sorted(new_categories):
                logger.info(f"    - {cat}")

    # T087: Build taxonomy_changes section
    taxonomy_changes = {
        "new_categories": list(new_categories) if 'new_categories' in locals() else [],
        "categories_modified": [],  # Future enhancement: track category definition changes
        "taxonomy_version": taxonomy_version if 'taxonomy_version' in locals() else "MVP-v1"
    }

    # Save standardized JSON output with preserved metadata
    output_path = save_stage_json(
        data=output_data,
        stage_name="categorize_benchmarks",
        input_count=len(benchmarks),
        errors=[],
        metadata={
            "models_without_benchmarks": models_without_benchmarks,
            "taxonomy_changes": taxonomy_changes  # T087: Add taxonomy changes to output
        }
    )

    logger.info(f"\n✓ Stage 5 complete")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 70)

    return output_path


def main():
    """CLI entry point for Stage 5."""
    parser = argparse.ArgumentParser(
        description="Stage 5: Categorize benchmarks into taxonomy"
    )
    parser.add_argument(
        "--input",
        help="Path to consolidate_names JSON output (auto-finds if not specified)"
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        default=True,
        help="Use AI to categorize uncategorized benchmarks (default: True)"
    )
    parser.add_argument(
        "--no-ai",
        dest="use_ai",
        action="store_false",
        help="Disable AI categorization, use rule-based only"
    )

    args = parser.parse_args()

    try:
        output_path = run(args.input, use_ai=args.use_ai)
        print(f"\n✓ Success! Output saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Stage 5 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
