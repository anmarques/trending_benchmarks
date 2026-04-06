# Ground Truth Data

## Overview

This directory contains verified ground truth data for testing the Benchmark Intelligence System. The data has been manually extracted and validated to serve as a reference for automated testing.

## Files

- **`ground_truth.yaml`**: Complete ground truth data for 2 test models
  - `meta-llama/Llama-3.1-8B`
  - `Qwen/Qwen2.5-72B-Instruct`

## Data Structure

Each test model includes:
- **Model ID**: HuggingFace model identifier
- **Sources**: All documents where benchmarks were found (model card, blog, arXiv paper)
- **Benchmarks**: For each source:
  - Benchmark name
  - Variant (e.g., "5-shot", "0-shot CoT", "proficiency exam")
  - Category (e.g., "General Knowledge", "Reasoning", "Code Generation")

**Note**: Ground truth tracks only benchmark names, variants, and categories. Scores are intentionally excluded—we're testing benchmark discovery, not score accuracy.

## Coverage

### meta-llama/Llama-3.1-8B
- **Model card**: 29 benchmarks (MMLU variants, GSM8K, MATH, HumanEval, etc.)
- **Blog**: 14 benchmarks from charts (IFEval, BBH, GPQA, etc.)
- **arXiv paper**: 25+ benchmarks from Tables 8-16 (GRE, LSAT, adversarial tests, multilingual)

### Qwen/Qwen2.5-72B-Instruct
- **Model card**: 8 benchmarks (MMLU, GPQA, MATH, LiveCodeBench, etc.)
- **Blog**: 40+ benchmarks from charts (multilingual variants, long-context tests, code tasks)
- **arXiv paper**: 15+ benchmarks (AMMLU, JMMLU, KMMLU, RULER, LongBench-Chat, etc.)

## Usage

This ground truth data is used for automated testing as defined in **SPECIFICATIONS.md Section 12**:

1. **Extraction Accuracy Test**: Verify system discovers all benchmarks from each source
2. **Consolidation Test**: Validate fuzzy matching and variant grouping
3. **Classification Test**: Check category assignments
4. **End-to-End Test**: Full pipeline validation

## Maintenance

Ground truth data should be updated when:
- Adding new test models
- Test model sources are updated with new benchmarks
- Category taxonomy changes significantly

---

**Reference**: See [SPECIFICATIONS.md](/SPECIFICATIONS.md) Section 12 for complete testing framework.
