# Data Model

**Feature**: Benchmark Intelligence System
**Date**: 2026-04-03
**Phase**: 1 - Design & Contracts

## Overview

This document defines the data entities, relationships, and validation rules for the Benchmark Intelligence System. The data model supports incremental updates, temporal tracking, and multi-variant benchmark associations.

## Entity Definitions

### 1. Model

Represents an AI model tracked by the system.

**Attributes**:
- `id` (TEXT, PK): Full identifier (e.g., "Qwen/Qwen2.5-7B")
- `name` (TEXT, NOT NULL): Model name extracted from ID
- `lab` (TEXT): Organization/lab name (e.g., "Qwen", "meta-llama")
- `release_date` (TEXT): ISO 8601 timestamp of model release
- `first_seen` (TEXT, NOT NULL): ISO 8601 timestamp when first discovered
- `last_updated` (TEXT, NOT NULL): ISO 8601 timestamp of last metadata update
- `deleted_at` (TEXT, NULLABLE): ISO 8601 timestamp if model deleted from HuggingFace
- `downloads` (INTEGER, DEFAULT 0): Download count from HuggingFace
- `likes` (INTEGER, DEFAULT 0): Like count from HuggingFace
- `tags` (TEXT): JSON array of pipeline tags (e.g., `["text-generation", "llm"]`)

**Constraints**:
- Primary key: `id`
- `name` derived from `id` (e.g., "Qwen/Qwen2.5-7B" → "Qwen2.5-7B")
- `deleted_at` is NULL for active models
- `downloads` and `likes` updated on every run

**Indexes**:
- `idx_models_lab` on `lab` (for lab-specific queries)
- `idx_models_release_date` on `release_date` (for temporal filtering)
- `idx_models_deleted` on `deleted_at` (for filtering deleted models)

**Lifecycle**:
1. **New**: Discovered from HuggingFace, `first_seen` set to current timestamp
2. **Active**: Regular metadata updates (`downloads`, `likes`) on each run
3. **Deleted**: Marked with `deleted_at` timestamp, excluded from trending reports but kept in historical snapshots

---

### 2. Benchmark

Represents a canonical evaluation benchmark.

**Attributes**:
- `id` (INTEGER, PK, AUTOINCREMENT): Unique benchmark identifier
- `canonical_name` (TEXT, UNIQUE, NOT NULL): Consolidated benchmark name (e.g., "MMLU")
- `categories` (TEXT): JSON array of category names (e.g., `["General Knowledge", "Language Understanding"]`)
- `first_seen` (TEXT, NOT NULL): ISO 8601 timestamp when first discovered
- `last_seen` (TEXT): ISO 8601 timestamp of most recent mention

**Constraints**:
- Primary key: `id`
- Unique constraint on `canonical_name`
- `canonical_name` is case-normalized and consolidated from variants
- `categories` supports multi-label classification (empty array if uncategorized)

**Indexes**:
- `idx_benchmarks_name` on `canonical_name` (for lookup queries)
- `idx_benchmarks_last_seen` on `last_seen` (for extinction detection)

**Consolidation Rules**:
- Case variations: "MMLU" = "mmlu" = "Mmlu" → "MMLU"
- Separator variations: "GSM8K" = "GSM-8K" = "gsm8k" → "GSM8K"
- Different benchmarks: "MMLU-Pro" ≠ "MMLU" (kept separate)

---

### 3. Model-Benchmark Association

Links models to benchmarks with variant details and source tracking.

**Attributes**:
- `id` (INTEGER, PK, AUTOINCREMENT): Unique association identifier
- `model_id` (TEXT, FK → models.id, NOT NULL): Reference to model
- `benchmark_id` (INTEGER, FK → benchmarks.id, NOT NULL): Reference to benchmark
- `variant_details` (TEXT): JSON object with variant information
  - `shots`: Shot count (e.g., "0-shot", "5-shot", "few-shot", null)
  - `method`: Prompting method (e.g., "CoT", "PoT", "TIR", null)
  - `model_type`: Model variant (e.g., "base", "instruct", "chat", null)
  - Additional fields as needed (e.g., "language": "multilingual")
- `source_type` (TEXT): Document type (e.g., "model_card", "blog", "arxiv_paper", "github_pdf")
- `source_url` (TEXT): URL where benchmark was mentioned
- `recorded_at` (TEXT, NOT NULL): ISO 8601 timestamp when association was recorded

**Constraints**:
- Primary key: `id`
- Foreign keys: `model_id`, `benchmark_id`
- Unique constraint: `(model_id, benchmark_id, variant_details)` - allows same benchmark with different variants
- `variant_details` stored as JSON string
- `recorded_at` set to current timestamp on insertion

**Indexes**:
- `idx_model_benchmarks_model` on `model_id` (for model queries)
- `idx_model_benchmarks_benchmark` on `benchmark_id` (for benchmark queries)

**Multi-Variant Support**:
- Same model can have multiple associations for same benchmark with different variants
- Example: Model X with "MMLU 5-shot" (from paper) AND "MMLU 0-shot" (from blog) → 2 separate associations

**Variant Details Examples**:
```json
{"shots": "5-shot", "method": null, "model_type": "base"}
{"shots": "8-shot", "method": "CoT", "model_type": "instruct"}
{"shots": "0-shot", "method": null, "model_type": "instruct"}
```

---

### 4. Source Document

Tracks documentation sources for change detection (metadata only, no content storage).

**Attributes**:
- `id` (INTEGER, PK, AUTOINCREMENT): Unique document identifier
- `model_id` (TEXT, FK → models.id, NOT NULL): Reference to model
- `doc_type` (TEXT, NOT NULL): Document type (e.g., "model_card", "blog", "arxiv_paper", "github_pdf")
- `url` (TEXT, NOT NULL): Document URL
- `content_hash` (TEXT, NOT NULL): SHA256 hash of extracted content
- `extraction_failed` (BOOLEAN, DEFAULT 0): Flag for failed extraction attempts
- `last_fetched` (TEXT, NOT NULL): ISO 8601 timestamp of last fetch

**Constraints**:
- Primary key: `id`
- Foreign key: `model_id`
- Unique constraint: `(model_id, doc_type, url)`
- `content_hash` computed from extracted text (post-truncation if applicable)
- `extraction_failed` prevents infinite retries on broken documents

**Indexes**:
- `idx_documents_model` on `model_id` (for model queries)
- `idx_documents_hash` on `content_hash` (for change detection)

**Change Detection Workflow**:
1. Fetch document and extract text
2. Compute SHA256 hash of extracted content
3. Compare with stored hash for `(model_id, url)`
4. If hash unchanged → skip extraction (use cached benchmarks)
5. If hash changed or new → run AI extraction, update hash
6. If extraction fails → set `extraction_failed=true`, cache hash to prevent retries

---

### 5. Temporal Snapshot

Represents the state of benchmark usage at a specific point in time.

**Attributes**:
- `id` (INTEGER, PK, AUTOINCREMENT): Unique snapshot identifier
- `timestamp` (TEXT, NOT NULL): ISO 8601 timestamp of snapshot creation
- `window_start` (TEXT, NOT NULL): ISO 8601 start of 12-month window
- `window_end` (TEXT, NOT NULL): ISO 8601 end of 12-month window (usually current date)
- `model_count` (INTEGER, NOT NULL): Total models in this time window
- `benchmark_count` (INTEGER, NOT NULL): Total unique benchmarks in this window
- `taxonomy_version` (TEXT): Reference to archived taxonomy file (e.g., "benchmark_taxonomy_20260403.md")
- `summary` (TEXT): JSON object with high-level metrics

**Constraints**:
- Primary key: `id`
- `window_end - window_start` = 12 months (rolling window)
- `summary` format: `{benchmark_id: {absolute: N, relative: X%}, ...}`

**Indexes**:
- `idx_snapshots_timestamp` on `timestamp` (for temporal queries)

**Creation Trigger**:
- Created after successful pipeline completion in `snapshot` or `full` mode
- One snapshot per run

**Window Calculation**:
```
window_end = current_date
window_start = current_date - 12 months
model_count = COUNT(models WHERE release_date BETWEEN window_start AND window_end)
```

---

### 6. Benchmark Mention

Denormalized table tracking benchmark usage within a specific snapshot (for fast temporal queries).

**Attributes**:
- `id` (INTEGER, PK, AUTOINCREMENT): Unique mention record identifier
- `snapshot_id` (INTEGER, FK → snapshots.id, NOT NULL): Reference to snapshot
- `benchmark_id` (INTEGER, FK → benchmarks.id, NOT NULL): Reference to benchmark
- `absolute_mentions` (INTEGER, NOT NULL): Count of models using this benchmark
- `relative_frequency` (REAL, NOT NULL): mentions / total_models_in_window (as decimal, e.g., 0.30 for 30%)
- `first_seen` (TEXT, NOT NULL): When benchmark was first discovered (copied from benchmarks table)
- `last_seen` (TEXT, NOT NULL): Most recent model using this benchmark in window
- `status` (TEXT, NOT NULL): Benchmark status ("emerging", "active", "almost_extinct")

**Constraints**:
- Primary key: `id`
- Foreign keys: `snapshot_id`, `benchmark_id`
- Unique constraint: `(snapshot_id, benchmark_id)`
- `status` values:
  - "emerging": `first_seen >= current_date - 3 months`
  - "almost_extinct": `last_seen <= current_date - 9 months`
  - "active": All others

**Indexes**:
- `idx_benchmark_mentions_snapshot` on `snapshot_id` (for snapshot queries)
- `idx_benchmark_mentions_benchmark` on `benchmark_id` (for benchmark history)
- `idx_benchmark_mentions_status` on `status` (for filtering by status)

**Calculation Logic**:
```python
for each benchmark in discovered_benchmarks:
    absolute_mentions = COUNT(DISTINCT model_id
                              FROM model_benchmarks mb
                              JOIN models m ON mb.model_id = m.id
                              WHERE mb.benchmark_id = benchmark_id
                              AND m.release_date BETWEEN window_start AND window_end)

    relative_frequency = absolute_mentions / model_count

    status = determine_status(benchmark.first_seen, benchmark.last_seen, current_date)
```

---

### 7. Category

Represents a benchmark classification category (managed via configuration).

**Attributes** (Logical, not a separate table):
- `name` (TEXT): Category name (e.g., "Math Reasoning", "Code Generation")
- `definition` (TEXT): Category description
- `examples` (TEXT ARRAY): Example benchmarks in this category

**Storage**:
- Defined in `categories.yaml` configuration file
- Stored as JSON array in `benchmarks.categories` field
- Auto-updated by taxonomy evolution but can be manually overridden

**Multi-label Support**:
- Benchmarks can belong to multiple categories
- Stored as JSON array: `["General Knowledge", "Language Understanding"]`

---

### 8. Lab

Represents an AI research organization being tracked (configuration-based, not a table).

**Attributes** (Logical, stored in labs.yaml):
- `name` (TEXT): Lab identifier (e.g., "Qwen", "meta-llama")
- `github_org` (TEXT): GitHub organization mapping (e.g., "QwenLM")
- `blog_url` (TEXT): Official blog URL pattern
- `discovery_config`: Filters and thresholds for this lab

**Usage**:
- Loaded from `labs.yaml` at runtime
- Used for model discovery filtering
- Determines source discovery patterns (GitHub, blogs)

---

## Relationships

```
┌─────────┐
│  Model  │
└────┬────┘
     │
     │ 1:N
     ├─────────────────┐
     │                 │
     ▼                 ▼
┌────────────┐   ┌───────────────┐
│  Document  │   │ Model-Bench   │
└────────────┘   └───────┬───────┘
                         │ N:1
                         ▼
                   ┌────────────┐
                   │ Benchmark  │
                   └─────┬──────┘
                         │ 1:N
                         ▼
                   ┌──────────────────┐
                   │ Benchmark Mention│
                   └─────────┬────────┘
                             │ N:1
                             ▼
                        ┌──────────┐
                        │ Snapshot │
                        └──────────┘
```

**Relationship Details**:

1. **Model → Document** (1:N): One model has multiple source documents
2. **Model → Model-Benchmark** (1:N): One model can be evaluated on multiple benchmarks
3. **Benchmark → Model-Benchmark** (1:N): One benchmark can be used by multiple models
4. **Model-Benchmark allows duplicates** with same `(model_id, benchmark_id)` but different `variant_details`
5. **Benchmark → Benchmark Mention** (1:N): One benchmark has mentions across multiple snapshots
6. **Snapshot → Benchmark Mention** (1:N): One snapshot contains mentions for all benchmarks in that time window

---

## Validation Rules

### Model Validation

1. `id` must be non-empty and follow HuggingFace format: `{org}/{model}`
2. `release_date` must be valid ISO 8601 timestamp
3. `tags` must be valid JSON array
4. `downloads` and `likes` must be non-negative integers
5. If `deleted_at` is set, model is excluded from "Trending Models" but kept in historical data

### Benchmark Validation

1. `canonical_name` must be non-empty after consolidation
2. `canonical_name` must be unique (case-sensitive after normalization)
3. `categories` must be valid JSON array (can be empty)
4. `first_seen` must be ≤ `last_seen`

### Model-Benchmark Association Validation

1. `model_id` must reference existing model
2. `benchmark_id` must reference existing benchmark
3. `variant_details` must be valid JSON (can be empty object `{}`)
4. `source_type` must be one of: "model_card", "blog", "arxiv_paper", "github_pdf", "github_readme"
5. `source_url` must be valid URL
6. Uniqueness enforced on `(model_id, benchmark_id, variant_details)` - same model/benchmark with different variants allowed

### Document Validation

1. `model_id` must reference existing model
2. `url` must be valid URL
3. `content_hash` must be 64-character hex string (SHA256)
4. `extraction_failed` must be boolean (0 or 1)
5. Uniqueness enforced on `(model_id, doc_type, url)`

### Snapshot Validation

1. `window_end - window_start` must equal 12 months
2. `model_count` must equal actual count of models in window
3. `benchmark_count` must equal actual count of unique benchmarks in window
4. `summary` must be valid JSON object

### Benchmark Mention Validation

1. `snapshot_id` must reference existing snapshot
2. `benchmark_id` must reference existing benchmark
3. `absolute_mentions` must be > 0 (only include benchmarks with at least 1 mention)
4. `relative_frequency` must be between 0 and 1 (inclusive)
5. `status` must be one of: "emerging", "active", "almost_extinct"
6. `first_seen` ≤ `last_seen`

---

## State Transitions

### Model Lifecycle

```
[Discovered] → [Active] → [Deleted]
     ↓            ↓
  first_seen  last_updated
               (every run)
```

1. **Discovered**: New model found, `first_seen` set
2. **Active**: Metadata updated regularly (`downloads`, `likes`)
3. **Deleted**: Model removed from HuggingFace, `deleted_at` set, excluded from trending but kept in history

### Benchmark Lifecycle

```
[Discovered] → [Active] → [Almost Extinct]
     ↓            ↓              ↓
  first_seen  last_seen    last_seen old
```

1. **Discovered**: New benchmark found, `first_seen` set
2. **Active**: Regularly mentioned in recent models, `last_seen` updated
3. **Almost Extinct**: No mentions in last 9 months (can become active again if re-mentioned)

### Document Lifecycle

```
[New] → [Unchanged] → [Changed] → [Unchanged] ...
  ↓         ↓            ↓
fetch   skip re-    re-extract
       extraction
```

1. **New**: Document fetched for first time, hash computed, benchmarks extracted
2. **Unchanged**: Hash matches cached hash, skip extraction
3. **Changed**: Hash differs from cache, re-extract benchmarks, update hash

---

## Performance Considerations

### Indexing Strategy

All foreign keys are indexed for join performance:
- `idx_model_benchmarks_model` speeds up queries like "all benchmarks for model X"
- `idx_model_benchmarks_benchmark` speeds up queries like "all models using benchmark Y"
- `idx_benchmark_mentions_snapshot` speeds up temporal queries
- `idx_benchmark_mentions_status` speeds up filtering by emerging/extinct status

### Denormalization Trade-offs

**Benchmark Mention Table**:
- **Pro**: Fast temporal queries without complex joins
- **Pro**: Snapshot isolation - historical data immutable
- **Con**: Redundant data (first_seen, last_seen copied from benchmarks table)
- **Justification**: Read-heavy workload for reporting, write-once per snapshot

### Query Optimization

**Common Queries**:
1. **Trending Models** (last 12 months):
   ```sql
   SELECT * FROM models
   WHERE release_date BETWEEN ? AND ?
   AND deleted_at IS NULL
   ORDER BY downloads DESC
   ```

2. **Most Common Benchmarks** (from latest snapshot):
   ```sql
   SELECT b.canonical_name, bm.absolute_mentions, bm.relative_frequency, bm.status
   FROM benchmark_mentions bm
   JOIN benchmarks b ON bm.benchmark_id = b.id
   WHERE bm.snapshot_id = ?
   ORDER BY bm.relative_frequency DESC
   ```

3. **Benchmark Temporal Trends** (across snapshots):
   ```sql
   SELECT s.timestamp, bm.absolute_mentions, bm.relative_frequency
   FROM benchmark_mentions bm
   JOIN snapshots s ON bm.snapshot_id = s.id
   WHERE bm.benchmark_id = ?
   ORDER BY s.timestamp DESC
   ```

---

## Data Integrity

### Referential Integrity

All foreign keys enforce cascading behavior:
- Deleting a model deletes associated documents and model-benchmark associations
- Deleting a benchmark deletes associated model-benchmark associations and benchmark mentions
- Deleting a snapshot deletes associated benchmark mentions

**However**: In practice, entities are never deleted, only marked (e.g., `deleted_at` for models).

### Transaction Boundaries

**Atomic Operations**:
1. Model discovery + metadata insert (per model)
2. Document fetch + hash update (per document)
3. Benchmark extraction + association insert (per document)
4. Snapshot creation + benchmark mention insert (per snapshot)

**Rollback Strategy**:
- Pipeline failures do not delete partial data
- Each model processed independently (failure on model X doesn't affect model Y)
- Snapshots created only after successful pipeline completion

---

## Schema Version

**Version**: 1.0
**Created**: 2026-04-03
**Compatibility**: SQLite 3.x (requires JSON functions for querying JSON fields)

**Migration Strategy**: Not applicable for initial version. Future schema changes will use migration scripts with version tracking.
