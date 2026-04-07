# Find Docs Skill

**Stage 2 of 6** - Find documentation URLs for filtered models

## Purpose

Locates documentation URLs (model cards, papers, blogs, GitHub) for each filtered model from Stage 1.

## How To Execute

When this skill is invoked, run:

```bash
cd /workspace/repos/trending_benchmarks
python -m agents.benchmark_intelligence.main find_docs
```

## Expected Output

- **File created**: `agents/benchmark_intelligence/data/model_docs.json`
- **Typical result**: 2-5 URLs per model

## After Completion

Show summary and recommend: "Run `/parse-docs` to extract benchmarks from these documents"
