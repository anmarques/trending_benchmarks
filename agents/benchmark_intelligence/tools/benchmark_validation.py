"""
Benchmark validation and filtering utilities.

Provides multi-layer validation to ensure extracted benchmarks are real benchmarks
and not model names, random words, or other false positives.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from ._claude_client import call_claude_json, is_anthropic_available

logger = logging.getLogger(__name__)


# Known AI model name patterns (compiled regex for performance)
MODEL_NAME_PATTERNS = [
    # Major model families
    r'\bqwen[-\s]?\d+',
    r'\bllama[-\s]?\d+',
    r'\bgpt[-\s]?\d+',
    r'\bclaude[-\s]?\d+',
    r'\bgemini[-\s]?\d+',
    r'\bmistral[-\s]?\d+',
    r'\bphi[-\s]?\d+',
    r'\bdeepseek[-\s]?\w+',
    r'\bglm[-\s]?\d+',
    r'\binternlm[-\s]?\d+',
    r'\bministral[-\s]?\d+',
    r'\bgranite[-\s]?\d+',
    r'\bnemotron[-\s]?\d+',
    r'\bvicuna[-\s]?\d+',
    r'\balpaca[-\s]?\d+',
    r'\bmpt[-\s]?\d+',
    r'\bfalcon[-\s]?\d+',
    r'\bstarcoder[-\s]?\d+',
    r'\bcodellama[-\s]?\d+',
    r'\bwizardlm[-\s]?\d+',

    # Specific model products (with names, not just patterns)
    r'\bllama\s+\w+\s+(guard|prompt)',  # "Llama Prompt Guard"
    r'\bgemini\s+embedding',  # "Gemini Embedding"
    r'\bgranite[-\s]?embedding',  # "granite-embedding-english-r2"
    r'\b(openai|anthropic|meta|google|microsoft)[-\s]?\w+',  # Company prefixed models

    # Model size indicators (e.g., "8B", "70B", "405B")
    r'\b\d+[bmk]\b',  # 8B, 70B, 1M, etc.
    r'\b\d+\.\d+[bmk]\b',  # 3.5B, 1.5B, etc.

    # Instruct/Chat/Embedding variants
    r'[-\s]?instruct\b',
    r'[-\s]?chat\b',
    r'[-\s]?turbo\b',
    r'[-\s]?preview\b',
    r'[-\s]?embedding[-\s]?',
]

# Compile patterns for performance
COMPILED_MODEL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in MODEL_NAME_PATTERNS]


def is_valid_benchmark_name(benchmark_name: str) -> bool:
    """
    Apply heuristic filters to determine if a name is likely a valid benchmark.

    Fast programmatic checks before more expensive AI validation.

    Args:
        benchmark_name: Extracted benchmark name to validate

    Returns:
        True if passes heuristic checks, False if clearly invalid

    Examples:
        >>> is_valid_benchmark_name("MMLU")
        True
        >>> is_valid_benchmark_name("Qwen3-8B")
        False
        >>> is_valid_benchmark_name("spotting")
        False
    """
    if not benchmark_name or not isinstance(benchmark_name, str):
        return False

    name = benchmark_name.strip()

    if not name:
        return False

    # Filter 1: Check against model name patterns
    for pattern in COMPILED_MODEL_PATTERNS:
        if pattern.search(name):
            logger.debug(f"Rejected '{name}': matches model pattern {pattern.pattern}")
            return False

    # Filter 2: Reject single generic words
    # Exception: Known benchmarks (even if short)
    KNOWN_SHORT_BENCHMARKS = {
        'mmlu', 'math', 'arc', 'gsm8k', 'mteb', 'glue', 'squad', 'race',
        'swag', 'winogrande', 'boolq', 'piqa', 'siqa', 'hellaswag',
        'aime', 'sat', 'act', 'gre', 'toefl', 'ielts', 'mbpp', 'apps',
        'humaneval', 'truthfulqa', 'gpqa', 'livebench', 'ifeval'
    }

    # Reject common English words that are clearly not benchmarks
    GENERIC_WORDS = {
        'spotting', 'reasoning', 'evaluation', 'testing', 'performance',
        'accuracy', 'score', 'metric', 'test', 'eval', 'benchmark',
        'model', 'data', 'training', 'inference', 'validation',
        'multimodal', 'document', 'context', 'parsing', 'length'
    }

    # Reject category/section headers (often appear in model cards)
    CATEGORY_PHRASES = {
        'general multimodal', 'long document', 'long context', 'context length',
        'reasoning mode', 'document parsing', 'text reasoning', 'image reasoning',
        'video reasoning', 'novel logical reasoning'
    }

    if name.lower() in GENERIC_WORDS:
        logger.debug(f"Rejected '{name}': generic word")
        return False

    # Check for category phrases
    if name.lower() in CATEGORY_PHRASES:
        logger.debug(f"Rejected '{name}': category/section header")
        return False

    # Filter: Reject markdown formatting (section headers from model cards)
    # **Text**, ##Text, ###Text, etc.
    if name.startswith('**') or name.startswith('##') or name.endswith('**'):
        logger.debug(f"Rejected '{name}': markdown formatting")
        return False

    # Filter: Reject text in square brackets [Description]
    # These are usually metadata or descriptions, not benchmark names
    if name.startswith('[') and name.endswith(']'):
        logger.debug(f"Rejected '{name}': bracketed description")
        return False

    # Filter: Reject training data descriptions
    # "Synthetic X", "X SFT", "Common Crawl X"
    training_patterns = [
        r'\bsft\b',  # Supervised Fine-Tuning
        r'^synthetic\s+\w+$',  # "Synthetic Math", "Synthetic Code"
        r'^common\s+crawl\s+\w+$',  # "Common Crawl Code"
        r'\bembedding\b',  # Embedding models, not benchmarks
    ]
    for pattern in training_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            logger.debug(f"Rejected '{name}': training data description")
            return False

    if len(name.split()) == 1 and len(name) < 10:
        if name.lower() not in KNOWN_SHORT_BENCHMARKS:
            # Allow if it contains:
            # - Numbers (GSM8K, C4, etc.)
            # - Uppercase letters (MMLU, ARC, etc.)
            # - Greek letters (τ²bench, μBench, etc.)
            # - Mathematical notation (superscripts, subscripts)
            has_numbers = re.search(r'\d', name)
            has_caps_structure = bool(re.search(r'[A-Z]{2,}', name))  # At least 2 caps in a row

            # Check for Greek letters
            greek_letters = set('αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ')
            has_greek = any(c in greek_letters for c in name)

            # Check for mathematical notation (superscripts, subscripts)
            math_notation = set('²³¹₂₃₁⁰⁴⁵⁶⁷⁸⁹₀')
            has_math_notation = any(c in math_notation for c in name)

            if not (has_numbers or has_caps_structure or has_greek or has_math_notation):
                logger.debug(f"Rejected '{name}': single generic word")
                return False

    # Filter 3: Reject if contains "from [Model]" pattern
    if re.search(r'\bfrom\s+\w+', name, re.IGNORECASE):
        logger.debug(f"Rejected '{name}': contains 'from [Model]' pattern")
        return False

    # Filter 4: Reject unicode artifacts or encoded characters
    # Allow Greek letters (common in math benchmarks) but reject \uXXXX patterns
    # Also reject tool names with special unicode characters like τ²bench
    if '\\u' in name or '\\x' in name:
        logger.debug(f"Rejected '{name}': contains unicode escape sequences")
        return False

    # Allow Greek letters and mathematical notation in benchmark names
    # (e.g., τ²bench, μBench, etc. are valid benchmarks)
    # Only reject if it's ONLY unicode escapes without readable text

    # Filter 5: Reject pure URLs or badges
    if name.startswith('http') or name.startswith('![') or name.startswith('[!['):
        logger.debug(f"Rejected '{name}': URL or badge syntax")
        return False

    # Filter 6: Reject if it's mostly punctuation or special characters
    alphanumeric_chars = sum(c.isalnum() for c in name)
    if len(name) > 0 and alphanumeric_chars / len(name) < 0.5:
        logger.debug(f"Rejected '{name}': too many special characters")
        return False

    # Passed all heuristic filters
    return True


def normalize_benchmark_name(benchmark_name: str) -> str:
    """
    Normalize benchmark name by applying standard transformation rules.

    Handles:
    - AIME variant consolidation (AIME24 → AIME 2024, AIME25 → AIME 2025)
    - Removing "from [Model]" suffixes
    - Cleaning "Synthetic X from Y" patterns

    Args:
        benchmark_name: Raw benchmark name

    Returns:
        Normalized benchmark name

    Examples:
        >>> normalize_benchmark_name("AIME24")
        "AIME 2024"
        >>> normalize_benchmark_name("MT-AIME24")
        "AIME 2024"
        >>> normalize_benchmark_name("Synthetic SWE-Gym from Qwen3")
        "Synthetic SWE-Gym"
    """
    name = benchmark_name.strip()

    # Rule 1: AIME variants
    # AIME24, AIME-24, AIME 24, MT-AIME24 → AIME 2024
    # AIME25, AIME-25, AIME 25 → AIME 2025

    # Match MT-AIME24, AIME24, AIME-24, etc.
    aime_pattern = r'(?:MT[-\s]?)?AIME[-\s]?(20)?(\d{2})\b'
    match = re.search(aime_pattern, name, re.IGNORECASE)
    if match:
        year_suffix = match.group(2)
        # Assume 20XX for two-digit years
        full_year = f"20{year_suffix}"
        name = f"AIME {full_year}"
        logger.debug(f"Normalized AIME variant: {benchmark_name} → {name}")
        return name

    # Rule 2: Remove "from [Model]" suffixes
    # "Synthetic SWE-Gym from Qwen3-Coder" → "Synthetic SWE-Gym"
    from_pattern = r'\s+from\s+[\w\-\.]+.*$'
    if re.search(from_pattern, name, re.IGNORECASE):
        cleaned = re.sub(from_pattern, '', name, flags=re.IGNORECASE).strip()
        if cleaned:  # Only use if something remains
            logger.debug(f"Removed 'from' suffix: {benchmark_name} → {cleaned}")
            name = cleaned

    # Rule 3: AIME with space (AIME 25 → AIME 2025)
    aime_space_pattern = r'AIME\s+(20)?(\d{2})\b'
    match = re.search(aime_space_pattern, name, re.IGNORECASE)
    if match:
        year_suffix = match.group(2)
        full_year = f"20{year_suffix}"
        name = f"AIME {full_year}"

    return name


def normalize_benchmark_entry(benchmark: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a full benchmark entry (name + context).

    Args:
        benchmark: Benchmark dictionary with 'name', 'score', 'context', etc.

    Returns:
        Normalized benchmark dictionary
    """
    if 'name' in benchmark:
        benchmark['name'] = normalize_benchmark_name(benchmark['name'])

    return benchmark


def validate_benchmark_with_ai(
    benchmark_name: str,
    context: Optional[str] = None
) -> Tuple[bool, float, str]:
    """
    Use AI to validate if an extracted name is a real benchmark.

    This is a more expensive validation step that should be used after
    heuristic filters have already removed obvious false positives.

    Args:
        benchmark_name: Name to validate
        context: Optional context from source document

    Returns:
        Tuple of (is_valid, confidence, reason)
        - is_valid: True if AI confirms it's a real benchmark
        - confidence: 0-100 confidence score
        - reason: Explanation of decision

    Examples:
        >>> validate_benchmark_with_ai("MMLU")
        (True, 95, "MMLU is a well-known multi-task benchmark...")
        >>> validate_benchmark_with_ai("Qwen3-8B")
        (False, 98, "This is a model name, not a benchmark...")
    """
    if not is_anthropic_available():
        logger.warning("AI validation unavailable, skipping")
        return (True, 50, "AI unavailable, defaulting to accept")

    prompt = f"""
You are a benchmark validation expert. Determine if the following extracted name is a REAL evaluation benchmark or a false positive.

**Extracted Name**: "{benchmark_name}"
{f'**Context**: {context[:200]}...' if context else ''}

**Analysis Required**:
1. Is this a real, standardized evaluation benchmark used to measure AI model performance?
2. Or is it a model name, random word, tool name, or other false positive?

**Known Patterns to REJECT**:
- Model names: Qwen, Llama, GPT, Claude, Gemini, Mistral, DeepSeek, GLM, etc.
- Model variants: Qwen3-8B, Llama-3.1-70B, GPT-4o, etc.
- Single generic words: "spotting", "reasoning", "evaluation"
- Tool/framework names: τ²bench, PyTorch, TensorFlow
- Descriptions: "Synthetic X from Y", "Art of Problem Solving"

**Known Valid Benchmarks** (partial list):
- MMLU, GSM8K, HumanEval, MATH, HellaSwag, ARC, TruthfulQA
- GPQA, LiveBench, SWE-bench, AIME, MBPP, HumanEval+
- C-EVAL, MMLU-Pro, IF-Eval, MT-Bench, AlpacaEval

**Output JSON**:
{{
  "is_valid_benchmark": true/false,
  "confidence": 0-100,
  "canonical_name": "Canonical benchmark name if valid, or null",
  "reason": "Brief explanation of decision"
}}

**Be strict**: When in doubt, reject. It's better to miss edge cases than accept false positives.
"""

    try:
        result = call_claude_json(prompt=prompt, max_tokens=512)

        is_valid = result.get('is_valid_benchmark', False)
        confidence = result.get('confidence', 0)
        reason = result.get('reason', 'No reason provided')
        canonical_name = result.get('canonical_name')

        logger.debug(
            f"AI validation for '{benchmark_name}': "
            f"valid={is_valid}, confidence={confidence}, reason={reason[:100]}"
        )

        return (is_valid, confidence, reason)

    except Exception as e:
        logger.warning(f"AI validation failed for '{benchmark_name}': {e}")
        # On error, default to accepting (heuristics already filtered obvious cases)
        return (True, 50, f"Validation error: {str(e)}")


def filter_benchmarks(
    benchmarks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply heuristic validation and normalization to filter benchmarks.

    Layers:
    1. Heuristic filters (fast, rejects obvious false positives)
    2. Normalization (cleans up variant names)

    Note: AI validation is done as post-processing on consolidated unique names,
    not during extraction. See validate_benchmarks_ai.py.

    Args:
        benchmarks: List of extracted benchmark dictionaries

    Returns:
        Filtered and normalized list of benchmarks
    """
    filtered = []
    rejected_count = 0

    for bench in benchmarks:
        name = bench.get('name', '')

        # Layer 1: Heuristic filters
        if not is_valid_benchmark_name(name):
            rejected_count += 1
            logger.debug(f"Heuristic filter rejected: {name}")
            continue

        # Layer 2: Normalization
        bench = normalize_benchmark_entry(bench)

        filtered.append(bench)

    if rejected_count > 0:
        logger.debug(
            f"Filtered {rejected_count}/{len(benchmarks)} benchmarks "
            f"({len(filtered)} remaining)"
        )

    return filtered
