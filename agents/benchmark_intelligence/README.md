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

### Full Pipeline (All Stages)

```bash
# Python execution
python -m agents.benchmark_intelligence.main generate

# Ambient workflow
/benchmark_intelligence.generate
```

### Individual Stages

```bash
# Stage 1: Filter trending models from target labs
python -m agents.benchmark_intelligence.main filter_models
# or: /benchmark_intelligence.filter_models

# Stage 2: Find documentation URLs for models
python -m agents.benchmark_intelligence.main find_docs
# or: /benchmark_intelligence.find_docs

# Stage 3: Parse documents and extract benchmarks (with concurrency)
python -m agents.benchmark_intelligence.main parse_docs --concurrency 20
# or: /benchmark_intelligence.parse_docs --concurrency 30

# Stage 4: Consolidate and deduplicate benchmark names
python -m agents.benchmark_intelligence.main consolidate_benchmarks
# or: /benchmark_intelligence.consolidate_benchmarks --from-db

# Stage 5: Categorize benchmarks using AI
python -m agents.benchmark_intelligence.main categorize_benchmarks
# or: /benchmark_intelligence.categorize_benchmarks

# Stage 6: Generate comprehensive reports
python -m agents.benchmark_intelligence.main report
# or: /benchmark_intelligence.report
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

All configuration is in `config.yaml` at the repository root.

### Labs to Track

```yaml
labs:
  - Qwen
  - meta-llama
  - mistralai
  - google
  - microsoft
  - anthropic
  - deepseek-ai
  # ... add more as needed
```

### Discovery Settings

```yaml
discovery:
  models_per_lab: 15           # Models to fetch per lab
  sort_by: "downloads"         # downloads | trending | lastModified
  filter_tags: []              # Task filters (empty = all)
  min_downloads: 1000          # Minimum popularity
  date_filter_months: 12       # Temporal window (12 months)
  exclude_tags:                # Skip irrelevant models
    - "time-series-forecasting"
    - "fill-mask"
    - "token-classification"
```

### PDF Parsing Constraints

```yaml
pdf_constraints:
  max_file_size_mb: 10
  download_timeout_seconds: 120
  max_extracted_chars: 50000
```

### Retry Policy

```yaml
retry_policy:
  max_attempts: 3
  initial_delay_seconds: 1
  backoff_multiplier: 2
  max_delay_seconds: 60
```

### Temporal Tracking

```yaml
temporal_tracking:
  timeframe_months: 12         # 12-month rolling window
```

### Parallelization (Concurrency)

```yaml
parallelization:
  max_concurrent_document_fetches: 5
  enabled: true
  timeout_per_document_seconds: 60
```

**Override via command line**:
```bash
python -m agents.benchmark_intelligence.main parse_docs --concurrency 30
```

### Benchmark Consolidation

```yaml
consolidation:
  fuzzy_match_threshold: 0.90  # 90% similarity for matching
  enable_web_search: true      # Use web search for disambiguation
  web_search_max_results: 3    # Results to analyze
```

### Taxonomy (Category Overrides)

```yaml
taxonomy:
  category_overrides:
    "MMLU": "Knowledge & General Understanding"
    "GSM8K": "Mathematical Reasoning"
    # Manual overrides take precedence over AI classification
```

### Rate Limiting (NEW - Prevents 429 Errors)

```yaml
rate_limiting:
  huggingface:
    requests_per_minute: 60
    max_retries: 5
    initial_backoff_seconds: 2.0
    max_backoff_seconds: 60.0
    backoff_multiplier: 2.0

  anthropic:
    requests_per_minute: 50
    max_retries: 5
    initial_backoff_seconds: 2.0
    max_backoff_seconds: 120.0
    backoff_multiplier: 2.0

  arxiv:
    requests_per_minute: 30
    max_retries: 3
    initial_backoff_seconds: 1.0
    max_backoff_seconds: 30.0
    backoff_multiplier: 2.0
```

**Features**:
- **Token bucket algorithm**: Smooth rate limiting
- **Automatic retry**: Exponential backoff on 429 errors
- **Per-API limits**: Customized for each service

### Environment Variables

```bash
# HuggingFace token (required)
export HF_TOKEN="hf_your_token_here"

# Anthropic API key (required outside Ambient)
export ANTHROPIC_API_KEY="your-key-here"
```

On **Ambient Code Platform**: Claude is natively available, no `ANTHROPIC_API_KEY` needed!

## Pipeline Stages

The benchmark intelligence system consists of 6 sequential stages:

### Stage 1: Filter Models (`filter_models`)

**Purpose**: Discover and filter trending models from target labs

**What it does**:
- Fetches models from HuggingFace API for configured labs
- Filters by downloads, recency (12-month window), and tags
- Excludes irrelevant model types (time-series, fill-mask, etc.)
- Outputs: `outputs/filtered_models/models_YYYYMMDD_HHMMSS.json`

**Configuration**: `config.yaml` → `labs`, `discovery`, `temporal_tracking`

**Example output**:
```json
[
  {
    "id": "Qwen/Qwen2.5-72B",
    "author": "Qwen",
    "downloads": 1500000,
    "likes": 450,
    "tags": ["text-generation", "conversational"],
    "created_at": "2024-09-15T10:30:00Z"
  }
]
```

### Stage 2: Find Documentation (`find_docs`)

**Purpose**: Locate documentation sources for each model

**What it does**:
- Searches for model cards, blogs, papers, and GitHub repos
- Identifies arXiv papers, HuggingFace model cards, and external links
- Validates document availability
- Outputs: `outputs/docs/docs_YYYYMMDD_HHMMSS.json`

**Sources checked**:
- HuggingFace model card
- arXiv papers (linked in model card)
- Blog posts and technical reports
- GitHub repositories

**Example output**:
```json
[
  {
    "model_id": "Qwen/Qwen2.5-72B",
    "documents": [
      {
        "type": "model_card",
        "url": "https://huggingface.co/Qwen/Qwen2.5-72B",
        "found": true
      },
      {
        "type": "arxiv",
        "url": "https://arxiv.org/abs/2409.12345",
        "found": true
      }
    ]
  }
]
```

### Stage 3: Parse Documents (`parse_docs`)

**Purpose**: Extract benchmark results from documents using AI

**What it does**:
- **Concurrent processing**: 20+ workers (configurable via `--concurrency`)
- Downloads and parses PDFs, model cards, and web pages
- Uses Claude AI to extract benchmark names, scores, and metrics
- **Hash-based caching**: Skips re-processing unchanged documents
- **Rate limiting**: Prevents API 429 errors with automatic backoff
- Outputs: `outputs/parsed/parsed_YYYYMMDD_HHMMSS.json`

**Configuration**: 
- `--concurrency N`: Number of concurrent workers (default: 20)
- `config.yaml` → `parallelization`, `rate_limiting`, `pdf_constraints`

**Example output**:
```json
[
  {
    "model_id": "Qwen/Qwen2.5-72B",
    "benchmarks": [
      {
        "name": "MMLU",
        "score": 86.5,
        "metric": "accuracy",
        "source": "model_card"
      },
      {
        "name": "GSM8K",
        "score": 91.2,
        "metric": "accuracy",
        "source": "arxiv"
      }
    ],
    "documents_processed": 2,
    "extraction_timestamp": "2024-01-01T12:00:00Z"
  }
]
```

**Performance**:
- **Concurrency**: 20-50 workers recommended
- **Rate limiting**: Automatic retry with exponential backoff
- **Resumability**: Hash cache enables resuming after interruption

### Stage 4: Consolidate Benchmarks (`consolidate_benchmarks`)

**Purpose**: Deduplicate and normalize benchmark names

**What it does**:
- Fuzzy matching to identify variants (e.g., "MMLU" = "mmlu" = "MMLU 5-shot")
- Groups similar benchmarks using 90% similarity threshold
- Optional web search for disambiguation (configurable)
- Outputs: `outputs/consolidated/benchmarks_YYYYMMDD_HHMMSS.json`

**Configuration**: `config.yaml` → `consolidation`

**Flags**:
- `--from-db`: Load from database instead of JSON files

**Example output**:
```json
[
  {
    "canonical_name": "MMLU",
    "variants": ["MMLU", "mmlu", "MMLU 5-shot", "MMLU-Pro"],
    "occurrences": 25,
    "models": [
      {"model_id": "Qwen/Qwen2.5-72B", "score": 86.5, "metric": "accuracy"},
      {"model_id": "meta-llama/Llama-3-70B", "score": 82.0, "metric": "accuracy"}
    ]
  }
]
```

### Stage 5: Categorize Benchmarks (`categorize_benchmarks`)

**Purpose**: Classify benchmarks into taxonomic categories

**What it does**:
- Uses Claude AI for multi-label classification
- Assigns primary category, subcategory, and confidence score
- References `categories.yaml` for taxonomy
- Outputs: `outputs/categorized/categorized_YYYYMMDD_HHMMSS.json`

**Categories** (13):
- Knowledge & General Understanding
- Mathematical Reasoning
- Code Generation & Understanding
- Vision & Multimodal Understanding
- Reasoning & Logic
- Multilingual Capabilities
- Safety & Alignment
- Long-Context Understanding
- Instruction Following
- Tool Use & Function Calling
- Agent Capabilities
- Domain-Specific Expertise
- Audio & Speech Processing

**Example output**:
```json
[
  {
    "benchmark_name": "MMLU",
    "category": "Knowledge & General Understanding",
    "subcategory": "Multidomain",
    "confidence": 0.98,
    "reasoning": "Tests broad knowledge across 57 subjects"
  }
]
```

### Stage 6: Generate Report (`report`)

**Purpose**: Create comprehensive markdown reports

**What it does**:
- Aggregates data from all previous stages
- Generates temporal trend analysis (12-month window)
- Identifies emerging benchmarks (<6 months old, high usage)
- Detects extinct benchmarks (usage decline >80%)
- Creates visualizations and statistics
- Outputs: `outputs/reports/report_YYYYMMDD_HHMMSS.md`

**Report sections**:
1. Executive Summary
2. Trending Models
3. Most Common Benchmarks
4. Emerging Benchmarks
5. Category Distribution
6. Lab Insights
7. Temporal Trends

### Execution Modes

**Mode 1: Full Pipeline** (`generate`)
Runs all 6 stages sequentially. Recommended for monthly production runs.

**Mode 2: Individual Stages**
Run specific stages for development, debugging, or selective updates.
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
