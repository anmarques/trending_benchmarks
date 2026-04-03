# Implementation Plan: Benchmark Intelligence System

**Branch**: `001-benchmark-intelligence` | **Date**: 2026-04-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-benchmark-intelligence/spec.md`

## Summary

Automatically track, extract, and analyze benchmark evaluation trends across Large Language Models (LLMs), Vision-Language Models (VLMs), and Audio-to-Text Models from major AI research labs. The system discovers models from HuggingFace, extracts benchmark mentions from multi-source documentation (model cards, papers, blogs, PDFs), consolidates naming variants, classifies benchmarks into categories, tracks temporal trends over 12-month rolling windows, and generates comprehensive markdown reports.

**Technical Approach**: Python-based CLI pipeline with SQLite caching, AI-powered extraction/classification, incremental update support, and three execution modes (snapshot, report, full).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- HuggingFace Hub API (model discovery)
- SQLite3 (caching & persistence)
- pdfplumber (PDF parsing)
- requests (HTTP downloads)
- PyYAML (configuration)
- Anthropic SDK (AI extraction & classification)

**Storage**: SQLite database (schema: models, benchmarks, model_benchmarks, documents, snapshots, benchmark_mentions)
**Testing**: pytest with modular test phases (source discovery, extraction, taxonomy, report generation)
**Target Platform**: Linux/macOS servers, scheduled execution environment (Ambient-compatible)
**Project Type**: Single CLI application with modular tool structure
**Performance Goals**:
- Complete pipeline: <2 hours for 150 models
- Incremental updates: Skip 60%+ unchanged documents
- Report generation: <2 minutes from cached data
**Constraints**:
- Documents: Max 50K characters extracted text
- PDFs: Max 10MB download size, 120s timeout
- Progress reporting: Every 10 models during processing
**Scale/Scope**:
- 15 models per lab × configurable lab count
- 12-month rolling temporal window
- Support for 4 model types (text-generation, image-text-to-text, text2text-generation, automatic-speech-recognition)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ PASSED (No constitution defined - using general best practices)

## Project Structure

### Documentation (this feature)

```text
specs/001-benchmark-intelligence/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli-interface.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
agents/benchmark_intelligence/
├── main.py                  # CLI entry point (snapshot/report/full modes)
├── config/
│   ├── labs.yaml           # Lab configuration & filters
│   └── categories.yaml     # Category definitions (manual overrides)
├── tools/                  # Modular pipeline tools
│   ├── discover_models.py  # HuggingFace API model discovery
│   ├── fetch_docs.py       # Multi-source document fetching
│   ├── pdf_parser.py       # PDF extraction with pdfplumber
│   ├── extract_benchmarks.py  # AI-powered benchmark extraction
│   ├── consolidate.py      # Benchmark name consolidation
│   ├── classify.py         # AI-powered categorization
│   ├── taxonomy_manager.py # Taxonomy evolution & archiving
│   ├── cache.py            # SQLite cache management
│   └── retry_utils.py      # Retry logic with backoff
├── prompts/                # AI prompt templates
│   ├── extract_benchmarks.md
│   ├── consolidate.md
│   └── classify.md
├── reporting.py            # Report generation (7 sections)
├── reports/                # Output directory for generated reports
└── benchmark_intelligence.db  # SQLite database (created at runtime)

tests/
├── ground_truth/
│   ├── ground_truth.yaml   # Known-good test data (2 models)
│   └── CHANGELOG.md
├── test_source_discovery.py  # Phase 1: Source discovery validation
├── test_benchmark_extraction.py  # Phase 2: Extraction validation
├── test_taxonomy_generation.py   # Phase 3: Taxonomy validation
├── test_report_generation.py     # Phase 4: End-to-end validation
└── reports/                # Test report outputs

archive/                    # Historical taxonomy versions
└── benchmark_taxonomy_YYYYMMDD.md

benchmark_taxonomy.md       # Current taxonomy (auto-updated)
labs.yaml                   # Root-level lab configuration
categories.yaml             # Root-level category definitions
requirements.txt            # Python dependencies
README.md                   # Project overview & usage
```

**Structure Decision**: Single project structure with modular tool-based architecture. Each pipeline phase (discovery, extraction, consolidation, classification, snapshot, reporting) is implemented as an independent tool module, enabling isolated testing and parallel development. Configuration files at root level for easy user access. CLI interface with mode-based execution (snapshot/report/full).

## Complexity Tracking

> No constitution violations - standard single-project CLI architecture


## Current Implementation Status

**Codebase Analysis Date**: 2026-04-03
**Location**: `/workspace/repos/trending_benchmarks/`
**Overall Completeness**: ~75%

### ✅ What's Already Implemented

**Core Pipeline Tools** (~6,700 lines):
- ✅ Model discovery (`discover_models.py`)
- ✅ Document fetching (`fetch_docs.py`, enhanced, fallback variants)
- ✅ PDF parsing (`pdf_parser.py` with pdfplumber)
- ✅ Benchmark extraction (`extract_benchmarks.py` with AI)
- ✅ Name consolidation (`consolidate.py` with fuzzy matching)
- ✅ Classification (`classify.py` with AI)
- ✅ Taxonomy evolution (`taxonomy_manager.py`)
- ✅ Cache manager (`cache.py` with SQLite)
- ✅ Retry utilities (`retry_utils.py`)
- ✅ Client infrastructure (HuggingFace API, MCP integration)

**Configuration & Data**:
- ✅ Main orchestrator (`main.py` with `BenchmarkIntelligenceAgent`)
- ✅ Reporting system (`reporting.py` with `ReportGenerator`)
- ✅ AI prompts (extract, consolidate, classify - comprehensive)
- ✅ Configuration (`labs.yaml` with 15 labs)
- ✅ Ground truth test data (2 models, 181 benchmarks, 4 documents)
- ✅ README with documentation

### ❌ Critical Gaps (Blocking Full Spec Compliance)

1. **CLI Mode Support** (High Priority)
   - ❌ No argparse mode handling (snapshot/report/full)
   - ❌ No mode-specific execution logic
   - ❌ No exit codes (0/1/2)
   - ❌ No help/version output
   - **Impact**: Can't run in different modes as specified
   - **Effort**: 2-3 hours

2. **Temporal Snapshot System** (High Priority)
   - ❌ `benchmark_mentions` table not implemented
   - ⚠️ `snapshots` table missing columns (window_start, window_end, taxonomy_version)
   - ❌ 12-month rolling window logic missing
   - ❌ Emerging/active/extinct status classification missing
   - ❌ Relative frequency calculations missing
   - **Impact**: No temporal trend tracking (P2 user story incomplete)
   - **Effort**: 4-6 hours

3. **Test Suite** (High Priority)
   - ❌ No test files (ground truth exists but no harness)
   - ❌ 4-phase testing approach not implemented
   - **Impact**: No validation of extraction quality
   - **Effort**: 6-8 hours

4. **Enhanced Reporting** (Medium Priority)
   - ⚠️ Temporal trends section incomplete
   - ❌ Emerging benchmarks section missing
   - ❌ Almost extinct benchmarks section missing
   - ❌ Historical snapshot comparison missing
   - **Impact**: 5/7 report sections complete
   - **Effort**: 3-4 hours

5. **Configuration Files** (Low Priority)
   - ❌ `categories.yaml` doesn't exist (spec calls for manual overrides)
   - ❌ `benchmark_taxonomy.md` doesn't exist (should be auto-generated)
   - ❌ Archive directory for historical taxonomies missing
   - **Impact**: Manual category overrides not supported
   - **Effort**: 1-2 hours

### 🎯 Recommended Implementation Roadmap

**Phase 1: Critical Gaps (MVP Completion)** - 12-17 hours
1. Add CLI mode support (2-3 hours)
2. Implement temporal snapshot system (4-6 hours)
3. Enhance reporting for temporal trends (3-4 hours)
4. Basic testing harness (3-4 hours)

**Phase 2: Polish & Completeness** - 3-5 hours
5. Generate configuration files (1-2 hours)
6. Enhance progress reporting (1-2 hours)
7. Schema consistency cleanup (1 hour)

**Total Estimated Effort**: 15-22 hours to reach 100% spec compliance

### 📊 Completeness by Component

| Component | Status | % Complete | Critical Gaps |
|-----------|--------|------------|---------------|
| Discovery & Extraction | ✅ Complete | 100% | None |
| Consolidation & Classification | ✅ Complete | 100% | None |
| Database Schema | ⚠️ Partial | 75% | benchmark_mentions table |
| Main Orchestrator | ⚠️ Partial | 70% | CLI modes |
| Reporting | ⚠️ Partial | 60% | Temporal sections |
| Testing | ❌ Missing | 0% | Entire suite |
| Configuration | ⚠️ Partial | 80% | categories.yaml |

## Planning Complete

✅ **Phase 0: Research & Technology Selection** - Complete
- Technology stack defined (Python 3.11+, SQLite, pdfplumber, Claude AI)
- Architecture patterns documented
- Integration strategies specified
- Research document: specs/001-benchmark-intelligence/research.md

✅ **Phase 1: Design & Contracts** - Complete
- Data model defined (8 entities, full schema with indexes)
- CLI interface contract specified
- User guide created
- Generated artifacts:
  - specs/001-benchmark-intelligence/data-model.md
  - specs/001-benchmark-intelligence/contracts/cli-interface.md
  - specs/001-benchmark-intelligence/quickstart.md

✅ **Implementation Status Analysis** - Complete
- Codebase reviewed and analyzed
- 75% implementation completeness confirmed
- Critical gaps identified and prioritized
- Implementation roadmap created
- Analysis document: specs/001-benchmark-intelligence/implementation-status.md

✅ **Agent Context Updated**
- Claude Code context file updated with:
  - Language: Python 3.11+
  - Database: SQLite (8-table schema)
  - Project type: Single CLI application with modular tools

## Next Steps

**Option 1**: Generate full task breakdown
```bash
/speckit.tasks
```
This will create `specs/001-benchmark-intelligence/tasks.md` with all implementation tasks organized by user story (including tasks for already-implemented components).

**Option 2**: Start implementation immediately
Focus on critical gaps identified in `implementation-status.md`:
1. CLI mode support
2. Temporal snapshot system
3. Enhanced reporting
4. Test suite

**Recommendation**: Review `implementation-status.md` first to understand what's already built, then use `/speckit.tasks` to generate a comprehensive task breakdown that accounts for existing implementation.

