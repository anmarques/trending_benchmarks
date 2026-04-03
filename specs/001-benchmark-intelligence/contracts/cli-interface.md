# CLI Interface Contract

**Feature**: Benchmark Intelligence System
**Date**: 2026-04-03
**Version**: 1.0

## Overview

This document defines the command-line interface contract for the Benchmark Intelligence System. The CLI provides three execution modes for pipeline management and reporting.

## Command Syntax

```bash
python agents/benchmark_intelligence/main.py [MODE] [OPTIONS]
```

### Positional Arguments

| Argument | Required | Values | Default | Description |
|----------|----------|--------|---------|-------------|
| MODE | No | `snapshot`, `report`, `full` | `full` | Execution mode |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--help` | `-h` | flag | - | Show help message and exit |
| `--version` | `-v` | flag | - | Show version and exit |
| `--verbose` | - | flag | false | Enable debug logging |
| `--quiet` | `-q` | flag | false | Suppress progress output (errors only) |

## Execution Modes

### Mode: `snapshot`

**Purpose**: Run full pipeline and create temporal snapshot without generating report.

**Usage**:
```bash
python agents/benchmark_intelligence/main.py snapshot
```

**Execution Flow**:
1. Discovery Phase: Query HuggingFace for models from configured labs
2. Processing Phase: Fetch and extract benchmarks from all sources
3. Consolidation Phase: Normalize benchmark names, classify into categories
4. Snapshot Phase: Create temporal snapshot with 12-month window metrics
5. Exit (no report generation)

**Output**:
- Updated SQLite database (`benchmark_intelligence.db`)
- New snapshot record with timestamp
- Updated taxonomy file (`benchmark_taxonomy.md`)
- Archived taxonomy (if changed)
- Console progress messages

**Exit Codes**:
- `0`: Success (snapshot created)
- `1`: Error (configuration invalid, API failure, database error)

**Use Cases**:
- Regular scheduled updates to keep database current
- Background data collection without report overhead
- Testing pipeline without report generation

---

### Mode: `report`

**Purpose**: Generate markdown report from latest snapshot without running pipeline.

**Usage**:
```bash
python agents/benchmark_intelligence/main.py report
```

**Execution Flow**:
1. Load latest snapshot from database
2. Query benchmark mentions and model data
3. Generate 7-section markdown report
4. Update root README with latest report link
5. Exit

**Output**:
- Markdown report: `agents/benchmark_intelligence/reports/report_YYYYMMDD_HHMMSS.md`
- Updated README.md with latest report link
- Console status messages

**Exit Codes**:
- `0`: Success (report generated)
- `1`: Error (database error, write failure)
- `2`: No snapshots found (database empty, run `snapshot` or `full` first)

**Use Cases**:
- Regenerate report after manual data fixes
- Generate report with updated template
- Quick report refresh without re-running pipeline

---

### Mode: `full` (default)

**Purpose**: Complete execution - run pipeline, create snapshot, and generate report.

**Usage**:
```bash
python agents/benchmark_intelligence/main.py full
# Or simply:
python agents/benchmark_intelligence/main.py
```

**Execution Flow**:
1. Discovery Phase: Query HuggingFace for models from configured labs
2. Processing Phase: Fetch and extract benchmarks from all sources
3. Consolidation Phase: Normalize benchmark names, classify into categories
4. Snapshot Phase: Create temporal snapshot with 12-month window metrics
5. Reporting Phase: Generate 7-section markdown report
6. Update root README with latest report link
7. Exit

**Output**:
- Updated SQLite database (`benchmark_intelligence.db`)
- New snapshot record with timestamp
- Updated taxonomy file (`benchmark_taxonomy.md`)
- Archived taxonomy (if changed)
- Markdown report: `agents/benchmark_intelligence/reports/report_YYYYMMDD_HHMMSS.md`
- Updated README.md
- Console progress messages

**Exit Codes**:
- `0`: Success (snapshot created and report generated)
- `1`: Error (configuration invalid, API failure, database error, report generation failure)

**Use Cases**:
- On-demand complete analysis
- Scheduled weekly/monthly execution
- Initial setup and testing
- Default mode for convenience

---

## Progress Output Format

### Standard Output (INFO level)

```
[Mode: full] Starting benchmark intelligence pipeline...

[Discovery] Querying 15 labs...
[Discovery] Found 127 models from Qwen, meta-llama, mistralai, ...
[Discovery] Applied filters: 89 models passed (38 excluded)

[Processing] Model 1/89: Qwen/Qwen2.5-7B
  ✓ Fetched model card
  ✓ Fetched GitHub README
  ✓ Found arXiv paper
  ✓ Extracted 15 benchmarks

[Processing] Model 2/89: meta-llama/Llama-3.1-8B
  ✓ Cached (no changes)
  ↻ Updated metadata (downloads: 15.2M → 15.4M)

[Consolidation] Found 87 unique benchmark names
[Consolidation] Consolidated to 72 canonical names
[Classification] Classified 72 benchmarks across 13 categories

[Snapshot] Calculating 12-month window: 2025-04-03 to 2026-04-03
[Snapshot] Found 150 models in window
[Snapshot] Processing 72 unique benchmarks...
[Snapshot] ✓ Snapshot created: ID=42, timestamp=2026-04-03T16:30:45
[Snapshot]   - Emerging: 5 benchmarks
[Snapshot]   - Active: 62 benchmarks
[Snapshot]   - Almost Extinct: 5 benchmarks

[Reporting] Loading snapshot ID=42 (2026-04-03T16:30:45)
[Reporting] Generating 7 sections...
[Reporting] ✓ Report saved: reports/report_20260403_163045.md
[Reporting] ✓ Updated root README.md

✅ Pipeline complete! (Runtime: 1h 23m 15s)
```

### Verbose Output (DEBUG level)

Enabled with `--verbose`:
- Per-source extraction details
- Hash comparison results
- API request/response logs
- Consolidation decisions
- Classification confidence scores

### Quiet Output (ERROR level only)

Enabled with `--quiet`:
- Only errors and critical failures
- Final success/failure status
- Suitable for cron jobs with email-on-error

---

## Status Symbols

| Symbol | Meaning |
|--------|---------|
| ✓ | Success / Completed |
| ✗ | Error / Failed |
| ↻ | Cached / Updated (from cache) |
| ⊕ | New / Added |
| ⚠ | Warning |

---

## Environment Variables

### Required (Standalone Execution)

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key for extraction/classification (not required on Ambient/Claude Code/Cursor) | `sk-ant-...` |

### Optional

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GITHUB_TOKEN` | GitHub PAT for higher rate limits | None | `ghp_...` |
| `HUGGINGFACE_TOKEN` | HuggingFace token (if accessing private models) | None | `hf_...` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `WARNING`, `ERROR` |

---

## Configuration Files

### Required Configuration

| File | Location | Purpose |
|------|----------|---------|
| `labs.yaml` | Project root | Lab configuration, discovery filters, GitHub mappings |
| `categories.yaml` | Project root | Manual category overrides |

### Generated Files

| File | Location | Purpose |
|------|----------|---------|
| `benchmark_taxonomy.md` | Project root | Current auto-generated taxonomy |
| `benchmark_intelligence.db` | `agents/benchmark_intelligence/` | SQLite database |
| `report_*.md` | `agents/benchmark_intelligence/reports/` | Generated reports |

### Archived Files

| File | Location | Purpose |
|------|----------|---------|
| `benchmark_taxonomy_YYYYMMDD.md` | `archive/` | Historical taxonomy versions |

---

## Error Handling

### Validation Errors (Exit 1)

**Configuration Invalid**:
```
❌ Error: Configuration validation failed
   - labs.yaml: Missing required field 'labs'
   - labs.yaml: Invalid filter_tags format (must be list)

Exit code: 1
```

**Missing API Key**:
```
❌ Error: ANTHROPIC_API_KEY environment variable not set

Please set your Claude API key (standalone execution only):
  export ANTHROPIC_API_KEY="sk-ant-..."

Note: If running on Ambient, Claude Code, or Cursor, check native
      Claude integration configuration.

Exit code: 1
```

### Runtime Errors (Exit 1)

**API Failure**:
```
❌ Error: HuggingFace API request failed
   Endpoint: /api/models?author=Qwen
   Status: 503 Service Unavailable
   Retry 3/3 failed

Suggestion: Wait and retry later

Exit code: 1
```

**Database Error**:
```
❌ Error: Database write failed
   Path: agents/benchmark_intelligence/benchmark_intelligence.db
   Error: disk full

Exit code: 1
```

### No Data Errors (Exit 2)

**No Snapshots (report mode)**:
```
❌ Error: No snapshots found in database

Please run in 'snapshot' or 'full' mode first:
  python agents/benchmark_intelligence/main.py snapshot

Exit code: 2
```

---

## Help Output

```bash
$ python agents/benchmark_intelligence/main.py --help
```

```
Benchmark Intelligence System

Track and analyze benchmark evaluation trends across LLMs, VLMs,
and Audio-to-Text models from major AI research labs.

USAGE:
    python agents/benchmark_intelligence/main.py [MODE] [OPTIONS]

MODES:
    snapshot    Run pipeline + create snapshot (no report)
    report      Generate report from latest snapshot (no pipeline)
    full        Complete execution (pipeline + snapshot + report) [default]

OPTIONS:
    -h, --help      Show this help message and exit
    -v, --version   Show version and exit
    --verbose       Enable debug logging
    -q, --quiet     Suppress progress output (errors only)

ENVIRONMENT VARIABLES:
    ANTHROPIC_API_KEY    Required for standalone execution (not needed on
                         Ambient/Claude Code/Cursor with native Claude integration)
    GITHUB_TOKEN         Optional: Higher GitHub API rate limits
    HUGGINGFACE_TOKEN    Optional: Access private models
    LOG_LEVEL            Optional: DEBUG|INFO|WARNING|ERROR (default: INFO)

EXAMPLES:
    # Full execution (default)
    python agents/benchmark_intelligence/main.py
    python agents/benchmark_intelligence/main.py full

    # Update database only (no report)
    python agents/benchmark_intelligence/main.py snapshot

    # Regenerate report from cached data
    python agents/benchmark_intelligence/main.py report

    # Verbose debugging
    python agents/benchmark_intelligence/main.py full --verbose

    # Quiet mode for cron jobs
    python agents/benchmark_intelligence/main.py snapshot --quiet

EXIT CODES:
    0    Success
    1    Error (configuration, API, database)
    2    No snapshots found (run snapshot or full mode first)

For detailed documentation, see: specs/001-benchmark-intelligence/quickstart.md
```

---

## Version Output

```bash
$ python agents/benchmark_intelligence/main.py --version
```

```
Benchmark Intelligence System v1.0.0
Python 3.11+
SQLite 3.x
```

---

## Integration Examples

### Cron Job (weekly snapshot)

```bash
# Run every Sunday at 2 AM
0 2 * * 0 cd /path/to/project && python agents/benchmark_intelligence/main.py snapshot --quiet
```

### Scheduled Task (Ambient)

```yaml
schedule:
  - name: "Weekly Benchmark Intelligence"
    cron: "0 2 * * 0"
    command: "python agents/benchmark_intelligence/main.py full"
    notify_on_error: true
```

### Manual Execution with Logging

```bash
# Capture detailed logs
python agents/benchmark_intelligence/main.py full --verbose 2>&1 | tee run_$(date +%Y%m%d).log
```

### Conditional Report Generation

```bash
# Generate report only if snapshot succeeded
python agents/benchmark_intelligence/main.py snapshot && \
python agents/benchmark_intelligence/main.py report
```

---

## Contract Guarantees

### Input Validation

1. Mode must be one of: `snapshot`, `report`, `full`, or omitted (defaults to `full`)
2. Invalid mode triggers help message and exit 1
3. Unknown options trigger help message and exit 1
4. Configuration files validated before execution starts

### Output Guarantees

1. **Snapshot mode**: Database updated OR exit 1 (never partial state)
2. **Report mode**: Report generated OR exit 2 (no snapshots) OR exit 1 (error)
3. **Full mode**: Both snapshot and report generated OR exit 1 (atomic failure)

### Progress Reporting

1. Mode indication always printed first
2. Progress messages every 10 models minimum
3. Phase transitions always logged
4. Final status (✅ success or ❌ error) always printed

### File System State

1. Database writes are atomic (SQLite transactions)
2. Reports written with timestamp to prevent overwrites
3. Taxonomy archives created before updates (no data loss)
4. Temporary files cleaned up on exit (success or failure)

---

## Backward Compatibility

**Version 1.0**: Initial release - no backward compatibility concerns

**Future Versions**:
- CLI arguments remain stable (no breaking changes)
- New modes/options added with defaults (opt-in)
- Database schema migrations handled transparently
- Configuration file format versioned

---

## Testing Contract

### Unit Tests

```bash
pytest tests/test_cli.py -v
```

**Test Coverage**:
- Mode selection validation
- Help/version output
- Error handling for each exit code
- Progress message formatting
- Environment variable validation

### Integration Tests

```bash
# End-to-end with test configuration
python agents/benchmark_intelligence/main.py snapshot --config tests/config/test_labs.yaml
```

**Test Scenarios**:
- Full pipeline with 2 test models
- Report generation from test snapshot
- Error recovery and graceful degradation
- Incremental updates (hash-based skipping)

---

## Contract Version

**Version**: 1.0
**Date**: 2026-04-03
**Status**: Stable

**Changes**:
- Initial contract definition
- Three execution modes defined
- Exit codes standardized
- Progress output format specified
