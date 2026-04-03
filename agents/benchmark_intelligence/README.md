# Benchmark Intelligence Agent

Automated system for discovering, extracting, and tracking AI model benchmarks from HuggingFace, blogs, papers, and GitHub.

## Overview

This agent monitors trending AI models and identifies which benchmarks are being used for evaluation. It provides insights into:
- Most commonly used benchmarks
- Emerging benchmarks (first seen ≤3 months)
- Almost extinct benchmarks (last seen ≥9 months)
- Benchmark usage trends over time
- Lab-specific benchmark preferences

**Full specification**: See [SPECIFICATIONS.md](/SPECIFICATIONS.md)

## Quick Start

```bash
# Full execution (discovery + snapshot + report)
python main.py

# Update database and create snapshot only
python main.py snapshot

# Regenerate report from latest snapshot
python main.py report
```

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

- **Multi-source extraction**: Model cards, blogs, arXiv papers, GitHub
- **Figure extraction**: Vision AI analyzes charts and tables in images
- **Variant tracking**: Captures shots (0-shot, 5-shot), methods (CoT, PoT), model types (base, instruct)
- **Temporal tracking**: 12-month rolling window with snapshot history
- **Smart caching**: Content-hash based caching to avoid re-processing unchanged sources
- **Taxonomy evolution**: AI-powered taxonomy that evolves as new benchmarks are discovered

## Testing

Ground truth data for validation:
- See `tests/ground_truth/ground_truth.yaml`
- Testing framework defined in SPECIFICATIONS.md Section 12

## Output

Generated reports include:
1. Executive Summary
2. Most Common Benchmarks (absolute counts)
3. Trending Benchmarks (relative frequency)
4. Emerging Benchmarks (first seen ≤3 months)
5. Almost Extinct Benchmarks (last seen ≥9 months)
6. Benchmark Categories
7. Lab-Specific Insights

---

**For complete technical specifications**, see [SPECIFICATIONS.md](/SPECIFICATIONS.md)
