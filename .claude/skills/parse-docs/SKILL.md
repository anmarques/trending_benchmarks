# Parse Docs Skill

**Stage 3 of 6** - Extract benchmarks from documentation using AI

## Purpose

Uses Claude AI to parse documentation and extract benchmark names and scores.

## How To Execute

When this skill is invoked, run:

```bash
cd /workspace/repos/trending_benchmarks
python -m agents.benchmark_intelligence.main parse_docs
```

Or with custom concurrency:

```bash
python -m agents.benchmark_intelligence.main parse_docs --concurrency 30
```

## Arguments

- `--concurrency N`: Number of concurrent workers (default: 20, max recommended: 50)

## Expected Output

- **File created**: `agents/benchmark_intelligence/data/parsed_docs.json`
- **Typical duration**: 5-15 minutes
- **Typical result**: 200-500 benchmark mentions extracted

## After Completion

Show summary and recommend: "Run `/consolidate-benchmarks` to deduplicate and normalize names"
