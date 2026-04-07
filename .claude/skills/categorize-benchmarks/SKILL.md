# Categorize Benchmarks Skill

**Stage 5 of 6** - Classify benchmarks into categories using AI

## Purpose

Uses Claude AI to classify each unique benchmark into meaningful categories.

## How To Execute

When this skill is invoked, run:

```bash
cd /workspace/repos/trending_benchmarks
python -m agents.benchmark_intelligence.main categorize_benchmarks
```

## Expected Output

- **Database updated**: Each benchmark tagged with category
- **Typical categories**: Mathematical Reasoning, Knowledge, Vision, Code Generation, etc.

## After Completion

Show category distribution and recommend: "Run `/report` to generate comprehensive analysis report"
