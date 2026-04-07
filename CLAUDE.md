# Benchmark Intelligence Workflow

AI-powered workflow for tracking trending benchmarks across LLMs, VLMs, and audio-language models.

## Overview

This workflow automatically discovers trending AI models from major labs (Qwen, Meta, Mistral, Google, Microsoft, etc.) and extracts the benchmarks they report. It uses AI to intelligently consolidate benchmark name variations and classify them into categories.

## Pipeline Stages

The workflow consists of 6 sequential stages:

### 1. Filter Models (`/filter-models`)
Discovers and filters trending models from target labs based on criteria in `config.yaml`.

**Output**: `agents/benchmark_intelligence/data/filtered_models.json`

### 2. Find Docs (`/find-docs`)
Locates documentation URLs (model cards, ArXiv papers, blogs, GitHub) for each filtered model.

**Output**: `agents/benchmark_intelligence/data/model_docs.json`

### 3. Parse Docs (`/parse-docs`)
Uses Claude AI to extract benchmark mentions from documentation. Supports concurrent processing for speed.

**Output**: `agents/benchmark_intelligence/data/parsed_docs.json`  
**Args**: `--concurrency N` (default: 20)

### 4. Consolidate Benchmarks (`/consolidate-benchmarks`)
Intelligently deduplicates benchmark name variations (GSM8K ≈ gsm8k ≈ GSM-8K) using fuzzy matching, web search, and AI review.

**Output**: Database with consolidated benchmarks  
**Args**: `--from-db` (load from database instead of JSON)

### 5. Categorize Benchmarks (`/categorize-benchmarks`)
Classifies benchmarks into categories (Mathematical Reasoning, Knowledge, Vision, Code Generation, etc.) using Claude AI.

**Output**: Database with categorized benchmarks

### 6. Generate Report (`/report`)
Creates a comprehensive markdown report with benchmark trends, category distribution, and lab-specific insights.

**Output**: `agents/benchmark_intelligence/reports/report_YYYYMMDD_HHMMSS.md`

## Quick Start

### Run Full Pipeline

```
/generate
```

Executes all 6 stages sequentially (typical runtime: 15-30 minutes).

### Run Individual Stages

```
/filter-models
/find-docs
/parse-docs
/consolidate-benchmarks
/categorize-benchmarks
/report
```

### Check Status

```
/controller
```

Shows pipeline status and recommends next steps.

## Configuration

All settings are in `config.yaml`:

- **Labs to track**: `labs` (Qwen, Meta, Mistral, etc.)
- **Discovery filters**: `discovery.min_downloads`, `discovery.date_filter_months`
- **Concurrency**: `parallelization.max_concurrent_document_fetches`
- **Consolidation**: `consolidation.fuzzy_match_threshold`, `consolidation.benchmark_aliases`
- **Categories**: `taxonomy.category_overrides`
- **Rate limiting**: `rate_limiting.huggingface`, `rate_limiting.anthropic`

## Environment Variables

Required:
- `HF_TOKEN`: HuggingFace API token (set in Workspace Settings → Environment Variables)
- `ANTHROPIC_API_KEY`: Claude API key (automatically available on Ambient platform)

## Typical Results

- **Models analyzed**: 40-60 from 12+ labs
- **Benchmark mentions**: 300-500 raw extractions
- **Unique benchmarks**: 80-100 after consolidation
- **Categories**: 7-10 distinct categories
- **Processing time**: 15-30 minutes for full pipeline

## Output Files

- **Data**: `agents/benchmark_intelligence/data/` (filtered_models.json, model_docs.json, parsed_docs.json)
- **Reports**: `agents/benchmark_intelligence/reports/` (timestamped markdown reports)
- **Database**: `agents/benchmark_intelligence/benchmark_intelligence.db` (SQLite with all findings)

## Best Practices

1. **Monthly runs**: Run the full pipeline monthly to track benchmark evolution
2. **Use `/generate`**: For complete runs, use the generate skill to run all stages
3. **Individual stages**: For debugging or partial updates, run stages individually
4. **Check status**: Use `/controller` to see where you are in the pipeline
5. **Review config**: Customize `config.yaml` for your specific needs (labs, thresholds, etc.)

## Troubleshooting

- **Missing HF_TOKEN**: Set in Workspace Settings → Environment Variables
- **Rate limits**: Configured in `config.yaml`, automatically respected
- **Slow parsing**: Adjust `--concurrency` in parse_docs stage
- **Pipeline status**: Run `/controller` to check completion status

## Architecture

- **Python agent**: `agents/benchmark_intelligence/main.py`
- **Configuration**: `config.yaml`
- **Database**: SQLite for persistent storage and trend tracking
- **Skills**: `.claude/skills/` for interactive workflow commands
