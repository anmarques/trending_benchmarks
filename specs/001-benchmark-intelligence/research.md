# Research & Technology Decisions

**Feature**: Benchmark Intelligence System
**Date**: 2026-04-03
**Phase**: 0 - Research & Technology Selection

## Overview

This document captures technology research and decisions for the Benchmark Intelligence System. All choices prioritize compatibility with the existing codebase at `/workspace/repos/trending_benchmarks/`.

## Technology Stack Decisions

### 1. Programming Language & Version

**Decision**: Python 3.11+

**Rationale**:
- Existing codebase is Python-based
- Excellent ecosystem for data processing, AI integration, and web scraping
- Native SQLite support without external dependencies
- Strong library support for PDF parsing (pdfplumber), HTTP requests, YAML configuration
- Compatible with Anthropic SDK for Claude AI integration (standalone execution) or native Claude integration (managed environments)

**Alternatives Considered**:
- **Node.js/TypeScript**: Good for async I/O but weaker PDF parsing ecosystem, would require codebase rewrite
- **Rust**: Maximum performance but steeper learning curve, limited AI SDK support, incompatible with existing codebase
- **Go**: Good concurrency but weaker data science/AI library ecosystem

### 2. Database & Caching

**Decision**: SQLite3 with file-based storage

**Rationale**:
- Zero-configuration embedded database (no server setup)
- ACID compliance for data integrity
- Sufficient performance for single-process workloads
- Built into Python standard library
- Portable database file (easy backup/transfer)
- Supports complex queries for temporal analysis

**Schema Design Approach**:
- Normalized schema with indexed foreign keys
- Content hash-based change detection (SHA256)
- Separate snapshots table for temporal point-in-time analysis
- Denormalized benchmark_mentions table for fast trend queries

**Alternatives Considered**:
- **PostgreSQL**: Overkill for single-process workload, requires server setup, adds deployment complexity
- **JSON files**: Simpler but lacks query capabilities, difficult to maintain referential integrity
- **Redis**: Fast but in-memory only, no persistent complex queries, requires separate server

### 3. PDF Parsing Library

**Decision**: pdfplumber (primary) with PyPDF2 fallback

**Rationale**:
- pdfplumber excels at table extraction (critical for benchmark tables)
- Maintains text structure and layout information
- Better handling of multi-column layouts than alternatives
- PyPDF2 as fallback for edge cases where pdfplumber fails

**Extraction Strategy**:
- Extract full text + tables from all pages
- Apply 50K character limit post-extraction
- Compute SHA256 hash for change detection
- AI-powered section identification to focus on relevant content

**Alternatives Considered**:
- **PyMuPDF (fitz)**: Faster but less accurate table extraction
- **pdfminer.six**: Good text extraction but poor table support
- **Camelot**: Excellent for tables but requires system dependencies (Ghostscript), adds complexity

### 4. HTTP Client & Web Fetching

**Decision**: Dual-mode approach
- **MCP webfetch tool** for HTML/blog content
- **requests library** for PDF downloads and GitHub raw content

**Rationale**:
- MCP webfetch handles JavaScript-rendered pages automatically
- MCP webfetch provides built-in markdown conversion for HTML
- requests library required for binary PDF downloads (MCP webfetch doesn't support binary)
- requests library more reliable for GitHub raw URLs

**Retry Strategy**:
- Exponential backoff: initial 1s, multiplier 2.0, max 60s
- Max 3 retry attempts per request
- Graceful degradation: skip failed sources, continue processing

**Alternatives Considered**:
- **httpx**: Modern async HTTP but adds complexity for minimal benefit in sequential processing
- **urllib3**: Lower-level, requires more boilerplate
- **selenium**: Overkill for static content, requires browser driver management

### 5. AI Integration for Extraction & Classification

**Decision**: Anthropic Claude API (via Python SDK)

**Rationale**:
- State-of-the-art text understanding for benchmark extraction
- Excellent at table parsing and structured data extraction
- Vision capabilities for chart/figure analysis
- Consistent API with predictable costs
- Strong instruction following for taxonomy evolution

**Extraction Approach**:
- Single AI call per document for section detection + extraction
- Structured output format (JSON) for benchmark data
- Prompt engineering for consistent extraction across document types
- Vision model for figure/chart processing

**Alternatives Considered**:
- **GPT-4**: Similar capabilities but less consistent structured output
- **Open-source models (LLaMA, Mistral)**: Lower cost but require local hosting, less accurate extraction
- **Rule-based extraction**: Faster but brittle, fails on varied document formats

### 6. Configuration Management

**Decision**: YAML files at project root with pyyaml parser

**Rationale**:
- Human-readable and editable
- Supports nested structures (labs, filters, exclusions)
- Comments for documentation
- Easy validation with schema
- Standard in Python ecosystem

**Configuration Files**:
- `labs.yaml`: Lab tracking, discovery filters, GitHub mappings, search configuration
- `categories.yaml`: Manual category overrides for benchmark classification
- `benchmark_taxonomy.md`: Auto-generated current taxonomy

**Alternatives Considered**:
- **TOML**: Good structure but less widely adopted in data science tools
- **JSON**: No comments, less human-friendly for configuration
- **Environment variables**: Poor for complex nested configuration

### 7. Testing Framework

**Decision**: pytest with modular ground-truth validation

**Rationale**:
- Industry standard for Python testing
- Excellent fixture support for test data management
- Parallel test execution support
- Rich ecosystem of plugins (coverage, benchmarks)

**Testing Approach** (4 Phases):
1. **Source Discovery**: Validate all sources found for test models
2. **Benchmark Extraction**: Precision/recall metrics against ground truth
3. **Taxonomy Generation**: Manual review of AI-generated categories
4. **End-to-End Report**: Full pipeline validation

**Ground Truth Format**: YAML with known models, sources, and benchmarks

**Alternatives Considered**:
- **unittest**: Standard library but more verbose, less flexible fixtures
- **nose2**: Less active development than pytest
- **doctest**: Good for documentation but insufficient for complex validation

### 8. CLI Interface Design

**Decision**: Argument-based mode selection (snapshot/report/full)

**Rationale**:
- Simple invocation: `python main.py [mode]`
- Clear separation of concerns (pipeline vs reporting)
- Supports scheduled execution (cron/Ambient)
- Default to full mode for convenience
- Exit codes for integration (0=success, 1=error, 2=no-snapshots)

**Mode Design**:
- **snapshot**: Run pipeline + create snapshot (no report)
- **report**: Generate report from latest snapshot (no pipeline)
- **full**: Complete execution (pipeline + snapshot + report)

**Alternatives Considered**:
- **Click/Typer framework**: Adds dependency for minimal benefit with simple CLI
- **Subcommands (git-style)**: More complex invocation for three simple modes
- **Interactive prompts**: Unsuitable for scheduled/automated execution

## Integration Patterns

### HuggingFace API Integration

**Approach**: Direct REST API calls with rate limit handling

**Endpoints Used**:
- `/api/models?author={lab}` - Model discovery with filters
- `/api/models/{model_id}` - Model metadata

**Rate Limiting**:
- Exponential backoff on 429 responses
- Sequential queries per lab (no parallelization to avoid rate limits)

### Document Fetching Strategy

**Multi-tiered Discovery**:
1. Model card: Always fetch from HuggingFace
2. arXiv papers: Check model card for URLs → Use lab→paper mapping → Fallback to MCP webfetch
3. GitHub docs: Use lab→org mapping + known URL patterns
4. Blogs: Use lab→blog URL mapping + MCP webfetch

**Content Type Detection**:
- `.pdf` extension or `arxiv.org/pdf/` → Use requests library
- All other URLs → Use MCP webfetch tool

### AI Extraction Pipeline

**Prompt Strategy**:
- Separate prompts for extraction, consolidation, classification
- Include few-shot examples in prompts
- Request structured JSON output for parsing
- Vision model for images with benchmark charts

**Error Handling**:
- Cache failed extractions to avoid retries
- Store extraction_failed flag in documents table
- Continue processing other documents on failure

## Performance Optimization

### Caching Strategy

**Document-level Caching**:
- Store SHA256 hash of extracted content
- Skip re-extraction if hash unchanged
- Update metadata (downloads, likes) on every run
- Cache failed extractions with flag

**Benefits**:
- 60%+ skip rate on incremental runs
- Reduced API costs for AI extraction
- Faster processing after initial run

### Incremental Processing

**Update Strategy**:
1. Update all model metadata from HuggingFace
2. Fetch all source documents
3. Compare content hashes
4. Re-extract only changed documents
5. Update benchmark associations

### Parallel Execution Opportunities

**Current Design** (Sequential):
- Discovery: One lab at a time
- Document fetching: 5 concurrent per model
- AI extraction: Sequential (rate limit concerns)
- Consolidation: Sequential
- Reporting: Sequential

**Future Optimization**: Can parallelize document fetching across models with semaphore-based concurrency control

## Deployment Considerations

### Environment Requirements

**System Dependencies**:
- Python 3.11+ runtime
- SQLite3 (bundled with Python)
- No external servers required (embedded database)

**Python Dependencies** (requirements.txt):
```
anthropic>=0.18.0        # Claude API
pdfplumber>=0.10.0       # PDF parsing
PyPDF2>=3.0.0            # Fallback PDF parser
requests>=2.31.0         # HTTP client
pyyaml>=6.0              # YAML configuration
huggingface-hub>=0.20.0  # HuggingFace API
```

### Execution Model

**Supported Execution**:
- Manual: `python agents/benchmark_intelligence/main.py [mode]`
- Scheduled: Ambient scheduled tasks or cron jobs
- Default mode: full (pipeline + snapshot + report)

**Output Locations**:
- Reports: `agents/benchmark_intelligence/reports/report_YYYYMMDD_HHMMSS.md`
- Database: `agents/benchmark_intelligence/benchmark_intelligence.db`
- Taxonomy: Root `benchmark_taxonomy.md` + `archive/`

### Observability

**Progress Reporting**:
- Console output with status symbols (✓ ✗ ↻ ⊕)
- Progress counters (X/Y models)
- Mode indication at start
- Phase transitions logged

**Logging Levels**:
- INFO: Progress updates, phase transitions
- DEBUG: Detailed processing (per-source)
- ERROR: Failures, exceptions

## Security & Privacy

### Data Handling

**No Sensitive Data Storage**:
- Only public model metadata cached
- No user credentials stored
- API keys via environment variables

**Content Handling**:
- Document content NOT persisted (only hashes)
- Temporary files cleaned after processing
- PDFs downloaded to temp directory with cleanup

### API Key Management

**Environment Variables**:
- `ANTHROPIC_API_KEY`: Required for standalone AI operations (not needed on Ambient/Claude Code/Cursor)
- `GITHUB_TOKEN`: Optional for authenticated GitHub requests (higher rate limits)
- `HUGGINGFACE_TOKEN`: Optional for private models (if needed)

## Risk Mitigation

### Known Limitations

1. **AI Extraction Accuracy**: Target 90% recall, 85% precision via ground truth testing
2. **Rate Limits**: HuggingFace and AI APIs have rate limits - handled via exponential backoff
3. **PDF Parsing**: Image-only PDFs may fail - skip with warning
4. **Google Search Blocking**: Fallback disabled by default (blocked frequently)

### Mitigation Strategies

1. **Extraction Quality**: Comprehensive ground truth testing with manual validation
2. **Rate Limiting**: Sequential processing with retry logic, respect Retry-After headers
3. **Failed Extractions**: Cache failures to prevent infinite retries, log for review
4. **Missing Sources**: Graceful degradation, continue processing with available sources

## Validation & Testing Strategy

### Ground Truth Approach

**Test Data**:
- 2 models from different labs
- All known sources documented
- Benchmark names manually verified
- Includes figure-based benchmarks

**Validation Phases**:
1. Source discovery: 100% recall required
2. Extraction: ≥90% recall, ≥85% precision
3. Taxonomy: Manual review for coherence
4. Report: End-to-end validation

### Quality Metrics

**Extraction Quality**:
- Precision: True positives / (True positives + False positives)
- Recall: True positives / (True positives + False negatives)
- F1 Score: Harmonic mean of precision and recall

**Taxonomy Quality**:
- Category coverage: % benchmarks assigned to categories
- Catch-all percentage: % benchmarks in "Other" (target <20%)
- Multi-label coherence: Justification for multiple categories

## Decision Summary

| Aspect | Choice | Key Reason |
|--------|--------|-----------|
| Language | Python 3.11+ | Existing codebase, rich ecosystem |
| Database | SQLite | Zero-config, sufficient performance |
| PDF Parser | pdfplumber + PyPDF2 | Best table extraction capabilities |
| HTTP Client | MCP webfetch + requests | Dual-mode for HTML/binary |
| AI Provider | Anthropic Claude | State-of-the-art extraction accuracy |
| Config Format | YAML | Human-readable, nested structures |
| Testing | pytest | Industry standard, flexible |
| CLI Design | Mode-based args | Simple, schedulable |

All decisions prioritize **simplicity, reliability, and maintainability** while meeting the comprehensive coverage and data quality requirements specified in the feature specification.
