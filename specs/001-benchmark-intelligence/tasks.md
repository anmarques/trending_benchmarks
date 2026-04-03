# Tasks: Benchmark Intelligence System

**Input**: Design documents from `/specs/001-benchmark-intelligence/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md, implementation-status.md

**Current Status**: ~75% Complete (~6,700 lines implemented)
**Remaining Work**: Critical gaps in CLI modes, temporal tracking, testing, and configuration

**Organization**: Tasks focus on completing the remaining 25% to reach 100% specification compliance

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup & Configuration (Infrastructure Completion)

**Purpose**: Complete missing configuration files and project setup

**Status**: Infrastructure 95% complete, only configuration files missing

- [ ] T001 [P] Create categories.yaml at project root with initial category definitions from ground truth
- [ ] T002 [P] Create archive/ directory at project root for historical taxonomy versions
- [ ] T003 Generate initial benchmark_taxonomy.md at project root using taxonomy_manager.py

**Checkpoint**: Configuration infrastructure complete

---

## Phase 2: Foundational (Database Schema Enhancements)

**Purpose**: Complete database schema to support temporal tracking

**⚠️ CRITICAL**: These schema changes MUST be complete before User Story 2 (temporal tracking) can function

- [ ] T004 Add missing columns to snapshots table in agents/benchmark_intelligence/tools/cache.py (window_start, window_end, taxonomy_version)
- [ ] T005 Create benchmark_mentions table with full schema in agents/benchmark_intelligence/tools/cache.py
- [ ] T006 Add benchmark_mentions indexes in agents/benchmark_intelligence/tools/cache.py (snapshot_id, benchmark_id, status)
- [ ] T007 [P] Implement add_snapshot method enhancement in agents/benchmark_intelligence/tools/cache.py to support new columns
- [ ] T008 [P] Implement add_benchmark_mention method in agents/benchmark_intelligence/tools/cache.py
- [ ] T009 [P] Implement get_models_in_date_range method in agents/benchmark_intelligence/tools/cache.py for 12-month window queries
- [ ] T010 [P] Implement get_benchmark_mentions_for_snapshot method in agents/benchmark_intelligence/tools/cache.py
- [ ] T011 Implement determine_benchmark_status method in agents/benchmark_intelligence/tools/cache.py (emerging/active/extinct logic)

**Checkpoint**: Database schema complete - temporal tracking ready

---

## Phase 3: CLI Mode Support (Affects All User Stories)

**Purpose**: Enable three execution modes (snapshot/report/full) as specified in contracts/cli-interface.md

**⚠️ HIGH PRIORITY**: Required for proper system operation per FR-034

- [ ] T012 Add argparse configuration in agents/benchmark_intelligence/main.py (mode, verbose, quiet, version, help)
- [ ] T013 Implement parse_args function in agents/benchmark_intelligence/main.py
- [ ] T014 [P] Create run_snapshot_only method in BenchmarkIntelligenceAgent class in agents/benchmark_intelligence/main.py
- [ ] T015 [P] Create run_report_only method in BenchmarkIntelligenceAgent class in agents/benchmark_intelligence/main.py
- [ ] T016 [P] Create run_full_pipeline method in BenchmarkIntelligenceAgent class in agents/benchmark_intelligence/main.py
- [ ] T017 Implement main() function with mode routing and exit codes (0/1/2) in agents/benchmark_intelligence/main.py
- [ ] T018 Add version output handler in agents/benchmark_intelligence/main.py
- [ ] T019 Add NoSnapshotsError exception class in agents/benchmark_intelligence/main.py for exit code 2
- [ ] T020 Update progress reporting to use symbols consistently (✓ ✗ ↻ ⊕) in agents/benchmark_intelligence/main.py

**Checkpoint**: CLI modes functional - all execution modes available

---

## Phase 4: User Story 1 - Discover Current Benchmark Landscape (Priority: P1) 🎯 MVP ENHANCEMENTS

**Goal**: Complete remaining 10% - enhance reporting with all 7 sections

**Status**: Core functionality 90% complete (discovery, extraction, consolidation working)

**Independent Test**: Run system once and verify comprehensive benchmark list with accurate counts in all 7 report sections

### Implementation for User Story 1

- [ ] T021 [US1] Enhance Executive Summary section in agents/benchmark_intelligence/reporting.py with variant statistics and benchmark status distribution
- [ ] T022 [US1] Update Trending Models section in agents/benchmark_intelligence/reporting.py to show ALL models (no arbitrary limits)
- [ ] T023 [US1] Enhance Most Common Benchmarks section in agents/benchmark_intelligence/reporting.py with categories and status indicators
- [ ] T024 [US1] Update Category Distribution section in agents/benchmark_intelligence/reporting.py with taxonomy change notes

**Checkpoint**: US1 complete with enhanced reporting - MVP functional

---

## Phase 5: User Story 2 - Track Benchmark Trends Over Time (Priority: P2)

**Goal**: Complete remaining 60% - implement full temporal tracking with 12-month rolling windows

**Status**: Core infrastructure 40% complete (snapshot table exists, temporal logic missing)

**Independent Test**: Run system multiple times and verify historical trends accurately captured in reports

**⚠️ MAJOR GAP**: This is the largest remaining work item (4-6 hours estimated)

### Implementation for User Story 2

- [ ] T025 [US2] Implement create_temporal_snapshot method in agents/benchmark_intelligence/tools/cache.py with 12-month window calculation
- [ ] T026 [US2] Implement count_benchmark_mentions_in_window method in agents/benchmark_intelligence/tools/cache.py
- [ ] T027 [US2] Implement calculate_relative_frequency method in agents/benchmark_intelligence/tools/cache.py
- [ ] T028 [US2] Add snapshot creation call in run_snapshot_only and run_full_pipeline methods in agents/benchmark_intelligence/main.py
- [ ] T029 [US2] Implement Emerging Benchmarks section in agents/benchmark_intelligence/reporting.py (first_seen ≤ 3 months)
- [ ] T030 [US2] Implement Almost Extinct section in agents/benchmark_intelligence/reporting.py (last_seen ≥ 9 months)
- [ ] T031 [US2] Implement Temporal Trends section in agents/benchmark_intelligence/reporting.py with historical comparison
- [ ] T032 [US2] Add relative frequency display to Most Common Benchmarks section in agents/benchmark_intelligence/reporting.py
- [ ] T033 [US2] Implement get_snapshot_history method in agents/benchmark_intelligence/tools/cache.py for trend visualization
- [ ] T034 [US2] Update report generation to query latest snapshot in agents/benchmark_intelligence/reporting.py

**Checkpoint**: US2 complete - full temporal tracking operational with emerging/extinct detection

---

## Phase 6: User Story 3 - Explore Models by Lab and Popularity (Priority: P3)

**Goal**: Verify and enhance remaining 5% - ensure lab filtering and popularity metrics working correctly

**Status**: Core functionality 95% complete (labs filtering works, lab-specific insights exist)

**Independent Test**: Query for models from specific lab and verify all qualifying models discovered and ranked

### Implementation for User Story 3

- [ ] T035 [US3] Verify lab filtering logic in agents/benchmark_intelligence/tools/discover_models.py matches FR-001
- [ ] T036 [US3] Enhance Lab-Specific Insights section in agents/benchmark_intelligence/reporting.py with all metrics from acceptance scenarios
- [ ] T037 [US3] Add benchmark diversity score calculation in agents/benchmark_intelligence/reporting.py
- [ ] T038 [US3] Verify metadata update logic in agents/benchmark_intelligence/tools/cache.py updates downloads/likes on every run

**Checkpoint**: US3 complete - lab filtering and popularity metrics verified

---

## Phase 7: User Story 4 - Understand Benchmark Categorization (Priority: P4)

**Goal**: Verify and enhance remaining 5% - ensure taxonomy evolution working correctly

**Status**: Core functionality 95% complete (classification and taxonomy manager complete)

**Independent Test**: Verify all discovered benchmarks classified into logical categories and taxonomy evolves

### Implementation for User Story 4

- [ ] T039 [US4] Verify taxonomy evolution logic in agents/benchmark_intelligence/tools/taxonomy_manager.py
- [ ] T040 [US4] Verify taxonomy archiving in agents/benchmark_intelligence/tools/taxonomy_manager.py creates archive files
- [ ] T041 [US4] Add manual category override support from categories.yaml in agents/benchmark_intelligence/tools/classify.py
- [ ] T042 [US4] Verify Category Distribution section in agents/benchmark_intelligence/reporting.py shows taxonomy update notes

**Checkpoint**: US4 complete - taxonomy evolution and categorization verified

---

## Phase 8: User Story 5 - Analyze Lab Benchmark Preferences (Priority: P5)

**Goal**: Verify remaining 10% - ensure lab preference analysis complete

**Status**: Core functionality 90% complete (lab insights in reporting)

**Independent Test**: Compare benchmark usage across labs and verify lab-specific preferences identified

### Implementation for User Story 5

- [ ] T043 [US5] Enhance Lab-Specific Insights section in agents/benchmark_intelligence/reporting.py with top 5 benchmarks per lab
- [ ] T044 [US5] Add variant details tracking in lab preferences in agents/benchmark_intelligence/reporting.py
- [ ] T045 [US5] Verify average downloads/likes per lab calculation in agents/benchmark_intelligence/reporting.py

**Checkpoint**: US5 complete - lab preference analysis operational

---

## Phase 9: User Story 6 - Access Multi-Source Documentation (Priority: P6)

**Goal**: Verify remaining functionality - multi-source fetching already complete

**Status**: Core functionality 100% complete (comprehensive multi-source fetching working)

**Independent Test**: Verify all available source types for a model discovered and processed

### Implementation for User Story 6

- [ ] T046 [US6] Verify multi-source document fetching in agents/benchmark_intelligence/tools/fetch_docs_enhanced.py handles all source types
- [ ] T047 [US6] Verify figure/chart extraction in agents/benchmark_intelligence/tools/extract_benchmarks.py processes visual content
- [ ] T048 [US6] Verify change detection logic in agents/benchmark_intelligence/tools/cache.py skips unchanged documents

**Checkpoint**: US6 verified - multi-source documentation complete

---

## Phase 10: Testing Suite (Quality Validation)

**Purpose**: Implement 4-phase testing approach from SPECIFICATIONS.md Section 13

**⚠️ CRITICAL**: Ground truth data exists (181 benchmarks, 2 models) but test harness missing

### Phase 1: Source Discovery Validation

- [ ] T049 [P] Create tests/conftest.py with pytest fixtures for ground truth data loading
- [ ] T050 [P] Create tests/test_source_discovery.py with test harness
- [ ] T051 Implement test_source_discovery_recall in tests/test_source_discovery.py (verify all sources found)
- [ ] T052 Implement test_source_discovery_precision in tests/test_source_discovery.py (no false positives)
- [ ] T053 Implement test_source_type_classification in tests/test_source_discovery.py (correct doc types)

### Phase 2: Benchmark Extraction Validation

- [ ] T054 [P] Create tests/test_benchmark_extraction.py with test harness
- [ ] T055 Implement test_extraction_recall in tests/test_benchmark_extraction.py (≥90% recall against ground truth)
- [ ] T056 Implement test_extraction_precision in tests/test_benchmark_extraction.py (≥85% precision)
- [ ] T057 Implement test_variant_extraction in tests/test_benchmark_extraction.py (shots, method, model_type)
- [ ] T058 Implement test_figure_extraction in tests/test_benchmark_extraction.py (visual content benchmarks)

### Phase 3: Taxonomy Generation Validation

- [ ] T059 [P] Create tests/test_taxonomy_generation.py with test harness
- [ ] T060 Implement test_category_coverage in tests/test_taxonomy_generation.py (all benchmarks assigned)
- [ ] T061 Implement test_category_coherence in tests/test_taxonomy_generation.py (definitions non-overlapping)
- [ ] T062 Implement test_multi_label_justification in tests/test_taxonomy_generation.py (validate multi-category assignments)

### Phase 4: End-to-End Report Validation

- [ ] T063 [P] Create tests/test_report_generation.py with test harness
- [ ] T064 Implement test_all_sections_present in tests/test_report_generation.py (7 sections exist)
- [ ] T065 Implement test_no_hardcoded_data in tests/test_report_generation.py (all data from pipeline)
- [ ] T066 Implement test_temporal_trends in tests/test_report_generation.py (historical data when available)
- [ ] T067 Implement test_link_validity in tests/test_report_generation.py (source links work)

### Test Reports

- [ ] T068 [P] Create tests/reports/ directory for test output
- [ ] T069 Generate test validation reports in tests/reports/ with precision/recall metrics

**Checkpoint**: Testing suite complete - quality validation operational

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and documentation

- [ ] T070 [P] Add progress counter (X/Y models) consistently in agents/benchmark_intelligence/main.py
- [ ] T071 [P] Enhance phase transition logging in agents/benchmark_intelligence/main.py
- [ ] T072 [P] Verify README.md updates with latest report link
- [ ] T073 [P] Update agents/benchmark_intelligence/README.md with CLI mode documentation
- [ ] T074 Create CHANGELOG.md documenting 1.0 release notes
- [ ] T075 Verify all success criteria (SC-001 to SC-024) met
- [ ] T076 Run end-to-end validation with ground truth models
- [ ] T077 Generate final benchmark_taxonomy.md with all discovered categories

**Checkpoint**: All polish complete - system 100% ready for production

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (1-2 hours)
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS User Story 2 (2-3 hours)
- **CLI Modes (Phase 3)**: Can run parallel with Phase 2 - AFFECTS all user stories (2-3 hours)
- **User Story 1 (Phase 4)**: Depends on CLI Modes (Phase 3) - Can start after Phase 3 (1-2 hours)
- **User Story 2 (Phase 5)**: Depends on Foundational (Phase 2) + CLI Modes (Phase 3) (4-6 hours)
- **User Stories 3-6 (Phases 6-9)**: Depend on CLI Modes (Phase 3) - mostly verification (2-3 hours total)
- **Testing (Phase 10)**: Can run parallel once US1-US6 complete (6-8 hours)
- **Polish (Phase 11)**: Depends on all above (1-2 hours)

### Critical Path

```
Setup (1-2h) → Foundational (2-3h) → US2 Temporal Tracking (4-6h)
                      ↓
                CLI Modes (2-3h) → US1 Enhancements (1-2h)
                      ↓
                US3-US6 Verification (2-3h)
                      ↓
                Testing Suite (6-8h)
                      ↓
                Polish (1-2h)
```

**Total Estimated Time**: 19-31 hours (sequential execution)
**Minimum Time** (with parallelization): 15-22 hours

### User Story Dependencies

- **User Story 1 (P1)**: Depends on CLI Modes - ~90% complete, needs reporting enhancements
- **User Story 2 (P2)**: Depends on Foundational + CLI Modes - ~40% complete, MAJOR GAP
- **User Story 3 (P3)**: Depends on CLI Modes - ~95% complete, needs verification
- **User Story 4 (P4)**: Depends on CLI Modes - ~95% complete, needs verification
- **User Story 5 (P5)**: Depends on CLI Modes - ~90% complete, needs minor enhancements
- **User Story 6 (P6)**: Depends on CLI Modes - ~100% complete, needs verification only

### Parallel Opportunities

**High Parallelization Potential**:
- Phase 1 (Setup): All 3 tasks can run in parallel
- Phase 2 (Foundational): T007-T011 can run in parallel after T004-T006 complete
- Phase 3 (CLI Modes): T014-T016 can run in parallel after T012-T013 complete
- Phase 10 (Testing): All test file creation (T049, T050, T054, T059, T063) can run in parallel

**Sequential Requirements**:
- CLI mode implementation MUST complete before user story enhancements
- Database schema MUST complete before temporal tracking (US2)
- Temporal tracking MUST complete before temporal trend reporting

---

## Parallel Example: Foundational Phase

```bash
# After T004-T006 (schema changes) complete, launch in parallel:
Task T007: "Implement add_snapshot method enhancement in cache.py"
Task T008: "Implement add_benchmark_mention method in cache.py"
Task T009: "Implement get_models_in_date_range method in cache.py"
Task T010: "Implement get_benchmark_mentions_for_snapshot method in cache.py"
Task T011: "Implement determine_benchmark_status method in cache.py"
```

---

## Implementation Strategy

### MVP First (Complete Critical Gaps)

**Phase A: Critical Infrastructure** (5-8 hours)
1. Complete Phase 1: Setup (configuration files)
2. Complete Phase 2: Foundational (database schema)
3. Complete Phase 3: CLI Modes
4. **MILESTONE**: All infrastructure complete

**Phase B: Temporal Tracking MVP** (6-8 hours)
5. Complete Phase 5: User Story 2 (temporal tracking)
6. Enhance Phase 4: User Story 1 (reporting improvements)
7. **MILESTONE**: Core functionality 100% complete

**Phase C: Validation** (6-8 hours)
8. Complete Phase 10: Testing Suite
9. Verify Phases 6-9: User Stories 3-6
10. **MILESTONE**: All user stories validated

**Phase D: Production Ready** (1-2 hours)
11. Complete Phase 11: Polish
12. **MILESTONE**: 100% spec compliance, production ready

### Incremental Delivery

**Iteration 1** (5-8 hours): Setup + Foundational + CLI Modes
- Result: System can run in three modes, configuration complete

**Iteration 2** (6-8 hours): User Story 2 + User Story 1 enhancements
- Result: Full temporal tracking operational, all 7 report sections complete

**Iteration 3** (8-10 hours): Testing + Verification + Polish
- Result: Quality validated, all user stories verified, 100% complete

### Parallel Team Strategy

With 2 developers:
1. **Developer A**: Setup + Foundational + User Story 2 (temporal tracking)
2. **Developer B**: CLI Modes + User Story 1 enhancements + User Stories 3-6 verification
3. Both: Testing suite (divide test phases)
4. Both: Polish and final validation

With 3 developers:
1. **Developer A**: Setup + Foundational + User Story 2 core logic
2. **Developer B**: CLI Modes + User Story 2 reporting integration
3. **Developer C**: User Story 1 enhancements + User Stories 3-6 verification
4. All: Testing suite (each takes different test phases)

---

## Task Summary

### By Phase

| Phase | Tasks | Est. Hours | Status | Priority |
|-------|-------|-----------|--------|----------|
| 1. Setup | 3 | 1-2 | Missing | High |
| 2. Foundational | 8 | 2-3 | Partial | Critical |
| 3. CLI Modes | 9 | 2-3 | Missing | Critical |
| 4. US1 Enhancements | 4 | 1-2 | Partial | High |
| 5. US2 Temporal | 10 | 4-6 | Missing | Critical |
| 6. US3 Verification | 4 | 0.5-1 | Complete | Low |
| 7. US4 Verification | 4 | 0.5-1 | Complete | Low |
| 8. US5 Enhancements | 3 | 0.5-1 | Partial | Low |
| 9. US6 Verification | 3 | 0.5 | Complete | Low |
| 10. Testing | 21 | 6-8 | Missing | High |
| 11. Polish | 8 | 1-2 | Partial | Medium |
| **TOTAL** | **77** | **19-31** | **~75%** | - |

### By Priority

- **Critical (MUST DO)**: 27 tasks, 8-12 hours (Foundational + CLI + US2 core)
- **High (MVP)**: 28 tasks, 8-12 hours (Setup + US1 + Testing)
- **Medium (Quality)**: 14 tasks, 2-4 hours (US5 + Polish)
- **Low (Verification)**: 8 tasks, 1-2 hours (US3, US4, US6 verification)

### Suggested MVP Scope

**Minimum Viable Product** (16-24 hours):
- Phase 1: Setup ✓
- Phase 2: Foundational ✓
- Phase 3: CLI Modes ✓
- Phase 4: US1 Enhancements ✓
- Phase 5: US2 Temporal Tracking ✓
- Phase 10: Testing (Phases 1-2 only) ✓

**Result**: Full temporal tracking, all execution modes, validated core functionality

---

## Notes

### Task Format Compliance

- ✅ All tasks follow checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
- ✅ All user story tasks labeled with [US1]-[US6]
- ✅ All parallelizable tasks marked with [P]
- ✅ All tasks include exact file paths
- ✅ Task IDs sequential (T001-T077)

### Implementation Notes

- Most core pipeline code already exists and works
- Focus is on completing gaps, not rewriting existing code
- Database schema changes are additive (no breaking changes)
- CLI mode support affects all existing orchestration
- Temporal tracking is the largest net-new work item
- Testing validates existing implementation quality
- Ground truth data (181 benchmarks) enables thorough validation

### Avoid

- Recreating existing extraction/consolidation/classification logic
- Breaking existing pipeline tools (all working correctly)
- Changing existing database tables (additive changes only)
- Modifying working AI prompts (already optimized)

### Best Practices

- Test database schema changes with sample data before full pipeline
- Verify CLI modes work with small dataset before production run
- Run ground truth validation after each major phase
- Keep existing code modular architecture intact
- Document any breaking changes clearly
