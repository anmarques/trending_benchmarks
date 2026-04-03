# Benchmark Intelligence Agent

Automated system for discovering, extracting, and tracking AI model benchmarks from HuggingFace, blogs, papers, and GitHub.

## Overview

This agent monitors trending AI models and identifies which benchmarks are being used for evaluation. It provides comprehensive insights into:

- **Most commonly used benchmarks** - Ranked by absolute usage across models
- **Emerging benchmarks** - New evaluations first seen ≤3 months ago
- **Almost extinct benchmarks** - Declining evaluations last seen ≥9 months ago
- **Temporal trends** - 12-month rolling window with snapshot-based tracking
- **Lab-specific preferences** - Benchmark choices by organization
- **Category distribution** - Taxonomy-based classification
- **Historical comparison** - Trend analysis across multiple snapshots

**Version**: 1.0.0
**Status**: Production Ready
**Full specification**: See [specs/001-benchmark-intelligence/spec.md](../../specs/001-benchmark-intelligence/spec.md)

## Quick Start

```bash
# Full execution (discovery + snapshot + report) - DEFAULT
python -m agents.benchmark_intelligence.main
python -m agents.benchmark_intelligence.main full

# Update database and create snapshot only (no report)
python -m agents.benchmark_intelligence.main snapshot

# Regenerate report from latest snapshot (no pipeline)
python -m agents.benchmark_intelligence.main report
```

**All 6 User Stories Implemented:**
- ✓ US1: Discover Current Benchmark Landscape
- ✓ US2: Track Benchmark Trends Over Time
- ✓ US3: Explore Models by Lab and Popularity
- ✓ US4: Understand Benchmark Categorization
- ✓ US5: Analyze Lab Benchmark Preferences
- ✓ US6: Access Multi-Source Documentation

## Directory Structure

```
agents/benchmark_intelligence/
├── main.py                    # Entry point
├── reporting.py               # Report generation
├── clients/                   # API client abstractions
│   ├── api_client.py          # Direct Anthropic API client
│   ├── mcp_client.py          # MCP integration client
│   ├── factory.py             # Client factory
│   └── base.py                # Base client interface
├── tools/                     # Core processing modules
│   ├── discover_models.py     # HuggingFace model discovery
│   ├── fetch_docs.py          # Document fetching (blogs, papers, GitHub)
│   ├── extract_benchmarks.py # AI-powered benchmark extraction
│   ├── consolidate.py         # Fuzzy matching and deduplication
│   ├── classify.py            # Benchmark categorization
│   ├── taxonomy_manager.py    # Taxonomy evolution
│   ├── cache.py               # SQLite persistence
│   └── pdf_parser.py          # PDF parsing (pdfplumber + PyPDF2)
├── prompts/                   # AI prompts
│   ├── extract_benchmarks.md
│   ├── consolidate.md
│   └── classify.md
├── config/
│   ├── auth.yaml.example      # Authentication template
│   └── (benchmark_taxonomy.md and categories.yaml auto-generated at root)
└── reports/                   # Generated reports
    └── .gitkeep
```

## Configuration

### 1. Labs Configuration (`labs.yaml` at root)

Define which organizations to track:

```yaml
labs:
  - id: meta
    name: Meta AI
    aliases: [meta-llama, facebook]
  - id: openai
    name: OpenAI
    aliases: [openai]
```

### 2. Authentication (`config/auth.yaml`)

Required for document fetching:

```bash
cp config/auth.yaml.example config/auth.yaml
# Edit config/auth.yaml with your credentials
```

### 3. Environment Variables

```bash
# Anthropic API key (required)
export ANTHROPIC_API_KEY="your-key-here"

# Optional: GitHub token for higher rate limits
export GITHUB_TOKEN="your-token-here"
```

## Execution Modes

### Mode 1: `snapshot` (pipeline + snapshot, no report)
Runs full discovery and processing pipeline, creates snapshot, skips report generation. Use for scheduled updates.

### Mode 2: `report` (report only)
Regenerates report from latest snapshot without running pipeline. Use when updating report templates.

### Mode 3: `full` (default)
Complete execution: pipeline → snapshot → report. Use for typical manual runs.

## Data Storage

- **Database**: SQLite database at root (gitignored)
- **Taxonomy**: Auto-generated at root level
  - `benchmark_taxonomy.md` - Complete reference
  - `categories.yaml` - Category definitions
- **Reports**: `reports/report_YYYYMMDD_HHMMSS.md`

## Key Features

### Core Capabilities (FR-001 to FR-040)

**Discovery & Filtering**:
- ✓ Multi-lab model discovery (HuggingFace API)
- ✓ Task type filtering (text-gen, multimodal, ASR)
- ✓ Rolling 12-month time window
- ✓ Popularity thresholds (min downloads)

**Source Processing**:
- ✓ Multi-source extraction (model cards, blogs, arXiv, GitHub)
- ✓ Multi-format parsing (Markdown, HTML, PDF)
- ✓ Visual content extraction (charts, tables, figures)
- ✓ Change detection and incremental updates
- ✓ Rate limiting and retry logic

**Benchmark Intelligence**:
- ✓ AI-powered benchmark extraction (Claude Sonnet 4)
- ✓ Variant tracking (shots, methods, model types)
- ✓ Name consolidation (fuzzy matching + AI)
- ✓ Multi-label classification
- ✓ Automatic taxonomy evolution

**Temporal Analysis**:
- ✓ Snapshot-based tracking (SC-009 to SC-012)
- ✓ Absolute counts and relative frequencies
- ✓ Emerging/Active/Almost-Extinct status
- ✓ Historical trend comparison
- ✓ 12-month rolling window accuracy

**Reporting**:
- ✓ 7 comprehensive sections (FR-027 to FR-031)
- ✓ No hardcoded data - all real pipeline results
- ✓ Source link verification
- ✓ Readable number formatting
- ✓ Historical snapshots for trend visualization

**Performance**:
- ✓ Smart caching (60%+ document skip rate on incremental runs)
- ✓ Progress reporting (every model + every 10 models)
- ✓ Graceful error handling
- ✓ Sub-2-hour execution for 150 models
- ✓ Sub-2-minute report generation

## Testing

Ground truth data for validation:
- See `tests/ground_truth/ground_truth.yaml`
- Testing framework defined in SPECIFICATIONS.md Section 12

## Output

### Generated Reports (7 Sections)

1. **Executive Summary** - Overview stats and benchmark status distribution
2. **Trending Models** - Last 12 months, sorted by downloads
3. **Most Common Benchmarks** - All-time top 20 + This month's top 20
4. **Temporal Trends** - Rolling window analysis with frequencies
5. **Emerging Benchmarks** - First seen ≤3 months, with adoption metrics
6. **Almost Extinct Benchmarks** - Last seen ≥9 months, declining usage
7. **Historical Comparison** - Snapshot-to-snapshot trend analysis
8. **Benchmark Categories** - Taxonomy-based distribution with evolution notes
9. **Lab-Specific Insights** - Per-lab statistics and preferences

### Report Features

- **No Hardcoded Data**: All sections use real pipeline results (SC-018)
- **Source Verification**: All links validated (SC-019)
- **Trend Visualization**: Multi-snapshot comparison when available (SC-020)
- **Fast Regeneration**: Report-only mode completes in <2 minutes (SC-021)
- **Taxonomy Tracking**: Versioned taxonomy with archived history (SC-023)
- **Adoption Analysis**: Identify gaining/declining benchmarks (SC-024)

## Success Criteria Status

All 24 success criteria (SC-001 to SC-024) verified:

✓ **Comprehensive Coverage** (SC-001 to SC-004)
✓ **Data Quality** (SC-005 to SC-008)
✓ **Temporal Accuracy** (SC-009 to SC-012)
✓ **Efficiency & Reliability** (SC-013 to SC-016)
✓ **Report Quality** (SC-017 to SC-020)
✓ **User Experience** (SC-021 to SC-024)

See [CHANGELOG.md](../../CHANGELOG.md) for full v1.0 release notes.

---

**For complete technical specifications**, see [specs/001-benchmark-intelligence/spec.md](../../specs/001-benchmark-intelligence/spec.md)
