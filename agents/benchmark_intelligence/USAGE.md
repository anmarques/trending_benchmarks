# Benchmark Intelligence Agent - Usage Guide

## Overview

The Benchmark Intelligence Agent is a comprehensive system for tracking, extracting, and analyzing benchmark results from trending AI models across major labs and organizations.

## Installation

The agent requires the following dependencies:

```bash
pip install anthropic huggingface-hub pyyaml
```

## Command Line Interface

### Basic Usage

Run the full benchmark intelligence workflow:

```bash
python -m agents.benchmark_intelligence.main
```

This will:
1. Discover trending models from configured labs
2. Parse model cards and extract benchmarks
3. Fetch related documentation
4. Consolidate and classify benchmarks
5. Generate comprehensive reports

### Options

```bash
# Show help
python -m agents.benchmark_intelligence.main --help

# Dry run (no cache or file writes)
python -m agents.benchmark_intelligence.main --dry-run

# Verbose output for debugging
python -m agents.benchmark_intelligence.main --verbose

# Force reprocess all models (ignore cache)
python -m agents.benchmark_intelligence.main --force

# Disable incremental mode
python -m agents.benchmark_intelligence.main --no-incremental

# Custom configuration file
python -m agents.benchmark_intelligence.main --config /path/to/config.yaml

# Custom cache database path
python -m agents.benchmark_intelligence.main --cache /path/to/cache.db
```

### Common Workflows

**Initial Run (First Time):**
```bash
# Process all models from configured labs
python -m agents.benchmark_intelligence.main --verbose
```

**Daily/Weekly Updates (Incremental):**
```bash
# Only process new or changed models
python -m agents.benchmark_intelligence.main
```

**Testing Changes (Dry Run):**
```bash
# Test without modifying cache or files
python -m agents.benchmark_intelligence.main --dry-run --verbose
```

**Force Refresh:**
```bash
# Reprocess all models regardless of cache
python -m agents.benchmark_intelligence.main --force
```

## Python API

### Using the Agent Programmatically

```python
from agents.benchmark_intelligence import BenchmarkIntelligenceAgent

# Create agent with default settings
agent = BenchmarkIntelligenceAgent()

# Run the workflow
result = agent.run()

# Check results
if result["success"]:
    print(f"Processed {result['stats']['models_processed']} models")
    print(f"Extracted {result['stats']['benchmarks_extracted']} benchmarks")
else:
    print(f"Failed: {result['message']}")
```

### Custom Configuration

```python
from agents.benchmark_intelligence import BenchmarkIntelligenceAgent

# Custom paths and options
agent = BenchmarkIntelligenceAgent(
    config_path="/path/to/custom_config.yaml",
    cache_path="/path/to/custom_cache.db",
    dry_run=False,
    verbose=True,
)

# Run with options
result = agent.run(
    incremental=True,  # Only process new/changed models
    force_reprocess=False,  # Don't ignore cache
)
```

### Direct Cache Access

```python
from agents.benchmark_intelligence import CacheManager

# Open cache database
cache = CacheManager("benchmark_cache.db")

# Get statistics
stats = cache.get_stats()
print(f"Total models: {stats['models']}")
print(f"Total benchmarks: {stats['benchmarks']}")

# Get all models
models = cache.get_all_models()

# Get trending models from last 30 days
from datetime import datetime, timedelta
thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
recent = cache.get_trending_models(thirty_days_ago)

# Get benchmark trends
trends = cache.get_benchmark_trends()
top_benchmarks = sorted(trends, key=lambda x: x['total_models'], reverse=True)[:10]

# Get models by lab
qwen_models = cache.get_models_by_lab("Qwen")
```

### Report Generation

```python
from agents.benchmark_intelligence import ReportGenerator, CacheManager

# Initialize
cache = CacheManager("benchmark_cache.db")
reporter = ReportGenerator(cache)

# Generate markdown report
report = reporter.generate_report()
print(report)

# Update README
reporter.update_readme(report)

# Save historical snapshot
snapshot_path = reporter.save_snapshot(report)
print(f"Snapshot saved to: {snapshot_path}")

# Generate JSON summary
summary = reporter.generate_json_summary()
print(f"Total models: {summary['summary']['total_models']}")
print(f"Top benchmark: {summary['top_benchmarks'][0]['name']}")
```

## Configuration

### Labs Configuration (`config/labs.yaml`)

```yaml
# Target model creators/organizations to track
labs:
  - Qwen
  - meta-llama
  - mistralai
  - google
  - microsoft
  - anthropic

# Discovery settings
discovery:
  models_per_lab: 20  # Top N models per lab
  sort_by: "downloads"  # Options: downloads, trending, lastModified
  filter_tags:
    - "text-generation"
    - "image-text-to-text"
  min_downloads: 1000  # Minimum downloads to consider

# Cadence settings
schedule:
  frequency: "monthly"  # monthly, weekly, daily
  day_of_month: 1
  hour: 9
```

## Output

### Reports

The agent generates two types of reports:

1. **README.md** - Main report (always updated)
   - Location: `agents/benchmark_intelligence/README.md`
   - Contains current state and latest insights

2. **Historical Snapshots** - Timestamped reports
   - Location: `agents/benchmark_intelligence/reports/report_YYYYMMDD_HHMMSS.md`
   - Preserved for historical analysis

### Report Sections

Each report includes:

1. **Executive Summary** - High-level statistics
2. **Trending Models This Month** - Recently discovered models
3. **Most Common Benchmarks** - All-time and recent top benchmarks
4. **Emerging Benchmarks** - New benchmarks in last 90 days
5. **Benchmark Categories** - Distribution across categories
6. **Lab-Specific Insights** - Per-lab statistics and preferences
7. **Temporal Trends** - Evolution over time

### Cache Database

The SQLite cache database stores:
- **Models**: All discovered models with metadata
- **Benchmarks**: Canonical benchmark names and classifications
- **Model-Benchmark Links**: Scores and evaluation contexts
- **Documents**: Fetched technical reports, blogs, papers
- **Snapshots**: Historical state captures

Database location: `benchmark_cache.db` (configurable)

## Workflow Details

### 1. Model Discovery

- Searches HuggingFace for models from configured labs
- Filters by tags and download thresholds
- Sorts by downloads/trending/lastModified

### 2. Model Card Parsing

- Fetches README.md from HuggingFace
- Extracts sections and metadata
- Detects presence of benchmark data

### 3. Benchmark Extraction (AI-Powered)

- Uses Claude to parse text and extract benchmarks
- Captures scores, metrics, and evaluation contexts
- Handles various formats (tables, lists, prose)

### 4. Documentation Fetching

- Searches for related blogs, papers, technical reports
- Fetches content from web sources
- Extracts additional benchmark data

### 5. Consolidation (AI-Powered)

- Uses Claude to map benchmark name variations
- Creates canonical names (e.g., "mmlu" → "MMLU")
- Distinguishes true variants from distinct benchmarks

### 6. Classification (AI-Powered)

- Uses Claude with comprehensive taxonomy
- Assigns multi-label categories
- Identifies modality, domain, difficulty

### 7. Caching

- Stores all data in SQLite database
- Uses content hashing to detect changes
- Supports incremental updates

### 8. Reporting

- Generates comprehensive markdown reports
- Calculates trends and statistics
- Creates visualizations (charts, graphs)

## Error Handling

The agent is designed to be fault-tolerant:

- **Individual Model Failures**: Logged and skipped, processing continues
- **API Rate Limits**: Handled gracefully with retries
- **Missing Data**: Defaults provided, warnings logged
- **Validation Errors**: Detected and reported

Error statistics are included in the run result:

```python
result = agent.run()
if result["stats"]["models_failed"] > 0:
    print(f"Failed models: {result['stats']['models_failed']}")
    for error in result["stats"]["errors"]:
        print(f"  {error['model_id']}: {error['error']}")
```

## Best Practices

1. **Initial Setup**: Run with `--verbose` to understand the workflow
2. **Regular Updates**: Use incremental mode for efficiency
3. **Monitoring**: Check error counts and logs regularly
4. **Cache Management**: Backup `benchmark_cache.db` periodically
5. **Configuration**: Adjust `models_per_lab` based on needs
6. **API Keys**: Set `ANTHROPIC_API_KEY` environment variable

## Troubleshooting

### Issue: No models discovered

**Solution**: Check that labs are configured correctly and have public models

### Issue: Benchmark extraction fails

**Solution**: Ensure `ANTHROPIC_API_KEY` is set and valid

### Issue: Cache locked

**Solution**: Ensure no other agent processes are running

### Issue: High API costs

**Solution**: Use `--dry-run` for testing, reduce `models_per_lab`

## Performance

Typical run times (varies by configuration):

- **Model Discovery**: 1-2 minutes per lab
- **Model Card Parsing**: 1-5 seconds per model
- **Benchmark Extraction**: 2-5 seconds per document (AI call)
- **Classification**: 1-3 seconds per unique benchmark (AI call)
- **Report Generation**: 1-5 seconds

For 20 models/lab × 10 labs = 200 models:
- **Full Run**: ~30-60 minutes
- **Incremental Run**: ~5-15 minutes (only new/changed models)

## Advanced Usage

### Custom Taxonomy

Edit `config/benchmark_taxonomy.md` to customize classification categories.

### Custom Prompts

Edit files in `prompts/` directory:
- `extract_benchmarks.md` - Benchmark extraction prompt
- `consolidate.md` - Name consolidation prompt
- `classify.md` - Classification prompt

### Integration

The agent can be integrated into CI/CD pipelines:

```bash
# In GitHub Actions
- name: Update Benchmark Intelligence
  run: |
    python -m agents.benchmark_intelligence.main
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Scheduling

Use cron for automated runs:

```bash
# Daily at 9 AM
0 9 * * * cd /path/to/repo && python -m agents.benchmark_intelligence.main
```

## License

See main repository LICENSE file.

## Support

For issues and questions, see the main repository documentation.
