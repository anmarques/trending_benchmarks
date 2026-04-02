# Benchmark Intelligence System - Technical Specifications

**Version:** 1.3
**Last Updated:** 2026-04-02
**Status:** Final - Updated web fetching strategy

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

For each model, the system must discover all documentation sources using a multi-tiered approach:

1. **Model Card**: Always fetch from HuggingFace (primary metadata source)
2. **arXiv Papers**:
   - First, check model card for arxiv.org URLs → use directly if found (use only that paper)
   - If not found → use lab→GitHub mapping and known URL patterns
   - If still not found → fallback to MCP webfetch with known URLs
   - If multiple papers found, select paper with authors from the lab that released the model
   - Process max 1 arXiv paper per model
3. **GitHub Technical Reports**:
   - Use lab→GitHub org mapping from `labs.yaml` (e.g., Qwen → QwenLM)
   - Try known URL patterns: `https://github.com/{org}/{model}/README.md`
   - Check releases folder: `https://github.com/{org}/{model}/releases/`
   - If not found → fallback to direct URL fetch if available
4. **Official Blogs**:
   - Use known blog URL patterns per lab (e.g., Qwen → qwenlm.github.io)
   - Fetch directly using MCP webfetch tool
   - Parse HTML to extract main content

**Web Fetching Strategy:**
The system uses the **MCP webfetch tool** (`mcp__webfetch__fetch`) for fetching web content:

- **Primary Method**: MCP webfetch (works reliably, no blocking issues)
- **Advantages**:
  - Handles JavaScript-rendered pages
  - No rate limiting concerns
  - Direct content extraction
  - Supports markdown conversion
- **Implementation**:
  ```python
  from mcp__webfetch__fetch import fetch

  content = fetch(
      url="https://qwenlm.github.io/blog/qwen2.5/",
      max_length=50000  # Adjust based on content size
  )
  ```

**Lab→GitHub Organization Mapping:**
Configuration in `labs.yaml`:
```yaml
lab_github_mappings:
  Qwen: QwenLM
  meta-llama: meta-llama
  mistralai: mistralai
  google: google
  microsoft: microsoft
  deepseek-ai: deepseek-ai
  internlm: InternLM
  # ... etc
```

**Google Search Fallback (Optional):**
Google search scraping is implemented but often blocked. Use as last resort:
- Configuration kept for backwards compatibility
- Implements retry with exponential backoff
- Falls back to "skip" strategy if blocked after 3 attempts
- Configuration:
  ```yaml
  google_search:
    max_results_per_query: 10
    delay_between_searches: 2  # seconds
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    max_retries_on_block: 3
    fallback_strategy: "skip"  # Skip if blocked after retries
  ```

### 2.3 Source Processing Requirements

**For each source, the system MUST:**

1. ✅ Fetch document from URL
2. ✅ Extract text content:
   - **Markdown**: Parse directly
   - **HTML**: Strip tags, extract main content
   - **PDF**: Extract text + tables using pdfplumber (see section 10.2 for details)
   - **Unreadable content**: Ignore PDFs that cannot be parsed or are image-only without text layer
3. ✅ Compute content hash (SHA256 of extracted text)
4. ✅ Check cache: Compare hash with stored hash for (model_id, url)
5. ✅ **If hash unchanged**: Skip processing (no extraction needed)
6. ✅ **If hash changed or new document**:
   - For PDFs: Use AI (Claude) to identify sections containing benchmark information
   - Extract benchmarks from relevant sections using AI
   - Store benchmarks in database
   - Update cached hash (even if extraction fails - prevents infinite retries)
7. ✅ **Do NOT cache document content** - only store metadata (url, doc_type, content_hash, last_fetched)
8. ✅ Handle rate limits and retries with exponential backoff:
   ```yaml
   retry_policy:
     max_attempts: 3
     initial_delay: 1.0  # seconds
     backoff_multiplier: 2.0
     max_delay: 60  # cap at 1 minute
   ```
9. ✅ Log failed fetches but continue processing other sources

**Caching Strategy:**
- Document content is re-fetched and re-extracted every run
- Only the content hash is cached for change detection
- Benchmark extraction (expensive Claude API call) only runs when content hash changes
- If extraction fails, cache the hash with `extraction_failed=true` flag
- **Never retry failed extractions** - once marked failed, skip even if content hash changes
- This prevents infinite retries on permanently broken or irrelevant documents

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
    - "zero-shot-classification"
  min_downloads: 10000
  date_filter_months: 12  # Rolling window from current date
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
- **Deleted models** (no longer on HuggingFace):
  - Keep in cache with `deleted_at` timestamp
  - Exclude from "Trending Models" report
  - Include in historical snapshots for data continuity

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
3. When same benchmark appears with different names across sources, adopt the most common nomenclature:
   - **Most common** = variant used by the most models
   - If tie, prefer: uppercase > lowercase > mixed case
   - Example: If 10 models use "MMLU" and 3 use "mmlu", canonical name is "MMLU"
4. Store consolidated name in database

---

## 5. Benchmark Classification & Adaptive Taxonomy

### 5.1 Taxonomy Evolution

**On each run, the agent must**:

1. **Classify all benchmarks** using Claude AI based on benchmark names and descriptions
2. **Analyze taxonomy fit**: Identify benchmarks that don't fit existing categories well
3. **Propose new categories**: AI suggests new categories based on discovered benchmark types
4. **Update taxonomy** (always, every run):
   - Add new categories if AI proposes them
   - Store updated taxonomy at root: `benchmark_taxonomy.md`
   - Archive previous taxonomy only if changes detected: `archive/benchmark_taxonomy_YYYYMMDD.md`
5. **Report changes**: Note in report if taxonomy was updated

**Classification Rules**:
- Multi-label: Benchmarks can have multiple categories
- AI-assisted: Claude classifies based on benchmark name and inferred purpose
- Confidence threshold: Minimum 0.7 confidence for category assignment
- Manual override: Users can edit `categories.yaml` at root (takes precedence over AI)

**No thresholds for evolution**: System always attempts to evolve taxonomy based on all discovered benchmarks, regardless of count or percentage

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
    deleted_at TEXT,                  -- Timestamp if model deleted from HuggingFace
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

-- Documents cache (metadata only, no content storage)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,            -- model_card, blog, paper, arxiv_paper, github_pdf
    url TEXT NOT NULL,
    content_hash TEXT NOT NULL,        -- SHA256 for change detection
    extraction_failed BOOLEAN DEFAULT 0, -- Flag failed extractions to avoid retries
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

-- Indexes for performance
CREATE INDEX idx_models_lab ON models(lab);
CREATE INDEX idx_models_release_date ON models(release_date);
CREATE INDEX idx_models_deleted ON models(deleted_at);
CREATE INDEX idx_benchmarks_name ON benchmarks(canonical_name);
CREATE INDEX idx_benchmarks_last_seen ON benchmarks(last_seen);
CREATE INDEX idx_model_benchmarks_model ON model_benchmarks(model_id);
CREATE INDEX idx_model_benchmarks_benchmark ON model_benchmarks(benchmark_id);
CREATE INDEX idx_documents_model ON documents(model_id);
CREATE INDEX idx_documents_hash ON documents(content_hash);
```

### 6.2 Incremental Update Logic

**On each run:**
1. Update model metadata (downloads, likes) for ALL models from HuggingFace API
2. For each model:
   - Discover and fetch all source documents (model card, PDFs, blogs)
   - For each document:
     - Extract text/tables from source
     - Compute content hash (SHA256)
     - Check cache: does (model_id, url) exist?
     - Compare stored hash with new hash
     - **If hash unchanged**: Skip extraction (content hasn't changed)
     - **If hash changed or new document**:
       - For PDFs: AI section detection → extract relevant sections
       - AI benchmark extraction from relevant content
       - Store benchmarks in database
       - Update cached hash (even if extraction fails)
   - Discard fetched content (not persisted)
3. Only documents with changed content trigger expensive AI extraction

**Benefits**:
- Faster incremental runs (skip unchanged content via hash comparison)
- Always have latest popularity data (downloads, likes updated every run)
- Detect when labs update their documentation
- Avoid infinite retries on broken documents (cache failed extraction attempts)
- No disk bloat from storing document content

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
  content_max_size: 50000  # Characters (Unicode code points)

extraction:
  use_ai: true
  consolidation_enabled: true
  classification_enabled: true

pdf_constraints:
  max_file_size_mb: 10
  download_timeout_seconds: 120
  max_extracted_chars: 50000

google_search:
  max_results_per_query: 10
  delay_between_searches: 2  # seconds
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  max_retries_on_block: 3
  fallback_strategy: "skip"

retry_policy:
  max_attempts: 3
  initial_delay: 1.0  # seconds
  backoff_multiplier: 2.0
  max_delay: 60  # seconds

reporting:
  timeframe_months: 12  # Rolling window from current date
  retry_on_failure: true
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

**PDF parsing library**:
- Use `pdfplumber` as primary library (better table extraction and structure handling)
- Fallback to `PyPDF2` if pdfplumber fails
- Skip PDFs that cannot be parsed (image-only, corrupted)

**Extraction strategy (AI-powered section detection)**:

**PDF constraints:**
```yaml
pdf_constraints:
  max_file_size_mb: 10
  download_timeout_seconds: 120
  max_extracted_chars: 50000  # Unicode characters, not bytes
```

**Processing steps:**
1. Download PDF from URL (abort if >10MB or timeout)
2. Extract all text + tables using pdfplumber:
   ```python
   with pdfplumber.open(pdf_path) as pdf:
       text = '\n'.join(page.extract_text() for page in pdf.pages)
       tables = [page.extract_tables() for page in pdf.pages]
   ```
3. Truncate to 50,000 characters if needed (applied after extraction, tables count toward limit)
4. Compute content hash: `SHA256(extracted_text)`
5. Check cache: If hash matches stored hash, skip processing
6. **If content changed (new or updated)**:
   - Send extracted text to Claude AI in single call: "Identify sections containing benchmark/evaluation information and extract all benchmark names"
   - Claude returns: relevant sections + extracted benchmark names
   - Store extracted benchmarks in database
7. Update cached hash (even if extraction fails)
8. Discard PDF and extracted text (do not persist)

**Table handling**:
- Extract table structure with pdfplumber
- Include tables in text sent to Claude (no need to reformat)
- Claude parses benchmark names from table data

**Error handling**:
- If extraction returns <500 chars, consider PDF unreadable → log warning, skip
- If Claude extraction fails, cache hash anyway with `extraction_failed=true` flag
- Prevents infinite retries on broken or irrelevant PDFs

**Section detection runs every time**:
- When document hash changes (content updated), always run AI section detection
- This ensures new benchmark mentions are captured even if document structure changes

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

**Technology Stack**:
- **Fully static approach**: Pre-generate all HTML/JSON during agent run
- Frontend: React + D3.js (charts) compiled to static HTML/JS
- Data: JSON files generated from SQLite queries
- Deployment: Static files hosted on GitHub Pages
- No backend server required

### 11.3 Data Access

Dashboard generation:
- Agent queries SQLite after report generation
- Generates static JSON files for each view (benchmarks.json, models.json, trends.json, etc.)
- Compiles React app to static HTML/CSS/JS bundle
- Static files deployed to GitHub Pages
- No real-time updates - regenerated on each agent run

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
- **Database optimization**: Indexed columns (see section 6.1), efficient queries
- **Parallelization strategy**:
  - Discovery phase: Serial (HuggingFace API sequential queries per lab)
  - Document fetching: Parallel (max 5 concurrent downloads per model)
  - AI extraction: Serial (one Claude API call at a time to avoid rate limits)
  - Consolidation & classification: Serial
  - Report generation: Serial

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
