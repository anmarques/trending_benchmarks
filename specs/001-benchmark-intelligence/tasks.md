# Implementation Tasks: Benchmark Intelligence System

**Feature**: Benchmark Intelligence System  
**Branch**: feature/001-benchmark-intelligence-spec  
**Spec**: [spec.md](spec.md)  
**Plan**: [plan.md](plan.md)  
**Created**: 2026-04-06  
**Status**: Ready for Implementation

---

## Overview

This document breaks down the implementation into executable tasks organized by user story. The existing codebase (~7500 LOC) provides substantial functionality; these tasks focus on targeted enhancements to align with specification requirements.

**Total Tasks**: 120  
**Total Phases**: 7  
**Estimated Effort**: 56-72 hours

---

## Implementation Strategy

### MVP Scope
**User Story 1 only** - Delivers core value: trending benchmarks report with basic consolidation

### Delivery Order
1. **Phase 1**: Setup & Project Initialization
2. **Phase 2**: Foundational infrastructure (blocking all user stories)
3. **Phase 3**: User Story 1 - Trending benchmarks (MVP - ~50% of value)
4. **Phase 4**: User Story 2 - Temporal tracking (emerging/extinct classification)
5. **Phase 5**: User Story 3 - Extraction quality & observability
6. **Phase 6**: User Story 4 - Taxonomy evolution
7. **Phase 7**: Polish & cross-cutting concerns

### Independent Testing Criteria
Each user story phase includes clear acceptance criteria that can be validated without implementing subsequent stories.

---

## Dependency Graph

### Story Completion Order

```
Phase 2 (Foundation)
    ↓
Phase 3 (US1: Trending) ← MVP Delivery Point
    ↓
Phase 4 (US2: Temporal) ← Can run in parallel with Phase 5 ↓
Phase 5 (US3: Quality)  ← Can run in parallel with Phase 4
    ↓
Phase 6 (US4: Taxonomy)
    ↓
Phase 7 (Polish)
```

### Task Dependencies

- **No dependencies**: T001-T004 (setup can run in parallel)
- **Blocks US1-US4**: T005-T014 (foundational infrastructure)
- **Blocks all stories**: T015-T018 (pipeline stage utilities - foundational)
- **US1 completes before US2**: T019-T050 (pipeline implementation needed for temporal tracking)
- **Independent**: T051-T088 (US2, US3, US4 can run in parallel after US1)
- **Final**: T089-T120 (polish depends on all user stories)

---

## Parallel Execution Examples

### Phase 2 (Foundational)
```bash
# Database schema can be updated while implementing connection pooling
parallel ::: \
  "# Task T005: Update snapshots table schema" \
  "# Task T007: Create ConnectionPool class"
```

### Phase 3 (User Story 1)
```bash
# All 6 stage scripts can be developed in parallel by different developers
parallel ::: \
  "# Task T015: Implement filter_models.py" \
  "# Task T016: Implement find_docs.py" \
  "# Task T017: Implement parse_docs.py" \
  "# Task T018: Implement consolidate_benchmarks.py" \
  "# Task T019: Implement categorize_benchmarks.py" \
  "# Task T020: Implement report.py"
```

### Phase 7 (Polish)
```bash
# Ambient registration and documentation can proceed in parallel
parallel ::: \
  "# Task T058-T061: Ambient workflow definitions" \
  "# Task T062-T064: Documentation updates"
```

---

## Phase 1: Setup & Project Initialization

**Purpose**: Verify project structure and prepare for implementation

### Tasks

- [X] T001 [P] Check agents/benchmark_intelligence/ directory exists with __init__.py, tools/, and clients/ subdirectories
- [X] T002 [P] Check config.yaml exists at project root and contains 'labs' key with at least one lab configured
- [X] T003 [P] Create outputs/ directory for JSON stage outputs
- [X] T004 [P] Run import tests: verify 'from agents.benchmark_intelligence.tools import cache' and 'from agents.benchmark_intelligence.clients import factory' succeed

**Completion Criteria**: All tasks pass; project structure validated ✓ COMPLETE

---

## Phase 2: Foundational Infrastructure

**Purpose**: Implement blocking infrastructure needed by all user stories

**Dependencies**: Phase 1 complete

### Database Schema Updates

- [X] T005 Add window_start, window_end, taxonomy_version columns to snapshots table in agents/benchmark_intelligence/tools/cache.py
- [X] T006 Create benchmark_mentions table with schema from plan.md in agents/benchmark_intelligence/tools/cache.py
- [X] T007 Add migration logic to CacheManager.__init__ to handle existing databases in agents/benchmark_intelligence/tools/cache.py
- [X] T008 Update CacheManager.create_snapshot() to populate new snapshot fields in agents/benchmark_intelligence/tools/cache.py

### Connection Pooling

- [X] T009 Create ConnectionPool class with configurable pool size in agents/benchmark_intelligence/connection_pool.py
- [X] T010 Implement context manager __enter__ and __exit__ methods in agents/benchmark_intelligence/connection_pool.py
- [X] T011 Add automatic retry on SQLITE_BUSY with exponential backoff (max 3 attempts) in agents/benchmark_intelligence/connection_pool.py
- [X] T012 Replace direct sqlite3.connect() calls in cache.py with ConnectionPool usage in agents/benchmark_intelligence/tools/cache.py

### Concurrent Processing Framework

- [X] T013 Create ConcurrentModelProcessor class using asyncio in agents/benchmark_intelligence/concurrent_processor.py
- [X] T014 Implement work queue with ThreadPoolExecutor for 20+ concurrent workers in agents/benchmark_intelligence/concurrent_processor.py

### 6-Stage Pipeline Infrastructure

- [X] T015 Create stage_utils.py with find_latest_stage_output(stage_name) function in agents/benchmark_intelligence/stage_utils.py
- [X] T016 Create load_stage_json(filepath) with schema validation in agents/benchmark_intelligence/stage_utils.py
- [X] T017 Create save_stage_json(data, stage_name) with standardized schema in agents/benchmark_intelligence/stage_utils.py
- [X] T018 Define JSON schema constants for all 6 stages in agents/benchmark_intelligence/stage_utils.py

**Completion Criteria**: ✓ ALL COMPLETE
- Database schema includes all new tables/columns ✓
- Connection pool handles 20+ concurrent writers without SQLITE_BUSY errors ✓
- ConcurrentModelProcessor can process work items in parallel ✓
- Stage utilities can save/load JSON with validation ✓

**Independent Test**: Create 20 threads that write to database concurrently using ConnectionPool; verify no data loss or corruption

---

## Phase 3: User Story 1 - Discover Trending Benchmarks [P1]

**Purpose**: Deliver MVP - ranked list of benchmarks by usage frequency

**User Story**: As an AI researcher, I want to see which benchmarks are most commonly used across recent AI models, so I can understand current evaluation standards.

**Dependencies**: Phase 2 complete

### Stage 1: Model Filtering

- [X] T019 [P] [US1] Create filter_models.py with run(config_path) function in agents/benchmark_intelligence/filter_models.py
- [X] T020 [P] [US1] Wrap discover_trending_models() from tools/discover_models.py in filter_models.run()
- [X] T021 [P] [US1] Add __main__ block with argparse for --config argument in agents/benchmark_intelligence/filter_models.py
- [X] T022 [P] [US1] Output JSON with stage schema to outputs/filter_models_<timestamp>.json in agents/benchmark_intelligence/filter_models.py

### Stage 2: Document Finding

- [X] T023 [P] [US1] Create find_docs.py with run(models_json) function in agents/benchmark_intelligence/find_docs.py
- [X] T024 [P] [US1] Wrap fetch_documentation() from tools/fetch_docs.py with hash checking in find_docs.run()
- [X] T025 [P] [US1] Add __main__ block with argparse for --input (auto-find if not provided) in agents/benchmark_intelligence/find_docs.py
- [X] T026 [P] [US1] Output JSON with document URLs per model to outputs/find_documents_<timestamp>.json in agents/benchmark_intelligence/find_docs.py

### Stage 3: Document Parsing

- [X] T027 [P] [US1] Create parse_docs.py with async run(docs_json, concurrency) function in agents/benchmark_intelligence/parse_docs.py
- [X] T028 [P] [US1] Integrate ConcurrentModelProcessor for parallel extraction in parse_docs.run()
- [X] T029 [P] [US1] Wrap extract_benchmarks() from tools/extract_benchmarks.py for each document in agents/benchmark_intelligence/parse_docs.py
- [X] T030 [P] [US1] Add __main__ block with argparse for --input and --concurrency in agents/benchmark_intelligence/parse_docs.py
- [X] T031 [P] [US1] Write extracted benchmarks to database via cache.py in agents/benchmark_intelligence/parse_docs.py
- [X] T032 [P] [US1] Output JSON with benchmark extractions to outputs/parse_documents_<timestamp>.json in agents/benchmark_intelligence/parse_docs.py

### Stage 4: Name Consolidation

- [ ] T033 [P] [US1] Create consolidate_benchmarks.py with run(source) function in agents/benchmark_intelligence/consolidate_benchmarks.py
- [ ] T034 [P] [US1] Wrap consolidate_benchmarks() from tools/consolidate.py with DB or JSON input in consolidate_benchmarks.run()
- [ ] T035 [P] [US1] Add __main__ block with argparse for --input or --from-db in agents/benchmark_intelligence/consolidate_benchmarks.py
- [ ] T036 [P] [US1] Output JSON with canonical benchmark names to outputs/consolidate_names_<timestamp>.json in agents/benchmark_intelligence/consolidate_benchmarks.py

### Stage 5: Categorization (Basic)

- [ ] T037 [P] [US1] Create categorize_benchmarks.py with run(source) function in agents/benchmark_intelligence/categorize_benchmarks.py
- [ ] T038 [P] [US1] Wrap classify_benchmarks_batch() from tools/classify.py in categorize_benchmarks.run()
- [ ] T039 [P] [US1] Add __main__ block with argparse for --input or --from-db in agents/benchmark_intelligence/categorize_benchmarks.py
- [ ] T040 [P] [US1] Output JSON with categorized benchmarks to outputs/categorize_benchmarks_<timestamp>.json in agents/benchmark_intelligence/categorize_benchmarks.py

### Stage 6: Reporting (Basic)

- [ ] T041 [P] [US1] Create report.py with run(snapshot_id) function in agents/benchmark_intelligence/report.py
- [ ] T042 [P] [US1] Generate trending benchmarks section using ReportGenerator from tools/reporting.py
- [ ] T043 [P] [US1] Add __main__ block with argparse for --snapshot-id (auto-find latest if not provided) in agents/benchmark_intelligence/report.py
- [ ] T044 [P] [US1] Write Markdown report to reports/report_<timestamp>.md in agents/benchmark_intelligence/report.py
- [ ] T045 [P] [US1] Output JSON metadata with report path to outputs/report_metadata_<timestamp>.json in agents/benchmark_intelligence/report.py

### Pipeline Orchestrator

- [ ] T046 [US1] Create generate.py to orchestrate all 6 stages sequentially in agents/benchmark_intelligence/generate.py
- [ ] T047 [US1] Import and call all 6 stage run() functions in sequence in agents/benchmark_intelligence/generate.py
- [ ] T048 [US1] Pass output from each stage as input to next stage in agents/benchmark_intelligence/generate.py
- [ ] T049 [US1] Add __main__ block for full pipeline execution in agents/benchmark_intelligence/generate.py
- [ ] T050 [US1] Handle errors gracefully and report which stage failed in agents/benchmark_intelligence/generate.py

**Completion Criteria**:
- All 6 stage scripts are executable individually via `python -m benchmark_intelligence.<stage>`
- Full pipeline executable via `python -m benchmark_intelligence.generate`
- Report shows ranked list of benchmarks with usage counts and percentages
- All JSON outputs match standardized schema

**Independent Test**:
1. Run full pipeline: `python -m benchmark_intelligence.generate`
2. Verify 6 JSON files created in outputs/ with correct schema
3. Verify report.md generated with trending benchmarks section
4. Verify top 10 benchmarks have usage counts and percentages
5. Run individual stage: `python -m benchmark_intelligence.parse_docs --input outputs/find_documents_*.json --concurrency 30`
6. Verify stage completes and outputs valid JSON

---

## Phase 4: User Story 2 - Emerging & Declining Benchmarks [P1]

**Purpose**: Identify temporal trends - which benchmarks are gaining or losing popularity

**User Story**: As an AI researcher tracking evaluation trends, I want to identify which benchmarks are newly emerging or becoming obsolete, so I can stay ahead of trends.

**Dependencies**: Phase 3 complete (User Story 1 working)

### 12-Month Rolling Window Implementation

- [ ] T051 [US2] Add create_snapshot_with_window(window_months=12) method to CacheManager in agents/benchmark_intelligence/tools/cache.py
- [ ] T052 [US2] Calculate window_start and window_end (current_date - 12 months to current_date) in agents/benchmark_intelligence/tools/cache.py
- [ ] T053 [US2] Query models in window by release_date in agents/benchmark_intelligence/tools/cache.py
- [ ] T054 [US2] Compute benchmark statistics (absolute_mentions, relative_frequency) via SQL aggregation in agents/benchmark_intelligence/tools/cache.py
- [ ] T055 [US2] Populate benchmark_mentions table with denormalized stats in agents/benchmark_intelligence/tools/cache.py

### Status Classification

- [ ] T056 [US2] Implement classify_benchmark_status(first_seen, last_seen, window_end) function in agents/benchmark_intelligence/tools/cache.py
- [ ] T057 [US2] Apply classification rules: emerging (≤3 months), almost_extinct (≥9 months), active (all others) in agents/benchmark_intelligence/tools/cache.py
- [ ] T058 [US2] Store status in benchmark_mentions.status column in agents/benchmark_intelligence/tools/cache.py

### Report Enhancement

- [ ] T059 [US2] Add generate_emerging_benchmarks_section() to ReportGenerator in agents/benchmark_intelligence/tools/reporting.py
- [ ] T060 [US2] Add generate_almost_extinct_section() to ReportGenerator in agents/benchmark_intelligence/tools/reporting.py
- [ ] T061 [US2] Query benchmark_mentions for status-based filtering in agents/benchmark_intelligence/tools/reporting.py
- [ ] T062 [US2] Update report.py to include emerging and almost-extinct sections in agents/benchmark_intelligence/report.py
- [ ] T062A [US2] Verify report clearly indicates actual time window when <12 months data available in agents/benchmark_intelligence/report.py

**Completion Criteria**:
- Snapshots include 12-month rolling window boundaries
- Benchmark status correctly classified based on first_seen/last_seen
- Report includes emerging and almost-extinct sections with visual indicators
- Report clearly shows actual window (e.g., "6-month window") when <12 months data available

**Independent Test**:
1. Create test data with models spanning 15 months
2. Include benchmarks with known first/last seen dates
3. Run pipeline and verify snapshot has correct window_start/window_end
4. Test first initialization: clear database, run with only 6 months of data, verify report states "6-month window (2025-10-06 to 2026-04-06)" not "12-month window"
5. Verify benchmarks first seen ≤3 months ago are marked "Emerging"
6. Verify benchmarks last seen ≥9 months ago are marked "Almost Extinct"
7. Verify report displays both sections correctly

---

## Phase 5: User Story 3 - Multi-Source Extraction Quality [P1]

**Purpose**: Ensure comprehensive extraction with visibility into quality and errors

**User Story**: As a user, I want confidence that benchmark data comes from all available sources, so I get complete and accurate coverage.

**Dependencies**: Phase 3 complete (can run in parallel with Phase 4)

### Error Aggregation

- [ ] T063 [P] [US3] Create ErrorAggregator class with type-based bucketing in agents/benchmark_intelligence/error_aggregator.py
- [ ] T064 [P] [US3] Implement add_error(error_type, model_id, details) method in agents/benchmark_intelligence/error_aggregator.py
- [ ] T065 [P] [US3] Implement get_summary() to return dict of error_type → {count, samples} in agents/benchmark_intelligence/error_aggregator.py
- [ ] T066 [US3] Integrate ErrorAggregator into parse_docs.py for extraction errors in agents/benchmark_intelligence/parse_docs.py
- [ ] T067 [US3] Add error aggregation to find_docs.py for fetch errors in agents/benchmark_intelligence/find_docs.py
- [ ] T068 [US3] Include error summary in JSON outputs for stages 2 and 3 in agents/benchmark_intelligence/parse_docs.py and find_docs.py

### Real-Time Progress Tracking

- [ ] T069 [P] [US3] Create ProgressTracker class with thread-safe counters in agents/benchmark_intelligence/progress_tracker.py
- [ ] T070 [P] [US3] Add increment methods: models_processed(), benchmarks_extracted(), errors_encountered() in agents/benchmark_intelligence/progress_tracker.py
- [ ] T071 [P] [US3] Implement periodic console updates (every 5 seconds) with live statistics in agents/benchmark_intelligence/progress_tracker.py
- [ ] T072 [US3] Integrate ProgressTracker into parse_docs.py in agents/benchmark_intelligence/parse_docs.py
- [ ] T073 [US3] Display progress during pipeline execution in generate.py in agents/benchmark_intelligence/generate.py

### Multi-Source Verification

- [ ] T074 [US3] Review fetch_docs.py code and confirm all 4 source types (model_card, arxiv, blog, github) are attempted; add missing sources if needed in agents/benchmark_intelligence/tools/fetch_docs.py
- [ ] T075 [US3] Review extract_benchmarks.py for vision AI calls (Claude with images); test with sample chart image and verify benchmark extraction works in agents/benchmark_intelligence/tools/extract_benchmarks.py
- [ ] T076 [US3] Add source_type tagging to extracted benchmarks in agents/benchmark_intelligence/tools/extract_benchmarks.py
- [ ] T076A [US3] Handle models with no benchmarks found - log count in report without blocking pipeline in agents/benchmark_intelligence/report.py

**Completion Criteria**:
- Errors aggregated by type with counts displayed at completion
- Real-time progress shows models processed, benchmarks extracted, errors encountered
- Multi-source extraction verified for all document types
- Models with no benchmarks logged in report with count (e.g., "N models with no benchmarks found")

**Independent Test**:
1. Run pipeline with a mix of models (some with missing sources)
2. Verify progress updates appear every 5 seconds during execution
3. Verify error summary at end shows counts by type (e.g., "15 arXiv fetch failures")
4. Select a known model with benchmarks in multiple sources
5. Verify extraction tagged each benchmark with correct source_type
6. Verify vision AI extracted benchmarks from chart images

---

## Phase 6: User Story 4 - Taxonomy Evolution & Categorization [P2]

**Purpose**: Structured benchmark categorization with intelligent disambiguation

**User Story**: As a researcher, I want to see benchmarks categorized by type, so I can understand coverage across capability dimensions.

**Dependencies**: Phase 3 complete (can run in parallel with Phase 4 and 5)

### Fuzzy Matching Threshold

- [ ] T077 [P] [US4] Add FUZZY_MATCH_THRESHOLD = 0.90 constant in agents/benchmark_intelligence/tools/consolidate.py
- [ ] T078 [P] [US4] Review consolidate_benchmarks() code to confirm FUZZY_MATCH_THRESHOLD constant is used in similarity comparisons; update if hardcoded in agents/benchmark_intelligence/tools/consolidate.py
- [ ] T079 [P] [US4] Add configuration option for threshold in config.yaml

### Web Search Disambiguation

- [ ] T080 [US4] Implement trigger_web_search(benchmark1, benchmark2) when similarity <90% in agents/benchmark_intelligence/tools/consolidate.py
- [ ] T081 [US4] Integrate google_search.py to fetch top 3 results for "{benchmark1} vs {benchmark2}" in agents/benchmark_intelligence/tools/consolidate.py
- [ ] T082 [US4] Use Claude to analyze search results and determine same/different in agents/benchmark_intelligence/tools/consolidate.py
- [ ] T083 [US4] Cache disambiguation decisions to avoid repeated searches in agents/benchmark_intelligence/tools/consolidate.py
- [ ] T084 [US4] Add web_search_used flag to consolidation JSON output in agents/benchmark_intelligence/consolidate_benchmarks.py

### Taxonomy Evolution

- [ ] T085 [US4] Review taxonomy_manager.py code to confirm new categories can be added dynamically; test by introducing novel benchmark type in agents/benchmark_intelligence/tools/taxonomy_manager.py
- [ ] T086 [US4] Add taxonomy_version tracking to snapshots in agents/benchmark_intelligence/tools/cache.py
- [ ] T087 [US4] Implement taxonomy_changes section in categorization JSON output in agents/benchmark_intelligence/categorize_benchmarks.py
- [ ] T088 [US4] Support manual category overrides via config.yaml in agents/benchmark_intelligence/tools/taxonomy_manager.py

**Completion Criteria**:
- Fuzzy matching uses 90% threshold with configurable override
- Web search triggers for ambiguous benchmark pairs (<90% similarity)
- Taxonomy automatically evolves with new categories
- Manual overrides respected from configuration

**Independent Test**:
1. Create test data with benchmark pairs at 85%, 90%, and 95% similarity
2. Verify 85% pair triggers web search
3. Verify 90%+ pairs do not trigger web search (consolidated immediately)
4. Test known ambiguous pair (MMLU vs MMLU-Pro)
5. Verify web search correctly identifies them as different benchmarks
6. Introduce a novel benchmark type (e.g., "Audio Understanding")
7. Verify taxonomy evolves to add new category
8. Add manual override in config.yaml
9. Verify override takes precedence over AI classification

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Production-ready features - rate limiting, testing, integration, documentation

**Dependencies**: All user stories complete (Phase 3-6)

### API Rate Limiting

- [ ] T089 [P] Create RateLimiter class with token bucket algorithm in agents/benchmark_intelligence/rate_limiter.py
- [ ] T090 [P] Implement request queue with exponential backoff on 429 errors in agents/benchmark_intelligence/rate_limiter.py
- [ ] T091 [P] Configure per-API limits (HuggingFace, Anthropic, arXiv) in config.yaml
- [ ] T092 Integrate RateLimiter into concurrent_processor.py in agents/benchmark_intelligence/concurrent_processor.py
- [ ] T093 Add rate limit error handling to API clients in agents/benchmark_intelligence/clients/

### Testing

- [ ] T094 [P] Create tests/ directory structure if not exists
- [ ] T095 [P] Add unit tests for ConnectionPool in tests/test_connection_pool.py
- [ ] T096 [P] Add unit tests for ErrorAggregator in tests/test_error_aggregator.py
- [ ] T097 [P] Add unit tests for ProgressTracker in tests/test_progress_tracker.py
- [ ] T098 [P] Add unit tests for RateLimiter in tests/test_rate_limiter.py
- [ ] T099 [P] Add integration test for concurrent processing (20+ workers) in tests/test_concurrent_processing.py
- [ ] T100 [P] Add integration test for full pipeline execution in tests/test_pipeline.py
- [ ] T101 [P] Add test for 12-month window calculation in tests/test_temporal_tracking.py
- [ ] T102 [P] Add test for status classification (emerging/extinct) in tests/test_temporal_tracking.py
- [ ] T103 Update existing ground truth validation tests in tests/
- [ ] T103A [P] Add test for pipeline resumability after interruption in tests/test_resumability.py
- [ ] T103B [P] Run ground truth validation and verify ≥95% extraction accuracy meets SC-002 in tests/test_ground_truth.py
- [ ] T103C [P] Run pytest-cov and verify ≥80% coverage for new modules (connection_pool, error_aggregator, progress_tracker, rate_limiter, concurrent_processor) in tests/

### Ambient Workflow Registration

- [ ] T104 Add workflow definition for filter_models in .ambient/ambient.json
- [ ] T105 Add workflow definition for find_docs in .ambient/ambient.json
- [ ] T106 Add workflow definition for parse_docs with --concurrency argument in .ambient/ambient.json
- [ ] T107 Add workflow definition for consolidate_benchmarks with --from-db flag in .ambient/ambient.json
- [ ] T108 Add workflow definition for categorize_benchmarks in .ambient/ambient.json
- [ ] T109 Add workflow definition for report in .ambient/ambient.json
- [ ] T110 Add workflow definition for generate (full pipeline) in .ambient/ambient.json
- [ ] T111 Verify /benchmark_intelligence.filter_models works in Ambient
- [ ] T112 Verify argument passing: /benchmark_intelligence.parse_docs --concurrency 30

### Documentation

- [ ] T113 [P] Update project root README.md with new execution modes (6 stages + generate) in README.md
- [ ] T114 [P] Document both Python and Ambient execution paths in README.md
- [ ] T115 [P] Document concurrency settings (default 20) in README.md
- [ ] T116 [P] Document JSON output locations and schemas in README.md
- [ ] T117 [P] Add troubleshooting section for common concurrency issues in README.md
- [ ] T118 [P] Update agents/benchmark_intelligence/README.md with stage details
- [ ] T119 [P] Add examples of individual stage execution in agents/benchmark_intelligence/README.md
- [ ] T120 [P] Document configuration options in agents/benchmark_intelligence/README.md

**Completion Criteria**:
- API rate limiting prevents 429 errors with automatic backoff
- Test coverage ≥80% for new code (verified via pytest-cov)
- Ground truth validation confirms ≥95% extraction accuracy (SC-002)
- Pipeline resumability validated (hash cache prevents re-processing)
- All 7 Ambient workflows registered and functional
- Documentation covers all execution modes with examples

**Independent Test**:
1. Simulate high API usage to trigger rate limiting
2. Verify requests queued and retried with backoff (no 429 errors)
3. Run all unit tests: `pytest tests/ -v`
4. Run coverage analysis: `pytest tests/ --cov=agents.benchmark_intelligence --cov-report=term-missing` and verify ≥80% coverage on new modules
5. Run ground truth validation and confirm ≥95% extraction accuracy
6. Test resumability: interrupt pipeline mid-execution, restart, verify hash cache prevents re-processing unchanged documents
7. Run full pipeline via Ambient: `/benchmark_intelligence.generate`
8. Run individual stage via Ambient with args: `/benchmark_intelligence.parse_docs --concurrency 30`
9. Review documentation and verify all examples work as documented

---

## Task Summary

### By Phase

| Phase | Task Range | Count | Effort (hrs) |
|-------|-----------|-------|--------------|
| Phase 1: Setup | T001-T004 | 4 | 1 |
| Phase 2: Foundation | T005-T018 | 14 | 12-15 |
| Phase 3: US1 (MVP) | T019-T050 | 32 | 15-20 |
| Phase 4: US2 | T051-T062A | 13 | 6-9 |
| Phase 5: US3 | T063-T076A | 15 | 7-10 |
| Phase 6: US4 | T077-T088 | 12 | 5-7 |
| Phase 7: Polish | T089-T120, T103A-C | 35 | 11-14 |
| **Total** | **T001-T120 + 5 new** | **125** | **57-76** |

### By Priority

| Priority | Description | Task Count |
|----------|-------------|------------|
| P0 | Foundational (blocks all stories) | 14 |
| P1 | User Stories 1-3 | 60 |
| P2 | User Story 4 | 12 |
| P3 | Polish & Documentation | 39 |

### Parallelization Opportunities

**Phase 2** (14 tasks): 
- T001-T004 (setup) can run in parallel (4 tasks)
- T005-T008 (schema) sequential
- T009-T012 (pooling) can overlap with T013-T014 (concurrent framework)

**Phase 3** (32 tasks):
- T019-T022, T023-T026, T027-T032, T033-T036, T037-T040, T041-T045 (6 stage groups) can run in parallel (~18 tasks)
- T046-T050 (orchestrator) depends on all stages

**Phase 7** (32 tasks):
- T089-T093 (rate limiting) independent (5 tasks)
- T094-T103 (tests) all parallel (10 tasks)
- T104-T112 (Ambient) sequential (9 tasks)
- T113-T120 (docs) all parallel (8 tasks)

**Total parallel capacity**: ~45 tasks can run concurrently with proper coordination

---

## Next Steps

1. **Review this task breakdown** with stakeholders
2. **Begin implementation** with Phase 1 (setup verification)
3. **Proceed to Phase 2** (foundational infrastructure - critical path)
4. **Deliver MVP** after Phase 3 (User Story 1 complete)
5. **Iterate** through remaining user stories (Phase 4-6)
6. **Polish** with Phase 7 (production readiness)

**Estimated Timeline** (single developer, sequential):
- Week 1: Phase 1-2 (setup + foundation)
- Week 2-3: Phase 3 (US1 - MVP delivery)
- Week 4: Phase 4 + 5 (US2 + US3)
- Week 5: Phase 6 + 7 (US4 + polish)

**Estimated Timeline** (team of 3, parallel):
- Week 1: Phase 1-2 (foundation - shared)
- Week 2: Phase 3 (US1 - split stage development)
- Week 3: Phase 4, 5, 6 (all 3 user stories in parallel)
- Week 4: Phase 7 (polish - shared)
