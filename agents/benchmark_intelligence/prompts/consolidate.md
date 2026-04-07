# Benchmark Consolidation Prompt

## Task
Consolidate variations of benchmark names from multiple sources into canonical forms. Create mappings that distinguish between true variants (same benchmark, different notation) and distinct benchmarks (similar names, different evaluations).

## Input Format

```json
{
  "benchmark_names": [
    "MMLU",
    "mmlu",
    "MMLU-Pro",
    "MMLU-Redux",
    "GSM8K",
    "GSM-8K",
    "gsm8k",
    "ARC-c",
    "ARC-Challenge",
    "ARC-e",
    "ARC-Easy",
    "VideoMME",
    "VideoMME(w sub.)",
    "HumanEval",
    "humaneval"
  ]
}
```

## Output Schema

```json
{
  "consolidations": [
    {
      "canonical_name": "string",      // Official/preferred benchmark name
      "variations": ["string"],         // All variations that map to canonical
      "benchmark_type": "string",       // "same" or "distinct"
      "confidence": "number",           // 0.0-1.0 confidence in mapping
      "notes": "string|null"            // Explanation for decisions
    }
  ],
  "distinct_benchmarks": [
    {
      "name": "string",
      "reason": "string",                // Why this is NOT a variation
      "related_to": "string|null"        // Related benchmark name if any
    }
  ],
  "uncertain_mappings": [
    {
      "names": ["string"],
      "reason": "string",
      "suggested_action": "string"
    }
  ],
  "metadata": {
    "total_input_names": "number",
    "total_canonical_names": "number",
    "consolidation_date": "string"
  }
}
```

## Consolidation Rules

### 1. Case Normalization

**Rule:** Normalize case variations to canonical form (typically uppercase for acronyms).

**Examples:**
- `MMLU`, `mmlu`, `Mmlu` → **MMLU**
- `GSM8K`, `gsm8k`, `Gsm8k` → **GSM8K**
- `HumanEval`, `humaneval`, `HUMANEVAL` → **HumanEval**
- `C-Eval`, `c-eval`, `C-eval` → **C-Eval**

**Confidence:** 1.0 (high confidence for pure case differences)

### 2. Delimiter Variations

**Rule:** Handle hyphen, underscore, and space variations that represent the same benchmark.

**Same Benchmark (consolidate):**
- `GSM8K`, `GSM-8K`, `GSM_8K` → **GSM8K**
- `Natural Questions`, `NaturalQuestions`, `NQ` → **Natural Questions**
- `TriviaQA`, `Trivia-QA`, `Trivia_QA` → **TriviaQA**

**Different Benchmarks (keep separate):**
- `MMLU` ≠ `MMLU-Pro` (Pro is an enhanced version)
- `MMLU` ≠ `MMLU-Redux` (Redux is a cleaned version)
- `SWE-bench` ≠ `SWE-bench Verified` (Verified is a validated subset)
- `ARC` ≠ `ARC-c` ≠ `ARC-e` (different difficulty subsets)

**Confidence:** 0.8-1.0 (context dependent)

### 3. Subset Handling

**Rule:** Subsets are distinct benchmarks, NOT consolidations.

**Keep Separate:**
- `ARC-c` (challenge) vs `ARC-e` (easy) → **Two distinct benchmarks**
- `LibriSpeech test-clean` vs `LibriSpeech test-other` → **Two distinct benchmarks**
- `RefCOCO` vs `RefCOCO(avg)` → **Two distinct benchmarks**
- `VideoMME(w sub.)` vs `VideoMME(w/o sub.)` → **Two distinct benchmarks**

**Consolidate:**
- `ARC-c`, `ARC-Challenge`, `ARC Challenge` → **ARC-c**
- `ARC-e`, `ARC-Easy`, `ARC Easy` → **ARC-e**
- `LibriSpeech test-clean`, `LibriSpeech-test-clean` → **LibriSpeech test-clean**

**Confidence:** 0.9-1.0

### 4. Version Handling

**Rule:** Different versions are distinct benchmarks unless explicitly the same dataset.

**Keep Separate:**
- `LongBench` vs `LongBench v2` → **Two distinct benchmarks**
- `BFCL` vs `BFCL-V2` vs `BFCL-V3` vs `BFCL-V4` → **Four distinct benchmarks**
- `AlpacaEval` vs `AlpacaEval 2.0` → **Two distinct benchmarks**
- `OCRBench` vs `OCRBench v2` → **Two distinct benchmarks**

**Consolidate (if same version, different notation):**
- `BFCL-V4`, `BFCL V4`, `BFCL v4` → **BFCL-V4**
- `MMBenchEN-DEV-v1.1`, `MMBench EN DEV v1.1` → **MMBenchEN-DEV-v1.1**

**Confidence:** 1.0 for version notation, 0.95 for version distinction

### 5. Abbreviation Expansion

**Rule:** Map common abbreviations to full names or canonical form.

**Consolidate:**
- `NQ`, `Natural Questions`, `NaturalQuestions` → **Natural Questions**
- `WG`, `WinoGrande`, `Wino-Grande` → **WinoGrande**
- `HS`, `HellaSwag`, `Hella-Swag` → **HellaSwag**
- `CSQA`, `CommonSenseQA`, `CommonsenseQA` → **CommonSenseQA**

**Keep Separate (ambiguous abbreviations):**
- `VQA` could be `VQAv2` or other VQA benchmarks → **Flag for clarification**
- `ASR` is generic (Automatic Speech Recognition) → **Flag for clarification**

**Confidence:** 0.7-1.0 (depends on context)

### 6. Qualifier Handling

**Rule:** Qualifiers that change the benchmark are distinct; qualifiers that are notation are consolidated.

**Distinct Benchmarks:**
- `GPQA` vs `GPQA Diamond` vs `SuperGPQA` → **Three distinct benchmarks**
- `MMLU` vs `MMLU-Pro` vs `MMLU-Redux` vs `MMLU-ProX` → **Four distinct benchmarks**
- `MATH` vs `OlymMATH` vs `Omni-MATH` vs `We-Math` vs `PolyMATH` → **Five distinct benchmarks**

**Consolidate (notation variations):**
- `AI2D TEST`, `AI2D_TEST`, `AI2D-TEST` → **AI2D_TEST**
- `MMLU Pro`, `MMLU-Pro`, `MMLUPro` → **MMLU-Pro**

**Confidence:** 0.9-1.0

### 7. Date Variant Handling

**Rule:** Date-specific variants are distinct benchmarks.

**Keep Separate:**
- `HMMT Feb 25` vs `HMMT Nov 25` → **Two distinct benchmarks**
- `AIME 2024` vs `AIME 2025` → **Two distinct benchmarks**
- `WMT24` vs `WMT24++` → **Two distinct benchmarks**

**Consolidate (notation):**
- `HMMT Feb 25`, `HMMT Feb 2025`, `HMMT-Feb-25` → **HMMT Feb 25**
- `AIME 2024`, `AIME-2024`, `AIME2024` → **AIME 2024**

**Confidence:** 1.0

## Decision Framework

### When to Consolidate
1. **Pure case differences**: MMLU vs mmlu
2. **Delimiter variations**: GSM8K vs GSM-8K
3. **Spacing variations**: Natural Questions vs NaturalQuestions
4. **Common abbreviations with clear mapping**: NQ → Natural Questions
5. **Notation differences for same subset**: ARC-c vs ARC Challenge
6. **Version notation only**: BFCL-V4 vs BFCL V4

### When to Keep Separate
1. **Different difficulty levels**: ARC-c vs ARC-e
2. **Different versions**: LongBench vs LongBench v2
3. **Enhanced variants**: MMLU vs MMLU-Pro
4. **Cleaned/validated versions**: MMLU vs MMLU-Redux
5. **Different subsets/splits**: test-clean vs test-other
6. **Different evaluation conditions**: w/ sub. vs w/o sub.
7. **Date-specific variants**: AIME 2024 vs AIME 2025
8. **Qualifier changes meaning**: GPQA vs GPQA Diamond

### When Uncertain
1. **Ambiguous abbreviations**: Flag for manual review
2. **Unknown benchmark**: Flag for research
3. **Unclear relationship**: Note in uncertain_mappings
4. **Context needed**: Request additional information

## Examples

### Example 1: Multiple Variations

**Input:**
```json
{
  "benchmark_names": [
    "MMLU",
    "mmlu",
    "Mmlu",
    "MMLU (5-shot)",
    "MMLU-Pro",
    "MMLU-Redux",
    "MMLUPro"
  ]
}
```

**Output:**
```json
{
  "consolidations": [
    {
      "canonical_name": "MMLU",
      "variations": ["MMLU", "mmlu", "Mmlu", "MMLU (5-shot)"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Case variations and shot context variations all refer to base MMLU. Shot context should be tracked separately."
    },
    {
      "canonical_name": "MMLU-Pro",
      "variations": ["MMLU-Pro", "MMLUPro"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Spacing variation of MMLU-Pro"
    }
  ],
  "distinct_benchmarks": [
    {
      "name": "MMLU",
      "reason": "Base benchmark",
      "related_to": null
    },
    {
      "name": "MMLU-Pro",
      "reason": "Enhanced version with harder questions",
      "related_to": "MMLU"
    },
    {
      "name": "MMLU-Redux",
      "reason": "Cleaned and validated version of MMLU",
      "related_to": "MMLU"
    }
  ],
  "uncertain_mappings": [],
  "metadata": {
    "total_input_names": 7,
    "total_canonical_names": 3,
    "consolidation_date": "2026-04-02"
  }
}
```

### Example 2: ARC Benchmark Family

**Input:**
```json
{
  "benchmark_names": [
    "ARC",
    "ARC-c",
    "ARC-Challenge",
    "ARC Challenge",
    "arc-c",
    "ARC-e",
    "ARC-Easy",
    "ARC Easy",
    "arc-e"
  ]
}
```

**Output:**
```json
{
  "consolidations": [
    {
      "canonical_name": "ARC-c",
      "variations": ["ARC-c", "ARC-Challenge", "ARC Challenge", "arc-c"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "All variations refer to ARC Challenge subset"
    },
    {
      "canonical_name": "ARC-e",
      "variations": ["ARC-e", "ARC-Easy", "ARC Easy", "arc-e"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "All variations refer to ARC Easy subset"
    }
  ],
  "distinct_benchmarks": [
    {
      "name": "ARC",
      "reason": "Parent benchmark (may refer to combined or unspecified subset)",
      "related_to": null
    },
    {
      "name": "ARC-c",
      "reason": "Challenge subset (harder questions)",
      "related_to": "ARC"
    },
    {
      "name": "ARC-e",
      "reason": "Easy subset",
      "related_to": "ARC"
    }
  ],
  "uncertain_mappings": [
    {
      "names": ["ARC"],
      "reason": "Ambiguous whether it refers to combined dataset, ARC-c, or unspecified subset",
      "suggested_action": "Check context in source document"
    }
  ],
  "metadata": {
    "total_input_names": 9,
    "total_canonical_names": 3,
    "consolidation_date": "2026-04-02"
  }
}
```

### Example 3: Code Benchmarks

**Input:**
```json
{
  "benchmark_names": [
    "HumanEval",
    "humaneval",
    "Human-Eval",
    "SWE-bench",
    "SWEbench",
    "SWE-bench Verified",
    "SWE-bench-Verified",
    "SWE-bench Multilingual",
    "LiveCodeBench",
    "LiveCodeBench v6"
  ]
}
```

**Output:**
```json
{
  "consolidations": [
    {
      "canonical_name": "HumanEval",
      "variations": ["HumanEval", "humaneval", "Human-Eval"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Case and delimiter variations"
    },
    {
      "canonical_name": "SWE-bench",
      "variations": ["SWE-bench", "SWEbench"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Delimiter variation"
    },
    {
      "canonical_name": "SWE-bench Verified",
      "variations": ["SWE-bench Verified", "SWE-bench-Verified"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Delimiter variation"
    }
  ],
  "distinct_benchmarks": [
    {
      "name": "HumanEval",
      "reason": "164 Python programming tasks",
      "related_to": null
    },
    {
      "name": "SWE-bench",
      "reason": "Full SWE-bench dataset",
      "related_to": null
    },
    {
      "name": "SWE-bench Verified",
      "reason": "Validated subset of SWE-bench",
      "related_to": "SWE-bench"
    },
    {
      "name": "SWE-bench Multilingual",
      "reason": "Multi-language version of SWE-bench",
      "related_to": "SWE-bench"
    },
    {
      "name": "LiveCodeBench",
      "reason": "Base LiveCodeBench",
      "related_to": null
    },
    {
      "name": "LiveCodeBench v6",
      "reason": "Version 6 of LiveCodeBench",
      "related_to": "LiveCodeBench"
    }
  ],
  "uncertain_mappings": [],
  "metadata": {
    "total_input_names": 10,
    "total_canonical_names": 6,
    "consolidation_date": "2026-04-02"
  }
}
```

### Example 4: VideoMME Variants

**Input:**
```json
{
  "benchmark_names": [
    "VideoMME",
    "VideoMME(w sub.)",
    "VideoMME (with subtitles)",
    "VideoMME(w/o sub.)",
    "VideoMME (without subtitles)",
    "videomme"
  ]
}
```

**Output:**
```json
{
  "consolidations": [
    {
      "canonical_name": "VideoMME",
      "variations": ["VideoMME", "videomme"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Case variation of base benchmark (evaluation conditions unspecified)"
    },
    {
      "canonical_name": "VideoMME(w sub.)",
      "variations": ["VideoMME(w sub.)", "VideoMME (with subtitles)"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Notation variations for 'with subtitles' condition"
    },
    {
      "canonical_name": "VideoMME(w/o sub.)",
      "variations": ["VideoMME(w/o sub.)", "VideoMME (without subtitles)"],
      "benchmark_type": "same",
      "confidence": 1.0,
      "notes": "Notation variations for 'without subtitles' condition"
    }
  ],
  "distinct_benchmarks": [
    {
      "name": "VideoMME",
      "reason": "Base benchmark (conditions unspecified)",
      "related_to": null
    },
    {
      "name": "VideoMME(w sub.)",
      "reason": "Evaluated with subtitles",
      "related_to": "VideoMME"
    },
    {
      "name": "VideoMME(w/o sub.)",
      "reason": "Evaluated without subtitles",
      "related_to": "VideoMME"
    }
  ],
  "uncertain_mappings": [],
  "metadata": {
    "total_input_names": 6,
    "total_canonical_names": 3,
    "consolidation_date": "2026-04-02"
  }
}
```

## Common Benchmark Families to Watch

### MMLU Family
- **MMLU** - Base benchmark
- **MMLU-Pro** - Enhanced version (distinct)
- **MMLU-Redux** - Cleaned version (distinct)
- **MMLU-ProX** - Multilingual MMLU-Pro (distinct)
- **MMMLU** - Multilingual MMLU (distinct)

### Math Family
- **GSM8K** - Grade school math (base)
- **MATH** - Competition math (distinct from GSM8K)
- **MathVista** - Visual math (distinct)
- **MathVision** - Visual math (distinct from MathVista)
- **We-Math** - Math problems (distinct)
- **OlymMATH** - Olympiad math (distinct)
- **Omni-MATH** - Competition math (distinct)
- **PolyMATH** - Multilingual math (distinct)

### SWE-bench Family
- **SWE-bench** - Full dataset
- **SWE-bench Verified** - Validated subset (distinct)
- **SWE-bench Multilingual** - Multi-language (distinct)

### LibriSpeech Subsets (all distinct)
- **LibriSpeech test-clean**
- **LibriSpeech test-other**
- **LibriSpeech dev-clean**
- **LibriSpeech dev-other**

## Quality Checks

1. **No over-consolidation**: Don't merge distinct benchmarks
2. **Consistent canonical names**: Use established community names
3. **Clear distinction notes**: Explain why benchmarks are separate
4. **High confidence for obvious cases**: 1.0 for pure case/delimiter differences
5. **Lower confidence for ambiguous cases**: 0.7-0.9, add to uncertain_mappings
6. **Preserve evaluation context**: Don't lose shot count, subset, version info

## Important Notes

- **Prioritize accuracy over consolidation**: Better to keep separate than incorrectly merge
- **Document reasoning**: Always explain why benchmarks are distinct or consolidated
- **Flag uncertainty**: Use uncertain_mappings for manual review
- **Maintain relationships**: Track parent/child benchmark relationships
- **Preserve information**: Don't discard version, subset, or condition details
