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
cp agents/benchmark_intelligence/config/auth.yaml.example agents/benchmark_intelligence/config/auth.yaml
# Edit auth.yaml with API keys

# Full execution (all 6 stages)
python -m agents.benchmark_intelligence.main

# Individual stages
python -m agents.benchmark_intelligence.main --stage filter_models
python -m agents.benchmark_intelligence.main --stage find_documents
python -m agents.benchmark_intelligence.main --stage parse_documents
python -m agents.benchmark_intelligence.main --stage consolidate_names
python -m agents.benchmark_intelligence.main --stage categorize_benchmarks  
python -m agents.benchmark_intelligence.main --stage generate_report

# JSON outputs stored in: agents/benchmark_intelligence/outputs/stage_<name>_<timestamp>.json
```

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
**Effort**: 8-10 hours  
**Files**: `agents/benchmark_intelligence/main.py`, `pipeline.py`

- [ ] Extract each stage into standalone function matching API contracts
- [ ] Implement JSON output writer with standardized schema
- [ ] Add CLI argument parsing for `--stage <name>`
- [ ] Create stage orchestrator supporting individual or sequential execution
- [ ] Store JSON outputs in `outputs/` directory
- [ ] **Test**: Run each stage individually, verify JSON schema compliance

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

#### T12: Documentation Updates (Priority: P3)
**Effort**: 2-3 hours  
**Files**: `README.md`, `agents/benchmark_intelligence/README.md`

- [ ] Update README with new execution modes (6 stages)
- [ ] Document concurrency settings (default 20)
- [ ] Document JSON output locations and schemas
- [ ] Add troubleshooting for common concurrency issues
- [ ] **Deliverable**: Updated documentation

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
agents/benchmark_intelligence/
├── main.py                          [MODIFY: T3, T4, T6, T9]
├── pipeline.py                      [NEW: T4]
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
