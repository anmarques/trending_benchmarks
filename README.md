# Benchmark Intelligence Agent

> Automatically track trending benchmarks across LLMs, VLMs, and audio-language models

[![Status](https://img.shields.io/badge/status-ready-success)](https://github.com) [![Python](https://img.shields.io/badge/python-3.9+-blue)](https://python.org) [![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

---

## 📊 Latest Report

**[View Latest Benchmark Report →](agents/benchmark_intelligence/reports/report_20260402_162723.md)**

**Key Findings** (2026-04-02):
- **84 unique benchmarks** discovered
- **43 models** analyzed from 12 major labs
- **Top benchmarks**: C-Eval (13 models), MMLU (9), GSM8K (6)
- **Categories**: Reasoning (32.5%), Knowledge (27.7%), Vision (15.1%)

---

## 🎯 What This Does

This AI agent automatically:

1. **Discovers trending models** from major labs (Qwen, Meta, Mistral, Google, Microsoft, etc.)
2. **Extracts benchmarks** from model cards, blogs, and technical reports using AI
3. **Consolidates variations** (GSM8K ≈ gsm8k ≈ GSM-8K) using intelligent matching
4. **Classifies benchmarks** into categories using Claude AI
5. **Tracks trends** over time with SQLite caching and snapshots
6. **Generates reports** showing evolution and emerging patterns

**Run it monthly** to stay current with the AI evaluation landscape.

---

## 🚀 Quick Start

### On Ambient Code Platform (Recommended)

```bash
# 1. Set HuggingFace token in Workspace Settings → Environment Variables
# HF_TOKEN = "hf_..."

# 2. Run (Claude is natively available, no API key needed!)
cd /workspace/repos/trending_benchmarks
python -m agents.benchmark_intelligence.main
```

### On Other Platforms

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys
export HF_TOKEN="your_huggingface_token"
export ANTHROPIC_API_KEY="your_claude_key"  # Not needed on Ambient

# 3. Run
python -m agents.benchmark_intelligence.main
```

**Expected runtime**: ~50-60 minutes for 65 models (with AI extraction)

---

## 📚 Documentation & Configuration

### Core Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| **[benchmark_taxonomy.md](benchmark_taxonomy.md)** | Complete reference of 30+ benchmarks | Root |
| **[categories.yaml](categories.yaml)** | 13 benchmark categories & definitions | Root |
| **[config.yaml](config.yaml)** | Target labs/organizations to track | Config |

### Reports & Data

| Resource | Description |
|----------|-------------|
| **[Latest Report](agents/benchmark_intelligence/reports/report_20260402_162723.md)** | Most recent benchmark intelligence |
| **[All Reports](agents/benchmark_intelligence/reports/)** | Historical snapshots |
| **[SQLite Database](benchmark_cache.db)** | Queryable cache (see below) |

---

## 💾 Caching System

The agent uses **SQLite** for intelligent caching with change detection:

### Database Schema

```
benchmark_cache.db
├── models           # Model metadata (name, lab, release_date, downloads)
├── benchmarks       # Unique benchmarks with categories
├── model_benchmarks # Benchmark scores/results per model
├── documents        # Cached model cards & docs (content-hash tracking)
└── snapshots        # Temporal snapshots for trend analysis
```

### How Caching Works

1. **Content-hash tracking**: Models are only reprocessed if their model card changes
2. **Incremental updates**: Subsequent runs only process new/changed models
3. **Historical snapshots**: Trend analysis without re-fetching old data
4. **Queryable**: Use SQL for custom analysis

### Query Examples

```bash
sqlite3 benchmark_cache.db

# Show all discovered models
SELECT id, lab, release_date, downloads, likes
FROM models
ORDER BY downloads DESC LIMIT 20;

# Top benchmarks by usage
SELECT b.canonical_name, COUNT(DISTINCT mb.model_id) as model_count, b.categories
FROM benchmarks b
JOIN model_benchmarks mb ON b.id = mb.benchmark_id
GROUP BY b.canonical_name
ORDER BY model_count DESC
LIMIT 15;

# Models released in last 12 months
SELECT id, lab, release_date, downloads
FROM models
WHERE release_date >= date('now', '-12 months')
ORDER BY release_date DESC;

# Benchmark trend over time
SELECT s.timestamp, s.benchmark_count, s.model_count
FROM snapshots s
ORDER BY s.timestamp;
```

### Cache Location

- **File**: `benchmark_cache.db` (in project root)
- **Size**: ~240KB (current)
- **Backed up**: Yes (snapshots table tracks history)

---

## 📊 What You Get

### 📝 Generated Reports

**7 automated sections**:

1. **Executive Summary**: Models & benchmarks tracked
2. **Trending Models**: Sorted by release date & significance
3. **Most Common Benchmarks**: All-time + monthly trends
4. **Emerging Benchmarks**: Recently introduced (<90 days)
5. **Category Distribution**: Breakdown by type (charts)
6. **Lab Insights**: Per-lab statistics & preferences
7. **Temporal Trends**: Evolution over time

### 📁 Historical Tracking

Timestamped reports in `agents/benchmark_intelligence/reports/`:
```
reports/
├── report_20260402_162723.md  # Latest
├── report_20260402_151316.md
└── ...
```

---

## 🏗️ Architecture

```
Discover Models (HuggingFace API)
    ↓
Check Cache (content-hash comparison)
    ↓
Parse Model Cards (if changed)
    ↓
Extract Benchmarks (Claude AI)
    ↓
Consolidate Names (fuzzy matching + AI)
    ↓
Classify Benchmarks (multi-label AI categorization)
    ↓
Store in SQLite Cache
    ↓
Create Temporal Snapshot
    ↓
Generate Markdown Report
```

**Key Components**:
- **HuggingFace Client**: Official `huggingface_hub` library
- **Universal Claude Client**: Auto-detects Ambient/Vertex AI/Anthropic API
- **AI Extraction**: Claude-powered parsing of unstructured model cards
- **Cache Manager**: SQLite with content-hash change detection
- **Smart Consolidation**: Handles variations ("MMLU", "MMLU-Pro", "MMLU 5-shot")

---

## 📚 Benchmark Taxonomy

### Categories (13)

**Knowledge** • **Reasoning** • **Math** • **Code** • **Vision** • **Audio** • **Multilingual** • **Safety** • **Long-Context** • **Instruction-Following** • **Tool-Use** • **Agent** • **Domain-Specific**

### Top Benchmarks Tracked (30+)

**Knowledge**: MMLU, MMLU-Pro, C-Eval, CMMLU, TriviaQA, GPQA
**Math**: GSM8K, MATH, AIME, Gaokao
**Code**: HumanEval, MBPP, LiveCodeBench, CFBench
**Vision**: MMMU, CMMMU, VQAv2, DocVQA, AI2D
**Reasoning**: ARC, BBH, HellaSwag, PIQA, WinoGrande, BoolQ
**Safety**: TruthfulQA, RewardBench
**Multimodal**: Open LLM Leaderboard, Arena-Hard

**See [benchmark_taxonomy.md](benchmark_taxonomy.md) for complete reference with definitions.**

---

## 🎯 Target Labs (15)

- **Qwen** • **01-ai** (Yi)
- **meta-llama** • **mistralai** • **google**
- **microsoft** • **anthropic**
- **alibaba-pai** • **tencent** • **deepseek-ai**
- **OpenGVLab** • **THUDM** (ChatGLM)
- **baichuan-inc** • **internlm**
- **MinimaxAI**

Configure in [`config.yaml`](config.yaml)

---

## ⚙️ Configuration

### Discovery Settings

Edit [`config.yaml`](config.yaml):

```yaml
discovery:
  models_per_lab: 10           # Models to fetch per lab
  sort_by: "downloads"         # downloads | trending | lastModified
  filter_tags: ["text-generation", "multimodal"]  # Task filters
  min_downloads: 10000         # Minimum popularity threshold
  date_filter_months: 12       # Only models from last N months
```

### Categories & Taxonomy

- **Categories**: Edit [`categories.yaml`](categories.yaml) at root
- **Taxonomy**: Update [`benchmark_taxonomy.md`](benchmark_taxonomy.md) at root

### Scheduling

**Monthly runs** (recommended):

```bash
# Via cron (automatically configured)
0 9 1 * * cd /workspace/repos/trending_benchmarks && python -m agents.benchmark_intelligence.main

# Or manual
python -m agents.benchmark_intelligence.main
```

---

## 🔧 Advanced Usage

### Dry Run (Test Mode)

```bash
python -m agents.benchmark_intelligence.main --dry-run --verbose
```

### Specific Labs Only

```bash
python -m agents.benchmark_intelligence.main \
  --labs Qwen,meta-llama,mistralai
```

### Force Refresh (Ignore Cache)

```bash
# Clear cache and start fresh
rm benchmark_cache.db
python -m agents.benchmark_intelligence.main
```

### Custom Date Range

```bash
# Edit config.yaml:
discovery:
  date_filter_months: 24  # Last 2 years
```

---

## 🛠️ Technical Stack

**Language**: Python 3.9+
**APIs**: HuggingFace Hub, Anthropic Claude (or Vertex AI)
**Storage**: SQLite
**AI**: Claude Sonnet 4 for intelligent extraction & classification
**Format**: Markdown, YAML, JSON

**Dependencies** (6):
- `huggingface_hub` - Model discovery
- `anthropic` - AI-powered parsing (or Vertex AI on Ambient)
- `pyyaml` - Configuration
- `requests` - HTTP
- `beautifulsoup4` - HTML parsing
- `python-dateutil` - Date handling

---

## 📖 Complete Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Get started in 5 minutes |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete build summary |
| [CLAUDE_API_SETUP.md](CLAUDE_API_SETUP.md) | Claude API configuration guide |
| [agents/.../README.md](agents/benchmark_intelligence/README.md) | Full technical documentation |
| [agents/.../USAGE.md](agents/benchmark_intelligence/USAGE.md) | CLI reference & examples |

---

## 🐛 Troubleshooting

### "HF_TOKEN not set"
```bash
export HF_TOKEN="hf_your_token"
```
Get token: https://huggingface.co/settings/tokens

### "ANTHROPIC_API_KEY not set"
Only needed outside Ambient. Get key: https://console.anthropic.com
On Ambient: Uses native Vertex AI Claude support (no key needed)

### Getting irrelevant models?
Edit `config.yaml` → remove labs that produce noise (e.g., "huggingface" org gets time-series models)

### Models from wrong time period?
Edit `config.yaml` → `date_filter_months: 12` (or higher)

### Cache corruption
```bash
rm benchmark_cache.db
# Re-run will rebuild from scratch
```

---

## 📋 Requirements

- Python 3.9 or higher
- HuggingFace account (for API token)
- Anthropic API key (for Claude) OR Ambient Code Platform
- Internet connection
- ~500MB disk space (for cache)

---

## 📜 License

Apache 2.0 - See [LICENSE](LICENSE) file

---

## 🔗 Links

- **[Latest Report](agents/benchmark_intelligence/reports/report_20260402_162723.md)** ⭐
- **[Benchmark Taxonomy](benchmark_taxonomy.md)** - Complete reference
- **[Categories](categories.yaml)** - Category definitions
- [HuggingFace Hub](https://huggingface.co)
- [Anthropic Claude](https://anthropic.com)

---

## 📊 Status

**Version**: 1.0.1
**Status**: ✅ Production Ready
**Last Run**: 2026-04-02
**Models**: 43 | **Benchmarks**: 84 | **Snapshots**: 3

---

**Built with ❤️ using AI • Powered by Claude & HuggingFace**
