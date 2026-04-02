# Execution Plan: Implementation to Meet SPECIFICATIONS.md v1.2

**Analysis Date:** 2026-04-02
**Current Code Review:** Complete
**Priority System:** P0 (Critical) → P1 (High) → P2 (Medium) → P3 (Low) → Phase 2 (Future)

---

## Executive Summary

**Current State Assessment:**
- ✅ Core discovery, extraction, consolidation, classification implemented
- ✅ Basic document fetching exists (model cards, some fallback)
- ✅ SQLite caching with content hashing partially implemented
- ✅ Reporting generates 7 sections
- ❌ **20 critical gaps** prevent specification compliance
- ❌ **Missing components:** PDF parsing, Google scraping, taxonomy evolution, proper progress reporting

**Total Work Items:**
- Phase 1 (v1.0): 30 tasks across 4 priority levels
- Phase 2 (v2.0): Web Dashboard + 6 tasks

---

## Implementation Checklist

### Phase 1: Core System (v1.0)

#### Priority 0: Critical Blockers
- [x] P0-1: Move labs.yaml to project root ✅
- [x] P0-2: Implement PDF parsing (pdfplumber + PyPDF2) ✅
- [x] P0-3: Implement Google search scraping ✅
- [x] P0-4: Implement adaptive taxonomy evolution ✅
- [x] P0-5: Fix progress reporting format (add ✓, ✗, ↻, ⊕ symbols) ✅

#### Priority 1: High Importance
- [x] P1-1: Update database schema (deleted_at, extraction_failed, indexes) ✅
- [x] P1-2: Implement "most common nomenclature" consolidation ✅
- [x] P1-3: Update root README auto-update ✅
- [x] P1-4: Implement retry policy configuration ✅
- [x] P1-5: Implement 12-month rolling window ✅
- [x] P1-6: Handle deleted models ✅
- [x] P1-7: Implement failed extraction "never retry" policy ✅

#### Priority 2: Medium Importance
- [ ] P2-1: Implement side-by-side benchmark disambiguation
- [ ] P2-2: Add lab→GitHub org mapping
- [ ] P2-3: Track source type in model_benchmarks
- [ ] P2-4: Implement deprecated benchmark tracking
- [ ] P2-5: Add Google search configuration
- [ ] P2-6: Add PDF constraints configuration
- [ ] P2-7: Implement report generation retry
- [ ] P2-8: Archive taxonomy only on change

#### Priority 3: Polish & Optimization
- [ ] P3-1: Implement document fetching parallelization
- [ ] P3-2: Add arXiv author filtering
- [ ] P3-3: Improve error messages
- [ ] P3-4: Add unit tests (>80% coverage)
- [ ] P3-5: Update documentation

### Phase 2: Web Dashboard (v2.0)
- [ ] Phase 2.1: Data export (JSON generation)
- [ ] Phase 2.2: React dashboard shell
- [ ] Phase 2.3: Benchmark Explorer view
- [ ] Phase 2.4: Visualizations (D3.js charts)
- [ ] Phase 2.5: Remaining views (Model Comparison, Lab Analytics, Taxonomy Browser)
- [ ] Phase 2.6: Polish & deploy to GitHub Pages

**Progress:** 12/36 tasks complete (33.3%)

---

## Priority 0: CRITICAL BLOCKERS (Must Fix First)

These items completely block specification compliance and must be addressed before anything else.

### P0-1: Move labs.yaml to Project Root ⚠️ BLOCKING
**Current:** `agents/benchmark_intelligence/config/labs.yaml`
**Required:** `/workspace/repos/trending_benchmarks/labs.yaml`
**Spec:** Section 3.1, 9.1
**Complexity:** Low

**Tasks:**
1. Move file from `agents/benchmark_intelligence/config/labs.yaml` → `labs.yaml` (root)
2. Update all imports in:
   - `agents/benchmark_intelligence/tools/discover_models.py`
   - `agents/benchmark_intelligence/main.py`
3. Update README references
4. Test discovery still works

**Risk:** Low - simple refactor
**Blocker for:** All configuration-dependent features

---

### P0-2: Implement PDF Parsing ⚠️ BLOCKING
**Current:** Not implemented
**Required:** pdfplumber + PyPDF2 with AI section detection
**Spec:** Section 2.1, 2.3, 10.2
**Complexity:** Medium

**Tasks:**
1. Add dependencies to requirements.txt:
   ```
   pdfplumber>=0.10.0
   PyPDF2>=3.0.0
   ```

2. Create `agents/benchmark_intelligence/tools/pdf_parser.py`:
   ```python
   def download_pdf(url, max_size_mb=10, timeout=120) -> bytes
   def extract_text_from_pdf(pdf_bytes) -> tuple[str, list[list]]
       # Returns (text, tables) using pdfplumber
       # Fallback to PyPDF2 if pdfplumber fails
   def truncate_content(text, max_chars=50000) -> str
   ```

3. Integrate into `fetch_docs.py`:
   - Detect PDF URLs
   - Download with size/timeout constraints
   - Extract text + tables
   - Pass to AI for section detection + extraction (single call)

4. Update extraction prompt to handle:
   "Identify sections with benchmark info AND extract all benchmark names"

5. Handle errors:
   - <500 chars → skip (unreadable)
   - Timeout/too large → log, skip
   - Cache hash with extraction_failed flag

**Dependencies:** None
**Blocker for:** arXiv papers, GitHub technical reports

---

### P0-3: Implement Google Search Scraping ⚠️ BLOCKING
**Current:** Not implemented
**Required:** Scrape Google results for document discovery
**Spec:** Section 2.2
**Complexity:** Medium

**Tasks:**
1. Create `agents/benchmark_intelligence/tools/google_search.py`:
   ```python
   def scrape_google_search(
       query: str,
       max_results: int = 10,
       delay: float = 2.0
   ) -> list[dict]
       # Returns: [{"url": "...", "title": "...", "snippet": "..."}, ...]
   ```

2. Implementation:
   - Construct Google search URL with query
   - Set User-Agent header (from config)
   - Parse results with BeautifulSoup
   - Extract URLs, titles, snippets
   - Handle rate limiting (retry with exponential backoff)
   - Handle CAPTCHAs (skip after 3 retries)

3. Update `fetch_docs.py` to use Google search:
   - For arXiv: Check model card first, else Google search
   - For GitHub PDFs: Try known patterns, else Google
   - For blogs: Google search only (no domain restrictions)

4. Add arXiv author filtering:
   - Fetch arXiv paper metadata
   - Check if authors include lab name
   - Select paper with lab authors if multiple found

**Dependencies:** BeautifulSoup (already installed)
**Blocker for:** All document types except HuggingFace model cards

---

### P0-4: Implement Adaptive Taxonomy Evolution ⚠️ BLOCKING
**Current:** Static categories, no evolution
**Required:** AI-powered taxonomy evolution on every run
**Spec:** Section 5.1, 5.2
**Complexity:** Medium

**Tasks:**
1. Create `agents/benchmark_intelligence/tools/taxonomy_manager.py`:
   ```python
   def load_current_taxonomy(path) -> dict
   def analyze_benchmark_fit(benchmarks, taxonomy) -> dict
       # Returns: {"well_categorized": [...], "poor_fit": [...]}
   def propose_new_categories(poor_fit_benchmarks, existing_taxonomy) -> list[str]
       # AI-powered category proposal
   def evolve_taxonomy(current, proposed_categories) -> dict
   def archive_taxonomy_if_changed(old, new, timestamp) -> Optional[Path]
   def update_taxonomy_file(taxonomy, path) -> None
   ```

2. Create `/archive/` directory structure

3. Update `main.py` consolidation phase:
   ```python
   # After consolidation
   taxonomy = load_current_taxonomy("benchmark_taxonomy.md")
   analysis = analyze_benchmark_fit(all_benchmarks, taxonomy)
   if analysis["poor_fit"]:
       new_categories = propose_new_categories(analysis["poor_fit"], taxonomy)
       evolved_taxonomy = evolve_taxonomy(taxonomy, new_categories)
       archive_path = archive_taxonomy_if_changed(taxonomy, evolved_taxonomy, timestamp)
       update_taxonomy_file(evolved_taxonomy, "benchmark_taxonomy.md")
   ```

4. Update `classify.py` to load taxonomy from file (not hardcoded)

5. Store taxonomy version in snapshots table

**Dependencies:** Claude client (exists)
**Blocker for:** Accurate benchmark categorization, reporting

---

### P0-5: Fix Progress Reporting Format ⚠️ BLOCKING
**Current:** Basic logs without symbols/structure
**Required:** Structured format with ✓, ✗, ↻, ⊕ symbols
**Spec:** Section 8.1, 8.2
**Complexity:** Medium

**Tasks:**
1. Update all `logger.info()` calls in `main.py`:

   **Discovery phase:**
   ```python
   logger.info(f"[Discovery] Querying {len(labs)} labs...")
   logger.info(f"[Discovery] Found {total} models from {', '.join(labs[:3])}...")
   logger.info(f"[Discovery] Applied filters: {passed} models passed ({excluded} excluded)")
   ```

   **Processing phase:**
   ```python
   logger.info(f"[Processing] Model {i}/{total}: {model_id}")
   logger.info(f"  ✓ Fetched model card")
   logger.info(f"  ✓ Fetched GitHub README")
   logger.info(f"  ✓ Found arXiv paper")
   logger.info(f"  ✓ Extracted {count} benchmarks")
   # OR
   logger.info(f"  ↻ Cached (no changes)")
   logger.info(f"  ↻ Updated metadata (downloads: {old} → {new})")
   ```

   **Consolidation phase:**
   ```python
   logger.info(f"[Consolidation] Found {unique} unique benchmark names")
   logger.info(f"[Consolidation] Consolidated to {canonical} canonical names")
   logger.info(f"[Classification] Classified {count} benchmarks across {categories} categories")
   ```

   **Reporting phase:**
   ```python
   logger.info(f"[Reporting] Generating 7 sections...")
   logger.info(f"[Reporting] ✓ Report saved: {path}")
   logger.info(f"[Reporting] ✓ Updated root README.md")
   ```

2. Add symbols helper function:
   ```python
   SYMBOLS = {"success": "✓", "error": "✗", "cached": "↻", "new": "⊕"}
   ```

**Dependencies:** None
**Blocker for:** User experience, specification compliance

---

## Priority 1: HIGH IMPORTANCE (Core Functionality)

These features are critical for data quality and specification compliance.

### P1-1: Update Database Schema
**Current:** Missing columns and indexes
**Required:** Add deleted_at, extraction_failed, indexes
**Spec:** Section 6.1
**Complexity:** Medium

**Tasks:**
1. Add migration script or update cache.py initialization:
   ```sql
   -- Add to models table
   ALTER TABLE models ADD COLUMN deleted_at TEXT;

   -- Add to documents table
   ALTER TABLE documents ADD COLUMN extraction_failed BOOLEAN DEFAULT 0;

   -- Remove content column (per spec)
   -- NOTE: This requires recreation, can't ALTER to remove in SQLite

   -- Add missing indexes
   CREATE INDEX IF NOT EXISTS idx_models_deleted ON models(deleted_at);
   CREATE INDEX IF NOT EXISTS idx_benchmarks_last_seen ON benchmarks(last_seen);
   CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);
   ```

2. Update `cache.py` to:
   - Set `deleted_at` when model no longer in HuggingFace
   - Set `extraction_failed` on errors
   - Never store document content (only hash)

**Dependencies:** None
**Impact:** Data integrity, performance

---

### P1-2: Implement "Most Common Nomenclature" Consolidation
**Current:** Basic fuzzy matching, no frequency analysis
**Required:** Count variants, choose most common
**Spec:** Section 4.3
**Complexity:** Medium

**Tasks:**
1. Update `consolidate.py`:
   ```python
   def count_variant_usage(benchmark_variants, model_benchmarks) -> dict:
       """Count how many models use each variant"""
       # Returns: {"MMLU": 10, "mmlu": 3, "Mmlu": 1}

   def select_canonical_name(variants, counts) -> str:
       """Choose most common, tie-break by case"""
       most_common = max(counts, key=counts.get)
       # If tie, prefer uppercase > lowercase > mixed
       return most_common
   ```

2. Update consolidation logic:
   - Group variants (existing fuzzy + AI)
   - Count usage per variant across all models
   - Select canonical name = most frequently used
   - Store mapping in database

**Dependencies:** Existing consolidate.py
**Impact:** Consistent benchmark names

---

### P1-3: Update Root README Auto-Update
**Current:** Updates agent README only
**Required:** Update root README with latest report
**Spec:** Section 7.3, 7.4
**Complexity:** Medium

**Tasks:**
1. Update `reporting.py` `_update_readme()`:
   ```python
   def _update_readme(self, report_path: str):
       root_readme = Path("/workspace/repos/trending_benchmarks/README.md")

       # Read current README
       content = root_readme.read_text()

       # Update "Latest Report" link
       # Replace link in ## 📊 Latest Report section

       # Update key findings (models, benchmarks, date)
       # Replace in **Key Findings** section

       root_readme.write_text(updated_content)
   ```

2. Add regex patterns to find and replace:
   - Latest report link
   - Key findings stats
   - Last updated date

**Dependencies:** None
**Impact:** Project navigation, visibility

---

### P1-4: Implement Retry Policy Configuration
**Current:** Hardcoded retries
**Required:** Configurable exponential backoff
**Spec:** Section 2.3, 9.1
**Complexity:** Medium

**Tasks:**
1. Add to `labs.yaml`:
   ```yaml
   retry_policy:
     max_attempts: 3
     initial_delay: 1.0
     backoff_multiplier: 2.0
     max_delay: 60
   ```

2. Create `agents/benchmark_intelligence/tools/retry_helper.py`:
   ```python
   def retry_with_backoff(func, config, *args, **kwargs):
       """Execute function with exponential backoff"""
   ```

3. Use in:
   - Document fetching
   - Google search
   - Claude API calls

**Dependencies:** None
**Impact:** Reliability, rate limit handling

---

### P1-5: Implement 12-Month Rolling Window
**Current:** Not consistently enforced
**Required:** All queries filter to 12 months from today
**Spec:** Section 1.3, 7.1
**Complexity:** Medium

**Tasks:**
1. Update `cache.py` query methods:
   ```python
   def get_trending_models(self, since_date=None):
       if since_date is None:
           # Default to 12 months ago from today
           since_date = (datetime.utcnow() - timedelta(days=365)).isoformat()
       # Query with filter
   ```

2. Update all temporal queries in `reporting.py`:
   - Trending models
   - Emerging benchmarks (90 days)
   - Temporal trends
   - Deprecated benchmarks (6 months)

3. Ensure discovery filter uses rolling window:
   ```python
   date_filter_months = config.get("date_filter_months", 12)
   cutoff = datetime.now(timezone.utc) - relativedelta(months=date_filter_months)
   ```

**Dependencies:** None
**Impact:** Data accuracy, specification compliance

---

### P1-6: Handle Deleted Models
**Current:** Not implemented
**Required:** Mark as deleted, exclude from reports
**Spec:** Section 3.3
**Complexity:** Medium

**Tasks:**
1. In `main.py` discovery phase:
   ```python
   # After discovering models from HuggingFace
   existing_model_ids = cache.get_all_model_ids()
   discovered_ids = {m["id"] for m in models}
   deleted_ids = existing_model_ids - discovered_ids

   for model_id in deleted_ids:
       cache.mark_as_deleted(model_id, timestamp=datetime.utcnow())
   ```

2. In `cache.py`:
   ```python
   def mark_as_deleted(self, model_id, timestamp):
       """Set deleted_at timestamp"""

   def get_active_models(self):
       """Return models where deleted_at IS NULL"""
   ```

3. Update reporting to filter out deleted models

**Dependencies:** Database schema update (P1-1)
**Impact:** Data integrity

---

### P1-7: Implement Failed Extraction "Never Retry" Policy
**Current:** May retry failed extractions
**Required:** Mark as failed, never retry
**Spec:** Section 2.3
**Complexity:** Medium

**Tasks:**
1. Update `cache.py`:
   ```python
   def mark_extraction_failed(self, model_id, url):
       """Set extraction_failed=true"""

   def should_skip_extraction(self, model_id, url, new_hash):
       """
       Skip if:
       - extraction_failed=true (regardless of hash)
       - hash unchanged and extraction succeeded previously
       """
   ```

2. Update extraction logic in `main.py`:
   ```python
   if cache.should_skip_extraction(model_id, url, content_hash):
       logger.info(f"  ↻ Skipping (failed previously or unchanged)")
       continue

   try:
       benchmarks = extract_benchmarks(content)
   except Exception as e:
       cache.mark_extraction_failed(model_id, url)
       cache.update_document_hash(model_id, url, content_hash)
       logger.warning(f"  ✗ Extraction failed: {e}")
   ```

**Dependencies:** Database schema update (P1-1)
**Impact:** Performance, avoid infinite retries

---

## Priority 2: MEDIUM IMPORTANCE (Quality & Features)

These improve data quality and user experience but aren't blocking.

### P2-1: Implement Side-by-Side Benchmark Disambiguation
**Current:** Basic consolidation
**Required:** Detect co-occurrence, mark as distinct
**Spec:** Section 4.3
**Complexity:** Medium

**Tasks:**
1. Update extraction to track co-occurrence:
   ```python
   def extract_benchmarks_with_cooccurrence(content):
       benchmarks = extract_benchmark_names(content)
       # Return: [{"name": "MMLU", "co_occurs_with": ["MMLU-Pro", "GSM8K"]}, ...]
   ```

2. Update `consolidate.py`:
   ```python
   def mark_distinct_benchmarks(variants):
       """If found side-by-side in same document, don't merge"""
       # Example: "MMLU" and "MMLU-Pro" mentioned together → distinct
   ```

**Dependencies:** None
**Impact:** Accuracy in consolidation

---

### P2-2: Add Lab→GitHub Org Mapping
**Current:** Guesswork
**Required:** Explicit mapping configuration
**Spec:** Section 2.2 (implied)
**Complexity:** Medium

**Tasks:**
1. Add to `labs.yaml`:
   ```yaml
   lab_mappings:
     Qwen: QwenLM
     meta-llama: meta-llama
     mistralai: mistralai
     google: google-research
     microsoft: microsoft
     deepseek-ai: deepseek-ai
     # ...
   ```

2. Update `fetch_docs.py` to use mapping:
   ```python
   def get_github_org(lab_name, mappings):
       return mappings.get(lab_name, lab_name)  # Fallback to lab name
   ```

**Dependencies:** None
**Impact:** Reliability of GitHub document discovery

---

### P2-3: Track Source Type in model_benchmarks
**Current:** source_type exists but may not be fully populated
**Required:** Every benchmark association has source_type
**Spec:** Section 6.1
**Complexity:** Medium

**Tasks:**
1. Update extraction to always pass source_type:
   ```python
   cache.add_benchmark_to_model(
       model_id=model_id,
       benchmark_name=benchmark,
       source_type=doc_type,  # model_card, arxiv_paper, github_pdf, blog
       source_url=url
   )
   ```

2. Add source breakdown to report:
   ```markdown
   ### Benchmark Sources
   - Model cards: 45
   - arXiv papers: 32
   - GitHub reports: 18
   - Blogs: 12
   ```

**Dependencies:** None
**Impact:** Data provenance visibility

---

### P2-4: Implement Deprecated Benchmark Tracking
**Current:** last_seen field exists but not used
**Required:** Track and report potentially deprecated benchmarks
**Spec:** Section 7.2
**Complexity:** Medium

**Tasks:**
1. Update `cache.py`:
   ```python
   def update_benchmark_last_seen(self, benchmark_id, timestamp):
       """Update last_seen whenever benchmark mentioned"""

   def get_potentially_deprecated(self, months=6):
       """Return benchmarks not seen in last N months"""
   ```

2. Update extraction to set last_seen:
   ```python
   for benchmark in extracted:
       cache.add_or_update_benchmark(benchmark, last_seen=datetime.utcnow())
   ```

3. Add to Temporal Trends report section:
   ```markdown
   ### Potentially Deprecated Benchmarks
   Benchmarks not seen in last 6 months:
   - BenchmarkX (last seen: 2025-09-15)
   - BenchmarkY (last seen: 2025-08-22)
   ```

**Dependencies:** None
**Impact:** Insight into benchmark lifecycle

---

### P2-5: Add Google Search Configuration
**Current:** Not implemented
**Required:** Configurable search parameters
**Spec:** Section 9.1
**Complexity:** Medium

**Tasks:**
1. Add to `labs.yaml`:
   ```yaml
   google_search:
     max_results_per_query: 10
     delay_between_searches: 2
     user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
     max_retries_on_block: 3
     fallback_strategy: "skip"
   ```

2. Load config in `google_search.py`

**Dependencies:** P0-3 (Google search implementation)
**Impact:** Configuration flexibility

---

### P2-6: Add PDF Constraints Configuration
**Current:** Not implemented
**Required:** Configurable PDF limits
**Spec:** Section 9.1, 10.2
**Complexity:** Medium

**Tasks:**
1. Add to `labs.yaml`:
   ```yaml
   pdf_constraints:
     max_file_size_mb: 10
     download_timeout_seconds: 120
     max_extracted_chars: 50000
   ```

2. Load config in `pdf_parser.py`

**Dependencies:** P0-2 (PDF parsing)
**Impact:** Resource management

---

### P2-7: Implement Report Generation Retry
**Current:** Unknown
**Required:** Retry on failure
**Spec:** Section 9.1 (retry_on_failure: true)
**Complexity:** Medium

**Tasks:**
1. Update `main.py`:
   ```python
   for attempt in range(3):
       try:
           report_path = self._generate_report()
           break
       except Exception as e:
           if attempt == 2:
               raise
           logger.warning(f"Report generation failed (attempt {attempt+1}/3): {e}")
           time.sleep(2 ** attempt)
   ```

**Dependencies:** None
**Impact:** Reliability

---

### P2-8: Archive Taxonomy Only on Change
**Current:** Not implemented
**Required:** Compare and archive only if different
**Spec:** Section 5.2
**Complexity:** Medium

**Tasks:**
1. In `taxonomy_manager.py`:
   ```python
   def archive_taxonomy_if_changed(old_taxonomy, new_taxonomy, timestamp):
       if old_taxonomy == new_taxonomy:
           logger.info("Taxonomy unchanged, no archive created")
           return None

       archive_path = f"archive/benchmark_taxonomy_{timestamp}.md"
       save_taxonomy(old_taxonomy, archive_path)
       return archive_path
   ```

**Dependencies:** P0-4 (Taxonomy evolution)
**Impact:** Avoid duplicate archives

---

## Priority 3: LOW IMPORTANCE (Polish & Optimization)

Nice-to-have improvements that can be deferred.

### P3-1: Implement Document Fetching Parallelization
**Current:** Serial
**Required:** Parallel (max 5 concurrent)
**Spec:** Section 12.3
**Complexity:** Medium

**Tasks:**
1. Use `concurrent.futures.ThreadPoolExecutor`:
   ```python
   from concurrent.futures import ThreadPoolExecutor, as_completed

   with ThreadPoolExecutor(max_workers=5) as executor:
       futures = [
           executor.submit(fetch_document, url)
           for url in document_urls
       ]
       for future in as_completed(futures):
           result = future.result()
   ```

**Dependencies:** None
**Impact:** Performance improvement

---

### P3-2: Add arXiv Author Filtering
**Current:** Not implemented
**Required:** Select paper with lab authors
**Spec:** Section 2.2
**Complexity:** Medium

**Tasks:**
1. Fetch arXiv metadata (author list)
2. Check if any author name contains lab name
3. Prefer paper with matching authors

**Dependencies:** P0-3 (Google search)
**Impact:** Accuracy of paper selection

---

### P3-3: Improve Error Messages
**Current:** Basic logging
**Required:** Detailed, actionable error messages
**Spec:** Section 12.1
**Complexity:** Medium

**Dependencies:** None
**Impact:** Debugging experience

---

### P3-4: Add Unit Tests
**Current:** Likely minimal
**Required:** >80% coverage for new code
**Spec:** Section 12.2
**Complexity:** Medium

**Dependencies:** All major features complete
**Impact:** Code quality, maintainability

---

### P3-5: Update Documentation
**Current:** Partially outdated
**Required:** README, inline comments consistent with spec
**Spec:** Section 13
**Complexity:** Medium

**Dependencies:** All features complete
**Impact:** Onboarding, maintenance

---


## Phase 2: Web Dashboard (v2.0 Feature)

The web dashboard is a future enhancement, not required for Phase 1 (v1.0) completion.

### Overview
**Purpose:** Interactive visualization of benchmark trends and model intelligence
**Approach:** Fully static site generation (no backend server)
**Spec:** Section 11

### Dashboard Features

#### Core Views
1. **Benchmark Explorer**
   - Filter/search all benchmarks
   - See usage trends over time
   - View models using each benchmark

2. **Model Comparison**
   - Side-by-side benchmark comparison for selected models
   - Highlight differences
   - Link to model cards

3. **Lab Analytics**
   - Per-lab statistics (models, benchmarks, preferences)
   - Average downloads/likes per lab
   - Benchmark diversity scores

4. **Temporal Trends**
   - Interactive time-series charts (D3.js)
   - Benchmark popularity evolution
   - New vs deprecated benchmarks

5. **Taxonomy Browser**
   - Explore benchmark categories
   - See examples per category
   - View category distributions

### Technical Implementation

**Stack:**
- Frontend: React + D3.js (charts)
- Data: Pre-generated JSON files from SQLite
- Build: Static HTML/CSS/JS bundle
- Deploy: GitHub Pages (no backend required)

**Generation Process:**
1. After report generation, query SQLite for dashboard data
2. Generate JSON files:
   - `benchmarks.json` - All benchmarks with metadata
   - `models.json` - All models with metadata
   - `trends.json` - Time-series data
   - `labs.json` - Lab-specific statistics
   - `taxonomy.json` - Current category structure
3. Build React app to static bundle
4. Deploy to `docs/` folder for GitHub Pages

### Implementation Tasks

#### Phase 2.1: Data Export
**Complexity:** Low

**Tasks:**
1. Create `agents/benchmark_intelligence/dashboard/export_data.py`:
   ```python
   def export_benchmarks_json(cache) -> None
   def export_models_json(cache) -> None
   def export_trends_json(cache) -> None
   def export_labs_json(cache) -> None
   def export_taxonomy_json() -> None
   ```

2. Integrate into `main.py` after report generation:
   ```python
   if config.get("dashboard", {}).get("enabled", False):
       export_dashboard_data(cache)
   ```

**Dependencies:** None
**Output:** JSON files in `docs/data/`

---

#### Phase 2.2: React Dashboard Shell
**Complexity:** Medium

**Tasks:**
1. Initialize React project in `dashboard/`:
   ```bash
   npx create-react-app dashboard
   cd dashboard
   npm install d3 react-router-dom
   ```

2. Create component structure:
   - `src/components/BenchmarkExplorer.jsx`
   - `src/components/ModelComparison.jsx`
   - `src/components/LabAnalytics.jsx`
   - `src/components/TemporalTrends.jsx`
   - `src/components/TaxonomyBrowser.jsx`

3. Configure build to output to `/docs`

**Dependencies:** Phase 2.1
**Output:** Basic navigation and layout

---

#### Phase 2.3: Benchmark Explorer View
**Complexity:** Medium

**Tasks:**
1. Implement search/filter functionality
2. Display benchmark list with metadata
3. Show models using each benchmark
4. Add sorting (by name, usage, date)

**Dependencies:** Phase 2.2
**Output:** Functional benchmark search

---

#### Phase 2.4: Visualizations (D3.js)
**Complexity:** High

**Tasks:**
1. Time-series charts for temporal trends
2. Bar charts for category distribution
3. Scatter plots for model comparisons
4. Interactive tooltips and zooming

**Dependencies:** Phase 2.2
**Output:** Interactive charts

---

#### Phase 2.5: Remaining Views
**Complexity:** Medium

**Tasks:**
1. Implement Model Comparison view
2. Implement Lab Analytics view
3. Implement Taxonomy Browser view
4. Add navigation between views

**Dependencies:** Phase 2.2, 2.4
**Output:** All 5 views functional

---

#### Phase 2.6: Polish & Deploy
**Complexity:** Low

**Tasks:**
1. Add CSS styling (responsive design)
2. Optimize bundle size
3. Add loading states
4. Configure GitHub Pages
5. Add README for dashboard

**Dependencies:** Phase 2.5
**Output:** Production-ready dashboard

---

### Dashboard Configuration

Add to `labs.yaml`:
```yaml
dashboard:
  enabled: false  # Enable when ready
  output_dir: "docs"
  data_dir: "docs/data"
  build_command: "cd dashboard && npm run build"
```

### Deployment

1. Build static files: `npm run build`
2. Output to `docs/` folder
3. Enable GitHub Pages in repository settings
4. Point to `docs/` folder
5. Access at: `https://username.github.io/trending_benchmarks/`

### Success Criteria

- ✅ All 5 views functional
- ✅ Data loads from JSON files
- ✅ Charts interactive and responsive
- ✅ Navigation between views works
- ✅ Deployed to GitHub Pages
- ✅ Updates automatically when agent runs

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Google blocking | High | High | Implement proper delays, user-agent rotation, fallback to skip |
| PDF parsing failures | Medium | Medium | Graceful fallback to PyPDF2, skip unreadable PDFs |
| Claude API rate limits | Medium | High | Serial processing, exponential backoff, cost monitoring |
| Taxonomy over-evolution | Low | Medium | Human review of new categories, confidence thresholds |
| Database migration issues | Low | High | Backup database before schema changes, test on copy first |
| Time estimation too optimistic | High | Medium | This is 2-2.5 weeks of focused work, likely will take 3-4 weeks |

---

## Testing Strategy

### Per-Priority Testing

**P0 tasks:** Integration test after each (run with 3-5 models)
**P1 tasks:** Unit test + integration test
**P2 tasks:** Unit test minimum
**P3 tasks:** Manual testing acceptable

### Full System Test (After Phase 1 Complete)
1. Clear cache completely
2. Run with 15 labs, all filters
3. Verify:
   - All models discovered
   - All document types fetched (including PDFs)
   - Benchmarks extracted from all sources
   - Taxonomy evolved
   - Report generated with all 7 sections
   - Root README updated
   - Progress reporting matches spec

---

## Success Metrics

**Acceptance Criteria (from SPECIFICATIONS.md Section 13):**
- ✅ All configured labs queried
- ✅ All document types fetched (model cards, GitHub, PDFs, blogs)
- ✅ Benchmarks extracted from all sources
- ✅ Consolidation handles variants
- ✅ Adaptive taxonomy working
- ✅ Zero irrelevant models
- ✅ ALL models in reports (no limits)
- ✅ Progress reporting matches spec format
- ✅ Incremental updates work
- ✅ Taxonomy archived
- ✅ labs.yaml at root
- ✅ Root README updated
- ✅ Documentation complete

**Performance Metrics:**
- Run time <90 minutes for 100 models
- Cache hit rate >70% on incremental runs
- PDF success rate >80%
- Google search success rate >90%

---

## Open Questions

1. **Should we implement P3 items at all, or defer to v2.0?**
   - Recommendation: Do P3-1, P3-2 (functional value), defer P3-4, P3-5 to later

2. **Database migration strategy?**
   - Option A: Backup and recreate (clean slate)
   - Option B: ALTER statements where possible
   - Recommendation: Option A - recreate for documents table (content removal)

3. **Testing dataset size?**
   - Start with 3 labs, 5 models each (15 total) for development
   - Full test with all 15 labs before production

4. **Who reviews taxonomy evolution proposals?**
   - Auto-approve for now (confidence threshold 0.7)
   - Add manual review workflow later if needed

---

**Status:** Ready for Review and Approval
**Next Step:** Stakeholder sign-off → Begin P0 tasks
**Execution:** Will be performed by AI agents
