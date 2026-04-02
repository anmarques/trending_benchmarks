# Benchmark Intelligence - Quick Start Guide

Track trending benchmarks across LLMs, VLMs, and audio-language models.

## Prerequisites

1. **HuggingFace Token**: Get from https://huggingface.co/settings/tokens
2. **Anthropic API Key**: Get from https://console.anthropic.com

## Installation

```bash
# Navigate to project
cd /workspace/repos/trending_benchmarks

# Install dependencies
pip install -r requirements.txt

# Set up authentication
export HF_TOKEN="your_huggingface_token"
export ANTHROPIC_API_KEY="your_anthropic_key"

# Create config (optional - uses defaults)
cp agents/benchmark_intelligence/config/auth.yaml.example \
   agents/benchmark_intelligence/config/auth.yaml
```

## First Run

### Option 1: Via Ambient (Recommended)

```bash
/scan-benchmarks
```

### Option 2: Direct Python

```bash
python -m agents.benchmark_intelligence.main
```

### Option 3: Test Run (Dry Run)

```bash
python -m agents.benchmark_intelligence.main --dry-run --verbose
```

## What Happens

The agent will:

1. **Discover Models** (2-3 min)
   - Query HuggingFace for trending models
   - From labs: Qwen, Meta, Mistral, Google, Microsoft, etc.

2. **Parse Model Cards** (5-10 min)
   - Extract benchmarks from model documentation
   - Fetch related blogs and technical reports

3. **Consolidate & Classify** (3-5 min)
   - Group benchmark variations (GSM8K, gsm8k → GSM8K)
   - AI-powered classification (Math, Code, Vision, etc.)

4. **Generate Report** (1 min)
   - Update README.md
   - Create snapshot in `reports/`

**Total time**: 15-20 minutes for first run

## Output

### README.md

Updated with:
- Executive summary
- Trending models this month
- Most common benchmarks (all-time + monthly)
- Emerging benchmarks
- Category distribution
- Lab-specific insights
- Temporal trends

### reports/YYYY-MM-DD_HHMMSS.md

Historical snapshot for comparison.

### cache/benchmarks.db

SQLite database with:
- Models discovered
- Benchmarks extracted
- Temporal snapshots

## Scheduled Execution

### Via Ambient Cron

Automatically runs monthly (1st at 9 AM):

```bash
# Check schedule
crontab -l | grep scan-benchmarks

# Manual trigger
/scan-benchmarks
```

### Via System Cron

```bash
# Add to crontab
0 9 1 * * cd /workspace/repos/trending_benchmarks && \
  python -m agents.benchmark_intelligence.main
```

## Common Issues

### "HF_TOKEN not set"
```bash
export HF_TOKEN="hf_..."
```

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Rate limit errors
- Wait a few minutes and retry
- HuggingFace has generous limits for authenticated users
- Claude API: 50 requests/min on standard tier

### Cache corruption
```bash
rm cache/benchmarks.db
# Re-run will rebuild cache
```

## Advanced Usage

### Scan specific labs only

```bash
python -m agents.benchmark_intelligence.main \
  --labs Qwen,meta-llama,mistralai
```

### Verbose mode (see all details)

```bash
python -m agents.benchmark_intelligence.main --verbose
```

### Incremental updates

```bash
# Only process new/changed models
python -m agents.benchmark_intelligence.main
```
(Default behavior - uses content hashing)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Benchmark Intelligence Agent               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Discovery   │───>│  Extraction  │───>│Consolidation │ │
│  │              │    │              │    │              │ │
│  │ • HF Models  │    │ • Model Card │    │ • Fuzzy      │ │
│  │ • Filter Labs│    │ • Blog Posts │    │   Matching   │ │
│  │ • Trending   │    │ • Papers     │    │ • AI-powered │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         v                    v                    v         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Classification & Caching               │  │
│  │  • Multi-label categorization                       │  │
│  │  • Temporal tracking                                │  │
│  │  • Change detection                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                                   │
│         v                                                   │
│  ┌──────────────┐                                          │
│  │  Reporting   │                                          │
│  │              │                                          │
│  │ • README.md  │                                          │
│  │ • Snapshots  │                                          │
│  │ • Trends     │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Review Output**: Check generated README.md
2. **Explore Cache**: Query `cache/benchmarks.db` with SQL
3. **Schedule**: Set up monthly runs
4. **Customize**: Edit `config/labs.yaml` to add/remove labs
5. **Extend**: Add new benchmark categories in `config/categories.yaml`

## Documentation

- Full docs: `agents/benchmark_intelligence/README.md`
- Usage guide: `agents/benchmark_intelligence/USAGE.md`
- Features: `agents/benchmark_intelligence/FEATURES.md`
- Config reference: `agents/benchmark_intelligence/config/`

## Support

For issues or questions:
1. Check troubleshooting in main README
2. Review logs in verbose mode
3. Verify API keys are valid
4. Check HuggingFace API status

Happy tracking! 🚀
