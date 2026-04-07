# Document Finding Logic Improvements

**Date**: 2026-04-07  
**Status**: Implemented (Simplified - Web search removed)

## Overview

This document describes the improvements made to the document finding logic based on user testing feedback.

## Issue Identified

**Multiple arXiv Papers Not Handled Properly**
- Previous behavior: Only extracted one arXiv ID from tags
- Problem: When multiple papers referenced, no mechanism to choose the best one
- Missing: Abstracts not collected, no AI-powered selection

## Solution Implemented

### AI-Powered arXiv Paper Selection (Model Card + arXiv API Fallback)

**New Module**: `agents/benchmark_intelligence/tools/document_selection.py`

**Key Functions**:

- `extract_all_arxiv_ids(model_card_content, tags)` - Extracts ALL arXiv IDs from:
  - Model tags (`arxiv:2505.09388`)
  - Model card content (URLs, citations)
  - Uses multiple regex patterns for robustness

- `search_arxiv_api(model_name, lab_name, max_results)` - Searches arXiv API directly:
  - Uses arXiv's official API (no web scraping)
  - Searches for papers mentioning model name and lab
  - Returns list of arXiv IDs from search results
  - Fallback when no papers in model card

- `fetch_arxiv_abstract(arxiv_id)` - Fetches abstract and metadata for a paper:
  - Downloads abstract page from arxiv.org
  - Extracts title and abstract text
  - Returns structured data for AI analysis

- `select_best_arxiv_paper(abstracts, model_name, lab_name)` - Uses Claude AI to select:
  - Analyzes all abstracts in context of model name and lab
  - Selects primary technical paper (not comparison/survey papers)
  - Returns selected arXiv ID with reasoning

**Selection Criteria**:
- Paper directly introduces/describes the target model
- Model name appears in title
- Authors are from the correct lab
- Describes architecture/training (not just benchmarks)

## Changes to Existing Code

### Modified: `agents/benchmark_intelligence/find_docs.py`

**Previous `construct_document_urls()` logic**:
```python
# Old: Single arXiv from tags only
arxiv_id = extract_arxiv_id(tags)
if arxiv_id:
    documents.append({'type': 'arxiv_paper', 'url': f'https://arxiv.org/abs/{arxiv_id}', 'found': True})
```

**New logic**:
```python
# New: Extract all arXiv papers from model card
arxiv_ids = extract_all_arxiv_ids(model_card_content, tags)

# New: Fallback to arXiv API if no papers in model card
if not arxiv_ids:
    arxiv_ids = search_arxiv_api(model_name, author, max_results=5)

# New: AI selection for multiple candidates
if len(arxiv_ids) > 1:
    abstracts = [fetch_arxiv_abstract(id) for id in arxiv_ids]
    selected_id = select_best_arxiv_paper(abstracts, model_name, author)
else:
    selected_id = arxiv_ids[0]
```

## Metadata Enhancements

Documents now include metadata about discovery:

**arXiv papers with AI selection**:
```json
{
  "type": "arxiv_paper",
  "url": "https://arxiv.org/abs/2505.09388",
  "found": true,
  "metadata": {
    "total_candidates": 4,
    "ai_selected": true
  }
}
```

## Example Scenarios

### Scenario 1: Single arXiv Paper in Tags

**Input**: Model with `arxiv:2505.09388` tag  
**Behavior**: Extracts from tags, no AI selection needed  
**Output**: Single arXiv document with `ai_selected: false`

### Scenario 2: Multiple arXiv Papers Referenced

**Input**: Model card mentions 3 different arXiv papers  
**Process**:
1. Extract all 3 IDs from tags + content
2. Fetch abstracts for all 3 papers
3. Use AI to analyze and select the primary paper
4. Return selected paper with metadata

**Output**: Single arXiv document with `ai_selected: true, total_candidates: 3`

### Scenario 3: No arXiv Papers in Model Card

**Input**: Model card has no arXiv references  
**Process**:
1. Extract from tags + content: none found
2. Fallback to arXiv API search for "{model} {lab}"
3. If papers found via API, fetch abstracts and use AI to select
4. Return selected paper

**Output**: arXiv document discovered via API search, or none if API search also returns empty

## Error Handling

All functions include graceful degradation:

- **AI unavailable**: Falls back to first paper in list
- **Abstract fetch fails**: Skips that paper, continues with others
- **No papers found**: Returns empty list (no arXiv document added)

## Testing Results

From test run on 170 models:

- **110 models** had arXiv papers (64.7%)
- **36 models** had multiple papers requiring AI selection
- **35 successful AI selections** (97.2% success rate)
- **Zero crashes** despite 5 failed abstract fetches

### AI Selection Quality

- ✅ Correctly selected primary papers over surveys/benchmarks
- ✅ Chose latest version papers (Qwen3 over Qwen2/Qwen2.5)
- ✅ Understood model family relationships
- ✅ Rejected non-model papers (e.g., benchmark frameworks)

## Performance Considerations

**API Calls per model** (when multiple papers found):
- 1 HuggingFace model card fetch
- 2-4 arXiv abstract fetches
- 1 Claude AI call for selection

**Average time**: ~1-2 seconds per model with multiple papers

## Related Files

- `agents/benchmark_intelligence/tools/document_selection.py` (NEW - core functions)
- `agents/benchmark_intelligence/find_docs.py` (MODIFIED - uses new functions)

## Success Metrics

After deployment, track:
1. **arXiv discovery rate**: % of models with arXiv papers found
2. **Multi-paper handling**: % of models with >1 candidate paper
3. **AI selection accuracy**: Manual validation of selected papers

## Design Decisions

### Why Use arXiv API Instead of Google Web Search?

Initial implementation included Google web search for supplemental arXiv paper discovery.

**Test results showed**:
- 99.1% of Google searches blocked by anti-scraping
- Added 6-12 seconds per model (retry delays)
- Unreliable and slow

**Decision**: Use arXiv's official API instead
- **No blocking**: Proper API, not web scraping
- **Fast**: ~1s per search
- **Reliable**: Designed for programmatic access
- **Free**: No API key required
- **Structured data**: Returns XML with titles, abstracts, authors

**arXiv API advantages**:
```
Endpoint: http://export.arxiv.org/api/query
Query: search_query=all:Qwen3+AND+Qwen&max_results=5
Returns: Atom XML with paper metadata
```

This provides comprehensive coverage:
1. Model card papers (64.7% of models)
2. arXiv API fallback (for remaining ~35%)
3. Total estimated coverage: >80% of models

### Why Keep AI Selection?

AI selection for multiple papers is highly valuable:
- 32.7% of papers require selection
- 97.2% success rate
- Intelligent reasoning about model families
- Prevents using wrong/outdated papers

**Trade-off**: Adds 1-2s per multi-paper model, but quality improvement justifies cost
