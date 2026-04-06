# Feature Specification: Benchmark Intelligence System

**Feature Branch**: `001-benchmark-intelligence`  
**Created**: 2026-04-06  
**Status**: Draft  
**Input**: User description: "Benchmark Intelligence System - An automated system that discovers trending AI models from major labs (Meta, OpenAI, Anthropic, Qwen, etc.) and extracts benchmark evaluation data from all available sources (model cards, research papers, blogs, GitHub). The system tracks which benchmarks are most commonly used, identifies emerging benchmarks (newly popular), detects almost-extinct benchmarks (rarely used anymore), and provides insights into benchmark usage trends over a 12-month rolling window. It handles multi-source extraction (including vision AI for charts/figures), variant tracking (0-shot vs 5-shot, CoT vs base), taxonomy evolution, and generates comprehensive reports for researchers and practitioners tracking AI evaluation trends."

## User Scenarios & Testing

### User Story 1 - Discover Trending Benchmarks (Priority: P1)

**As a** AI researcher or practitioner,  
**I want to** see which benchmarks are most commonly used across recent AI models,  
**So that** I can understand current evaluation standards and choose appropriate benchmarks for my own model evaluation.

**Why this priority**: This is the core value proposition - helping users understand the current benchmark landscape. Without this, the system has no value.

**Independent Test**: Can be fully tested by running the system on a configured set of labs (e.g., Meta, OpenAI) and verifying that it produces a ranked list of benchmarks by usage frequency. Delivers immediate value by answering "What benchmarks should I care about right now?"

**Acceptance Scenarios**:

1. **Given** the system has discovered 50 models from 5 labs in the last 12 months, **When** I request a trending benchmarks report, **Then** I see a ranked list showing benchmark names, number of models using each benchmark, and percentage of models (relative frequency)

2. **Given** multiple models use the same benchmark with different variants (e.g., MMLU 0-shot vs 5-shot), **When** viewing trending benchmarks, **Then** I see each variant tracked separately with clear labels

3. **Given** benchmark data has been collected over multiple months, **When** viewing a benchmark's details, **Then** I see historical usage counts showing how popularity has changed over time

---

### User Story 2 - Identify Emerging and Declining Benchmarks (Priority: P1)

**As a** AI researcher tracking evaluation trends,  
**I want to** identify which benchmarks are newly emerging or becoming obsolete,  
**So that** I can stay ahead of evaluation trends and avoid investing time in deprecated benchmarks.

**Why this priority**: Temporal tracking is critical for understanding trends. This is part of the core value alongside P1 Story 1.

**Independent Test**: Can be tested by running the system with test data containing models from different time periods, then verifying that benchmarks first seen within 3 months are flagged as "emerging" and those not seen in 9+ months are flagged as "almost extinct". Delivers value by answering "What's new and what's dying?"

**Acceptance Scenarios**:

1. **Given** a benchmark first appeared in model evaluations 2 months ago, **When** viewing the benchmark report, **Then** it is clearly marked as "Emerging" with a visual indicator

2. **Given** a benchmark hasn't been used in any models for the last 10 months, **When** viewing the benchmark report, **Then** it is marked as "Almost Extinct" with a warning indicator

3. **Given** I'm viewing emerging benchmarks, **When** I see the list, **Then** each entry shows when it was first seen and how many models are using it

---

### User Story 3 - Multi-Source Comprehensive Extraction (Priority: P1)

**As a** user of the system,  
**I want to** be confident that benchmark data comes from all available sources (model cards, papers, blogs, GitHub),  
**So that** I get complete and accurate benchmark coverage without missing important evaluation details.

**Why this priority**: Data quality and completeness is fundamental - incomplete extraction makes all insights unreliable.

**Independent Test**: Can be tested by selecting a known model (e.g., Llama 3.1) with benchmarks in multiple sources and verifying the system extracts from model card, arXiv paper, official blog, and GitHub. Delivers value by ensuring data completeness.

**Acceptance Scenarios**:

1. **Given** a model has benchmarks mentioned in its model card, arXiv paper, and official blog post, **When** the system processes this model, **Then** it extracts benchmarks from all three sources and tags each benchmark with its source

2. **Given** a blog post contains benchmark charts as images, **When** the system processes the blog, **Then** it uses vision AI to extract benchmark names from the chart images

3. **Given** a PDF paper contains benchmark tables, **When** the system processes the paper, **Then** it correctly extracts benchmark names, variants (shots, methods), and categories

---

### User Story 4 - Lab-Specific Benchmark Preferences (Priority: P2)

**As a** AI researcher or product manager,  
**I want to** see which benchmarks specific labs prefer,  
**So that** I can understand evaluation strategies of leading organizations and align my evaluation approach with industry leaders.

**Why this priority**: Provides strategic insights but builds on the foundation of P1 stories. Useful but not essential for core value.

**Independent Test**: Can be tested by running the system on models from at least 3 different labs and verifying it produces lab-specific benchmark preference reports. Delivers value by answering "What does Meta focus on vs OpenAI?"

**Acceptance Scenarios**:

1. **Given** the system has tracked models from Meta, OpenAI, and Anthropic, **When** I view lab-specific insights, **Then** I see a breakdown of which benchmarks each lab uses most frequently

2. **Given** a lab consistently uses certain benchmark variants (e.g., always 5-shot), **When** viewing lab preferences, **Then** I see variant preferences clearly shown

---

### User Story 5 - Automated Scheduled Updates (Priority: P2)

**As a** system administrator,  
**I want to** schedule the system to run automatically on a recurring basis,  
**So that** benchmark intelligence stays current without manual intervention.

**Why this priority**: Automation is valuable for ongoing use but not required for initial value delivery. Can be added after manual execution works.

**Independent Test**: Can be tested by configuring a schedule and verifying the system runs at specified times, creates snapshots, and generates reports. Delivers ongoing value by keeping data fresh.

**Acceptance Scenarios**:

1. **Given** I configure the system to run weekly, **When** the scheduled time arrives, **Then** the system discovers new models, extracts benchmarks, creates a snapshot, and generates an updated report

2. **Given** a scheduled run completes, **When** I view the system logs, **Then** I see a summary of what was processed (models discovered, benchmarks extracted, new vs cached sources)

---

### User Story 6 - Taxonomy Evolution and Categorization (Priority: P3)

**As a** researcher using the system,  
**I want to** see benchmarks categorized by type (e.g., reasoning, math, code, knowledge),  
**So that** I can understand benchmark coverage across different capability dimensions.

**Why this priority**: Categorization adds analytical depth but is not essential for basic trending insights. Can be improved iteratively.

**Independent Test**: Can be tested by running the system and verifying that benchmarks are automatically assigned to categories, with the taxonomy evolving when new benchmark types are discovered. Delivers value by providing structured insights.

**Acceptance Scenarios**:

1. **Given** benchmarks have been extracted from models, **When** the system classifies them, **Then** each benchmark is assigned to one or more categories (e.g., "Reasoning", "Math", "Code Generation")

2. **Given** a new type of benchmark is discovered that doesn't fit existing categories, **When** the system processes it, **Then** the taxonomy evolves to include the new category

3. **Given** I want to override automatic categorization, **When** I manually edit the categories configuration, **Then** manual overrides take precedence over AI-generated categories

---

### Edge Cases

- **What happens when a model card is updated with new benchmarks?** System should detect content changes via hash comparison and re-extract only from changed sources
- **How does the system handle models with no benchmark data?** System should log these models but not block processing; report should show "N models with no benchmarks found"
- **What if a source is temporarily unavailable (404, timeout)?** System should retry with exponential backoff, cache last successful fetch, and continue processing other sources
- **How are benchmark name variants handled (e.g., "MMLU" vs "MMLU-Pro" vs "MMLU 5-shot")?** System should use fuzzy matching to consolidate similar names but preserve meaningful variants
- **What happens with the 12-month rolling window when the system is first initialized?** System should work with whatever data is available, clearly indicating the actual time window in reports
- **How does the system handle benchmarks mentioned in figures/charts vs text?** Both should be extracted and tagged with extraction method; figure-extracted benchmarks should be validated against text mentions where possible

## Requirements

### Functional Requirements

- **FR-001**: System MUST discover AI models from configured labs on HuggingFace based on filters (date range, task type, minimum downloads)
- **FR-002**: System MUST extract benchmark names from model cards, arXiv papers, official blogs, and GitHub documentation
- **FR-003**: System MUST extract benchmark variants including number of shots (0-shot, 5-shot, etc.), methods (CoT, PoT, TIR), and model types (base, instruct, chat)
- **FR-004**: System MUST use vision-capable AI to extract benchmarks from charts, figures, and images embedded in blog posts and PDFs
- **FR-005**: System MUST consolidate duplicate benchmark names using fuzzy matching while preserving meaningful variants
- **FR-006**: System MUST categorize benchmarks into taxonomy categories (e.g., General Knowledge, Reasoning, Math, Code)
- **FR-007**: System MUST track benchmark usage over a 12-month rolling window from current date
- **FR-008**: System MUST classify benchmarks as "Emerging" (first seen ≤3 months), "Almost Extinct" (last seen ≥9 months), or "Active" (all others)
- **FR-009**: System MUST calculate both absolute mentions (count of models) and relative frequency (percentage) for each benchmark
- **FR-010**: System MUST create temporal snapshots after each execution run, storing window boundaries and benchmark statistics
- **FR-011**: System MUST cache source documents using content hashes to avoid re-processing unchanged content
- **FR-012**: System MUST support three execution modes: snapshot (pipeline + snapshot), report (report only from latest snapshot), and full (pipeline + snapshot + report)
- **FR-013**: System MUST generate comprehensive reports showing trending benchmarks, emerging benchmarks, almost-extinct benchmarks, category distribution, and lab-specific preferences
- **FR-014**: System MUST allow manual configuration of labs to track via configuration file
- **FR-015**: System MUST persist all data in SQLite database with tables for models, benchmarks, model-benchmark associations, documents, snapshots, and benchmark mentions
- **FR-016**: System MUST support both automatic-speech-recognition (ASR) models and text/vision models, excluding text-to-speech and audio generation models
- **FR-017**: System MUST preserve historical taxonomy versions when taxonomy evolves
- **FR-018**: Users MUST be able to manually override AI-generated taxonomy categories via configuration file

### Key Entities

- **Model**: Represents an AI model from a specific lab
  - Attributes: model_id, lab, release_date, task_type, downloads, likes
  - Relationships: has many benchmarks through model_benchmarks association

- **Benchmark**: Represents a unique evaluation benchmark
  - Attributes: canonical_name, categories (JSON array), first_seen, last_seen
  - Relationships: used by many models through model_benchmarks association

- **Model-Benchmark Association**: Links models to benchmarks with context
  - Attributes: model_id, benchmark_id, variant_details (JSON: shots, method, model_type), source_type, source_url, recorded_at
  - Relationships: belongs to model and benchmark

- **Document**: Represents source documents fetched for each model
  - Attributes: model_id, source_type, url, content_hash, content, fetched_at
  - Relationships: belongs to model

- **Snapshot**: Represents a point-in-time capture of benchmark statistics
  - Attributes: timestamp, window_start, window_end, model_count, benchmark_count, taxonomy_version
  - Relationships: has many benchmark_mentions

- **Benchmark Mention**: Denormalized temporal tracking record per snapshot
  - Attributes: snapshot_id, benchmark_id, absolute_mentions, relative_frequency, first_seen, last_seen, status
  - Relationships: belongs to snapshot and benchmark

## Success Criteria

### Measurable Outcomes

- **SC-001**: System successfully discovers and processes 100% of models from configured labs within the specified date range and filter criteria
- **SC-002**: System extracts benchmarks from all available source types (model cards, papers, blogs, GitHub) with 95%+ accuracy compared to manual verification
- **SC-003**: Benchmark reports are generated within 30 minutes for up to 100 models across 10 labs
- **SC-004**: Emerging benchmark detection correctly identifies benchmarks first seen within 3 months with 100% accuracy
- **SC-005**: Almost-extinct benchmark detection correctly identifies benchmarks not seen in 9+ months with 100% accuracy
- **SC-006**: Fuzzy matching consolidates 90%+ of obvious duplicates (case differences, separator variations) while preserving distinct variants
- **SC-007**: Vision AI successfully extracts benchmarks from charts/figures with 85%+ accuracy when validated against available ground truth
- **SC-008**: Cache effectiveness: 80%+ of unchanged source documents are skipped on subsequent runs
- **SC-009**: Reports include lab-specific insights showing benchmark preferences for each configured lab with at least 5 models
- **SC-010**: System completes full execution (discovery + extraction + consolidation + classification + snapshot + report) without manual intervention
- **SC-011**: Taxonomy evolution captures new benchmark categories within one execution cycle of first discovery
- **SC-012**: Generated reports are readable by non-technical stakeholders and answer key questions: "What benchmarks are trending?", "What's new?", "What's dying?"

### Assumptions

- HuggingFace API provides reliable model discovery within specified date ranges
- AI model evaluation benchmarks are primarily documented in English-language sources
- Model cards, papers, and blogs follow reasonably consistent formatting patterns that can be parsed
- Vision AI (Claude with vision capabilities) can reliably extract text from benchmark charts and tables
- 12-month window provides sufficient trend data for meaningful insights
- Benchmark names, while varied in formatting, can be consolidated using fuzzy matching without losing important distinctions
- Labs maintain relatively stable benchmark evaluation practices over time
- SQLite database is sufficient for the expected data volume (thousands of models, tens of thousands of benchmark mentions)

### Dependencies

- HuggingFace Hub API for model discovery
- Anthropic API (Claude) for AI-powered extraction, consolidation, and classification
- External document sources: arXiv API, GitHub, lab blogs
- PDF parsing libraries for extracting content from research papers
- Vision-capable AI for chart/figure extraction

### Constraints

- System is triggered manually by user or via scheduled tasks (no automatic execution)
- Temporal tracking limited to 12-month rolling window
- Only tracks models from configured labs (not all HuggingFace models)
- Content extraction accuracy depends on source document quality and formatting
- API rate limits may affect processing speed for large numbers of models
- Vision AI accuracy for figure extraction depends on image quality and chart complexity

## Out of Scope

- Real-time benchmark tracking (system runs on-demand or scheduled, not continuously)
- Benchmark score tracking or leaderboard functionality (only tracks which benchmarks are used, not scores)
- Comparison of model performance across benchmarks
- Automated email notifications or alerts
- User authentication or multi-user access control
- Web-based user interface (reports are generated as markdown files)
- Integration with external analytics or BI platforms
- Support for non-HuggingFace model repositories in initial version
