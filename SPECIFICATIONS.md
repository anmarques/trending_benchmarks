# Benchmark Intelligence System - Technical Specifications

**Version:** 1.2
**Last Updated:** 2026-04-02
**Status:** Final

---

## 1. Project Overview

### 1.1 Purpose
Automatically track, extract, and analyze benchmark evaluation trends across Large Language Models (LLMs), Vision-Language Models (VLMs), and Audio-Language Models from major AI research labs.

### 1.2 Goals
- **Comprehensive Coverage**: Track benchmarks from all major AI labs and organizations
- **Multi-Source Intelligence**: Extract benchmark data from all available sources (model cards, technical reports, research papers, official blogs)
- **Temporal Tracking**: Monitor evolution of benchmark usage over 12 months
- **High Quality**: Filter noise, consolidate duplicates, provide accurate categorization
- **Adaptive Taxonomy**: Evolve benchmark categorization based on discovered benchmarks

### 1.3 Success Criteria
- ✅ All relevant models from configured labs are discovered and processed
- ✅ All available source documents are fetched and analyzed (model cards, GitHub READMEs, papers, blogs)
- ✅ All benchmarks mentioned in sources are extracted and classified
- ✅ Benchmark name consolidation handles common variants (case, separators)
- ✅ Zero irrelevant models (no time-series forecasting, fill-mask, token-classification models)
- ✅ Reports show ALL discovered models without arbitrary limits
- ✅ SQLite cache enables incremental updates (only process new/changed content)
- ✅ Taxonomy adapts to newly discovered benchmark types on every run
- ✅ Progress is reported to user as agent executes
- ✅ Historical taxonomy versions are preserved
- ✅ Trend tracking capped at 12 months

---

## 2. Data Sources

### 2.1 Source Types

#### Model Cards (HuggingFace)
- **What**: Official model documentation on HuggingFace Hub
- **Format**: Markdown README files
- **Access**: HuggingFace Hub API + direct URL fetch
- **Characteristics**: Easy to parse, may have limited benchmark details
- **Example**: `https://huggingface.co/Qwen/Qwen2.5-7B/raw/main/README.md`

#### Technical Reports (GitHub - Markdown)
- **What**: Repository README files, documentation
- **Format**: Markdown, GitHub-hosted content
- **Access**: GitHub raw content URLs
- **Characteristics**: Often contains detailed benchmark tables and methodology
- **Example**: `https://raw.githubusercontent.com/QwenLM/Qwen2.5/main/README.md`

#### Technical Reports (PDF)
- **What**: Detailed model documentation in PDF format
- **Format**: PDF (hosted on GitHub, arXiv, lab websites)
- **Access**: PDF download + parsing using PDF libraries
- **Characteristics**: Most comprehensive, requires PDF extraction
- **Examples**:
  - GitHub releases: `https://github.com/meta-llama/llama3/releases/download/v1.0/llama3_report.pdf`
  - arXiv papers: `https://arxiv.org/pdf/2407.21783` (Llama 3.1)

#### Research Papers (arXiv, Conferences)
- **What**: Academic papers introducing models
- **Format**: PDF from arXiv, ACL, NeurIPS, ICML, etc.
- **Access**: arXiv API + PDF parsing, conference proceedings
- **Characteristics**: Rich evaluation details, standardized format
- **Examples**:
  - arXiv: `https://arxiv.org/abs/2407.21783`
  - ACL Anthology: Papers from major NLP conferences

#### Official Blogs & Announcements
- **What**: Announcement posts from labs
- **Format**: HTML blog posts
- **Access**: Web scraping from lab domains
- **Characteristics**: Often highlights key benchmarks, curated results
- **Examples**:
  - Meta AI: `https://ai.meta.com/blog/`
  - Anthropic: `https://www.anthropic.com/news/`
  - Qwen: `https://qwenlm.github.io/blog/`
  - DeepSeek: `https://www.deepseek.com/`

### 2.2 Source Discovery Strategy

For each model, the system should:

1. **Model Card**: Always fetch from HuggingFace (primary metadata source)
2. **GitHub README**: Construct URL based on lab → GitHub org mapping
3. **GitHub PDFs**: Search releases and docs folders for technical reports
4. **arXiv Papers**: Search using model name + lab name
5. **Official Blogs**: Search known blog domains for model announcements

### 2.3 Source Processing Requirements

**For each source, the system MUST:**
1. ✅ Check content hash before processing (skip if unchanged)
2. ✅ Store source URL, type, and fetch timestamp
3. ✅ Handle rate limits and retries (3 attempts with exponential backoff)
4. ✅ Extract clean text content:
   - **Markdown**: Parse directly
   - **HTML**: Strip tags, extract main content
   - **PDF**: Use PDF parser libraries (PyPDF2, pdfplumber, or similar)
   - **Unreadable content**: Ignore PDFs that cannot be parsed or are image-only without text layer
5. ✅ Limit content size to prevent overwhelming AI (<50K chars per source)
6. ✅ Log failed fetches but continue processing other sources

**Note**: If a source document is not found (e.g., no arXiv paper exists) or cannot be read, this is NOT a failure. The system should search all potential sources but gracefully handle missing or unreadable ones.

---

## 3. Model Discovery

### 3.1 Discovery Configuration

**Labs to track** are configured in: **`labs.yaml`** (at project root)

Example structure:
```yaml
labs:
  - Qwen
  - meta-llama
  - mistralai
  - google
  # ... etc

discovery:
  models_per_lab: 15
  sort_by: "downloads"
  filter_tags:
    - "text-generation"
    - "image-text-to-text"
    - "text2text-generation"
  exclude_tags:
    - "time-series-forecasting"
    - "fill-mask"
    - "token-classification"
    - "table-question-answering"
  min_downloads: 10000
  date_filter_months: 12
```

### 3.2 Discovery Filters

**Include models that**:
- ✅ Have task tags: `text-generation`, `image-text-to-text`, `text2text-generation`
- ✅ Released in last 12 months
- ✅ Have ≥10,000 downloads (popularity threshold)

**Exclude models that**:
- ❌ Have tags: `time-series-forecasting`, `fill-mask`, `token-classification`, `table-question-answering`, `zero-shot-classification`

### 3.3 Model Metadata to Capture

For each model:
- `id`: Full identifier (e.g., "Qwen/Qwen2.5-7B")
- `lab`: Organization name
- `release_date`: Model release timestamp
- `downloads`: Download count (update on each run)
- `likes`: Like count (update on each run)
- `tags`: Pipeline tags (for filtering)

**Update Strategy**:
- **New models**: Full processing (fetch all sources, extract benchmarks)
- **Cached models**:
  - Update metadata (downloads, likes) from HuggingFace API
  - Check content hash for each source document
  - Only re-process documents with changed content
  - Do NOT re-extract benchmarks if no sources changed

---

## 4. Benchmark Extraction

### 4.1 What Constitutes a Benchmark?

A **benchmark** is a standardized evaluation dataset or task with a clear name mentioned in model documentation.

**Examples**:
- MMLU, GSM8K, HumanEval (standard names)
- MMLU-Pro, GSM8K-Hard (variants)
- C-Eval, CMMLU (language-specific)

**What to extract**:
- ✅ Benchmark name
- ✅ Presence (yes/no - model was evaluated on it)
- ❌ **Do NOT extract scores** (too variable, context-dependent)

### 4.2 Extraction Method

**AI-Powered Parsing** using Claude:
- Parse markdown tables
- Extract from prose ("evaluated on MMLU")
- Handle multiple formats (tables, lists, inline mentions)
- Normalize names (case-insensitive, handle variants)

**Output Format**:
```json
{
  "benchmarks": [
    {
      "name": "MMLU",
      "source": "model_card"
    },
    {
      "name": "GSM8K",
      "source": "technical_report"
    }
  ]
}
```

### 4.3 Consolidation Rules

**Benchmark Name Variants** must be consolidated:
- ✅ Case variations: `MMLU` = `mmlu` = `Mmlu`
- ✅ Separator variations: `GSM8K` = `GSM-8K` = `gsm8k`
- ❌ Different benchmarks: `MMLU-Pro` ≠ `MMLU`
- ❌ Subsets: Track separately (`MMLU-STEM` vs `MMLU`)

**Benchmark Disambiguation**:
- If benchmarks are routinely reported side-by-side with different names (e.g., both "MMLU" and "MMLU-Pro" in same model card), they are distinct benchmarks
- When in doubt, treat as separate unless consolidation rules clearly indicate they are variants

**Consolidation Method**:
1. Fuzzy string matching (Levenshtein distance < 0.2)
2. AI-assisted grouping (Claude identifies variants)
3. When same benchmark appears with different names across sources, adopt the most common nomenclature
4. Store consolidated name in database

---

## 5. Benchmark Classification & Adaptive Taxonomy

### 5.1 Taxonomy Evolution

**On each run, the agent must**:

1. **Classify all benchmarks** using Claude AI based on benchmark names and descriptions
2. **Identify gaps**: If many benchmarks don't fit existing categories, propose new ones
3. **Update taxonomy**:
   - Add new categories if discovered (e.g., "Robotics", "Scientific Reasoning")
   - Store updated taxonomy at root: `benchmark_taxonomy.md`
   - Archive previous taxonomy: `benchmark_taxonomy_YYYYMMDD.md`
4. **Report changes**: Note in report if taxonomy was updated

**Classification Rules**:
- Multi-label: Benchmarks can have multiple categories
- AI-assisted: Claude classifies based on description
- Confidence threshold: Minimum 0.6 confidence for assignment
- Manual override: Users can edit `categories.yaml` at root

### 5.2 Taxonomy Storage

```
/benchmark_taxonomy.md               # Current taxonomy (auto-updated)
/archive/
  /benchmark_taxonomy_20260402.md    # Historical versions
  /benchmark_taxonomy_20260501.md
  ...
```

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
    downloads INTEGER DEFAULT 0,      -- Updated each run
    likes INTEGER DEFAULT 0,          -- Updated each run
    tags TEXT                         -- JSON array
);

-- Benchmarks table
CREATE TABLE benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE NOT NULL,
    categories TEXT,                   -- JSON array
    attributes TEXT,                   -- JSON object
    first_seen TEXT NOT NULL,
    last_seen TEXT                     -- Track when last mentioned
);

-- Model-Benchmark associations (no scores)
CREATE TABLE model_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    benchmark_id INTEGER NOT NULL,
    source_type TEXT,                  -- model_card, blog, paper, etc.
    source_url TEXT,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id),
    UNIQUE(model_id, benchmark_id)
);

-- Documents cache
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,            -- model_card, blog, paper, etc.
    url TEXT NOT NULL,
    content_hash TEXT NOT NULL,        -- SHA256 for change detection
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
    taxonomy_version TEXT,             -- Link to archived taxonomy
    summary TEXT                       -- JSON stats
);
```

### 6.2 Incremental Update Logic

**On each run:**
1. Update model metadata (downloads, likes) for ALL models
2. For each model:
   - Check if documents exist in cache
   - For each document:
     - Fetch current version
     - Compare `content_hash`
     - If **unchanged**: Skip processing
     - If **changed**: Re-extract benchmarks from this document
3. Only models with changed documents trigger benchmark re-extraction

**Benefits**:
- Faster incremental runs (skip unchanged content)
- Always have latest popularity data (downloads, likes)
- Detect when labs update their documentation

---

## 7. Reporting Requirements

### 7.1 Report Sections (7 Required)

#### 1. Executive Summary
- Total models tracked
- Total unique benchmarks discovered
- Number of active labs
- Time period covered (12 months)
- Number of source documents processed
- Key highlights

#### 2. Trending Models (Last 12 Months)
- **Show ALL models** that meet quality criteria
- Sorted by: Downloads (desc), then release date (desc)
- Columns: Model, Lab, Downloads, Likes, Release Date
- No arbitrary limits (e.g., "top 20") - show everything

#### 3. Most Common Benchmarks
- Benchmarks sorted by usage (how many models report them)
- Show: All-time top benchmarks + This period's top benchmarks
- Include: Name, Model count, Categories, First seen
- No minimum threshold - include all discovered benchmarks

#### 4. Emerging Benchmarks
- New benchmarks discovered in last 90 days
- Sorted by first seen (newest first)
- Highlight potential new evaluation trends
- Note if any benchmarks are explicitly deprecated

#### 5. Category Distribution
- Pie chart / bar chart data (JSON format)
- Percentage breakdown by category
- Trend over time (if multiple snapshots exist)
- Note if taxonomy was updated this run

#### 6. Lab-Specific Insights
- Models per lab
- Average downloads/likes per lab
- Preferred benchmarks per lab (top 5)
- Benchmark diversity score (unique benchmarks used)

#### 7. Temporal Trends
- Benchmark popularity over time
- New vs. deprecated benchmarks
- Snapshot comparison data
- Note on benchmarks trending down (potential deprecation)

### 7.2 Deprecated Benchmarks

- **Natural trend**: Benchmarks will naturally trend down in usage
- **Explicit deprecation**: If a source explicitly says "benchmark X is deprecated", note this in the report
- **Detection**: Track `last_seen` date in database
- **Reporting**: In "Temporal Trends" section, list benchmarks not seen in last 6 months as "Potentially Deprecated"

### 7.3 Report Format

- **Primary**: Markdown (auto-generated)
- **Filename**: `report_YYYYMMDD_HHMMSS.md`
- **Location**: `agents/benchmark_intelligence/reports/`
- **Linked from**: Root `README.md` (auto-updated with latest link)

### 7.4 Report Quality Standards

- ✅ All data sourced from cache (no hardcoded examples)
- ✅ Handle empty states gracefully (e.g., "No new benchmarks discovered")
- ✅ Include generation timestamp and metadata
- ✅ Provide links to sources (HuggingFace, GitHub, arXiv)
- ✅ Format numbers with K/M suffixes (13.9M, 516K)
- ✅ Note taxonomy updates if any

---

## 8. Progress Reporting

### 8.1 Requirements

The agent MUST report short progress summaries as it executes:

**During Discovery**:
```
[Discovery] Querying 15 labs...
[Discovery] Found 127 models from Qwen, meta-llama, mistralai, ...
[Discovery] Applied filters: 89 models passed (38 excluded)
```

**During Processing**:
```
[Processing] Model 1/89: Qwen/Qwen2.5-7B
  ✓ Fetched model card
  ✓ Fetched GitHub README
  ✓ Found arXiv paper
  ✓ Extracted 15 benchmarks
[Processing] Model 2/89: meta-llama/Llama-3.1-8B
  ✓ Cached (no changes)
  ↻ Updated metadata (downloads: 15.2M → 15.4M)
```

**During Consolidation**:
```
[Consolidation] Found 87 unique benchmark names
[Consolidation] Consolidated to 72 canonical names
[Classification] Classified 72 benchmarks across 13 categories
```

**During Reporting**:
```
[Reporting] Generating 7 sections...
[Reporting] ✓ Report saved: reports/report_20260402_163045.md
[Reporting] ✓ Updated root README.md
```

### 8.2 Implementation

- Use logging at INFO level
- Print to console/stdout
- Include progress counters (X/Y)
- Show status symbols: ✓ (success), ✗ (error), ↻ (cached), ⊕ (new)

---

## 9. Configuration Files

### 9.1 Root-Level Configuration

All configuration files should be at project root for easy access:

**`labs.yaml`** (project root):
```yaml
labs:
  - Qwen
  - meta-llama
  - mistralai
  # ...

discovery:
  models_per_lab: 15
  sort_by: "downloads"
  filter_tags: ["text-generation", "image-text-to-text"]
  exclude_tags: ["time-series-forecasting", "fill-mask"]
  min_downloads: 10000
  date_filter_months: 12

documentation:
  fetch_enabled: true
  max_docs_per_model: 10
  content_max_size: 50000

extraction:
  use_ai: true
  consolidation_enabled: true
  classification_enabled: true

reporting:
  timeframe_months: 12
```

**`categories.yaml`** (project root):
- Category definitions
- Attributes and descriptions
- User can manually add categories here

**`benchmark_taxonomy.md`** (project root):
- Auto-generated, updated each run
- Current taxonomy with examples
- Links to archived versions

**Archive folder** (`/archive/`):
- Historical taxonomy versions
- Previous reports (optional backup)

---

## 10. Architecture

### 10.1 Execution Flow

```
1. Discovery Phase
   ├── Load configuration from labs.yaml
   ├── Query HuggingFace API (configured labs)
   ├── Apply filters (date, tags, downloads)
   ├── Report: "Found X models"
   └── Output: List of models to process

2. Processing Phase (per model)
   ├── Update metadata (downloads, likes)
   ├── Fetch all source documents:
   │   ├── Model card (HuggingFace)
   │   ├── GitHub README (Markdown)
   │   ├── GitHub PDFs (if exist)
   │   ├── arXiv papers (if exist)
   │   └── Blog posts (if exist)
   ├── Check content hash for each source
   ├── If changed: Extract benchmarks (AI)
   ├── If unchanged: Skip extraction
   ├── Report progress: "Model X/Y: status"
   └── Store in cache

3. Consolidation Phase
   ├── Collect all unique benchmark names
   ├── Group variants (fuzzy + AI)
   ├── Classify benchmarks (AI)
   ├── Update taxonomy if needed
   ├── Report: "Consolidated X to Y names"
   └── Store canonical benchmarks

4. Snapshot Phase
   ├── Create temporal snapshot
   ├── Store current taxonomy version
   └── Archive old taxonomy if updated

5. Reporting Phase
   ├── Query cache for data
   ├── Generate 7 report sections
   ├── Note taxonomy updates
   ├── Write markdown file
   ├── Update root README
   └── Report: "Report saved at X"
```

### 10.2 PDF Parsing

**Use proper PDF parsing libraries**:
- `PyPDF2` for basic text extraction
- `pdfplumber` for tables and structured data
- `pdfminer.six` for complex layouts
- OCR (`pytesseract`) only as fallback for image-based PDFs

**Extraction strategy**:
1. Download PDF
2. Extract all text using parser
3. Clean and normalize text
4. Limit to 50K chars (truncate if needed)
5. Pass to AI for benchmark extraction

---

## 11. Web Dashboard

### 11.1 Purpose
Interactive visualization of benchmark trends and model intelligence.

### 11.2 Features

**Core Views**:
- **Benchmark Explorer**: Filter/search all benchmarks, see usage trends
- **Model Comparison**: Side-by-side benchmark comparison for selected models
- **Lab Analytics**: Per-lab statistics and benchmark preferences
- **Temporal Trends**: Interactive charts showing benchmark evolution
- **Taxonomy Browser**: Explore benchmark categories, see examples

**Interactivity**:
- Filter by: Lab, Category, Date range, Benchmark
- Sort tables by any column
- Export data (CSV, JSON)
- Link to original sources (HuggingFace, GitHub, arXiv)

**Technology Stack** (suggested):
- Frontend: React + D3.js (charts)
- Backend: FastAPI (serves data from SQLite)
- Deployment: Static site generation for GitHub Pages

### 11.3 Data Access

Dashboard reads directly from SQLite database:
- No real-time updates (uses cached data)
- Regenerate dashboard after each agent run
- Static HTML/JS hosted on GitHub Pages

---

## 12. Non-Functional Requirements

### 12.1 Reliability

- **Error handling**: Graceful degradation (skip failed models, continue processing)
- **Retry logic**: 3 retries with exponential backoff for rate limits
- **Logging**: INFO level for progress, DEBUG for details, ERROR for failures
- **Crash recovery**: Resume from cache on restart

### 12.2 Maintainability

- **Modularity**: Separate tools for each function (discovery, extraction, etc.)
- **Configuration**: All parameters in YAML at root level
- **Documentation**: Inline comments + comprehensive README + this SPEC
- **Testing**: Unit tests for each tool module

### 12.3 Scalability

- **Cache-first**: Always check cache before processing
- **Incremental**: Only process changed content
- **Content limits**: Max 50K chars per document
- **Database optimization**: Indexed columns, efficient queries
- **Batch processing**: Process documents in parallel where possible

---

## 13. Acceptance Criteria

**The system is considered complete when:**

- ✅ All configured labs are queried and relevant models discovered
- ✅ All available source documents are fetched (model cards, GitHub, PDFs, blogs)
- ✅ All benchmarks mentioned in sources are extracted and stored
- ✅ Benchmark names are consolidated (variants grouped)
- ✅ Benchmarks are classified using adaptive taxonomy
- ✅ Zero irrelevant models in output (proper filtering applied)
- ✅ Reports show ALL discovered models (no arbitrary limits)
- ✅ Progress is reported to user during execution
- ✅ Incremental updates work (skip unchanged documents)
- ✅ Taxonomy updated when new benchmark types discovered
- ✅ Historical taxonomy versions archived
- ✅ Configuration files at root level (labs.yaml, categories.yaml, benchmark_taxonomy.md)
- ✅ Root README links to latest report
- ✅ Documentation complete (README, SPEC, inline comments)
- ✅ PDF parsing works for technical reports

---

**Document Status**: Updated based on stakeholder feedback
**Next Steps**: Implement based on finalized specifications
