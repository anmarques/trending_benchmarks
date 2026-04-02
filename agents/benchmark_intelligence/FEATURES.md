# Benchmark Intelligence Agent - Feature Overview

## Core Features

### 1. Main Orchestrator (`main.py`)

The `BenchmarkIntelligenceAgent` class orchestrates the complete workflow:

**Key Methods:**
- `run(incremental=True, force_reprocess=False)` - Execute full workflow
- `_discover_models()` - Find trending models from configured labs
- `_process_model(model)` - Process individual model through pipeline
- `_should_skip_model(model)` - Check cache for changes (incremental support)
- `_store_model_in_cache()` - Persist results to database
- `_create_snapshot()` - Save state snapshot
- `_generate_report()` - Create comprehensive report

**Features:**
- ✅ Progress tracking with detailed logging
- ✅ Error handling (continue on individual failures)
- ✅ Incremental processing (skip unchanged models)
- ✅ Dry-run mode for testing
- ✅ Verbose mode for debugging
- ✅ Statistics collection and reporting
- ✅ CLI interface with argparse
- ✅ Configuration via YAML files

**CLI Usage:**
```bash
python -m agents.benchmark_intelligence.main [OPTIONS]
  --config PATH      Custom config file
  --cache PATH       Custom cache database
  --dry-run          No writes (testing)
  --verbose          Debug logging
  --force            Reprocess all
  --no-incremental   Disable incremental mode
```

### 2. Report Generator (`reporting.py`)

The `ReportGenerator` class creates comprehensive markdown reports:

**Report Sections:**

1. **Executive Summary**
   - Total models, benchmarks, labs tracked
   - Time period coverage
   - High-level statistics

2. **Trending Models This Month**
   - Models discovered in last 30 days
   - Table with name, lab, downloads, likes, date
   - Limited to top 20

3. **Most Common Benchmarks**
   - All-time top 20 benchmarks by usage
   - This month's top 20 benchmarks
   - Comparison and trends
   - Categories and first seen dates

4. **Emerging Benchmarks**
   - New benchmarks in last 90 days
   - Sorted by recency
   - Limited to top 15

5. **Benchmark Categories**
   - Distribution pie chart data
   - Top 15 categories by count
   - Percentage breakdown
   - JSON data for visualization

6. **Lab-Specific Insights**
   - Models per lab
   - Average downloads and likes
   - Top 20 labs by model count
   - Benchmark preferences (coming soon)

7. **Temporal Trends**
   - Benchmark activity over time
   - First/last recorded dates
   - Active days tracking
   - Growth metrics

**Key Methods:**
- `generate_report()` - Create full markdown report
- `update_readme(content)` - Write to README.md
- `save_snapshot(content)` - Save timestamped historical report
- `generate_json_summary()` - Export key metrics as JSON
- `_format_number(num)` - Human-readable formatting (1.2M, 3.5K)

**Output Files:**
- `README.md` - Main report (always current)
- `reports/report_YYYYMMDD_HHMMSS.md` - Historical snapshots

### 3. Package Initialization (`__init__.py`)

**Exports:**
- `BenchmarkIntelligenceAgent` - Main orchestrator
- `ReportGenerator` - Report generation
- `CacheManager` - Database access

**Version:** 1.0.0

## Workflow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Load Configuration (config/labs.yaml)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  2. Discover Trending Models (from HuggingFace)                 │
│     - Query each configured lab                                 │
│     - Filter by tags, downloads, sort criteria                  │
│     - Return top N models per lab                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  3. For Each Model:                                             │
│                                                                  │
│  a. Check Cache                                                 │
│     - Compare model card hash                                   │
│     - Skip if unchanged (incremental mode)                      │
│                                                                  │
│  b. Parse Model Card                                            │
│     - Fetch README.md from HuggingFace                          │
│     - Extract sections and metadata                             │
│                                                                  │
│  c. Extract Benchmarks from Card (AI)                           │
│     - Use Claude to parse and extract                           │
│     - Capture scores, metrics, contexts                         │
│                                                                  │
│  d. Fetch Related Documentation                                 │
│     - Search for blogs, papers, reports                         │
│     - Fetch content from web sources                            │
│                                                                  │
│  e. Extract Benchmarks from Docs (AI)                           │
│     - Process each document                                     │
│     - Aggregate results                                         │
│                                                                  │
│  f. Consolidate All Benchmarks (AI)                             │
│     - Map name variations to canonical forms                    │
│     - Distinguish variants from distinct benchmarks             │
│                                                                  │
│  g. Classify Benchmarks (AI)                                    │
│     - Assign multi-label categories                             │
│     - Identify modality, domain, difficulty                     │
│                                                                  │
│  h. Store in Cache                                              │
│     - Save model, benchmarks, classifications                   │
│     - Store documents and links                                 │
│                                                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  4. Create Snapshot (cache state + statistics)                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  5. Generate Report                                             │
│     - Analyze trends and statistics                             │
│     - Create markdown report                                    │
│     - Update README.md                                          │
│     - Save timestamped snapshot                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Points

### Existing Tools Used

1. **discover_models.py**
   - Model discovery from HuggingFace
   - Lab/organization filtering
   - Tag-based filtering

2. **parse_model_card.py**
   - Fetch and parse README files
   - Section extraction
   - Metadata analysis

3. **extract_benchmarks.py**
   - AI-powered benchmark extraction
   - Multi-source aggregation
   - Structured data capture

4. **fetch_docs.py**
   - Web search for documentation
   - Content fetching
   - Document classification

5. **consolidate.py**
   - AI-powered name consolidation
   - Variation mapping
   - Canonical name creation

6. **classify.py**
   - AI-powered benchmark classification
   - Multi-label categorization
   - Taxonomy-based assignment

7. **cache.py**
   - SQLite database management
   - Content hashing
   - Query methods for analytics

### External Dependencies

- **anthropic** - Claude API for AI processing
- **huggingface_hub** - HuggingFace API client
- **pyyaml** - Configuration file parsing
- **sqlite3** - Built-in database (no install needed)

## Statistics Tracking

The agent tracks comprehensive statistics during execution:

```python
{
    "models_discovered": 200,      # Total models found
    "models_processed": 185,       # Successfully processed
    "models_skipped": 10,          # Skipped (no changes)
    "models_failed": 5,            # Processing failed
    "benchmarks_extracted": 1523,  # Total benchmarks found
    "documents_fetched": 142,      # External docs fetched
    "errors": [                    # Error details
        {
            "model_id": "...",
            "error": "..."
        }
    ]
}
```

## Incremental Processing

The system supports efficient incremental updates:

1. **Content Hashing**: SHA256 hash of model card content
2. **Change Detection**: Compare hash with cached version
3. **Skip Logic**: Skip models with unchanged content
4. **Force Override**: `--force` flag to reprocess all

**Benefits:**
- Reduced API calls (lower costs)
- Faster execution (skip unchanged)
- Focus on new content

## Error Recovery

Fault-tolerant design:

- **Per-Model Isolation**: Failures don't stop pipeline
- **Error Logging**: All errors captured with context
- **Graceful Degradation**: Continue with available data
- **Statistics Reporting**: Error counts in results

## Output Formats

### Markdown Reports
- Human-readable
- GitHub-compatible
- Tables and charts
- Historical snapshots

### JSON Summary
```python
{
    "timestamp": "2026-04-02T14:30:00Z",
    "summary": {
        "total_models": 200,
        "total_benchmarks": 85,
        "total_labs": 15,
        "models_this_month": 23
    },
    "top_benchmarks": [...],
    "category_distribution": {...},
    "cache_stats": {...}
}
```

### SQLite Database
- Queryable with SQL
- Relational structure
- Indexed for performance
- Portable single file

## Configuration Options

### Labs Configuration
```yaml
labs:
  - Qwen
  - meta-llama
  - mistralai
  # ...more labs

discovery:
  models_per_lab: 20
  sort_by: "downloads"
  filter_tags:
    - "text-generation"
  min_downloads: 1000

schedule:
  frequency: "monthly"
  day_of_month: 1
  hour: 9
```

## Extension Points

The system is designed for extensibility:

1. **Custom Discovery**: Add new model sources
2. **Custom Extraction**: Add extraction patterns
3. **Custom Classification**: Modify taxonomy
4. **Custom Reports**: Add report sections
5. **Custom Storage**: Add data exporters

## Performance Characteristics

**Scalability:**
- Handles 100s of models efficiently
- Incremental processing for 1000s of models
- Caching reduces redundant work

**Resource Usage:**
- Low memory footprint
- Disk I/O for cache
- Network I/O for APIs

**Cost Considerations:**
- AI API calls (primary cost)
- HuggingFace API (free tier usually sufficient)
- Incremental mode reduces costs

## Future Enhancements

Potential additions:
- Web search/fetch integration
- Automated scheduling with cron
- Email/Slack notifications
- Data visualization dashboard
- API endpoint for queries
- Multi-lab benchmark comparison
- Historical trend analysis
- Benchmark recommendation engine

## Testing Support

Built-in testing features:
- `--dry-run` mode (no writes)
- `--verbose` mode (detailed logs)
- Isolated error handling
- Deterministic outputs
- Mock injection points

## Documentation

Complete documentation set:
- **USAGE.md** - Comprehensive usage guide
- **FEATURES.md** - This file (feature overview)
- **README.md** - Generated report (output)
- **Inline docstrings** - Code documentation
- **Type hints** - Function signatures

## Support Matrix

**Python Versions:** 3.8+
**Operating Systems:** Linux, macOS, Windows
**Databases:** SQLite 3.x
**APIs:** Anthropic Claude, HuggingFace Hub
