# Running on Ambient - Quick Start Guide

**Project**: Benchmark Intelligence System  
**Platform**: Ambient Code Platform  
**Last Updated**: 2026-04-07

---

## Prerequisites

### 1. Environment Variables (Required)

Set these in **Workspace Settings → Environment Variables**:

- **`HF_TOKEN`** (Required): Your HuggingFace API token
  - Get it from: https://huggingface.co/settings/tokens
  - Permissions needed: Read access

- **`ANTHROPIC_API_KEY`** (Auto-detected on Ambient)
  - Not needed on Ambient - uses Vertex AI automatically
  - Only required if running outside Ambient

### 2. Repository Setup

The repository should already be available at:
```
/workspace/repos/trending_benchmarks/
```

If not, clone it:
```bash
git clone <repository-url> /workspace/repos/trending_benchmarks
cd /workspace/repos/trending_benchmarks
```

---

## Running on Ambient

### Quick Start: Full Pipeline

Run the complete 6-stage pipeline in one command:

```bash
/benchmark_intelligence.generate
```

**This will**:
1. Discover trending models from 15+ labs
2. Find documentation (model cards, papers, blogs)
3. Extract benchmarks using AI (parallel processing)
4. Consolidate benchmark names (fuzzy matching + aliases)
5. Categorize benchmarks by type
6. Generate comprehensive reports

**Expected Runtime**: ~50-60 minutes for 65 models (default concurrency: 20)

---

## Individual Stage Execution

For debugging or running specific stages:

### Stage 1: Filter Models
```bash
/benchmark_intelligence.filter_models
```
**Output**: `outputs/filter_models_<timestamp>.json`  
**Purpose**: Discover trending models from target labs

### Stage 2: Find Documents
```bash
/benchmark_intelligence.find_docs
```
**Output**: `outputs/find_documents_<timestamp>.json`  
**Purpose**: Locate model cards, papers, blogs for each model

### Stage 3: Parse Documents
```bash
/benchmark_intelligence.parse_docs --concurrency 30
```
**Output**: `outputs/parse_documents_<timestamp>.json`  
**Purpose**: Extract benchmarks from documents using AI  
**Concurrency**: Adjust `--concurrency` based on API rate limits (default: 20)

### Stage 4: Consolidate Benchmarks
```bash
/benchmark_intelligence.consolidate_benchmarks
```
**Output**: `outputs/consolidate_names_<timestamp>.json`  
**Purpose**: Deduplicate benchmark name variations  
**Features**: Fuzzy matching, alias resolution, AI review

### Stage 5: Categorize Benchmarks
```bash
/benchmark_intelligence.categorize_benchmarks
```
**Output**: `outputs/categorize_benchmarks_<timestamp>.json`  
**Purpose**: Classify benchmarks by category (Knowledge, Math, Code, etc.)

### Stage 6: Generate Report
```bash
/benchmark_intelligence.report
```
**Output**: `reports/report_<timestamp>.md`  
**Purpose**: Create comprehensive Markdown report with trends

---

## Advanced Usage

### Running with Custom Concurrency

Higher concurrency = faster but more API usage:
```bash
/benchmark_intelligence.parse_docs --concurrency 50
```

Or for the full pipeline:
```bash
/benchmark_intelligence.generate --concurrency 50
```

**Recommended Values**:
- **Development**: 10-20 workers
- **Production**: 30-50 workers (watch API rate limits)

### Loading from Database

Skip JSON files and load from database:
```bash
/benchmark_intelligence.consolidate_benchmarks --from-db
```

---

## Configuration

### Edit Target Labs

Modify which labs to track:

```bash
# Edit config.yaml
cd /workspace/repos/trending_benchmarks
nano config.yaml

# Add/remove labs in the 'labs' section
labs:
  - Qwen
  - meta-llama
  - mistralai
  - google
  # ... etc
```

### Adjust Discovery Settings

```yaml
discovery:
  models_per_lab: 15           # Models to fetch per lab
  sort_by: "downloads"         # downloads | trending | lastModified
  min_downloads: 1000          # Minimum popularity threshold
  date_filter_months: 12       # Only models from last N months
```

### Configure Rate Limiting

```yaml
rate_limiting:
  huggingface:
    requests_per_minute: 60
  anthropic:
    requests_per_minute: 50
  arxiv:
    requests_per_minute: 30
```

### Add Benchmark Aliases

```yaml
consolidation:
  benchmark_aliases:
    "ARC-C": "ARC-Challenge"
    "BBH": "BIG-Bench Hard"
    "GSM8K": "GSM-8K"
    # Add more as discovered
```

---

## Output Files

### JSON Outputs (Intermediate Data)

Located in `agents/benchmark_intelligence/outputs/`:
```
outputs/
├── filter_models_20260407_140530.json          # Discovered models
├── find_documents_20260407_140845.json        # Document URLs
├── parse_documents_20260407_142315.json       # Extracted benchmarks
├── consolidate_names_20260407_143200.json     # Deduplicated names
└── categorize_benchmarks_20260407_143545.json # Categorized benchmarks
```

### Reports (Final Output)

Located in `agents/benchmark_intelligence/reports/`:
```
reports/
├── report_20260407_144012.md  # Latest comprehensive report
├── report_20260406_162723.md  # Previous runs
└── ...
```

### Database Cache

Located in `agents/benchmark_intelligence/benchmark_cache.db`:
- Content-hash based caching
- Only re-processes changed documents
- Enables fast resumability

---

## Monitoring Progress

### Real-Time Progress Updates

The system provides live progress every 5 seconds:

```
Stage 3: Parsing Documents
  Progress: 45/65 models processed (69.2%)
  Benchmarks extracted: 2,847
  Errors encountered: 3
  Elapsed time: 25m 14s
  Estimated remaining: 11m 32s
```

### Error Handling

Errors are aggregated by type and reported at completion:

```
Error Summary:
  - fetch_error: 5 cases (arXiv timeouts)
  - extraction_error: 2 cases (malformed HTML)
  - api_error: 1 case (rate limit)
```

### Resumability

If the pipeline is interrupted, it will resume from where it left off:
- Hash-based change detection skips unchanged documents
- Only re-processes new or modified content

---

## Troubleshooting

### Issue: "HF_TOKEN not set"

**Solution**: Set HuggingFace token in Workspace Settings → Environment Variables

```bash
# Verify it's set
echo $HF_TOKEN
```

### Issue: "Rate limit exceeded (429)"

**Solution**: Reduce concurrency or adjust rate limits in `config.yaml`

```bash
# Lower concurrency
/benchmark_intelligence.parse_docs --concurrency 10
```

### Issue: "No benchmarks found"

**Solution**: Check if models have public model cards

```bash
# Run individual stages to debug
/benchmark_intelligence.filter_models
/benchmark_intelligence.find_docs
/benchmark_intelligence.parse_docs
```

### Issue: "Slow processing"

**Solution**: Increase concurrency (if within API limits)

```bash
/benchmark_intelligence.generate --concurrency 40
```

### Issue: "Out of memory"

**Solution**: Process in batches or reduce concurrency

```bash
# Process fewer models at once
/benchmark_intelligence.parse_docs --concurrency 10
```

---

## Scheduled Execution

The system includes a monthly scheduled workflow (configured in `.ambient/ambient.json`):

```json
"scan-benchmarks": {
  "description": "Discover models and track benchmarks",
  "agent": "benchmark-intelligence",
  "schedule": "0 9 1 * *"  // 9 AM on the 1st of every month
}
```

To modify the schedule, edit `.ambient/ambient.json`.

---

## Example Workflows

### 1. Quick Test Run (5 models)

```bash
# Edit config temporarily
labs:
  - Qwen  # Only one lab

discovery:
  models_per_lab: 5  # Only 5 models

# Run pipeline
/benchmark_intelligence.generate --concurrency 10
```

**Runtime**: ~10-15 minutes

### 2. Full Production Run (All labs, 15 models each)

```bash
# Default config (15 labs × 15 models)
/benchmark_intelligence.generate --concurrency 30
```

**Runtime**: ~50-60 minutes

### 3. Update Existing Report (Re-process changed models only)

```bash
# Cache will skip unchanged models
/benchmark_intelligence.generate
```

**Runtime**: ~5-20 minutes (depending on changes)

### 4. Debug Single Stage

```bash
# Run stages individually to isolate issues
/benchmark_intelligence.filter_models
# Check outputs/filter_models_*.json

/benchmark_intelligence.find_docs
# Check outputs/find_documents_*.json

/benchmark_intelligence.parse_docs --concurrency 5
# Check outputs/parse_documents_*.json
```

---

## Best Practices

### For Development/Testing
- ✅ Use low concurrency (10-20 workers)
- ✅ Test with 1-2 labs first
- ✅ Run individual stages to debug
- ✅ Check `outputs/` JSON files after each stage

### For Production
- ✅ Use higher concurrency (30-50 workers)
- ✅ Monitor rate limits (check error summaries)
- ✅ Run full pipeline with `generate` command
- ✅ Schedule monthly runs for trend tracking

### Performance Optimization
- ✅ Increase concurrency within API limits
- ✅ Use hash cache (automatic - no action needed)
- ✅ Adjust `models_per_lab` based on needs
- ✅ Filter by `min_downloads` to skip low-usage models

### Data Quality
- ✅ Check ground truth validation results (≥95% accuracy)
- ✅ Review error summaries for systematic issues
- ✅ Monitor benchmark alias consolidation
- ✅ Validate report output for completeness

---

## Support & Documentation

- **Full Documentation**: See [README.md](README.md)
- **Testing Coverage**: See [TESTING_COVERAGE.md](TESTING_COVERAGE.md)
- **Consolidation Analysis**: See [consolidation_inspection_report.md](consolidation_inspection_report.md)
- **Task Breakdown**: See [specs/001-benchmark-intelligence/tasks.md](specs/001-benchmark-intelligence/tasks.md)
- **Implementation Plan**: See [specs/001-benchmark-intelligence/plan.md](specs/001-benchmark-intelligence/plan.md)

---

## Summary

**Simplest Way to Run**:
```bash
/benchmark_intelligence.generate
```

**Expected Output**: Comprehensive benchmark report in `reports/report_<timestamp>.md`

**Need Help?**: Check troubleshooting section above or review individual stage outputs in `outputs/`

🚀 **Ready to track benchmarks!**
