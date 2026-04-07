# Generate Skill

**Full Pipeline** - Run all 6 stages sequentially

## Purpose

Executes the complete benchmark intelligence pipeline: filter → find docs → parse → consolidate → categorize → report.

## How To Execute

When this skill is invoked, run:

```bash
cd /workspace/repos/trending_benchmarks
python -m agents.benchmark_intelligence.main generate
```

Or with custom concurrency:

```bash
python -m agents.benchmark_intelligence.main generate --concurrency 30
```

## Arguments

- `--concurrency N`: Number of concurrent workers for Stage 3 (default: 20)

## Expected Duration

**Typical runtime**: 15-30 minutes

- Stage 1: ~1 minute
- Stage 2: ~2-3 minutes
- Stage 3: ~8-15 minutes (slowest, uses Claude AI)
- Stage 4: ~2-3 minutes
- Stage 5: ~1-2 minutes
- Stage 6: ~30 seconds

## Expected Output

- Comprehensive benchmark report
- Complete database with models, benchmarks, categories
- Intermediate data files

## After Completion

Show comprehensive summary of all stages, key findings, and file paths.
