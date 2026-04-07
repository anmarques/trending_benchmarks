# Implementation Plan: Benchmark Intelligence System

**Feature**: Benchmark Intelligence System  
**Branch**: feature/001-benchmark-intelligence-spec  
**Spec**: [spec.md](spec.md)  
**Created**: 2026-04-06  
**Status**: Draft

---

## Executive Summary

This plan outlines the changes needed to align the **existing implementation** (~7500 LOC) with the updated specification requirements. The system already has substantial functionality implemented; this plan focuses on targeted enhancements rather than a full rewrite.

### Current Implementation Status

**Existing** (~7500 LOC across 20+ Python modules):
- ✅ Model discovery from HuggingFace (discover_models.py)
- ✅ Multi-source document fetching (fetch_docs.py, fetch_docs_enhanced.py, fetch_docs_fallback.py)
- ✅ PDF parsing (pdf_parser.py with pdfplumber + PyPDF2 fallback)
- ✅ Benchmark extraction with AI (extract_benchmarks.py)
- ✅ Fuzzy matching consolidation (consolidate.py)
- ✅ Benchmark classification (classify.py)
- ✅ Taxonomy evolution (taxonomy_manager.py)
- ✅ SQLite caching with content hashing (cache.py)
- ✅ Report generation (reporting.py)
- ✅ Retry logic utilities (retry_utils.py)
- ✅ Client abstractions (clients/)
- ✅ Sequential orchestration (main.py)

**Gaps Identified** (from spec clarifications):
- ❌ **High concurrency**: Currently sequential; spec requires 20+ parallel model processing
- ❌ **6-stage pipeline**: Current 5-step monolithic flow; spec requires modular stages with JSON outputs
- ❌ **Error aggregation**: Basic error list; spec requires type-based aggregation with summaries
- ❌ **Real-time progress**: Basic logging; spec requires live statistics (models processed, benchmarks extracted, errors)
- ❌ **Database concurrency**: Simple connection; spec requires connection pooling with retry on conflicts
- ❌ **Temporal tracking**: Basic snapshots; spec requires 12-month rolling window, benchmark_mentions table, status classification
- ❌ **Web search disambiguation**: Not implemented; spec requires top-3 search for fuzzy match <90%
- ❌ **API rate limiting**: Not explicitly handled; spec requires backoff queue strategy
- ❌ **Resumability**: Hash caching exists but not explicitly documented as restart-safe
- ❌ **90% fuzzy threshold**: Need to verify/configure in consolidate.py

---

## Technical Context

### Technology Stack (Existing)

- **Language**: Python 3.9+
- **Database**: SQLite 3 with content-hash based caching
- **AI**: Anthropic Claude (via API client or MCP)
- **APIs**: HuggingFace Hub, arXiv, GitHub
- **Libraries**:
  - `huggingface_hub` - Model discovery
  - `anthropic` - AI extraction/classification  
  - `pdfplumber` + `PyPDF2` - PDF parsing
  - `beautifulsoup4` - HTML parsing
  - `requests` - HTTP operations
  - `pyyaml` - Configuration
  - `python-dateutil` - Date handling

### Architecture Pattern (Current)

**Sequential Pipeline**:
```
Discovery → Process Models (loop) → Consolidate → Snapshot → Report
```

**Target Architecture** (from spec):
```
6-Stage Modular Pipeline with Parallel Execution:
Stage 1: Model Filtering (JSON output)
Stage 2: Document Finding (JSON output)
Stage 3: Document Parsing/Extraction (JSON output, 20+ concurrent)
Stage 4: Name Consolidation (JSON output)
Stage 5: Categorization/Taxonomy (JSON output)
Stage 6: Reporting (Markdown output)
```

### Individual Stage Execution Design

**Key Requirements** (from FR-012):
- Each stage callable individually via CLI
- Intermediate results stored as JSON for verification
- Stages can run in sequence (default) or individually
- State management via JSON files and database

**Implementation Approach**:

Each stage is a **standalone function** that:
- Reads input from JSON file (from previous stage) OR queries database directly
- Writes output to JSON file with standardized schema
- Updates database with persistent state

**No class hierarchy needed** - just simple functions with consistent I/O patterns.

**Stage Scripts** (Separate Entry Points):

Each stage is a **standalone Python script** with its own `__main__` block:

```python
# benchmark_intelligence/filter_models.py
def run(config_path: str = "config.yaml") -> str:
    """Query HuggingFace, filter models, write JSON, return output path"""
    # Reads: config.yaml
    # Writes: outputs/filter_models_<timestamp>.json
    # DB: None (read-only discovery)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    output_path = run(args.config)
    print(f"Output: {output_path}")

# benchmark_intelligence/find_docs.py
def run(models_json: str = None) -> str:
    """Find docs for models, write JSON, return output path"""
    # Reads: outputs/stage_01_*.json (auto-find if not specified)
    # Writes: outputs/find_documents_<timestamp>.json
    # DB: Check documents table for cached hashes
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to filter_models JSON output")
    args = parser.parse_args()
    output_path = run(args.input)
    print(f"Output: {output_path}")

# benchmark_intelligence/parse_docs.py
def run(docs_json: str = None, concurrency: int = 20) -> str:
    """Extract benchmarks from docs, write JSON, return output path"""
    # Reads: outputs/stage_02_*.json (auto-find if not specified)
    # Writes: outputs/parse_documents_<timestamp>.json
    # DB: Insert into model_benchmarks table
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to find_docs JSON output")
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()
    output_path = run(args.input, args.concurrency)
    print(f"Output: {output_path}")

# Similar pattern for:
# - consolidate_benchmarks.py
# - categorize_benchmarks.py
# - report.py
```

**CLI Command Structure** (Separate Entry Points):
   ```bash
   # Individual stages - each has its own entry point
   python -m benchmark_intelligence.filter_models
   python -m benchmark_intelligence.find_docs
   python -m benchmark_intelligence.parse_docs --concurrency 30
   python -m benchmark_intelligence.consolidate_benchmarks --from-db
   python -m benchmark_intelligence.categorize_benchmarks
   python -m benchmark_intelligence.report
   
   # Full pipeline (all stages sequentially)
   python -m benchmark_intelligence.generate
   
   # Each stage script supports options:
   python -m benchmark_intelligence.parse_docs --input outputs/stage_02_*.json --concurrency 30
   ```

3. **State Management**:
   - **JSON files**: Intermediate artifacts for verification and re-running stages
   - **Database**: Persistent state (models, benchmarks, associations, snapshots)
   - Stages read from previous JSON file OR query database (depending on stage)
   - When running individual stage without input file, automatically find latest from previous stage
   - Option to specify input file: `--input outputs/find_documents_20260406.json`

4. **JSON File Naming Convention**:
   ```
   outputs/
   ├── filter_models_20260406_120000.json
   ├── find_documents_20260406_120500.json
   ├── parse_documents_20260406_121500.json
   ├── consolidate_names_20260406_122500.json
   ├── categorize_benchmarks_20260406_123000.json
   └── report_metadata_20260406_123500.json
   ```

5. **Stage Dependencies & Data Flow**:
   ```
   Stage 1 (Filter)      → Input: config.yaml
                         → Output: JSON (model list)
                         → DB: None
   
   Stage 2 (Find Docs)   → Input: Stage 1 JSON
                         → Output: JSON (doc URLs per model)
                         → DB: Check documents table for hashes
   
   Stage 3 (Parse)       → Input: Stage 2 JSON
                         → Output: JSON (extracted benchmarks)
                         → DB: Insert model_benchmarks, update documents
   
   Stage 4 (Consolidate) → Input: DB (query model_benchmarks) OR Stage 3 JSON
                         → Output: JSON (canonical benchmark names)
                         → DB: Update benchmarks table
   
   Stage 5 (Categorize)  → Input: DB (query benchmarks) OR Stage 4 JSON
                         → Output: JSON (categorized benchmarks)
                         → DB: Update benchmarks.categories
   
   Stage 6 (Report)      → Input: DB (query snapshots, benchmark_mentions)
                         → Output: Markdown report
                         → DB: Read-only
   ```

6. **Helper Functions** (simple utilities, no classes):
   ```python
   def find_latest_stage_output(stage_num: int) -> str:
       """Find most recent JSON output from given stage number"""
       
   def load_stage_json(filepath: str) -> dict:
       """Load and validate JSON from stage output file"""
       
   def save_stage_json(data: dict, stage_num: int, stage_name: str) -> str:
       """Save stage output with standardized schema and naming"""
   ```

7. **Error Handling for Individual Stages**:
   - If input file missing → search for latest from previous stage; clear error if none found
   - If input JSON schema invalid → validation error with specific field issues
   - If stage fails → partial output saved with error details for debugging

### Database Schema

**Current Tables**:
- `models` - Model metadata with hash tracking
- `benchmarks` - Canonical benchmark names with categories
- `model_benchmarks` - Model-benchmark associations with context (maps to variant_details)
- `documents` - Document metadata with content_hash (no content storage ✓)
- `snapshots` - Execution snapshots (missing: window_start, window_end, taxonomy_version)

**Missing Tables**:
- `benchmark_mentions` - Denormalized temporal tracking per snapshot

**Schema Changes Needed**:
1. Add columns to `snapshots`: window_start, window_end, taxonomy_version
2. Create `benchmark_mentions` table for 12-month rolling window queries
3. Rename `model_benchmarks.context` → `variant_details` (or map transparently)
4. Remove `benchmarks.attributes` column (deprecated per spec feedback)

---

## Constitution Check

**Prerequisites**: .specify/memory/constitution.md not found - skipping constitution validation.

If a constitution exists in future iterations, verify:
- ✓ Specification-driven development (spec.md → plan.md → tasks.md → implementation)
- ✓ Test-driven where applicable (ground truth validation defined in spec)
- ✓ Incremental delivery (existing implementation provides foundation)
- ✓ Documentation standards (inline docstrings present in existing code)

---

## Phase 0: Research & Design Decisions

### Research Tasks

1. **Python Concurrency for I/O-Bound Operations**
   - Decision: `asyncio` with `aiohttp` for API calls + `concurrent.futures.ThreadPoolExecutor` for CPU-bound operations (PDF parsing, AI extraction)
   - Rationale: Mixed workload (I/O-heavy API calls + CPU-heavy AI/parsing); asyncio handles API concurrency well, ThreadPoolExecutor prevents blocking on compute
   - Alternatives considered: Pure threading (complex), pure asyncio (blocks on CPU work), multiprocessing (overhead for data sharing)

2. **SQLite Connection Pooling**
   - Decision: Custom connection pool with context manager + automatic retry on `SQLITE_BUSY`
   - Rationale: SQLite serializes writes; pool manages contention gracefully; Python sqlite3 supports timeout parameter
   - Alternatives considered: Switch to PostgreSQL (out of scope), serialize all writes (defeats concurrency), ignore conflicts (data loss risk)

3. **Progress Reporting Strategy**
   - Decision: Shared `ProgressTracker` class with thread-safe counters + periodic console updates
   - Rationale: Real-time visibility critical for long-running jobs; thread-safe incrementers simple and efficient
   - Alternatives considered: Logging only (no live stats), tqdm library (less control), external monitoring (complexity)

4. **Error Aggregation Pattern**
   - Decision: `ErrorAggregator` class with type-based bucketing (dict of error_type → count/samples)
   - Rationale: Enables pattern detection ("15 arXiv fetch failures"); summary output at completion
   - Alternatives considered: Individual error logs (no patterns), halt on first error (spec forbids), silent failure (spec forbids)

5. **Web Search Integration**
   - Decision: Optional web search module using existing `google_search.py` + Claude for result analysis
   - Rationale: Code already exists; integrate into consolidate.py when fuzzy match <90%
   - Alternatives considered: Manual disambiguation (defeats automation), skip ambiguous benchmarks (data loss), always search (API costs)

6. **API Rate Limiting Strategy**
   - Decision: Token bucket algorithm with exponential backoff on 429/rate limit errors
   - Rationale: Industry standard; graceful throttling; automatic retry; preserves throughput
   - Alternatives considered: Fixed delays (inefficient), fail fast (defeats concurrency), ignore limits (API bans)

7. **12-Month Rolling Window Calculation**
   - Decision: Query models by `release_date` in window; compute stats in SQL; denormalize to benchmark_mentions for fast reads
   - Rationale: SQL aggregation efficient; denormalized table enables historical comparison without recomputation
   - Alternatives considered: Compute on-the-fly (slow for reports), store raw snapshots only (no trend queries), fixed window (spec requires rolling)

8. **JSON Output Format for Pipeline Stages**
   - Decision: Standardized schema per stage: `{stage: str, timestamp: str, input_count: int, output_count: int, data: [], errors: []}`
   - Rationale: Consistent structure enables validation; errors array supports debugging; timestamps enable performance analysis
   - Alternatives considered: Ad-hoc formats (inconsistent), no JSON (spec requires), separate error files (harder to correlate)

9. **Benchmark Extraction Routing Strategy**
   - **Decision**: Route extraction by document structure:
     - **HTML/Markdown tables** → Deterministic parsing with BeautifulSoup/regex
     - **Prose/narrative text** → AI extraction with Claude
     - **PDF charts/figures** → Vision AI extraction (Phase 5)
   - **Rationale**: 
     - **Performance**: HTML table parsing is deterministic, instant (<100ms vs 10min+ for AI)
     - **Reliability**: Tables have fixed structure; no AI timeout/token limits
     - **Cost**: BeautifulSoup is free; Claude API costs $0.015/1K tokens
     - **Ground truth testing**: Llama-3.1-8B model card (41KB HTML tables) hit 10min timeout with AI extraction, failed to complete even with 32K max_tokens
   - **Implementation**:
     - Detect document format in `parallel_fetcher.py` when content is fetched
     - Add `content_format` field: `"html_table"`, `"markdown_table"`, `"prose"`, `"pdf"`
     - Route in `parse_docs.py`:
       ```python
       if content_format in ["html_table", "markdown_table"]:
           benchmarks = parse_table_deterministic(content)
       elif content_format == "prose":
           benchmarks = extract_benchmarks_ai(content)
       ```
     - Table parser extracts: benchmark name, score, metric, shot count, model name from `<td>` cells
     - AI extraction only for unstructured text (blog posts, paper prose)
   - **Alternatives considered**:
     - Always use AI (current): Timeout on large tables, expensive, slow
     - Always use deterministic parsing: Cannot handle prose text ("achieves 94.2% on GSM8K")
     - Manual curation: Defeats automation goal
   - **Phase 3 Scope**: Implement HTML/Markdown table parsing
   - **Phase 5 Scope**: Add vision AI for PDF chart extraction

10. **arXiv Document Fetching Strategy**
   - **Decision**: Fetch full HTML-converted papers instead of abstracts only
     - Use **ar5iv.labs.arxiv.org** HTML conversion service: `https://ar5iv.labs.arxiv.org/html/{arxiv_id}`
     - Fallback to abstract if HTML conversion unavailable (404)
   - **Rationale**:
     - **Content completeness**: Abstracts are 1-2KB and mention benchmark names without scores; full papers are 500KB-1MB with 10+ HTML tables containing all benchmark data
     - **Ground truth impact**: Llama-3.1-8B paper (arXiv:2407.21783) contains 45 benchmarks across Tables 8-16; abstract extraction yielded 0 benchmarks
     - **ar5iv reliability**: HTML conversion preserves LaTeX table structure as proper `<table>` tags, enabling deterministic parsing
     - **Performance**: HTML tables can be parsed deterministically (instant) vs PDF processing (requires OCR/vision AI in Phase 5)
   - **Implementation**:
     - Update `parallel_fetcher.py` arXiv fetching logic:
       ```python
       # Try HTML conversion first
       html_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
       response = requests.get(html_url, timeout=30)
       if response.status_code == 200:
           return response.text, "text/html"
       
       # Fallback to abstract if HTML unavailable
       abstract_url = f"https://export.arxiv.org/abs/{arxiv_id}"
       # ... extract abstract as before
       ```
     - HTML papers with tables → routed to deterministic table parser
     - HTML papers without tables (rare) → routed to AI prose extraction
   - **Alternatives considered**:
     - Keep abstract-only fetching (current): Misses 90% of benchmark data
     - PDF fetching + OCR: Complex, slow, error-prone; deferred to Phase 5
     - arXiv API bulk download: Adds infrastructure complexity; HTML conversion is simpler
   - **Impact**: Expected to increase extraction rate from 64% to >90% on ground truth validation
   - **Phase 3 Scope**: Implement HTML fetching with abstract fallback

### Research Artifacts

**Output**: research.md (included above as inline decisions)

---

## Phase 1: Data Model & Design

### Entity Model

**From Specification** (already implemented with minor gaps):

```
Model (entity) - Existing ✓
├── model_id: str (PK)
├── lab: str
├── release_date: datetime
├── task_type: str
├── downloads: int
├── likes: int
├── first_seen: datetime
├── last_updated: datetime
└── model_card_hash: str

Benchmark (entity) - Existing ✓ (needs: remove attributes column)
├── id: int (PK)
├── canonical_name: str (unique)
├── categories: JSON array
├── first_seen: datetime
└── last_seen: datetime

Model-Benchmark Association - Existing ✓ (needs: rename context → variant_details)
├── model_id: str (FK)
├── benchmark_id: int (FK)
├── variant_details: JSON {shots, method, model_type}
├── source_type: str
├── source_url: str
└── recorded_at: datetime

Document (entity) - Existing ✓
├── model_id: str (FK)
├── source_type: str
├── url: str
├── content_hash: str
├── fetched_at: datetime
└── extraction_failed: bool

Snapshot (entity) - Needs enhancement
├── id: int (PK)
├── timestamp: datetime
├── window_start: datetime          [ADD]
├── window_end: datetime            [ADD]
├── model_count: int
├── benchmark_count: int
├── taxonomy_version: str           [ADD]
└── summary: JSON

Benchmark Mention (entity) - NEW ENTITY
├── snapshot_id: int (FK)
├── benchmark_id: int (FK)
├── absolute_mentions: int
├── relative_frequency: float
├── first_seen: datetime
├── last_seen: datetime
└── status: enum (emerging, active, almost_extinct)
```

### API Contracts / Stage Interfaces

Since this is a CLI tool (not a web service), contracts are defined as **Python function signatures** with JSON I/O:

**Stage 1: Model Filtering**
```python
def filter_models(config: dict) -> dict:
    """
    Output JSON schema:
    {
      "stage": "filter_models",
      "timestamp": "2026-04-06T12:00:00Z",
      "input_count": 1000,
      "output_count": 150,
      "data": [
        {"model_id": "meta-llama/Llama-3.1-8B", "lab": "meta", "release_date": "2024-07-23", ...}
      ],
      "errors": []
    }
    """
```

**Stage 2: Document Finding**
```python
def find_documents(models: list[dict]) -> dict:
    """
    Output JSON schema:
    {
      "stage": "find_documents",
      "timestamp": "2026-04-06T12:05:00Z",
      "input_count": 150,
      "output_count": 450,  # 3 docs/model avg
      "data": [
        {
          "model_id": "meta-llama/Llama-3.1-8B",
          "documents": [
            {"type": "model_card", "url": "https://...", "found": true},
            {"type": "arxiv_paper", "url": "https://...", "found": true},
            {"type": "blog", "url": "https://...", "found": false, "error": "404"}
          ]
        }
      ],
      "errors": [{"model_id": "...", "error_type": "github_rate_limit", "count": 5}]
    }
    """
```

**Stage 3: Document Parsing (Benchmark Extraction)**
```python
async def parse_documents(documents: list[dict], concurrency: int = 20) -> dict:
    """
    Output JSON schema:
    {
      "stage": "parse_documents",
      "timestamp": "2026-04-06T12:15:00Z",
      "input_count": 450,
      "output_count": 1200,  # benchmarks extracted
      "data": [
        {
          "model_id": "meta-llama/Llama-3.1-8B",
          "source_type": "arxiv_paper",
          "source_url": "https://arxiv.org/abs/...",
          "benchmarks": [
            {"name": "MMLU", "variant": "5-shot", "method": "CoT"},
            {"name": "GSM8K", "variant": "8-shot"}
          ]
        }
      ],
      "errors": [
        {"error_type": "extraction_timeout", "count": 12},
        {"error_type": "pdf_parse_failed", "count": 3}
      ]
    }
    """
```

**Stage 4: Name Consolidation**
```python
def consolidate_names(extractions: list[dict]) -> dict:
    """
    Output JSON schema:
    {
      "stage": "consolidate_names",
      "timestamp": "2026-04-06T12:25:00Z",
      "input_count": 1200,
      "output_count": 150,  # unique benchmarks after consolidation
      "data": [
        {
          "canonical_name": "MMLU",
          "variants": ["MMLU", "MMLU 5-shot", "MMLU-test"],
          "similarity_scores": [100, 95, 92],
          "web_search_used": false
        },
        {
          "canonical_name": "MMLU-Pro",
          "variants": ["MMLU-Pro", "MMLU Pro"],
          "similarity_scores": [100, 88],
          "web_search_used": true,
          "web_search_result": "Confirmed separate benchmark per Papers with Code"
        }
      ],
      "errors": [{"error_type": "web_search_failed", "count": 2}]
    }
    """
```

**Stage 5: Categorization (Taxonomy)**
```python
def categorize_benchmarks(benchmarks: list[dict]) -> dict:
    """
    Output JSON schema:
    {
      "stage": "categorize_benchmarks",
      "timestamp": "2026-04-06T12:30:00Z",
      "input_count": 150,
      "output_count": 150,
      "data": [
        {
          "canonical_name": "MMLU",
          "categories": ["General Knowledge", "Reasoning"],
          "taxonomy_version": "1.2",
          "newly_created_category": false
        }
      ],
      "taxonomy_changes": [
        {"action": "added_category", "name": "Audio Understanding", "reason": "Whisper benchmarks discovered"}
      ],
      "errors": []
    }
    """
```

**Stage 6: Reporting**
```python
def generate_report(snapshot_id: int) -> dict:
    """
    Output: Markdown file written to disk
    
    JSON metadata output:
    {
      "stage": "generate_report",
      "timestamp": "2026-04-06T12:35:00Z",
      "snapshot_id": 42,
      "report_path": "reports/report_20260406_123500.md",
      "sections_generated": 6,
      "errors": []
    }
    """
```

### Quickstart Guide

```bash
# Installation
pip install -r requirements.txt

# Configuration
cp benchmark_intelligence/config/auth.yaml.example benchmark_intelligence/config/auth.yaml
# Edit auth.yaml with API keys

# Full execution (all 6 stages)
python -m benchmark_intelligence.generate

# Individual stages (standard Python)
python -m benchmark_intelligence.filter_models
python -m benchmark_intelligence.find_docs
python -m benchmark_intelligence.parse_docs --concurrency 30
python -m benchmark_intelligence.consolidate_benchmarks --from-db
python -m benchmark_intelligence.categorize_benchmarks
python -m benchmark_intelligence.report

# Individual stages (Ambient workflow paths)
/benchmark_intelligence.filter_models
/benchmark_intelligence.find_docs
/benchmark_intelligence.parse_docs --concurrency 30
/benchmark_intelligence.consolidate_benchmarks --from-db
/benchmark_intelligence.categorize_benchmarks
/benchmark_intelligence.report
/benchmark_intelligence.generate

# JSON outputs stored in: benchmark_intelligence/outputs/stage_<name>_<timestamp>.json
```

### Ambient Integration

Each stage module must be exposed as an Ambient workflow command by registering in `.ambient/ambient.json`:

```json
{
  "workflows": {
    "benchmark_intelligence.filter_models": {
      "command": "python -m benchmark_intelligence.filter_models",
      "description": "Stage 1: Filter and discover AI models from configured labs",
      "outputs": ["outputs/filter_models_*.json"]
    },
    "benchmark_intelligence.find_docs": {
      "command": "python -m benchmark_intelligence.find_docs",
      "description": "Stage 2: Find documentation sources for filtered models",
      "inputs": ["outputs/filter_models_*.json"],
      "outputs": ["outputs/find_documents_*.json"]
    },
    "benchmark_intelligence.parse_docs": {
      "command": "python -m benchmark_intelligence.parse_docs",
      "description": "Stage 3: Parse documents and extract benchmarks (concurrent)",
      "inputs": ["outputs/find_documents_*.json"],
      "outputs": ["outputs/parse_documents_*.json"],
      "arguments": {
        "--concurrency": {"type": "int", "default": 20}
      }
    },
    "benchmark_intelligence.consolidate_benchmarks": {
      "command": "python -m benchmark_intelligence.consolidate_benchmarks",
      "description": "Stage 4: Consolidate benchmark names and resolve variants",
      "inputs": ["outputs/parse_documents_*.json"],
      "outputs": ["outputs/consolidate_names_*.json"],
      "arguments": {
        "--from-db": {"type": "flag", "description": "Query from database instead of JSON"}
      }
    },
    "benchmark_intelligence.categorize_benchmarks": {
      "command": "python -m benchmark_intelligence.categorize_benchmarks",
      "description": "Stage 5: Categorize benchmarks into taxonomy",
      "inputs": ["outputs/consolidate_names_*.json"],
      "outputs": ["outputs/categorize_benchmarks_*.json"]
    },
    "benchmark_intelligence.report": {
      "command": "python -m benchmark_intelligence.report",
      "description": "Stage 6: Generate benchmark intelligence report",
      "outputs": ["reports/report_*.md"]
    },
    "benchmark_intelligence.generate": {
      "command": "python -m benchmark_intelligence.generate",
      "description": "Full pipeline: Execute all 6 stages sequentially",
      "outputs": [
        "outputs/stage_*.json",
        "reports/report_*.md"
      ]
    }
  }
}
```

This enables:
- Ambient UI to discover and display available workflows
- Slash command execution: `/benchmark_intelligence.filter_models`
- Workflow composition and scheduling within Ambient
- Input/output tracking for each stage

---

## Phase 2: Implementation Tasks (Gap Closure)

### Task Breakdown

#### T1: Database Schema Updates (Priority: P0)
**Effort**: 2-3 hours  
**Files**: `agents/benchmark_intelligence/tools/cache.py`

- [ ] Add columns to `snapshots` table:
  - `window_start TEXT NOT NULL`
  - `window_end TEXT NOT NULL`
  - `taxonomy_version TEXT`
- [ ] Create `benchmark_mentions` table with schema from data model
- [ ] Add migration logic to handle existing databases
- [ ] Update `CacheManager` methods to populate new fields
- [ ] **Test**: Verify schema with sample data insertion

#### T2: Connection Pooling & Retry Logic (Priority: P0)
**Effort**: 3-4 hours  
**Files**: `agents/benchmark_intelligence/tools/cache.py`, new file `connection_pool.py`

- [ ] Create `ConnectionPool` class with configurable pool size
- [ ] Implement context manager with automatic retry on `SQLITE_BUSY`
- [ ] Configure retry backoff (max 3 attempts per clarification)
- [ ] Replace direct `sqlite3.connect()` calls with pool
- [ ] **Test**: Concurrent write stress test (20+ threads)

#### T3: Concurrent Model Processing (Priority: P0)
**Effort**: 6-8 hours  
**Files**: `agents/benchmark_intelligence/main.py`, new file `concurrent_processor.py`

- [ ] Create `ConcurrentModelProcessor` class using `asyncio` + `ThreadPoolExecutor`
- [ ] Implement work queue with 20+ concurrent workers
- [ ] Integrate with existing `_process_model()` method
- [ ] Add rate limiting with token bucket algorithm
- [ ] Handle backoff on API 429 errors
- [ ] **Test**: Process 100 models concurrently, verify DB consistency

#### T4: 6-Stage Pipeline with JSON Outputs (Priority: P1)
**Effort**: 6-8 hours  
**Files**: `filter_models.py`, `find_docs.py`, `parse_docs.py`, `consolidate_benchmarks.py`, `categorize_benchmarks.py`, `report.py`, `stage_utils.py`, `generate.py`

**Subtasks**:
- [ ] Create `stage_utils.py` with shared helper functions:
  - [ ] `find_latest_stage_output(stage_num)` → finds most recent JSON from stage
  - [ ] `load_stage_json(filepath)` → loads and validates JSON
  - [ ] `save_stage_json(data, stage_num, stage_name)` → saves with standard schema
- [ ] Create 6 separate stage scripts (each with `run()` function + `__main__` block):
  - [ ] `filter_models.py`:
    - [ ] `run(config_path)` → wraps `discover_trending_models()`, returns JSON path
    - [ ] `__main__` block with argparse for `--config`
  - [ ] `find_docs.py`:
    - [ ] `run(models_json)` → wraps `fetch_documentation()`, returns JSON path
    - [ ] `__main__` block with argparse for `--input` (auto-finds if not provided)
  - [ ] `parse_docs.py`:
    - [ ] `run(docs_json, concurrency)` → wraps extraction with concurrency, returns JSON path
    - [ ] `__main__` block with argparse for `--input` and `--concurrency`
  - [ ] `consolidate_benchmarks.py`:
    - [ ] `run(source)` → wraps `consolidate_benchmarks()`, source can be JSON file or queries DB, returns JSON path
    - [ ] `__main__` block with argparse for `--input` or `--from-db`
  - [ ] `categorize_benchmarks.py`:
    - [ ] `run(source)` → wraps `classify_benchmarks_batch()`, returns JSON path
    - [ ] `__main__` block with argparse for `--input` or `--from-db`
  - [ ] `report.py`:
    - [ ] `run(snapshot_id)` → wraps `ReportGenerator`, returns report path
    - [ ] `__main__` block with argparse for `--snapshot-id` (auto-finds latest if not provided)
- [ ] Create `generate.py` to orchestrate all stages:
  - [ ] Import all 6 stage modules
  - [ ] Call each `module.run()` sequentially
  - [ ] Pass output from one stage as input to next
  - [ ] `__main__` block for full pipeline execution
- [ ] Implement JSON standardized schema in `save_stage_json()`:
  - [ ] Schema: `{stage, timestamp, input_count, output_count, data, errors}`
  - [ ] Filename: `<name>_<timestamp>.json`
  - [ ] Create `outputs/` directory on first write
- [ ] **Test**: 
  - [ ] Run each stage script individually: `python -m benchmark_intelligence.filter_models`
  - [ ] Run parse_docs with explicit input: `python -m benchmark_intelligence.parse_docs --input outputs/stage_02_*.json --concurrency 30`
  - [ ] Run full pipeline: `python -m benchmark_intelligence.generate` - verify all 6 JSON files + report created
  - [ ] Verify all JSON files match standardized schema
  - [ ] Test auto-finding previous stage output
  - [ ] Test error when running stage without required previous output

#### T5: Error Aggregation by Type (Priority: P1)
**Effort**: 2-3 hours  
**Files**: New file `error_aggregator.py`, `main.py`

- [ ] Create `ErrorAggregator` class with type-based bucketing
- [ ] Collect errors during execution with categorization
- [ ] Generate summary at completion (error_type → count + samples)
- [ ] Integrate into JSON stage outputs
- [ ] **Test**: Inject various error types, verify aggregation accuracy

#### T6: Real-Time Progress Reporting (Priority: P1)
**Effort**: 3-4 hours  
**Files**: New file `progress_tracker.py`, `main.py`

- [ ] Create `ProgressTracker` class with thread-safe counters
- [ ] Track: models_processed, benchmarks_extracted, errors_encountered
- [ ] Implement periodic console updates (every 5 seconds)
- [ ] Display progress bar or live statistics
- [ ] **Test**: Verify live updates during execution

#### T7: Web Search Disambiguation (Priority: P2)
**Effort**: 4-5 hours  
**Files**: `agents/benchmark_intelligence/tools/consolidate.py`, `google_search.py`

- [ ] Integrate web search trigger when fuzzy match <90%
- [ ] Fetch top 3 search results for "{benchmark1} vs {benchmark2}"
- [ ] Use Claude to analyze results and determine if same/different
- [ ] Cache disambiguation decisions to avoid repeated searches
- [ ] **Test**: Test with known ambiguous pairs (MMLU vs MMLU-Pro)

#### T8: 90% Fuzzy Matching Threshold (Priority: P2)
**Effort**: 1 hour  
**Files**: `agents/benchmark_intelligence/tools/consolidate.py`

- [ ] Verify current threshold in fuzzy matching logic
- [ ] Configure as constant: `FUZZY_MATCH_THRESHOLD = 0.90`
- [ ] Add to documentation/configuration
- [ ] **Test**: Unit test with benchmark name pairs at various similarity levels

#### T9: 12-Month Rolling Window & Temporal Tracking (Priority: P1)
**Effort**: 5-6 hours  
**Files**: `agents/benchmark_intelligence/tools/cache.py`, `main.py`

- [ ] Implement `create_snapshot_with_window()` method
- [ ] Calculate window_start, window_end (current_date - 12 months to current_date)
- [ ] Query models in window by release_date
- [ ] Compute benchmark statistics (absolute_mentions, relative_frequency)
- [ ] Classify benchmark status (emerging/active/almost_extinct per clarification rules)
- [ ] Populate `benchmark_mentions` table
- [ ] **Test**: Create snapshot, verify window calculation and status classification

#### T10: API Rate Limiting with Backoff Queue (Priority: P1)
**Effort**: 4-5 hours  
**Files**: New file `rate_limiter.py`, integrate into API clients

- [ ] Implement token bucket rate limiter
- [ ] Add request queue with automatic backoff on 429 errors
- [ ] Configure per-API limits (HuggingFace, Anthropic, arXiv)
- [ ] Integrate with `ConcurrentModelProcessor`
- [ ] **Test**: Simulate rate limiting, verify backoff behavior

#### T11: Update Existing Tests for New Features (Priority: P2)
**Effort**: 4-6 hours  
**Files**: `tests/` (create if not exists)

- [ ] Add unit tests for connection pool
- [ ] Add integration tests for concurrent processing
- [ ] Add tests for error aggregation
- [ ] Add tests for progress tracking
- [ ] Update ground truth validation to use new schema
- [ ] **Test**: All tests pass with >80% coverage

#### T12: Ambient Workflow Registration (Priority: P2)
**Effort**: 1-2 hours  
**Files**: `.ambient/ambient.json`

- [ ] Add workflow definitions for all 7 entry points (6 stages + generate)
- [ ] Define input/output paths for each stage
- [ ] Define command-line arguments for stages that support them
- [ ] Add descriptions for each workflow
- [ ] **Test**: Verify `/benchmark_intelligence.filter_models` works in Ambient
- [ ] **Test**: Verify argument passing: `/benchmark_intelligence.parse_docs --concurrency 30`

#### T13: Documentation Updates (Priority: P3)
**Effort**: 2-3 hours  
**Files**: `README.md`, `benchmark_intelligence/README.md`

- [ ] Update README with new execution modes (6 stages)
- [ ] Document both Python and Ambient execution paths
- [ ] Document concurrency settings (default 20)
- [ ] Document JSON output locations and schemas
- [ ] Add troubleshooting for common concurrency issues
- [ ] **Deliverable**: Updated documentation

#### Task Numbering Note

The 13 high-level tasks (T1-T13) outlined in this plan represent **gap closure themes** from the existing implementation. These have been expanded into **125 detailed implementation tasks (T001-T120 plus 5 added during analysis)** in `tasks.md`, organized by user story for incremental delivery:

- **T1** (Database Schema) → T005-T008
- **T2** (Connection Pooling) → T009-T012
- **T3** (Concurrent Processing) → T013-T014
- **T4** (6-Stage Pipeline) → T015-T050
- **T5** (Error Aggregation) → T063-T068
- **T6** (Progress Tracking) → T069-T073
- **T7** (Web Search Disambiguation) → T080-T084
- **T8** (90% Fuzzy Threshold) → T077-T079
- **T9** (12-Month Window) → T051-T055, T062A
- **T10** (Rate Limiting) → T089-T093
- **T11** (Testing) → T094-T103, T103A-C
- **T12** (Ambient Registration) → T104-T112
- **T13** (Documentation) → T113-T120

Additional tasks added during specification analysis:
- **T076A**: Edge case handling for models with no benchmarks
- **T062A**: Edge case handling for <12-month data windows
- **T103A**: Pipeline resumability validation
- **T103B**: Ground truth accuracy validation (≥95%)
- **T103C**: Code coverage measurement (≥80%)

See `tasks.md` for the complete task breakdown with dependencies, phases, and acceptance criteria.

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQLite write contention with 20+ workers | High | Connection pooling + retry logic (T2); stress testing (T3) |
| API rate limits block execution | Medium | Backoff queue with automatic throttling (T10) |
| Memory usage with high concurrency | Medium | Monitor and tune worker count; consider batching |
| Breaking changes to existing code | High | Incremental changes; preserve backward compatibility where possible |
| JSON schema validation overhead | Low | Lightweight validation; cache schemas |
| Web search API costs | Medium | Cache disambiguation results; limit to <90% fuzzy matches |

---

## Success Criteria Alignment

| Spec SC | Implementation Task | Validation Method |
|---------|---------------------|-------------------|
| SC-001: 100% model discovery | Existing + T3 (concurrency) | Ground truth test |
| SC-002: 95%+ extraction accuracy | Existing + T7 (web search) | Ground truth comparison |
| SC-003: Reports for all models | Existing + T4 (pipeline) | No size limits in code |
| SC-004: End-to-end automation | T4 (pipeline orchestration) | Full run without intervention |
| SC-005: Taxonomy evolution | Existing (taxonomy_manager.py) | Verify new category capture |
| SC-006: Report readability | Existing (reporting.py) | Manual review of output |

---

## Appendix: File Structure

```
benchmark_intelligence/
├── generate.py                      [NEW: T4 - orchestrates all stages]
├── filter_models.py                 [NEW: T4 - stage 1 entry point]
├── find_docs.py                     [NEW: T4 - stage 2 entry point]
├── parse_docs.py                    [NEW: T4 - stage 3 entry point]
├── consolidate_benchmarks.py        [NEW: T4 - stage 4 entry point]
├── categorize_benchmarks.py         [NEW: T4 - stage 5 entry point]
├── report.py                        [NEW: T4 - stage 6 entry point]
├── stage_utils.py                   [NEW: T4 - shared JSON helpers]
├── concurrent_processor.py          [NEW: T3]
├── connection_pool.py               [NEW: T2]
├── error_aggregator.py              [NEW: T5]
├── progress_tracker.py              [NEW: T6]
├── rate_limiter.py                  [NEW: T10]
├── clients/
│   ├── __init__.py
│   ├── api_client.py
│   ├── mcp_client.py
│   ├── base.py
│   └── factory.py
├── tools/
│   ├── cache.py                     [MODIFY: T1, T2, T9]
│   ├── consolidate.py               [MODIFY: T7, T8]
│   ├── discover_models.py
│   ├── extract_benchmarks.py
│   ├── fetch_docs.py
│   ├── classify.py
│   ├── taxonomy_manager.py
│   ├── pdf_parser.py
│   ├── google_search.py             [MODIFY: T7]
│   └── retry_utils.py
├── config/
│   └── auth.yaml.example
├── prompts/
│   ├── extract_benchmarks.md
│   ├── consolidate.md
│   └── classify.md
└── outputs/                         [NEW: T4 - JSON stage outputs]
    ├── stage_filter_models_*.json
    ├── stage_find_documents_*.json
    └── ...
```

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Create tasks.md** with detailed task definitions from Phase 2
3. **Begin implementation** starting with P0 tasks (T1, T2, T3)
4. **Validate against ground truth** after each major task completion

**Ready for** `/speckit.tasks` to generate detailed task breakdown.
