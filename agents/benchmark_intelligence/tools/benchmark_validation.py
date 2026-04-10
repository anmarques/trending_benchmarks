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
        'multimodal', 'document', 'context', 'parsing', 'length',
        'modality', 'html', 'json', 'yaml', 'xml', 'sql',
        'portuguese', 'multilingual', 'english'
    }

    # Reject category/section headers (often appear in model cards)
    CATEGORY_PHRASES = {
        'general multimodal', 'long document', 'long context', 'context length',
        'reasoning mode', 'document parsing', 'text reasoning', 'image reasoning',
        'video reasoning', 'novel logical reasoning'
    }

    # Reject table column headers and metadata fields
    TABLE_METADATA_HEADERS = {
        'dataset size', 'collection period', 'collecting organisation',
        'modality', 'seed dataset', 'model(s) used for generation',
        'collecting organization', 'dataset', 'source', 'format',
        'model size', 'parameters', 'architecture', 'training data'
    }

    # Reject programming languages and file types
    PROGRAMMING_LANGUAGES = {
        'html', 'json', 'yaml', 'xml', 'sql', 'dockerfile',
        'php', 'typescript', 'javascript', 'visualbasic.net',
        'systemverilog', 'vhdl', 'commonlisp', 'mathematica',
        'jupyternotebook', 'restructuredtext', 'python', 'java',
        'c++', 'c#', 'ruby', 'go', 'rust', 'scala', 'kotlin',
        'swift', 'perl', 'bash', 'shell', 'powershell'
    }

    # Reject aggregate metric names (summary scores, not benchmarks)
    AGGREGATE_METRIC_PATTERNS = [
        r'\bmean\b',           # "MTEB Mean", "NanoBEIR Mean"
        r'\baverage\b',        # "Average Score"
        r'\bavg\b',            # "Fleurs-avg"
        r'\boverall\b',        # "VoiceBench-Overall", "MMMU-Pro-overall"
        r'-mean$',             # Ends with "-mean"
        r'-avg$',              # Ends with "-avg"
        r'-overall$',          # Ends with "-overall"
        r'\(task\)',           # "Mean (Task)"
        r'\(all languages\)',  # "Mean (All Languages)"
    ]

    # Reject validation/test split indicators (these are splits, not benchmarks)
    SPLIT_INDICATORS = [
        r'\bval\b$',           # "DocVQA val", "InfoVQA Val"
        r'\btest\b$',          # "AI2D_TEST", "TEDS_TEST"
        r'-test$',             # "Opencpop-test", "SEED-test-zh"
        r'-val$',              # Ends with "-val"
        r'-dev$',              # "MMBenchEN-DEV-v1.1"
        r'\bdev\b',            # "DEV" in name
    ]

    # Known MTEB component tasks (not the benchmark suite itself)
    # Includes both regular MTEB and NanoBEIR variants
    MTEB_TASK_IDS = {
        'banking77classification', 'biosses', 'askubuntuduplication',
        'fiqa2018', 'scidocs', 'sts12', 'sts13', 'sts14', 'sts15',
        'sts17', 'sts22.v2', 'touche2020retrieval.v3',
        'twentynewsgroupsclustering.v2', 'summevalsummarization.v2',
        'stackexchangeclustering.v2', 'stackexchangeclusteringp2p.v2',
        # NanoBEIR variants
        'nanofiqa2018', 'nanoscidocs', 'nanotouche2020', 'nanobeir',
        'nanosts12', 'nanosts13', 'nanosts14', 'nanosts15'
    }

    if name.lower() in GENERIC_WORDS:
        logger.debug(f"Rejected '{name}': generic word")
        return False

    # Check for category phrases
    if name.lower() in CATEGORY_PHRASES:
        logger.debug(f"Rejected '{name}': category/section header")
        return False

    # Check for table metadata headers
    if name.lower() in TABLE_METADATA_HEADERS:
        logger.debug(f"Rejected '{name}': table metadata header")
        return False

    # Check for programming languages
    if name.lower() in PROGRAMMING_LANGUAGES:
        logger.debug(f"Rejected '{name}': programming language/file type")
        return False

    # Check for aggregate metric patterns
    for pattern in AGGREGATE_METRIC_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            logger.debug(f"Rejected '{name}': aggregate metric pattern")
            return False

    # Check for split indicators (val, test, dev)
    for pattern in SPLIT_INDICATORS:
        if re.search(pattern, name, re.IGNORECASE):
            logger.debug(f"Rejected '{name}': validation/test split indicator")
            return False

    # Check for MTEB task IDs (reject component tasks, keep suite)
    if name.lower() in MTEB_TASK_IDS:
        logger.debug(f"Rejected '{name}': MTEB component task ID")
        return False

    # Reject individual language slices (e.g., "XOR-Retrieve - Arabic")
    # Pattern: "BenchmarkName - LanguageName"
    language_slice_pattern = r'^.+\s+-\s+(Arabic|Bengali|Hindi|Tamil|Chinese|English|French|Spanish|German|Italian|Japanese|Korean|Portuguese|Russian|Turkish|Swahili|Telugu)$'
    if re.search(language_slice_pattern, name, re.IGNORECASE):
        logger.debug(f"Rejected '{name}': language slice")
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
    # "Synthetic X", "X SFT", "Common Crawl X", "RL data", etc.
    training_patterns = [
        r'\bsft\b',  # Supervised Fine-Tuning
        r'\bsynthetic\b',  # Any "Synthetic" mention (Synthetic Math, Synthetic SWE, etc.)
        r'\bcrawl\b',  # Common Crawl, GitHub Crawl, etc.
        r'\bembedding\b',  # Embedding models, not benchmarks
        r'\brl\s+data\b',  # RL data, RL Data
        r'\bfor\s+rl\b',  # "for RL", "Synthetic X for RL"
        r'\s+rl$',  # Ends with " RL" (Long context RL, etc.)
        r'^rl\s+',  # Starts with "RL " (RL data for Search)
        r'\bdata\s+for\b',  # "data for X", "Synthetic Data for Search"
        r'tool\s+calling\s+data',  # Tool Calling Data
        r'instruction\s+following',  # Instruction Following data
        r'\btranslated\s+',  # Translated Synthetic X
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
    # AIME24, AIME-24, AIME 24, AIME'24, MT-AIME24 → AIME 2024
    # AIME25, AIME-25, AIME 25, AIME'25 → AIME 2025

    # Match MT-AIME24, AIME24, AIME-24, AIME'24, etc.
    # Supports hyphen, space, apostrophe (regular and smart quote) as separators
    aime_pattern = r"(?:MT[-\s]?)?AIME[-\s'']?(20)?(\d{2})\b"
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


def validate_model_benchmarks_with_ai(
    model_id: str,
    benchmarks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Use AI to validate all benchmarks extracted for a single model.

    More efficient and contextual than validating each name individually.
    Claude can assess benchmarks in the context of the full set extracted
    from one model's documentation.

    Args:
        model_id: Model identifier
        benchmarks: List of benchmark dicts extracted from this model

    Returns:
        Dictionary with validation results:
            - valid_benchmarks: List of benchmark names that passed validation
            - rejected_benchmarks: List of dicts with name, reason, confidence
            - validation_summary: Overall assessment

    Examples:
        >>> validate_model_benchmarks_with_ai("Qwen3-8B", [
        ...     {"name": "MMLU", "score": "85.2"},
        ...     {"name": "Qwen3-8B", "score": "baseline"},
        ...     {"name": "GSM8K", "score": "79.1"}
        ... ])
        {
            "valid_benchmarks": ["MMLU", "GSM8K"],
            "rejected_benchmarks": [
                {"name": "Qwen3-8B", "reason": "This is the model name...", "confidence": 99}
            ],
            ...
        }
    """
    if not is_anthropic_available():
        logger.warning("AI validation unavailable, accepting all benchmarks")
        return {
            "valid_benchmarks": [b.get("name") for b in benchmarks],
            "rejected_benchmarks": [],
            "validation_summary": "AI unavailable, all benchmarks accepted by default"
        }

    if not benchmarks:
        return {
            "valid_benchmarks": [],
            "rejected_benchmarks": [],
            "validation_summary": "No benchmarks to validate"
        }

    # Format benchmark list for prompt
    benchmark_list = "\n".join([
        f"  - {b.get('name', 'UNNAMED')}: {b.get('score', 'N/A')}"
        for b in benchmarks
    ])

    prompt = f"""
You are a benchmark validation expert. Review the following list of benchmarks extracted from the documentation for model "{model_id}".

**Your Task**: Identify which extracted names are REAL evaluation benchmarks vs. false positives (model names, generic words, section headers, training data, etc.).

**Extracted Benchmarks**:
{benchmark_list}

**CRITICAL: Known Patterns to REJECT**:

1. **Training Data Descriptions** (NOT benchmarks):
   - Anything with "Crawl": "Common Crawl", "GitHub Crawl", "Translated Synthetic Crawl"
   - Anything with "RL data" or "for RL": "Synthetic Data for RL", "RL data for Search", "Long context RL"
   - Anything with "Synthetic": "Synthetic Math", "Synthetic SWE", "Synthetic Agentless SWE", "Synthetic Tool Call Schema"
   - Dataset descriptions: "Tool Calling Data", "Instruction Following Data"

2. **Table Column Headers/Metadata**:
   - "Dataset Size", "Collection Period", "Collecting Organisation", "Modality"
   - "Seed Dataset", "Model(s) used for generation", "Training Data"

3. **Programming Languages/File Types**:
   - "HTML", "JSON", "YAML", "XML", "SQL", "Dockerfile"
   - "TypeScript", "JavaScript", "PHP", "Python", "SystemVerilog", "VHDL"
   - "JupyterNotebook", "reStructuredText", "CommonLisp"

4. **Model Names & Products**:
   - Model names: Qwen, Llama, GPT, Claude, Gemini, Mistral, DeepSeek
   - Model variants: Qwen3-8B, Llama-3.1-70B, GPT-4o
   - Embedding models: "e5-base-v2", "bge-base-en-v1.5", "granite-embedding-english-r2"

5. **Generic Words & Labels**:
   - Single words: "Portuguese", "Multilingual", "English", "Modality"
   - Section headers: "General Multimodal", "Long Context", "Reasoning Mode"
   - Markdown: **Text**, ##Section

**Known Valid Benchmarks** (partial list):
- MMLU, GSM8K, HumanEval, MATH, HellaSwag, ARC, TruthfulQA
- GPQA, LiveBench, SWE-bench, AIME, MBPP, HumanEval+
- C-EVAL, MMLU-Pro, IF-Eval, MT-Bench, AlpacaEval

**Output JSON**:
{{
  "valid_benchmarks": ["MMLU", "GSM8K", ...],
  "rejected_benchmarks": [
    {{
      "name": "Common Crawl",
      "confidence": 99,
      "reason": "This is a training dataset (crawl), not a benchmark"
    }},
    {{
      "name": "Dataset Size",
      "confidence": 99,
      "reason": "This is a table column header, not a benchmark"
    }},
    ...
  ],
  "validation_summary": "Brief overall assessment (1-2 sentences)"
}}

**Be VERY strict**: When in doubt, REJECT. Training data, table headers, programming languages, and metadata are NOT benchmarks.
Review the complete set together - patterns of false positives are easier to spot when seeing all extractions from one model.
"""

    try:
        result = call_claude_json(prompt=prompt, max_tokens=2048)

        valid = result.get('valid_benchmarks', [])
        rejected = result.get('rejected_benchmarks', [])
        summary = result.get('validation_summary', 'No summary provided')

        logger.debug(
            f"Batch validation for {model_id}: "
            f"{len(valid)} valid, {len(rejected)} rejected"
        )

        return {
            "valid_benchmarks": valid,
            "rejected_benchmarks": rejected,
            "validation_summary": summary
        }

    except Exception as e:
        logger.warning(f"Batch AI validation failed for {model_id}: {e}")
        # On error, default to accepting all (heuristics already filtered obvious cases)
        return {
            "valid_benchmarks": [b.get("name") for b in benchmarks],
            "rejected_benchmarks": [],
            "validation_summary": f"Validation error: {str(e)}, accepted all by default"
        }


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

**CRITICAL Patterns to REJECT**:

1. **Aggregate Metrics** (NOT benchmarks):
   - Anything with "Mean", "Average", "Overall", "avg": "NanoBEIR Mean", "VoiceBench-Overall", "MTEB Multilingual v2 - Mean (Task)"

2. **Validation/Test Splits** (splits, NOT benchmarks):
   - Ends with "val", "test", "dev": "DocVQA val", "InfoVQA Val", "AI2D_TEST", "SEED-test-zh", "MMBenchEN-DEV-v1.1"

3. **Language Slices** (subsets, NOT standalone benchmarks):
   - Individual languages: "XOR-Retrieve - Arabic", "XTREME-UP - Hindi", "OCRBenchV2 English"

4. **MTEB Component Task IDs** (tasks, NOT suite):
   - Individual task IDs: "Banking77Classification", "BIOSSES", "FiQA2018", "SCIDOCS", "STS12", "Touche2020Retrieval.v3"
   - Only accept: "MTEB", "MTEB (Code)", "MTEB (English)", etc. (suite names)

5. **Datasets/Challenge Sets** (NOT standard benchmarks):
   - "GTZAN", "MagnaTagATune", "Monash Time Series Forecasting Repository"
   - Statistical datasets: "NAB (Univariate)", "TODS (Univariate)", "UCR (Univariate)"

6. **Model Names & Training Data**:
   - Model names: Qwen, Llama, GPT, Claude, Gemini, Mistral
   - Training data: "Common Crawl", "Synthetic X", "RL data"

**Known Valid Benchmarks** (partial list):
- MMLU, GSM8K, HumanEval, MATH, HellaSwag, ARC, TruthfulQA
- GPQA, LiveBench, SWE-bench, AIME, MBPP, HumanEval+
- C-EVAL, MMLU-Pro, IF-Eval, MT-Bench, AlpacaEval
- MTEB (suite name, not individual tasks)

**Output JSON**:
{{
  "is_valid_benchmark": true/false,
  "confidence": 0-100,
  "canonical_name": "Canonical benchmark name if valid, or null",
  "reason": "Brief explanation of decision"
}}

**Be VERY strict**: Aggregate metrics, splits, language slices, and component task IDs are NOT benchmarks. When in doubt, REJECT.
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
