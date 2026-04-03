# Quickstart Guide

**Feature**: Benchmark Intelligence System
**Date**: 2026-04-03
**For**: End users, researchers, and system administrators

## Overview

The Benchmark Intelligence System automatically tracks benchmark evaluation trends across Large Language Models (LLMs), Vision-Language Models (VLMs), and Audio-to-Text models from major AI research labs. This guide will help you get started quickly.

---

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Linux or macOS
- **Disk Space**: Minimum 500MB (for database and downloads)
- **Internet**: Required for API access and document fetching

### API Access

**Required**:
- **Anthropic API Key**: For AI-powered extraction and classification
  - Sign up at: https://console.anthropic.com/
  - Set environment variable: `export ANTHROPIC_API_KEY="sk-ant-..."`

**Optional**:
- **GitHub Personal Access Token**: For higher rate limits when fetching GitHub docs
  - Create at: https://github.com/settings/tokens
  - Set environment variable: `export GITHUB_TOKEN="ghp_..."`
- **HuggingFace Token**: Only needed if tracking private models
  - Create at: https://huggingface.co/settings/tokens
  - Set environment variable: `export HUGGINGFACE_TOKEN="hf_..."`

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/trending_benchmarks.git
cd trending_benchmarks
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed**:
- `anthropic` - Claude API client
- `pdfplumber` - PDF parsing
- `PyPDF2` - Fallback PDF parser
- `requests` - HTTP client
- `pyyaml` - YAML configuration
- `huggingface-hub` - HuggingFace API client

### 3. Set API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Make it permanent** (optional):
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Verify Installation

```bash
python agents/benchmark_intelligence/main.py --version
```

Expected output:
```
Benchmark Intelligence System v1.0.0
Python 3.11+
SQLite 3.x
```

---

## Configuration

### Edit `labs.yaml` (Root Directory)

This file controls which AI labs to track and what models to discover.

```yaml
labs:
  - Qwen
  - meta-llama
  - mistralai
  - google
  - microsoft
  # Add more labs as needed

discovery:
  models_per_lab: 15              # How many top models per lab
  sort_by: "downloads"            # Ranking criteria
  filter_tags:
    - "text-generation"           # LLMs
    - "image-text-to-text"        # VLMs
    - "text2text-generation"      # Seq2seq models
    - "automatic-speech-recognition"  # Audio-to-text models
  exclude_tags:
    - "time-series-forecasting"
    - "fill-mask"
    - "token-classification"
    - "text-to-speech"            # Exclude TTS
    - "text-to-audio"
    - "audio-to-audio"
  min_downloads: 10000            # Popularity threshold
  date_filter_months: 12          # Rolling window size

lab_github_mappings:
  Qwen: QwenLM
  meta-llama: meta-llama
  mistralai: mistralai
  google: google
  microsoft: microsoft
  # Map lab names to GitHub organizations
```

**Key Settings**:
- `labs`: List of AI organizations to track
- `models_per_lab`: How many models to discover per lab (top N by downloads)
- `filter_tags`: Model types to include (only these will be processed)
- `exclude_tags`: Model types to explicitly exclude
- `min_downloads`: Minimum popularity threshold

### Edit `categories.yaml` (Root Directory)

Define or override benchmark categories.

```yaml
categories:
  - name: "General Knowledge"
    description: "Broad knowledge and reasoning benchmarks"
    examples: ["MMLU", "C-Eval", "CMMLU"]

  - name: "Math Reasoning"
    description: "Mathematical problem solving"
    examples: ["GSM8K", "MATH", "MathQA"]

  - name: "Code Generation"
    description: "Programming and code understanding"
    examples: ["HumanEval", "MBPP", "CodeXGLUE"]

  # System auto-evolves taxonomy, but you can manually override
```

---

## Basic Usage

### First Run: Complete Pipeline

```bash
python agents/benchmark_intelligence/main.py full
```

**What it does**:
1. Discovers models from configured labs (15 per lab by default)
2. Fetches documentation (model cards, papers, blogs, PDFs)
3. Extracts benchmarks using AI
4. Consolidates naming variants
5. Classifies benchmarks into categories
6. Creates temporal snapshot (12-month window)
7. Generates comprehensive markdown report
8. Updates root README with latest report link

**Expected duration**: 1-2 hours for 150 models (depends on API speed)

**Output**:
- Database: `agents/benchmark_intelligence/benchmark_intelligence.db`
- Report: `agents/benchmark_intelligence/reports/report_20260403_163045.md`
- Taxonomy: `benchmark_taxonomy.md` (root)
- Archive: `archive/benchmark_taxonomy_20260403.md` (if taxonomy changed)

### Subsequent Runs: Incremental Updates

```bash
python agents/benchmark_intelligence/main.py full
```

**Incremental behavior**:
- Only re-processes documents that changed (60%+ skip rate)
- Updates model metadata (downloads, likes) every run
- Detects new models from labs
- Adds new benchmarks to database
- Creates new snapshot for temporal comparison

**Duration**: Much faster (30-45 minutes) due to caching

---

## Advanced Usage

### Snapshot Only (No Report)

Useful for regular scheduled updates:

```bash
python agents/benchmark_intelligence/main.py snapshot
```

**Use cases**:
- Cron job to keep database current
- Background data collection
- Testing pipeline without report overhead

### Report Only (No Pipeline)

Generate report from existing data:

```bash
python agents/benchmark_intelligence/main.py report
```

**Use cases**:
- Regenerate report after manual data fixes
- Update report with new template
- Quick report refresh (< 2 minutes)

**Note**: Requires at least one snapshot in database (run `snapshot` or `full` first)

### Verbose Debugging

Enable detailed logging:

```bash
python agents/benchmark_intelligence/main.py full --verbose
```

**Shows**:
- Per-source extraction details
- Hash comparison results
- API request/response logs
- Consolidation decisions
- Classification confidence scores

### Quiet Mode (Cron/Scheduled)

Suppress progress output:

```bash
python agents/benchmark_intelligence/main.py snapshot --quiet
```

**Shows**:
- Only errors and critical failures
- Final success/failure status
- Suitable for cron jobs with email-on-error

---

## Understanding Output

### Report Sections

Generated reports contain 7 sections:

1. **Executive Summary**
   - Total models and benchmarks tracked
   - Time period covered (12-month window)
   - Source document statistics
   - Benchmark status distribution (emerging/active/extinct)

2. **Trending Models (Last 12 Months)**
   - ALL models matching criteria (no limits)
   - Sorted by downloads (most popular first)
   - Includes: Model name, Lab, Downloads, Likes, Release date

3. **Most Common Benchmarks**
   - Sorted by relative frequency (% of models using it)
   - Columns: Name, Absolute mentions, Relative frequency, Categories, Status
   - Includes historical trends if multiple snapshots exist

4. **Emerging Benchmarks**
   - Benchmarks first mentioned ≤3 months ago
   - Identifies new evaluation trends
   - Shows which models introduced them

5. **Category Distribution**
   - Pie chart data (JSON format)
   - Percentage breakdown by category
   - Trend over time (if multiple snapshots)

6. **Lab-Specific Insights**
   - Models per lab
   - Average downloads/likes per lab
   - Top 5 preferred benchmarks per lab
   - Benchmark diversity score

7. **Temporal Trends**
   - Historical mention counts (if multiple snapshots)
   - Emerging vs. active vs. almost extinct benchmarks
   - No explicit "trending up/down" (users interpret raw data)

### Benchmark Status Indicators

- **🆕 Emerging**: First mention ≤3 months ago (new benchmarks)
- **Active**: Regularly mentioned (first seen >3 months, last seen <9 months)
- **⚠️ Almost Extinct**: Last mention ≥9 months ago (declining usage)

### Progress Symbols

- **✓**: Success / Completed
- **✗**: Error / Failed
- **↻**: Cached / Updated from cache
- **⊕**: New / Added
- **⚠**: Warning

---

## Scheduled Execution

### Cron Job (Linux/macOS)

Run weekly on Sundays at 2 AM:

```bash
crontab -e
```

Add:
```
0 2 * * 0 cd /path/to/trending_benchmarks && python agents/benchmark_intelligence/main.py snapshot --quiet
```

**Tips**:
- Use absolute paths for reliability
- Add `--quiet` for minimal output
- Redirect output to log file: `>> /path/to/log/benchmark.log 2>&1`
- Ensure API keys are set in cron environment

### Ambient Scheduled Task

```yaml
schedule:
  - name: "Weekly Benchmark Intelligence"
    cron: "0 2 * * 0"
    command: "python agents/benchmark_intelligence/main.py full"
    notify_on_error: true
```

---

## Troubleshooting

### Error: API Key Not Set

```
❌ Error: ANTHROPIC_API_KEY environment variable not set
```

**Solution**:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Error: No Snapshots Found

```
❌ Error: No snapshots found in database
```

**Solution**: Run `snapshot` or `full` mode first:
```bash
python agents/benchmark_intelligence/main.py snapshot
```

### Error: Configuration Invalid

```
❌ Error: Configuration validation failed
   - labs.yaml: Missing required field 'labs'
```

**Solution**: Check `labs.yaml` format, ensure all required fields present

### Warning: PDF Parsing Failed

```
⚠ Warning: Failed to parse PDF (image-only, no text layer)
   File: https://example.com/report.pdf
```

**Expected behavior**: System skips unreadable PDFs and continues

### Warning: Google Search Blocked

```
⚠ Warning: Google search blocked after 3 retries
   Query: "Qwen2.5 technical report"
   Falling back to skip strategy
```

**Expected behavior**: Google search disabled by default (often blocked). System relies on direct URL patterns.

### Performance: Pipeline Too Slow

**Check**:
1. Number of models configured (`models_per_lab` in `labs.yaml`)
2. Network connectivity (slow API responses)
3. Incremental updates enabled (should skip 60%+ unchanged documents)

**Optimization**:
- Reduce `models_per_lab` for faster runs
- Increase `min_downloads` threshold to filter less popular models
- Use `snapshot` mode for scheduled runs (skip report generation)

---

## Data Management

### Database Location

```
agents/benchmark_intelligence/benchmark_intelligence.db
```

**Size**: Typically 10-50MB depending on model count

**Backup**:
```bash
cp agents/benchmark_intelligence/benchmark_intelligence.db backup/benchmark_intelligence_$(date +%Y%m%d).db
```

### Report Location

```
agents/benchmark_intelligence/reports/report_YYYYMMDD_HHMMSS.md
```

**Cleanup** (keep last 10 reports):
```bash
cd agents/benchmark_intelligence/reports
ls -t report_*.md | tail -n +11 | xargs rm
```

### Taxonomy Archives

```
archive/benchmark_taxonomy_YYYYMMDD.md
```

**Purpose**: Historical taxonomy versions for tracking category evolution

---

## Testing

### Run Test Suite

```bash
pytest tests/ -v
```

**Test Phases**:
1. **Source Discovery**: Validates all sources found for test models (2 models)
2. **Benchmark Extraction**: Precision/recall metrics against ground truth
3. **Taxonomy Generation**: AI-generated categories for manual review
4. **End-to-End Report**: Full pipeline validation

### Ground Truth Data

```
tests/ground_truth/ground_truth.yaml
```

Contains known-good data for validation:
- 2 test models (from different labs)
- All documented sources (model cards, papers, blogs)
- Benchmark names manually verified
- Includes figure-based benchmarks

---

## Best Practices

### Initial Setup

1. Start with small configuration (2-3 labs, 5 models per lab)
2. Run full pipeline and validate output
3. Review generated taxonomy for accuracy
4. Gradually increase scope (more labs, more models)

### Regular Operation

1. Run `full` mode weekly for comprehensive updates
2. Review emerging benchmarks section for new trends
3. Check taxonomy changes (archived versions)
4. Monitor report quality (links, data accuracy)

### Configuration Tuning

1. Adjust `models_per_lab` based on interest (5-20 typical)
2. Set `min_downloads` to filter noise (10K-100K range)
3. Add/remove labs based on research focus
4. Manually override categories in `categories.yaml` if AI misclassifies

### Performance Optimization

1. Use `snapshot` mode for scheduled runs (faster, no report overhead)
2. Generate reports on-demand with `report` mode
3. Monitor database size (clean old snapshots if needed)
4. Keep taxonomy archives manageable (delete very old versions)

---

## Next Steps

### After First Run

1. **Review the report**: Check `agents/benchmark_intelligence/reports/report_*.md`
2. **Validate taxonomy**: Review `benchmark_taxonomy.md` for category accuracy
3. **Check quality**: Look for false positives or missed benchmarks
4. **Adjust configuration**: Tune labs, filters, and thresholds as needed

### Regular Workflow

1. **Weekly**: Run `snapshot` mode via cron or Ambient
2. **Monthly**: Generate fresh report with `report` mode
3. **Quarterly**: Review taxonomy evolution and category coherence
4. **As needed**: Run `full` mode for immediate comprehensive updates

### Advanced Features

1. **Custom Categories**: Override AI classification in `categories.yaml`
2. **Lab-Specific Analysis**: Filter reports by lab for competitive insights
3. **Temporal Analysis**: Compare multiple snapshots for trend identification
4. **Data Export**: Query SQLite database directly for custom analysis

---

## Support & Resources

### Documentation

- **Feature Spec**: `specs/001-benchmark-intelligence/spec.md`
- **Implementation Plan**: `specs/001-benchmark-intelligence/plan.md`
- **Data Model**: `specs/001-benchmark-intelligence/data-model.md`
- **CLI Contract**: `specs/001-benchmark-intelligence/contracts/cli-interface.md`

### Common Issues

See **Troubleshooting** section above for solutions to common problems.

### Getting Help

1. Check documentation in `specs/001-benchmark-intelligence/`
2. Review test cases in `tests/` for usage examples
3. Enable `--verbose` mode for detailed debugging
4. Check GitHub Issues for known problems

---

## Appendix: Example Workflow

### Scenario: Weekly Benchmark Tracking

**Goal**: Keep database updated weekly, generate monthly reports

**Setup** (one-time):
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure labs
# Edit labs.yaml: 10 labs, 10 models per lab

# 3. Set API key
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc

# 4. Initial run
python agents/benchmark_intelligence/main.py full
```

**Weekly** (automated via cron):
```bash
# Every Sunday at 2 AM
0 2 * * 0 cd /path/to/trending_benchmarks && python agents/benchmark_intelligence/main.py snapshot --quiet >> logs/benchmark_$(date +\%Y\%m\%d).log 2>&1
```

**Monthly** (manual):
```bash
# Generate fresh report from accumulated snapshots
python agents/benchmark_intelligence/main.py report

# Review report
cat agents/benchmark_intelligence/reports/report_$(ls -t agents/benchmark_intelligence/reports/ | head -1)

# Check taxonomy changes
diff archive/benchmark_taxonomy_$(ls -t archive/ | head -2 | tail -1) benchmark_taxonomy.md
```

**Result**:
- Always-current database with 4 snapshots per month
- Monthly reports showing temporal trends
- Taxonomy evolution tracking
- Minimal manual intervention

---

**Version**: 1.0
**Last Updated**: 2026-04-03
**Status**: Stable
