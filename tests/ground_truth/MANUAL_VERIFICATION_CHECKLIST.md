# Manual Verification Checklist

**Purpose:** Establish ground truth data for testing the Benchmark Intelligence System
**Your Role:** Verify and complete the data I've collected
**Time Required:** ~30-45 minutes

---

## ✅ What I've Done (Ready for Your Verification)

### Model 1: Llama 3.1 8B ✅
- **Status:** Data collection COMPLETE
- **Source:** HuggingFace model card
- **Benchmarks Found:** 29 unique benchmarks
- **File:** `ground_truth_draft.yaml` (lines 9-204)

**Your Task:**
1. Visit: https://huggingface.co/meta-llama/Llama-3.1-8B
2. Scroll through the model card and verify:
   - ✓ All 29 benchmarks I listed are actually there
   - ✓ Scores match exactly
   - ✓ Benchmark names are spelled correctly (case matters!)
   - ✓ No benchmarks were missed

---

## 🔍 What Needs Your Input

### Model 2: Qwen 2.5 72B-Instruct ⏳
- **Status:** NEEDS YOUR INPUT
- **Issue:** Benchmarks are in external blog, not model card
- **Primary Source:** https://qwenlm.github.io/blog/qwen2.5/

**Your Task:**
1. Visit the Qwen blog: https://qwenlm.github.io/blog/qwen2.5/
2. Find the section with benchmark results for **72B-Instruct** specifically
3. For EACH benchmark you find, record:
   - Exact benchmark name (as written)
   - Score/metric value
   - Any variant info (shots, CoT, etc.)
   - What category it belongs to (from our taxonomy)

4. Add them to `ground_truth_draft.yaml` under the Qwen section (around line 215)

**Expected Format:**
```yaml
- name: "MMLU"
  variant: "5-shot"
  score: "XX.X"
  metric: "accuracy"
  category: "General Knowledge"
```

---

## 🔎 Optional: Additional Sources

If you have time, search for these additional sources:

### Llama 3.1
- [ ] **arXiv Paper:** Search "Llama 3.1 arXiv" or "Llama 3.1 technical report"
  - If found, add URL to ground_truth_draft.yaml line 207
  - Extract any additional benchmarks not in model card

- [ ] **Meta AI Blog:** Search "Meta AI Llama 3.1 blog"
  - If found, add URL to ground_truth_draft.yaml line 213
  - Cross-verify benchmarks match model card

- [ ] **GitHub PDFs:** Check https://github.com/meta-llama/llama for technical reports
  - Look for PDF files with benchmark results

### Qwen 2.5
- [ ] **arXiv Paper:** Search "Qwen2.5 arXiv" or "Qwen2.5 technical report"
  - If found, add URL to ground_truth_draft.yaml line 222
  - Extract benchmarks

- [ ] **GitHub PDFs:** Check https://github.com/QwenLM/Qwen2.5 for technical reports
  - Look for PDF files with benchmark results

---

## 📋 Verification Checklist

Before you tell me you're done, please verify:

### Data Quality
- [ ] All benchmark names are **exactly** as written in source (case-sensitive)
- [ ] All scores are **exact** numbers from source (not rounded)
- [ ] Variants are noted (5-shot, 0-shot, CoT, etc.)
- [ ] Categories assigned based on `benchmark_taxonomy.md`

### Completeness
- [ ] Llama 3.1: All 29 benchmarks verified ✓
- [ ] Qwen 2.5: All benchmarks from blog extracted and added
- [ ] No obvious benchmarks missed from either model
- [ ] URLs for all documents recorded

### Accuracy
- [ ] Double-checked at least 5 random benchmark scores
- [ ] Verified spelling of all benchmark names
- [ ] Confirmed no hallucinated benchmarks

---

## 🎯 What Happens Next

Once you complete this checklist:

1. **Save your changes** to `ground_truth_draft.yaml`
2. **Tell me:** "Ground truth verification complete"
3. **I will then:**
   - Review your additions
   - Rename to `ground_truth.yaml`
   - Create automated test suite
   - Run system on these 2 models
   - Compare results against ground truth
   - Generate test report showing accuracy

---

## 📝 Notes Section

Use this space to record any findings or questions:

```
YOUR NOTES HERE:

-

```

---

## ⚠️ Important Reminders

1. **Case Matters:** "MMLU" ≠ "mmlu" ≠ "Mmlu"
2. **Exact Scores:** Use "84.5" not "84" or "~85"
3. **Side-by-Side:** If two similar benchmarks appear together (e.g., "MMLU" and "MMLU-Pro"), they're distinct
4. **Variants:** Note if same benchmark appears multiple times with different settings

---

**Questions?** Just ask me in the chat and I'll clarify!
