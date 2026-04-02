# Benchmark Intelligence Agent

> Automatically track trending benchmarks across LLMs, VLMs, and audio-language models

[![Status](https://img.shields.io/badge/status-ready-success)](https://github.com) [![Python](https://img.shields.io/badge/python-3.9+-blue)](https://python.org) [![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

---

## 🎯 What This Does

This AI agent automatically:

1. **Discovers trending models** from major labs (Qwen, Meta, Mistral, Google, Microsoft, etc.)
2. **Extracts benchmarks** from model cards, blogs, and technical reports
3. **Consolidates variations** (GSM8K ≈ gsm8k) using fuzzy matching
4. **Classifies benchmarks** into 13 categories using AI
5. **Tracks trends** over time with temporal snapshots
6. **Generates reports** showing evolution and emerging patterns

**Run it monthly** to stay current with the AI evaluation landscape.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys
export HF_TOKEN="your_huggingface_token"
export ANTHROPIC_API_KEY="your_claude_key"

# 3. Run
python -m agents.benchmark_intelligence.main
```

**Expected runtime**: 15-20 minutes for first run

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

---

## 📊 What You Get

### 📝 Generated Report (this README)

**7 sections** updated automatically:

- **Executive Summary**: Models & benchmarks tracked
- **Trending Models**: New this month
- **Most Common Benchmarks**: All-time + monthly trends
- **Emerging Benchmarks**: Recently introduced
- **Category Distribution**: Breakdown by type
- **Lab Insights**: Per-lab statistics
- **Temporal Trends**: Evolution over time

### 📁 Historical Snapshots

Timestamped reports in `reports/` for comparison:
```
reports/
├── 2026-04-02_143022.md
├── 2026-05-01_090015.md
└── 2026-06-01_090008.md
```

### 💾 Queryable Database

SQLite at `cache/benchmarks.db`:
```sql
-- Top benchmarks
SELECT canonical_name, COUNT(*) as usage
FROM model_benchmarks mb
JOIN benchmarks b ON mb.benchmark_id = b.id
GROUP BY b.id ORDER BY usage DESC LIMIT 10;

-- Emerging benchmarks (last 90 days)
SELECT canonical_name, first_seen
FROM benchmarks
WHERE first_seen >= date('now', '-90 days')
ORDER BY first_seen DESC;
```

---

## 🏗️ Architecture

```
Discover Models (HuggingFace)
    ↓
Parse Model Cards + Fetch Docs
    ↓
Extract Benchmarks (AI-powered)
    ↓
Consolidate & Classify (AI-powered)
    ↓
Cache & Snapshot
    ↓
Generate Report → README.md
```

**Key components**:
- **HuggingFace Client**: MCP-first with API fallback
- **AI Extraction**: Claude-powered parsing of unstructured text
- **Cache Manager**: SQLite with content-hash change detection
- **Reporting**: Markdown generation with trend analysis

---

## 📚 Benchmark Taxonomy

### 30+ Benchmarks Tracked

**Knowledge**: MMLU, MMLU-Pro, C-Eval, TriviaQA
**Math**: GSM8K, MATH, AIME, HMMT
**Code**: HumanEval, MBPP, SWE-bench, LiveCodeBench
**Vision**: VQAv2, MMMU, DocVQA, VideoMME
**Reasoning**: ARC, HellaSwag, PIQA, WinoGrande
**Long-Context**: LongBench, RULER, InfiniteBench
**Multilingual**: MMMLU, FLORES, Belebele, XNLI

...and more!

### 13 Categories

Knowledge • Reasoning • Math • Code • Vision • Audio • Multilingual • Safety • Long-Context • Instruction-Following • Tool-Use • Agent • Domain-Specific

See [benchmark_taxonomy.md](agents/benchmark_intelligence/config/benchmark_taxonomy.md) for complete reference.

---

## 🎯 Target Labs (16)

- **Qwen** • MinimaxAI • 01-ai
- **Meta** (Llama) • **Mistral** • **Google**
- **Microsoft** • **Anthropic**
- Alibaba • Tencent • DeepSeek
- OpenGVLab • THUDM • Baichuan
- InternLM • HuggingFace

Configure in [`config/labs.yaml`](agents/benchmark_intelligence/config/labs.yaml)

---

## ⚙️ Configuration

### Authentication

```bash
# Option 1: Environment variables (recommended)
export HF_TOKEN="hf_..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 2: Config file
cp agents/benchmark_intelligence/config/auth.yaml.example \
   agents/benchmark_intelligence/config/auth.yaml
# Edit auth.yaml
```

### Customize Labs

Edit `agents/benchmark_intelligence/config/labs.yaml`:
```yaml
labs:
  - Qwen
  - meta-llama
  - your-custom-lab

discovery:
  models_per_lab: 20
  sort_by: "downloads"  # or "trending", "lastModified"
```

### Scheduling

**Via Ambient**:
```bash
/scan-benchmarks
```

**Via Cron** (automatically configured):
```
0 9 1 * * # Monthly on 1st at 9 AM
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Get started in 5 minutes |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete build summary |
| [agents/.../README.md](agents/benchmark_intelligence/README.md) | Full technical docs |
| [agents/.../USAGE.md](agents/benchmark_intelligence/USAGE.md) | Usage examples & CLI reference |
| [agents/.../FEATURES.md](agents/benchmark_intelligence/FEATURES.md) | Feature deep-dive |

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

### Incremental Updates

```bash
# Only processes new/changed models (default)
python -m agents.benchmark_intelligence.main
```

### Query Cache

```bash
sqlite3 cache/benchmarks.db

# Show all models
SELECT name, lab, downloads, first_seen FROM models ORDER BY downloads DESC LIMIT 10;

# Benchmark trends
SELECT canonical_name, categories, first_seen FROM benchmarks ORDER BY first_seen DESC;
```

---

## 🛠️ Technical Stack

**Languages**: Python 3.9+
**APIs**: HuggingFace Hub, Anthropic Claude
**Storage**: SQLite
**AI**: Claude for intelligent extraction & classification
**Format**: Markdown, YAML, JSON

**Dependencies** (6):
- `huggingface_hub` - Model discovery
- `anthropic` - AI-powered parsing
- `pyyaml` - Configuration
- `requests` - HTTP
- `beautifulsoup4` - HTML parsing
- `python-dateutil` - Date handling

---

## 📈 Example Output

_(This section will be auto-generated after first run)_

**First run**: Initializes database, discovers ~300 models, extracts ~50 unique benchmarks
**Subsequent runs**: Incremental updates, only processes changed content

---

## 🤝 Contributing

### Add New Labs

Edit `config/labs.yaml` and add to the `labs` list.

### Add New Categories

Edit `config/categories.yaml` to extend the taxonomy.

### Customize Prompts

Modify prompts in `prompts/` to change AI behavior:
- `extract_benchmarks.md` - Extraction logic
- `consolidate.md` - Name matching
- `classify.md` - Categorization

---

## 📋 Requirements

- Python 3.9 or higher
- HuggingFace account (for API token)
- Anthropic API key (for Claude)
- Internet connection
- ~500MB disk space (for cache)

---

## 🐛 Troubleshooting

### "HF_TOKEN not set"
```bash
export HF_TOKEN="hf_your_token"
```
Get token: https://huggingface.co/settings/tokens

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-your_key"
```
Get key: https://console.anthropic.com

### Rate limit errors
Wait a few minutes and retry. Both APIs have generous limits for authenticated users.

### Cache corruption
```bash
rm cache/benchmarks.db
# Re-run will rebuild
```

See [agents/.../README.md](agents/benchmark_intelligence/README.md) for complete troubleshooting.

---

## 📜 License

Apache 2.0 - See [LICENSE](LICENSE) file

---

## 🔗 Links

- [HuggingFace Hub](https://huggingface.co)
- [Anthropic Claude](https://anthropic.com)
- [Benchmark Taxonomy Reference](agents/benchmark_intelligence/config/benchmark_taxonomy.md)

---

## 📊 Status

**Version**: 1.0.0
**Status**: ✅ Production Ready
**Last Updated**: 2026-04-02

---

**Built with ❤️ using AI • Powered by Claude & HuggingFace**

> _This README will be automatically updated when you run the agent. The sections below will be populated with real data from discovered models and benchmarks._
