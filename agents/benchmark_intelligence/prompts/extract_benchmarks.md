# Benchmark Extraction Prompt

## Task
Extract all benchmarks, scores, and evaluation contexts from model cards, research papers, and technical documents. Output structured JSON data suitable for database ingestion.

## Input Format
- Raw markdown text from model cards
- HTML tables from documentation
- Plain text with embedded benchmark results
- Mixed formats (tables, lists, prose)

## Output Schema

```json
{
  "benchmarks": [
    {
      "name": "string",           // Canonical benchmark name (e.g., "MMLU", "GSM8K")
      "score": "number|null",     // Numerical score (null for missing: "--", "N/A")
      "metric": "string|null",    // Metric type: "accuracy", "pass@1", "wer", "f1", etc.
      "context": {
        "shot_count": "number|null",      // 0, 1, 3, 5, 8, etc. (null if not specified)
        "subset": "string|null",          // "challenge", "easy", "test-clean", "avg", etc.
        "version": "string|null",         // "v2", "V4", "1.1", etc.
        "special_conditions": "string|null"  // "with subtitles", "without CI", "CoT", etc.
      },
      "model_name": "string|null",        // Model being evaluated (if specified)
      "source_location": "string|null"    // Where in document (e.g., "Table 1", "Section 3.2")
    }
  ],
  "metadata": {
    "document_source": "string",   // Document name or URL
    "extraction_date": "string",   // ISO date
    "total_benchmarks": "number"
  }
}
```

## Extraction Rules

### 1. Benchmark Name Extraction

**From Tables:**
- First column typically contains benchmark names
- Look for rows with recognizable benchmark names
- Extract name before any parenthetical context

**Examples:**
- `MMLU (5-shot)` → name: "MMLU", shot_count: 5
- `ARC-Challenge` → name: "ARC-c", subset: "challenge"
- `VideoMME(w sub.)` → name: "VideoMME", special_conditions: "with subtitles"
- `GSM8K (8-shot)` → name: "GSM8K", shot_count: 8
- `LibriSpeech test-clean` → name: "LibriSpeech", subset: "test-clean"

**From Lists:**
- Pattern: `Benchmark: Score` or `Benchmark - Score%`
- Example: `HumanEval: 86.6%` → name: "HumanEval", score: 86.6

**From Prose:**
- Pattern: "achieves X% on Benchmark"
- Pattern: "scores X on Benchmark"
- Example: "achieves 94.2% on GSM8K with 8-shot prompting"
  - name: "GSM8K", score: 94.2, shot_count: 8

### 2. Score Extraction

**Numeric Formats:**
- `82.5%` → 82.5
- `82.5` → 82.5
- `0.825` → 82.5 (convert if 0-1 range for percentage metrics)
- `Pass@1: 86.6` → 86.6, metric: "pass@1"
- `EM: 75.3 / F1: 82.1` → Extract both with different metric labels

**Missing Values:**
- `--` → null
- `N/A` → null
- `TBD` → null
- Empty cell → null
- `Coming soon` → null

**Score Ranges:**
- Validate: Most scores are 0-100 (percentages)
- WER/error rates: Can be >100
- MT-Bench: Typically 1-10 scale
- Flag unusual values for review

### 3. Context Extraction

**Shot Count Patterns:**
- `5-shot MMLU` → shot_count: 5
- `MMLU (5-shot)` → shot_count: 5
- `0-shot`, `zero-shot` → shot_count: 0
- `few-shot` → shot_count: null (unspecified, note in special_conditions)
- No mention → shot_count: null

**Subset Patterns:**
- `ARC-c`, `ARC-Challenge` → subset: "challenge"
- `ARC-e`, `ARC-Easy` → subset: "easy"
- `test-clean` → subset: "test-clean"
- `test-other` → subset: "test-other"
- `RefCOCO(avg)` → subset: "avg"
- `ZEROBench_sub` → subset: "sub"

**Version Patterns:**
- `LongBench v2` → version: "v2"
- `BFCL-V4` → version: "V4"
- `MMBenchEN-DEV-v1.1` → version: "v1.1"
- `OmniDocBench1.5` → version: "1.5"

**Special Conditions:**
- `VideoMME(w sub.)` → special_conditions: "with subtitles"
- `VideoMME(w/o sub.)` → special_conditions: "without subtitles"
- `BabyVision (w/ CI)` → special_conditions: "with CI"
- `MATH (CoT)` → special_conditions: "chain-of-thought"

### 4. Metric Inference

**By Benchmark Type:**
- **Code benchmarks** (HumanEval, MBPP, SWE-bench): "pass@1" (default)
- **QA benchmarks** (MMLU, ARC, HellaSwag): "accuracy"
- **Audio benchmarks** (LibriSpeech): "wer" (word error rate)
- **NLP benchmarks** (SQuAD, Natural Questions): "em" or "f1"
- **Document benchmarks** (DocVQA): "anls"
- **Agent benchmarks** (WebArena, OSWorld): "success_rate"
- **Comparison benchmarks** (AlpacaEval, Arena-Hard): "win_rate"

**Explicit Metric Mentions:**
- Look for: "Pass@1:", "EM:", "F1:", "WER:", "BLEU:", "ANLS:"
- Extract both score and metric type

## Handling Tables

### Standard Table Format
```markdown
| Benchmark         | Model A | Model B | Model C |
|-------------------|---------|---------|---------|
| MMLU-Pro          | 82.5    | 80.8    | 79.1    |
| GSM8K (8-shot)    | 94.2    | 92.1    | --      |
| HumanEval         | 86.6    | 78.5    | N/A     |
```

**Extraction:**
- Row 1: name: "MMLU-Pro", score: 82.5 (Model A), 80.8 (Model B), 79.1 (Model C)
- Row 2: name: "GSM8K", shot_count: 8, score: 94.2 (Model A), 92.1 (Model B), null (Model C)
- Row 3: name: "HumanEval", metric: "pass@1", score: 86.6 (Model A), 78.5 (Model B), null (Model C)

### Grouped Tables

```markdown
### Knowledge & STEM
| Benchmark    | Score |
|--------------|-------|
| MMLU         | 82.5  |
| C-Eval       | 78.3  |

### Reasoning & Coding
| Benchmark    | Score |
|--------------|-------|
| ARC-c        | 85.2  |
| HumanEval    | 86.6  |
```

**Extraction:**
- Store category information in source_location or metadata
- Tag benchmarks with their section headings when possible

## Examples

### Example 1: Table Extraction

**Input:**
```markdown
| Benchmark         | Qwen3.5-9B | Llama-3.1-8B |
|-------------------|------------|--------------|
| MMLU (5-shot)     | 82.5       | 80.8         |
| GSM8K (8-shot)    | 94.2       | 92.1         |
| HumanEval (0-shot)| 86.6       | --           |
| ARC-c (25-shot)   | 85.2       | 83.5         |
```

**Output:**
```json
{
  "benchmarks": [
    {
      "name": "MMLU",
      "score": 82.5,
      "metric": "accuracy",
      "context": {
        "shot_count": 5,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": "Qwen3.5-9B",
      "source_location": "Table 1, Row 1"
    },
    {
      "name": "MMLU",
      "score": 80.8,
      "metric": "accuracy",
      "context": {
        "shot_count": 5,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": "Llama-3.1-8B",
      "source_location": "Table 1, Row 1"
    },
    {
      "name": "GSM8K",
      "score": 94.2,
      "metric": "accuracy",
      "context": {
        "shot_count": 8,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": "Qwen3.5-9B",
      "source_location": "Table 1, Row 2"
    },
    {
      "name": "GSM8K",
      "score": 92.1,
      "metric": "accuracy",
      "context": {
        "shot_count": 8,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": "Llama-3.1-8B",
      "source_location": "Table 1, Row 2"
    },
    {
      "name": "HumanEval",
      "score": 86.6,
      "metric": "pass@1",
      "context": {
        "shot_count": 0,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": "Qwen3.5-9B",
      "source_location": "Table 1, Row 3"
    },
    {
      "name": "HumanEval",
      "score": null,
      "metric": "pass@1",
      "context": {
        "shot_count": 0,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": "Llama-3.1-8B",
      "source_location": "Table 1, Row 3"
    },
    {
      "name": "ARC-c",
      "score": 85.2,
      "metric": "accuracy",
      "context": {
        "shot_count": 25,
        "subset": "challenge",
        "version": null,
        "special_conditions": null
      },
      "model_name": "Qwen3.5-9B",
      "source_location": "Table 1, Row 4"
    },
    {
      "name": "ARC-c",
      "score": 83.5,
      "metric": "accuracy",
      "context": {
        "shot_count": 25,
        "subset": "challenge",
        "version": null,
        "special_conditions": null
      },
      "model_name": "Llama-3.1-8B",
      "source_location": "Table 1, Row 4"
    }
  ],
  "metadata": {
    "document_source": "Qwen3.5-9B Model Card",
    "extraction_date": "2026-04-02",
    "total_benchmarks": 8
  }
}
```

### Example 2: List Format

**Input:**
```markdown
Performance highlights:
- MMLU: 82.5%
- GSM8K (8-shot): 94.2%
- HumanEval: 86.6% (Pass@1)
- VideoMME(w sub.): 75.3%
```

**Output:**
```json
{
  "benchmarks": [
    {
      "name": "MMLU",
      "score": 82.5,
      "metric": "accuracy",
      "context": {
        "shot_count": null,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": null,
      "source_location": "Performance highlights, item 1"
    },
    {
      "name": "GSM8K",
      "score": 94.2,
      "metric": "accuracy",
      "context": {
        "shot_count": 8,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": null,
      "source_location": "Performance highlights, item 2"
    },
    {
      "name": "HumanEval",
      "score": 86.6,
      "metric": "pass@1",
      "context": {
        "shot_count": null,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": null,
      "source_location": "Performance highlights, item 3"
    },
    {
      "name": "VideoMME",
      "score": 75.3,
      "metric": "accuracy",
      "context": {
        "shot_count": null,
        "subset": null,
        "version": null,
        "special_conditions": "with subtitles"
      },
      "model_name": null,
      "source_location": "Performance highlights, item 4"
    }
  ],
  "metadata": {
    "document_source": "Unknown",
    "extraction_date": "2026-04-02",
    "total_benchmarks": 4
  }
}
```

### Example 3: Prose Format

**Input:**
```
Our model achieves state-of-the-art performance on mathematical reasoning benchmarks,
scoring 94.2% on GSM8K with 8-shot prompting and 78.5% on MATH (0-shot). For code
generation, we report 86.6% Pass@1 on HumanEval and 80.3% on MBPP.
```

**Output:**
```json
{
  "benchmarks": [
    {
      "name": "GSM8K",
      "score": 94.2,
      "metric": "accuracy",
      "context": {
        "shot_count": 8,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": null,
      "source_location": "Paragraph 1"
    },
    {
      "name": "MATH",
      "score": 78.5,
      "metric": "accuracy",
      "context": {
        "shot_count": 0,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": null,
      "source_location": "Paragraph 1"
    },
    {
      "name": "HumanEval",
      "score": 86.6,
      "metric": "pass@1",
      "context": {
        "shot_count": null,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": null,
      "source_location": "Paragraph 1"
    },
    {
      "name": "MBPP",
      "score": 80.3,
      "metric": "accuracy",
      "context": {
        "shot_count": null,
        "subset": null,
        "version": null,
        "special_conditions": null
      },
      "model_name": null,
      "source_location": "Paragraph 1"
    }
  ],
  "metadata": {
    "document_source": "Unknown",
    "extraction_date": "2026-04-02",
    "total_benchmarks": 4
  }
}
```

## Edge Cases & Handling

### Multiple Metrics for Same Benchmark
Extract as separate entries with different metric fields:
```json
{
  "name": "SQuAD",
  "score": 75.3,
  "metric": "em"
},
{
  "name": "SQuAD",
  "score": 82.1,
  "metric": "f1"
}
```

### Split Scores (e.g., "with/without")
```
BabyVision: 78.5 / 82.3 (w/ CI / w/o CI)
```
Extract as two entries:
```json
{
  "name": "BabyVision",
  "score": 78.5,
  "special_conditions": "with CI"
},
{
  "name": "BabyVision",
  "score": 82.3,
  "special_conditions": "without CI"
}
```

### Comparative Statements
```
"outperforms GPT-4 on MMLU by 2.5 points"
```
Cannot extract absolute score (requires baseline), mark as null but note in metadata.

### Ambiguous Names
If unsure about exact benchmark name, extract as written and flag for manual review.

## Quality Checks

1. **Score validation**: Most should be 0-100 for accuracy/percentage metrics
2. **Name consistency**: Check against known benchmark names
3. **Shot count validation**: Common values are 0, 1, 3, 5, 8, 10, 25
4. **Completeness**: Ensure all table rows/list items are captured
5. **Null handling**: Missing values properly marked as null, not omitted

## Important Notes

- **Preserve original formatting context**: Keep subset, version, shot information separate
- **Don't normalize names yet**: Extract as-is (consolidation is a separate step)
- **Handle multiple models**: Create separate entries for each model's score
- **Mark uncertainty**: If extraction confidence is low, note in metadata
- **Date variants**: For benchmarks like "AIME 2024" vs "AIME 2025", include year in version field
