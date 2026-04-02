# Benchmark Intelligence System - Technical Specifications

**Version:** 1.0
**Last Updated:** 2026-04-02
**Status:** Draft for Review

---

## 1. Project Overview

### 1.1 Purpose
Automatically track, extract, and analyze benchmark evaluation trends across Large Language Models (LLMs), Vision-Language Models (VLMs), and Audio-Language Models from major AI research labs.

### 1.2 Goals
- **Comprehensive Coverage**: Track benchmarks from all major labs (Meta, Google, Anthropic, Mistral, Qwen, DeepSeek, etc.)
- **Multi-Source Intelligence**: Extract benchmark data from model cards, technical reports, research papers, and official blogs
- **Temporal Tracking**: Monitor evolution of benchmark usage over time (12+ month horizon)
- **Automated Reporting**: Generate actionable intelligence reports monthly
- **High Quality**: Filter noise, consolidate duplicates, provide accurate categorization

### 1.3 Success Criteria
- [ ] Discover 100+ relevant models per run from 15+ labs
- [ ] Extract benchmarks from ≥3 source types (model cards, papers, blogs)
- [ ] Identify 80+ unique benchmarks with proper categorization
- [ ] ≥90% accuracy in benchmark name consolidation (GSM8K = gsm8k = GSM-8K)
- [ ] Zero irrelevant models (no time-series, BERT variants, etc.)
- [ ] Reports generated in <90 minutes
- [ ] SQLite cache enables incremental updates (only process new/changed models)

---

## 2. Data Sources

### 2.1 Primary Sources (REQUIRED)

#### Model Cards (HuggingFace)
- **What**: Official model documentation on HuggingFace Hub
- **Format**: Markdown README files
- **Access**: HuggingFace Hub API + direct URL fetch
- **Priority**: HIGH - Most reliable source
- **Example**: `https://huggingface.co/Qwen/Qwen2.5-7B/raw/main/README.md`

#### Technical Reports (GitHub)
- **What**: Repository README files, documentation
- **Format**: Markdown, GitHub-hosted content
- **Access**: GitHub raw content URLs
- **Priority**: HIGH - Often contains detailed benchmark tables
- **Example**: `https://raw.githubusercontent.com/QwenLM/Qwen2.5-7B/main/README.md`

#### Research Papers (arXiv, etc.)
- **What**: Academic papers introducing models
- **Format**: PDF/HTML from arXiv, ACL, NeurIPS, etc.
- **Access**: arXiv API, paper PDF extraction
- **Priority**: MEDIUM - Rich but harder to parse
- **Example**: arXiv papers for Llama 3, Qwen 2.5, etc.

#### Official Blogs
- **What**: Announcement posts from labs
- **Format**: HTML blog posts
- **Access**: Web scraping from known lab domains
- **Priority**: MEDIUM - Often has curated benchmark highlights
- **Examples**:
  - Meta AI Blog: `https://ai.meta.com/blog/`
  - Anthropic: `https://www.anthropic.com/news/`
  - Qwen: `https://qwenlm.github.io/blog/`

### 2.2 Secondary Sources (OPTIONAL)

#### Official Documentation Sites
- Dedicated model documentation pages
- Technical specification sheets
- API documentation with benchmark claims

#### Model Leaderboards
- Open LLM Leaderboard (HuggingFace)
- Chatbot Arena (LMSYS)
- AlpacaEval leaderboard

### 2.3 Source Requirements

**For each source, the system MUST:**
1. Check content hash before processing (skip if unchanged)
2. Store source URL and fetch timestamp
3. Handle rate limits and retries
4. Extract clean text content (no HTML tags, minimal noise)
5. Limit content size to prevent overwhelming AI extraction (<50K chars)

---

## 3. Model Discovery

### 3.1 Discovery Criteria

**Labs to Track** (15 organizations):
- Qwen, MinimaxAI, 01-ai (Yi)
- meta-llama, mistralai, google
- microsoft, anthropic
- alibaba-pai, tencent, deepseek-ai
- OpenGVLab, THUDM, baichuan-inc, internlm

**Filters**:
- ✅ Task tags: `text-generation`, `image-text-to-text`, `text2text-generation`
- ✅ Date range: Last 12 months
- ✅ Minimum downloads: 10,000
- ❌ Exclude: `time-series-forecasting`, `fill-mask`, `token-classification`, `table-question-answering`

**Limits**:
- 15 models per lab (top by downloads)
- Expected total: 100-150 models per run

### 3.2 Model Metadata to Capture

For each model:
- `id`: Full identifier (e.g., "Qwen/Qwen2.5-7B")
- `lab`: Organization name
- `release_date`: Model release timestamp
- `downloads`: Download count
- `likes`: Like count
- `tags`: Pipeline tags (for filtering)
- `model_card_hash`: Content hash for change detection

---

## 4. Benchmark Extraction

### 4.1 What Constitutes a Benchmark?

A **benchmark** is a standardized evaluation dataset or task with:
- A clear name (e.g., "MMLU", "GSM8K", "HumanEval")
- A score/metric (accuracy, pass@1, F1, etc.)
- Optional context (shot count, subset, variant)

### 4.2 Extraction Method

**AI-Powered Parsing** using Claude:
- Parse markdown tables
- Extract from prose ("achieved 85.2% on MMLU")
- Handle multiple formats (tables, lists, inline mentions)
- Normalize names (case-insensitive, handle variants)

**Output Format**:
```json
{
  "benchmarks": [
    {
      "name": "MMLU",
      "score": 85.2,
      "metric": "accuracy",
      "context": {"shots": 5, "subset": "all"},
      "source": "model_card"
    }
  ]
}
```

### 4.3 Consolidation Rules

**Benchmark Name Variants** must be consolidated:
- Case variations: `MMLU` = `mmlu` = `Mmlu`
- Separator variations: `GSM8K` = `GSM-8K` = `gsm8k`
- Abbreviations: `MMLU-Pro` ≠ `MMLU` (different benchmarks)
- Subsets: Track separately (`MMLU-STEM` vs `MMLU`)

**Consolidation Method**:
1. Fuzzy string matching (Levenshtein distance)
2. AI-assisted grouping (Claude identifies variants)
3. Manual overrides in configuration

---

## 5. Benchmark Classification

### 5.1 Category Taxonomy (13 categories)

| Category | Description | Examples |
|----------|-------------|----------|
| **Knowledge** | Factual knowledge, Q&A | MMLU, TriviaQA, NaturalQuestions |
| **Reasoning** | Logic, common sense | ARC, HellaSwag, PIQA, BoolQ |
| **Math** | Mathematical problem solving | GSM8K, MATH, AIME, Gaokao |
| **Code** | Programming tasks | HumanEval, MBPP, SWE-bench, LiveCodeBench |
| **Vision** | Visual understanding | VQAv2, MMMU, DocVQA, AI2D |
| **Audio** | Speech/audio tasks | FLEURS, LibriSpeech |
| **Multilingual** | Non-English languages | MMMLU, C-Eval, CMMLU, FLORES |
| **Safety** | Toxicity, bias, jailbreaks | TruthfulQA, RewardBench |
| **Long-Context** | Extended context handling | LongBench, RULER, InfiniteBench |
| **Instruction-Following** | Adherence to instructions | IFEval, AlpacaEval |
| **Tool-Use** | API calling, tool integration | ToolBench, API-Bank |
| **Agent** | Multi-step reasoning, planning | AgentBench, WebArena |
| **Domain-Specific** | Medical, legal, finance | MedQA, LegalBench, FinQA |

### 5.2 Classification Rules

- **Multi-label**: Benchmarks can have multiple categories (e.g., MMMU = Knowledge + Vision + Reasoning)
- **AI-Assisted**: Claude classifies based on description and name
- **Confidence threshold**: Minimum 0.6 confidence for assignment
- **Human override**: Allow manual corrections in config

### 5.3 Additional Attributes

Beyond categories, track:
- **Difficulty**: Easy, Medium, Hard, Expert
- **Modality**: Text, Vision, Audio, Multimodal
- **Language**: English, Chinese, Multilingual
- **Format**: Multiple choice, Free-form, Code generation
- **Domain**: General, Academic, Professional

---

## 6. Caching & Persistence

### 6.1 Database Schema (SQLite)

```sql
-- Models table
CREATE TABLE models (
    id TEXT PRIMARY KEY,              -- e.g., "Qwen/Qwen2.5-7B"
    name TEXT NOT NULL,
    lab TEXT,
    release_date TEXT,
    first_seen TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    downloads INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    tags TEXT,                        -- JSON array
    model_card_hash TEXT              -- SHA256 of model card
);

-- Benchmarks table
CREATE TABLE benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE NOT NULL,
    categories TEXT,                   -- JSON array
    attributes TEXT,                   -- JSON object
    first_seen TEXT NOT NULL
);

-- Model-Benchmark associations
CREATE TABLE model_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    benchmark_id INTEGER NOT NULL,
    score REAL,
    context TEXT,                      -- JSON: {shots, subset, etc.}
    source_url TEXT,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id),
    UNIQUE(model_id, benchmark_id, context)
);

-- Documents cache
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,            -- model_card, blog, paper, etc.
    url TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content TEXT,
    last_fetched TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES models(id),
    UNIQUE(model_id, doc_type, url)
);

-- Temporal snapshots
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    model_count INTEGER NOT NULL,
    benchmark_count INTEGER NOT NULL,
    summary TEXT                       -- JSON stats
);
```

### 6.2 Incremental Update Logic

**On each run:**
1. Check if model exists in cache
2. If exists:
   - Compare `model_card_hash` with current
   - If unchanged: Skip processing
   - If changed: Re-extract and update
3. If new model: Full processing

**For documents:**
- Check `content_hash` before re-fetching
- Update `last_fetched` timestamp
- Re-extract only if content changed

---

## 7. Reporting Requirements

### 7.1 Report Sections (7 required)

#### 1. Executive Summary
- Total models tracked
- Total unique benchmarks
- Number of labs
- Time period covered
- Key highlights

#### 2. Trending Models (Last 12 Months)
- **ALL models**, not limited to top 20
- Sorted by: Downloads (desc), then release date (desc)
- Columns: Model, Lab, Downloads, Likes, Release Date
- Show models that meet quality filters only

#### 3. Most Common Benchmarks
- Top benchmarks by usage (how many models report them)
- Show: All-time top 20 + This period's top 20
- Include: Name, Model count, Categories, First seen

#### 4. Emerging Benchmarks
- New benchmarks discovered in last 90 days
- Sorted by first seen (newest first)
- Highlight: Potential new trends

#### 5. Category Distribution
- Pie chart / bar chart data (JSON)
- Percentage breakdown
- Trend over time (if multiple snapshots)

#### 6. Lab-Specific Insights
- Models per lab
- Average downloads/likes
- Preferred benchmarks per lab
- Benchmark diversity score

#### 7. Temporal Trends
- Benchmark popularity over time
- New vs deprecated benchmarks
- Snapshot comparison data

### 7.2 Report Format

- **Primary**: Markdown (auto-generated)
- **Filename**: `report_YYYYMMDD_HHMMSS.md`
- **Location**: `agents/benchmark_intelligence/reports/`
- **Linked from**: Root `README.md` (auto-updated)

### 7.3 Report Quality Standards

- ✅ All data must be sourced from cache (no hardcoded examples)
- ✅ Handle empty states gracefully (e.g., "No models discovered")
- ✅ Include generation timestamp and metadata
- ✅ Provide links to sources (HuggingFace, GitHub)
- ✅ Format numbers with K/M suffixes (13.9M, 516K)

---

## 8. Configuration

### 8.1 Configuration Files

**`categories.yaml`** (root):
- Benchmark category definitions
- Category descriptions
- Attribute taxonomies

**`benchmark_taxonomy.md`** (root):
- Reference list of 30+ known benchmarks
- Definitions and descriptions
- Normalization rules

**`labs.yaml`** (agents/.../config/):
- Target labs to track
- Discovery settings (models_per_lab, filters)
- Scheduling configuration

### 8.2 Key Configuration Parameters

```yaml
# labs.yaml
discovery:
  models_per_lab: 15               # Models to fetch per lab
  sort_by: "downloads"             # Sorting criterion
  filter_tags:                     # REQUIRED task types
    - "text-generation"
    - "image-text-to-text"
  exclude_tags:                    # EXCLUDED model types
    - "time-series-forecasting"
    - "fill-mask"
  min_downloads: 10000             # Popularity threshold
  date_filter_months: 12           # Historical window

documentation:
  fetch_enabled: true              # Enable multi-source fetching
  max_docs_per_model: 5            # Limit documents per model
  source_types:                    # Enabled source types
    - model_card
    - technical_report
    - blog_post
    - research_paper
  content_max_size: 50000          # Max chars per document

extraction:
  use_ai: true                     # AI-powered extraction (vs regex)
  consolidation_enabled: true      # Consolidate benchmark variants
  classification_enabled: true     # Classify benchmarks

reporting:
  include_all_models: true         # Show ALL models (not top N)
  timeframe_months: 12             # Report timeframe
  min_benchmark_usage: 2           # Min models to list benchmark
```

---

## 9. Architecture

### 9.1 System Components

```
┌─────────────────────────────────────────────────────────┐
│                  Benchmark Intelligence Agent            │
└─────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼──────┐   ┌────▼─────┐
    │ Discovery │   │ Extraction │   │ Reporting│
    └─────┬─────┘   └─────┬──────┘   └────┬─────┘
          │               │               │
    ┌─────▼──────────┐    │               │
    │ HuggingFace API│    │               │
    └────────────────┘    │               │
                     ┌────▼────────────┐  │
                     │ Document Fetch  │  │
                     │ - Model Cards   │  │
                     │ - GitHub README │  │
                     │ - arXiv Papers  │  │
                     │ - Blog Posts    │  │
                     └────┬────────────┘  │
                          │               │
                     ┌────▼────────┐      │
                     │ AI Extract  │      │
                     │ (Claude)    │      │
                     └────┬────────┘      │
                          │               │
                     ┌────▼────────┐      │
                     │Consolidate &│      │
                     │  Classify   │      │
                     └────┬────────┘      │
                          │               │
                     ┌────▼─────────────┐ │
                     │  SQLite Cache    │ │
                     │  - Models        │ │
                     │  - Benchmarks    │ │
                     │  - Documents     │ │
                     │  - Snapshots     │ │
                     └──────────────────┘ │
                                          │
                                    ┌─────▼──────┐
                                    │  Markdown  │
                                    │  Report    │
                                    └────────────┘
```

### 9.2 Execution Flow

```
1. Discovery Phase
   ├── Query HuggingFace API (15 labs × 15 models)
   ├── Apply filters (date, tags, downloads)
   └── Output: List of 100-150 models

2. Processing Phase (per model)
   ├── Check cache (skip if unchanged)
   ├── Parse model card
   ├── Fetch additional docs (GitHub, papers, blogs)
   ├── Extract benchmarks (AI-powered)
   ├── Aggregate results across sources
   └── Store in cache

3. Consolidation Phase
   ├── Collect all unique benchmark names
   ├── Group variants (fuzzy matching + AI)
   ├── Classify benchmarks (categories + attributes)
   └── Update benchmark metadata

4. Snapshot Phase
   ├── Create temporal snapshot
   └── Store summary statistics

5. Reporting Phase
   ├── Query cache for data
   ├── Generate 7 report sections
   ├── Write markdown file
   └── Update root README
```

---

## 10. Non-Functional Requirements

### 10.1 Performance

- **Execution time**: <90 minutes for 150 models (full run)
- **Incremental updates**: <15 minutes for changed models only
- **API rate limits**: Respect HuggingFace (no more than 10 req/sec)
- **Claude API usage**: <$2 per run (optimize prompt sizes)

### 10.2 Reliability

- **Error handling**: Graceful degradation (skip failed models, continue)
- **Retry logic**: 3 retries with exponential backoff for rate limits
- **Logging**: INFO level for progress, DEBUG for details
- **Crash recovery**: Resume from cache on restart

### 10.3 Maintainability

- **Modularity**: Separate tools for each function (discovery, extraction, etc.)
- **Configuration**: All parameters in YAML (no hardcoded values)
- **Documentation**: Inline comments + comprehensive README
- **Testing**: Unit tests for each tool module

### 10.4 Scalability

- **Cache-first**: Always check cache before processing
- **Batch processing**: Process models in batches of 10
- **Content limits**: Max 50K chars per document
- **Database optimization**: Indexed columns, efficient queries

---

## 11. Open Questions & Future Enhancements

### 11.1 Open Questions

1. **Paper Extraction**: How to effectively extract benchmarks from PDF research papers? (OCR, PDF parsing)
2. **Benchmark Scores**: Should we store actual scores, or just presence/absence?
3. **Multi-version Tracking**: How to handle model updates (v1.0 vs v1.5)?
4. **Benchmark Deprecation**: How to identify and mark deprecated benchmarks?
5. **Source Prioritization**: If benchmark X appears in model card AND paper with different scores, which to trust?

### 11.2 Future Enhancements

- [ ] **Web Dashboard**: Interactive visualization of trends
- [ ] **Benchmark Definitions**: Auto-fetch from Papers with Code
- [ ] **Model Comparison**: Side-by-side benchmark comparison tool
- [ ] **Alert System**: Notify when new benchmarks emerge
- [ ] **API Export**: REST API for querying cached data
- [ ] **Historical Analysis**: Trend prediction using ML
- [ ] **Paper Linking**: Auto-link to arXiv/ACL for each benchmark

---

## 12. Success Metrics

**After 3 monthly runs, the system should achieve:**

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Models discovered per run | 100+ | TBD | 🟡 |
| Unique benchmarks tracked | 80+ | TBD | 🟡 |
| Source types utilized | ≥3 | 2 | 🔴 |
| Model relevance (no noise) | 95%+ | TBD | 🟡 |
| Benchmark consolidation accuracy | 90%+ | TBD | 🟡 |
| Report generation time | <90 min | ~60 min | 🟢 |
| Cache hit rate (incremental) | 70%+ | TBD | 🟡 |
| Total cost per run | <$2 | ~$1 | 🟢 |

**Legend**: 🟢 Met | 🟡 In Progress | 🔴 Not Met

---

## 13. Acceptance Criteria

**The system is considered complete when:**

- ✅ All 7 report sections generate correctly
- ✅ Benchmarks extracted from ≥3 source types (model cards + GitHub + papers/blogs)
- ✅ Zero irrelevant models in output (no time-series, BERT variants)
- ✅ ALL discovered models shown in report (not limited to top 20)
- ✅ Incremental updates work (skip unchanged models)
- ✅ Categories and taxonomy files visible at root
- ✅ Root README links to latest report
- ✅ Documentation complete (README, this SPEC file, inline comments)
- ✅ Can run monthly on schedule (cron or manual trigger)

---

**Document Status**: Draft for Review
**Next Steps**: Review with stakeholders, iterate on requirements, finalize design
