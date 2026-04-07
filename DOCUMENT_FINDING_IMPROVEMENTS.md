# Document Finding Logic Improvements

**Date**: 2026-04-07  
**Status**: Implemented

## Overview

This document describes the improvements made to the document finding logic based on user testing feedback.

## Issues Identified

1. **Multiple arXiv Papers Not Handled Properly**
   - Previous behavior: Only extracted one arXiv ID from tags
   - Problem: When multiple papers referenced, no mechanism to choose the best one
   - Missing: Abstracts not collected, no AI-powered selection

2. **Hardcoded GitHub Paths**
   - Previous behavior: Hardcoded dictionary mapping labs to GitHub organizations
   - Problem: Brittle, fails for new labs, incorrect for repos not following naming pattern
   - Missing: Dynamic discovery via web search

## Solutions Implemented

### 1. AI-Powered arXiv Paper Selection

**New Module**: `agents/benchmark_intelligence/tools/document_selection.py`

**Key Functions**:

- `extract_all_arxiv_ids(model_card_content, tags)` - Extracts ALL arXiv IDs from:
  - Model tags (`arxiv:2505.09388`)
  - Model card content (URLs, citations)
  - Uses multiple regex patterns for robustness

- `fetch_arxiv_abstract(arxiv_id)` - Fetches abstract and metadata for a paper:
  - Downloads abstract page from arxiv.org
  - Extracts title and abstract text
  - Returns structured data for AI analysis

- `select_best_arxiv_paper(abstracts, model_name, lab_name)` - Uses Claude AI to select:
  - Analyzes all abstracts in context of model name and lab
  - Selects primary technical paper (not comparison/survey papers)
  - Returns selected arXiv ID with reasoning

- `discover_arxiv_papers_via_search(model_name, lab_name)` - Web search supplementation:
  - Finds papers not mentioned in model card
  - Uses Google search with targeted queries
  - Returns additional arXiv IDs

**Selection Criteria**:
- Paper directly introduces/describes the target model
- Model name appears in title
- Authors are from the correct lab
- Describes architecture/training (not just benchmarks)

### 2. Web Search-Based GitHub Discovery

**Key Functions**:

- `search_github_repository(model_name, lab_name)` - Dynamic GitHub discovery:
  - Uses Google search to find actual repository
  - Pattern matches `github.com/org/repo` URLs
  - Filters out false positives (issues, pulls, etc.)
  - Returns clean repository URL

**Benefits**:
- Works for all labs (no hardcoded mapping needed)
- Finds correct repo even if naming doesn't follow pattern
- Adapts to organizational changes

## Changes to Existing Code

### Modified: `agents/benchmark_intelligence/find_docs.py`

**Previous `construct_document_urls()` logic**:
```python
# Old: Single arXiv from tags
arxiv_id = extract_arxiv_id(tags)
if arxiv_id:
    documents.append({'type': 'arxiv_paper', 'url': f'https://arxiv.org/abs/{arxiv_id}', 'found': True})

# Old: Hardcoded GitHub org mapping
github_orgs = {'Qwen': 'QwenLM', 'meta-llama': 'meta-llama', ...}
github_org = github_orgs.get(author)
if github_org:
    documents.append({'type': 'github', 'url': f'https://github.com/{github_org}/{model_name}', 'found': False})
```

**New logic**:
```python
# New: Discover all arXiv papers
arxiv_ids_from_card = extract_all_arxiv_ids(model_card_content, tags)
arxiv_ids_from_search = discover_arxiv_papers_via_search(model_name, author)
all_arxiv_ids = list(set(arxiv_ids_from_card + arxiv_ids_from_search))

# New: AI selection for multiple candidates
if len(all_arxiv_ids) > 1:
    abstracts = [fetch_arxiv_abstract(id) for id in all_arxiv_ids]
    selected_id = select_best_arxiv_paper(abstracts, model_name, author)
else:
    selected_id = all_arxiv_ids[0]

# New: Web search for GitHub (no hardcoded paths)
github_url = search_github_repository(model_name, author)
if github_url:
    documents.append({'type': 'github', 'url': github_url, 'found': True, 'metadata': {'discovery_method': 'web_search'}})
```

## Metadata Enhancements

Documents now include metadata about discovery:

```python
{
    'type': 'arxiv_paper',
    'url': 'https://arxiv.org/abs/2505.09388',
    'found': True,
    'metadata': {
        'total_candidates': 3,           # How many papers were considered
        'ai_selected': True              # Whether AI selection was used
    }
}
```

```python
{
    'type': 'github',
    'url': 'https://github.com/QwenLM/Qwen2.5',
    'found': True,
    'metadata': {
        'discovery_method': 'web_search'  # How the URL was found
    }
}
```

## Example Scenarios

### Scenario 1: Single arXiv Paper in Tags

**Input**: Model with `arxiv:2505.09388` tag  
**Behavior**: Extracts from tags, no AI selection needed  
**Output**: Single arXiv document with `ai_selected: False`

### Scenario 2: Multiple arXiv Papers Referenced

**Input**: Model card mentions 3 different arXiv papers  
**Process**:
1. Extract all 3 IDs from content
2. Fetch abstracts for all 3 papers
3. Use AI to analyze and select the primary paper
4. Return selected paper with metadata

**Output**: Single arXiv document with `ai_selected: True, total_candidates: 3`

### Scenario 3: arXiv Papers from Web Search

**Input**: Model card has no arXiv references  
**Process**:
1. Extract from tags/content: none found
2. Perform web search for "{lab} {model} arxiv paper"
3. Find 2 papers via search
4. Fetch abstracts and use AI to select
5. Return selected paper

**Output**: arXiv document discovered via web search

### Scenario 4: GitHub Discovery

**Input**: New lab not in hardcoded mapping  
**Process**:
1. Search Google for "{lab} {model} github repository"
2. Find and validate github.com URLs
3. Return first valid repository URL

**Output**: GitHub document with `discovery_method: 'web_search'`

## Error Handling

All functions include graceful degradation:

- **AI unavailable**: Falls back to first paper in list
- **Web search blocked**: Returns None, continues without GitHub/extra arXiv papers
- **Abstract fetch fails**: Skips that paper, continues with others
- **No papers found**: Returns empty list (no arXiv document added)

## Testing Recommendations

1. **Test with multiple arXiv papers**: Use models with 2-3 papers in model card
2. **Test AI selection**: Verify it chooses the primary paper (not comparison papers)
3. **Test web search fallback**: Use model with no arXiv tags to trigger web search
4. **Test GitHub discovery**: Use new lab not in previous hardcoded mapping
5. **Test error cases**: Disable API key, block web search, verify graceful degradation

## Performance Considerations

**Additional API Calls**:
- +1 arXiv abstract fetch per candidate paper (typically 1-3 papers)
- +1 Claude API call for paper selection (only if >1 candidate)
- +1-2 Google searches per model (GitHub + optional arXiv)

**Optimization**:
- Caching abstracts (same arXiv ID may appear across models)
- Rate limiting already in place for all external calls
- Parallel processing in Stage 3 continues to work

## Migration Notes

**Backward Compatibility**:
- Models with single arXiv tag: No behavior change
- Output format unchanged (still returns list of document dicts)
- Metadata additions are optional fields

**Breaking Changes**:
- None - this is an enhancement that improves discovery, doesn't break existing functionality

## Related Files

- `agents/benchmark_intelligence/tools/document_selection.py` (NEW)
- `agents/benchmark_intelligence/find_docs.py` (MODIFIED)
- `agents/benchmark_intelligence/tools/google_search.py` (USED, not modified)
- `agents/benchmark_intelligence/tools/parallel_fetcher.py` (NO CHANGES, uses URLs from find_docs)

## Success Metrics

After deployment, track:
1. **arXiv discovery rate**: % of models with arXiv papers found
2. **Multi-paper handling**: % of models with >1 candidate paper
3. **AI selection accuracy**: Manual validation of selected papers
4. **GitHub discovery rate**: % of models with GitHub repos found
5. **Web search success**: % of searches returning valid results

## Future Enhancements

1. **Cache abstracts**: Reuse abstracts across multiple models citing same paper
2. **Confidence scores**: Return AI confidence in paper selection
3. **GitHub validation**: Verify GitHub URLs return 200 before adding to documents
4. **Blog post discovery**: Apply similar web search logic to blog posts
5. **Multiple GitHub repos**: Handle models with multiple official repos
