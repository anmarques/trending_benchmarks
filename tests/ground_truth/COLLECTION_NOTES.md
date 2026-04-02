# Ground Truth Data Collection Notes

**Date:** 2026-04-02
**Target Models:**
1. meta-llama/Llama-3.1-8B
2. Qwen/Qwen2.5-72B-Instruct

---

## Model 1: meta-llama/Llama-3.1-8B

### Document Sources

#### Source 1: HuggingFace Model Card
**URL:** https://huggingface.co/meta-llama/Llama-3.1-8B
**Type:** model_card
**Status:** ✅ Successfully fetched

**Benchmarks Found (Base Model):**
- MMLU (5-shot): 66.7
- MMLU-Pro (CoT, 5-shot): 37.1
- AGIEval English (3-5 shot): 47.8
- CommonSenseQA (7-shot): 75.0
- Winogrande (5-shot): 60.5
- BIG-Bench Hard (CoT, 3-shot): 64.2
- ARC-Challenge (25-shot): 79.7
- TriviaQA-Wiki (5-shot): 77.6
- SQuAD (1-shot): 77.0
- QuAC F1 (1-shot): 44.9
- BoolQ (0-shot): 75.0
- DROP F1 (3-shot): 59.5

**Benchmarks Found (Instruct Model):**
- MMLU (5-shot): 69.4
- MMLU CoT (0-shot): 73.0
- MMLU-Pro (CoT, 5-shot): 48.3
- IFEval: 80.4
- ARC-C (0-shot): 83.4
- GPQA (0-shot): 30.4
- HumanEval (0-shot): 72.6
- MBPP++ (0-shot): 72.8
- Multipl-E HumanEval (0-shot): 50.8
- Multipl-E MBPP (0-shot): 52.4
- GSM-8K CoT (8-shot): 84.5
- MATH CoT (0-shot): 51.9
- API-Bank (0-shot): 82.6
- BFCL (0-shot): 76.1
- Gorilla Benchmark API Bench (0-shot): 8.2
- Nexus (0-shot): 38.5
- Multilingual MGSM CoT (0-shot): 68.9

**Multilingual MMLU (5-shot):**
- Portuguese: 62.12
- Spanish: 62.45
- Italian: 61.63
- German: 60.59
- French: 62.34
- Hindi: 50.88
- Thai: 50.32

**Total Benchmarks:** 29 unique benchmarks

#### Source 2: arXiv Paper
**URL:** https://arxiv.org/abs/2407.21783 (PDF: https://arxiv.org/pdf/2407.21783)
**Title:** "The Llama 3 Herd of Models"
**Status:** ✅ Found - Needs WebFetch permission to extract benchmarks
**Note:** Published July 31, 2024, updated November 23, 2024

#### Source 3: Meta AI Blog
**URL:** https://ai.meta.com/blog/meta-llama-3-1/
**Title:** "Introducing Llama 3.1: Our most capable models to date"
**Status:** ✅ Found - Needs WebFetch permission to extract benchmarks
**Note:** Official Meta announcement with benchmark comparisons

---

## Model 2: Qwen/Qwen2.5-72B-Instruct

### Document Sources

#### Source 1: HuggingFace Model Card
**URL:** https://huggingface.co/Qwen/Qwen2.5-72B-Instruct
**Type:** model_card
**Status:** ✅ Fetched - No benchmarks in card itself
**Note:** Model card references external blog for benchmarks

#### Source 2: Qwen Blog Posts
**URL 1:** https://qwenlm.github.io/blog/qwen2.5/
**URL 2:** https://qwenlm.github.io/blog/qwen2.5-llm/
**Type:** blog_post
**Status:** ✅ Found - Needs WebFetch permission to extract benchmarks
**Expected Content:** Comprehensive benchmark results for 72B-Instruct
**Note:** Blog mentions MMLU 86.1, MATH 83.1, LiveCodeBench 55.5, Arena-Hard 81.2

#### Source 3: arXiv Paper
**URL:** https://arxiv.org/abs/2412.15115 (PDF: https://arxiv.org/pdf/2412.15115)
**Title:** "Qwen2.5 Technical Report"
**Status:** ✅ Found - Needs WebFetch permission to extract benchmarks
**Note:** Published December 19, 2024, updated January 3, 2025

---

## Document Sources Found

### Llama 3.1 8B
1. ✅ HuggingFace model card - 29 benchmarks extracted
2. ✅ arXiv paper found - https://arxiv.org/pdf/2407.21783
3. ✅ Meta blog found - https://ai.meta.com/blog/meta-llama-3-1/

### Qwen 2.5 72B-Instruct
1. ✅ HuggingFace model card - No benchmarks (references blog)
2. ✅ Qwen blogs found - https://qwenlm.github.io/blog/qwen2.5/ and /qwen2.5-llm/
3. ✅ arXiv paper found - https://arxiv.org/pdf/2412.15115

## Next Steps

1. ⏳ WebFetch permission needed to extract benchmarks from PDFs and blogs
2. ⏳ Extract all benchmarks from 4 additional sources (2 PDFs + 2 blogs)
3. ⏳ Consolidate all benchmarks into ground_truth.yaml
4. ⏳ User final verification of complete ground truth data

---

## Notes

- Llama 3.1 has very comprehensive benchmark coverage in model card
- Qwen separates benchmarks into external blog (common pattern)
- Both models likely have arXiv papers with additional benchmarks
- Need to check for PDF technical reports in GitHub repos
