# Consolidate Benchmarks Skill

**Stage 4 of 6** - Deduplicate and normalize benchmark names

## Purpose

Intelligently consolidates benchmark name variations (GSM8K ≈ gsm8k ≈ GSM-8K) into canonical forms.

## How To Execute

When this skill is invoked, run:

```bash
cd /workspace/repos/trending_benchmarks
python -m agents.benchmark_intelligence.main consolidate_benchmarks
```

Or load from database:

```bash
python -m agents.benchmark_intelligence.main consolidate_benchmarks --from-db
```

## Arguments

- `--from-db`: Load benchmarks from database instead of `parsed_docs.json`

## Expected Output

- **Database updated**: Consolidated benchmarks stored
- **Typical result**: 300+ raw names → 80-100 unique benchmarks

## After Completion

Show consolidation stats and recommend: "Run `/categorize-benchmarks` to classify benchmarks"
