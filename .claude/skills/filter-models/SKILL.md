# Filter Models Skill

**Stage 1 of 6** - Filter trending models from target labs

## Purpose

Discovers and filters trending AI models from major labs (Qwen, Meta, Mistral, Google, Microsoft, etc.) based on criteria in `config.yaml`.

## How To Execute

When this skill is invoked, run:

```bash
cd /workspace/repos/trending_benchmarks
python -m agents.benchmark_intelligence.main filter_models
```

## Expected Output

- **File created**: `agents/benchmark_intelligence/data/filtered_models.json`
- **Typical result**: 40-60 models total

## After Completion

Show summary and recommend: "Run `/find-docs` to locate documentation URLs for these models"

## Configuration

Users can customize in `config.yaml`:
- `labs`: Which organizations to track
- `discovery.models_per_lab`: How many models per lab (default: 15)
- `discovery.min_downloads`: Minimum download threshold (default: 1000)
