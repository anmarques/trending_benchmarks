# Quick Start Guide - Benchmark Intelligence System

**Target**: First-time users who want to run the system immediately

---

## ⚡ 60-Second Setup

### Step 1: Set HuggingFace Token

Go to Ambient **Workspace Settings** → **Environment Variables** and add:

```
HF_TOKEN = "hf_your_token_here"
```

Get a free token at: https://huggingface.co/settings/tokens

**Note**: On Ambient, you DON'T need `ANTHROPIC_API_KEY` - Claude is built-in!

---

### Step 2: Navigate to Repository

```bash
cd /workspace/repos/trending_benchmarks
```

---

### Step 3: Choose Your Run Mode

#### **First Run (Full System Test)**

```bash
# Run complete pipeline (~50-60 minutes for 65 models)
python -m agents.benchmark_intelligence.main full
```

#### **Quick Test (5-10 minutes)**

Edit `labs.yaml` to test with just 2 labs:

```yaml
labs:
  - Qwen
  - meta-llama
```

Then run:

```bash
python -m agents.benchmark_intelligence.main full
```

---

## 📊 What Happens During Execution

You'll see progress like this:

```
================================================
Benchmark Intelligence System v1.0.0
Mode: full | Verbose: False | Quiet: False
================================================

Phase 1: Model Discovery
  ✓ Discovering models from Qwen...
  ✓ Discovering models from meta-llama...
  ⊕ Found 30 models

Phase 2: Document Fetching
  ✓ Fetching docs for Qwen/Qwen2.5-72B-Instruct...
  ↻ Using cached docs for meta-llama/Llama-3.1-8B...
  ⊕ Fetched 28/30 documents (2 cached)

Phase 3: Benchmark Extraction
  ✓ Extracting benchmarks from Qwen2.5-72B-Instruct...
  ✓ Found 47 benchmark mentions
  ⊕ Extracted 181 total mentions

Phase 4: Consolidation & Classification
  ✓ Consolidating benchmark variants...
  ✓ Classifying into categories...
  ⊕ 90 unique benchmarks identified

Phase 5: Temporal Snapshot
  ✓ Creating 12-month rolling window...
  ✓ Recording benchmark mentions...
  ⊕ Snapshot created (snapshot_id: 1)

Phase 6: Report Generation
  ✓ Generating Executive Summary...
  ✓ Generating Trending Models section...
  ✓ Generating Most Common Benchmarks...
  ✓ Generating Category Distribution...
  ✓ Generating Temporal Trends...
  ✓ Generating Emerging Benchmarks...
  ✓ Generating Lab Insights...
  ⊕ Report saved: agents/benchmark_intelligence/reports/report_20260403_120000.md

================================================
✓ Pipeline complete! (54m 23s)
================================================
```

---

## 📁 Where to Find Results

### Generated Report (Main Output)

```bash
# Latest report location:
agents/benchmark_intelligence/reports/report_YYYYMMDD_HHMMSS.md
```

**The report contains**:
- Executive Summary (key metrics)
- Trending Models (all discovered models)
- Most Common Benchmarks (top 20)
- Category Distribution (14 categories)
- Temporal Trends (12-month window)
- Emerging Benchmarks (≤3 months old)
- Almost Extinct Benchmarks (≥9 months inactive)
- Lab Insights (per-lab breakdowns)

### Database

```bash
# SQLite database with all snapshots:
agents/benchmark_intelligence/benchmark_intelligence.db

# View with:
sqlite3 agents/benchmark_intelligence/benchmark_intelligence.db
```

### Auto-Generated Taxonomy

```bash
# Current taxonomy (auto-updated):
benchmark_taxonomy.md

# Historical versions:
archive/benchmark_taxonomy_YYYYMMDD.md
```

---

## 🎮 CLI Modes Explained

### Mode 1: **full** (Default) - Complete Pipeline

```bash
python -m agents.benchmark_intelligence.main full
```

**Does**: Discovery → Extraction → Snapshot → Report
**Use case**: Regular monthly runs, complete updates
**Time**: ~50-60 minutes (65 models)

---

### Mode 2: **snapshot** - Data Collection Only

```bash
python -m agents.benchmark_intelligence.main snapshot
```

**Does**: Discovery → Extraction → Snapshot (NO report)
**Use case**: Automated data collection (cron jobs)
**Time**: ~48-54 minutes (65 models)

---

### Mode 3: **report** - Report Generation Only

```bash
python -m agents.benchmark_intelligence.main report
```

**Does**: Report generation from latest snapshot
**Use case**: Regenerate report after manual edits
**Time**: ~18 seconds

---

## 🔧 Useful CLI Options

### Verbose Mode (See Everything)

```bash
python -m agents.benchmark_intelligence.main full --verbose
```

Shows detailed API calls, cache hits, extraction results.

---

### Quiet Mode (Automation-Friendly)

```bash
python -m agents.benchmark_intelligence.main snapshot --quiet
```

Only shows errors (perfect for cron jobs).

---

### Force Reprocess (Ignore Cache)

```bash
python -m agents.benchmark_intelligence.main full --force
```

Reprocesses all documents even if cached.

---

### Dry Run (No Database Writes)

```bash
python -m agents.benchmark_intelligence.main full --dry-run
```

Test run without modifying the database.

---

## 🔄 Scheduled Runs (Monthly Automation)

### Option 1: Ambient Scheduled Workflow

Create a workflow in Ambient to run monthly:

```yaml
schedule: "0 0 1 * *"  # 1st of every month at midnight
command: |
  cd /workspace/repos/trending_benchmarks
  python -m agents.benchmark_intelligence.main snapshot --quiet
```

---

### Option 2: Manual Cron Job

```bash
# Add to crontab (monthly on 1st at 2 AM)
0 2 1 * * cd /workspace/repos/trending_benchmarks && python -m agents.benchmark_intelligence.main snapshot --quiet
```

---

## 🐛 Troubleshooting

### Error: "HF_TOKEN not found"

**Solution**: Set HuggingFace token in environment variables:

```bash
export HF_TOKEN="hf_your_token_here"
# Or add to Ambient Workspace Settings
```

---

### Error: "ANTHROPIC_API_KEY required"

**Solution**: You're NOT on Ambient Code Platform. Set API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
```

Or comment out the anthropic dependency in `requirements.txt` if running on Ambient.

---

### Error: "Rate limit exceeded"

**Solution**: HuggingFace API rate limit hit. Wait 1 hour or:

```bash
# Reduce models in labs.yaml
labs:
  - Qwen  # Just one lab for testing
```

---

### Slow Execution

**Expected**: 50-60 minutes for 65 models is normal (AI extraction is CPU-intensive)

**Speed it up**:
1. Reduce labs in `labs.yaml`
2. Use snapshot mode (skip report generation)
3. Second run will use cache (much faster)

---

### No Report Generated

**Check**:

```bash
# Look for reports:
ls -lh agents/benchmark_intelligence/reports/

# Check for errors:
python -m agents.benchmark_intelligence.main report --verbose
```

---

## ✅ Verify Installation

Run the test suite to verify everything works:

```bash
# Run all tests (should pass in ~1.24 seconds)
./run_tests.sh all

# Expected output:
# 17 passed in 1.24s
```

---

## 📚 Additional Resources

- **README.md** - Project overview
- **CHANGELOG.md** - Version history
- **TEST_REPORT.md** - Test execution results
- **specs/001-benchmark-intelligence/spec.md** - Full feature specification
- **docs/implementation/** - Detailed implementation docs

---

## 🎯 Next Steps After First Run

1. **Review the generated report**: `agents/benchmark_intelligence/reports/report_*.md`
2. **Customize labs**: Edit `labs.yaml` to track specific organizations
3. **Set up monthly runs**: Use Ambient workflows or cron
4. **Explore the database**: `sqlite3 agents/benchmark_intelligence/benchmark_intelligence.db`

---

## 💡 Pro Tips

1. **First run is slow** - Second run uses cache and is 60% faster
2. **Run monthly** - Get temporal trends and emerging benchmark detection
3. **Use `snapshot` mode** for automation - Generate reports manually when needed
4. **Check taxonomy evolution** - Compare `archive/benchmark_taxonomy_*.md` over time
5. **Customize categories** - Edit `categories.yaml` to override AI classifications

---

**Questions?** Check the main [README.md](README.md) or open an issue on GitHub.

**Ready to run?** Jump back to [Step 1: Set HuggingFace Token](#step-1-set-huggingface-token)
