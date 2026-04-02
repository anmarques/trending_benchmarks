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
**URL:** Need to search for "Llama 3.1" arXiv paper
**Status:** ⏳ Pending

#### Source 3: Meta AI Blog
**URL:** Need to search
**Status:** ⏳ Pending

---

## Model 2: Qwen/Qwen2.5-72B-Instruct

### Document Sources

#### Source 1: HuggingFace Model Card
**URL:** https://huggingface.co/Qwen/Qwen2.5-72B-Instruct
**Type:** model_card
**Status:** ✅ Fetched - No benchmarks in card itself
**Note:** Model card references external blog for benchmarks

#### Source 2: Qwen Blog Post
**URL:** https://qwenlm.github.io/blog/qwen2.5/
**Type:** blog_post
**Status:** ⏳ Requires permission to fetch
**Expected Content:** Comprehensive benchmark results for 72B-Instruct

#### Source 3: arXiv Paper
**URL:** Need to search for "Qwen2.5" arXiv paper
**Status:** ⏳ Pending

---

## Next Steps

1. ⏳ Fetch Qwen blog post (requires WebFetch permission)
2. ⏳ Search for arXiv papers for both models
3. ⏳ Search for official GitHub repositories with technical reports
4. ✅ Create ground_truth.yaml with all discovered benchmarks
5. ⏳ User manual verification of ground truth data

---

## Notes

- Llama 3.1 has very comprehensive benchmark coverage in model card
- Qwen separates benchmarks into external blog (common pattern)
- Both models likely have arXiv papers with additional benchmarks
- Need to check for PDF technical reports in GitHub repos
