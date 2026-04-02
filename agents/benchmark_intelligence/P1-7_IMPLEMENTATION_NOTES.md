# P1-7: Failed Extraction "Never Retry" Policy - Implementation Notes

## Overview
P1-7 implements the "never retry" policy for failed document extractions as specified in SPECIFICATIONS.md Section 2.4. Once a document extraction fails, it is marked and will never be retried, preventing infinite retries on permanently broken or irrelevant documents.

## Database Changes
The `extraction_failed` column has been added to the `documents` table:
```sql
extraction_failed BOOLEAN DEFAULT 0  -- Flag failed extractions to avoid retries
```

## New Cache Methods

### 1. `mark_extraction_failed(model_id, doc_type, url)`
Marks a document's extraction as failed. Once marked, the document will never be retried for extraction.

```python
try:
    benchmarks = extract_benchmarks(content)
except Exception as e:
    # Mark extraction as failed
    cache.mark_extraction_failed(model_id, doc_type, url)
    # Still cache the content hash to avoid re-downloading
    cache.add_document(model_id, doc_type, url, content_hash, extraction_failed=True)
    logger.warning(f"Extraction failed: {e}")
```

### 2. `should_skip_extraction(model_id, doc_type, url, new_content_hash)`
Determines if document extraction should be skipped.

Returns `True` if:
1. `extraction_failed=True` (never retry failed extractions)
2. Content hash unchanged and extraction succeeded previously

```python
# Before extracting benchmarks from a document
if cache.should_skip_extraction(model_id, doc_type, url, content_hash):
    logger.info(f"Skipping extraction - previous extraction failed or content unchanged")
    continue

# Proceed with extraction...
```

## Usage Example in main.py

```python
# Step 2d: Extract benchmarks from documentation
doc_benchmarks = []
if docs:
    logger.info(f"Extracting benchmarks from {len(docs)} documents...")

    for doc in docs:
        if not doc.get("content"):
            continue

        doc_type = doc.get("doc_type", "unknown")
        url = doc.get("url", "")
        content = doc["content"]
        content_hash = cache._compute_hash(content)

        # P1-7: Check if extraction should be skipped
        if cache.should_skip_extraction(model_id, doc_type, url, content_hash):
            logger.info(f"  ↻ Skipping {doc_type} - failed previously or unchanged")
            continue

        # Attempt extraction
        try:
            benchmarks = extract_benchmarks_from_text(
                text=content,
                source_type=doc_type,
                source_name=url,
            )
            doc_benchmarks.extend(benchmarks.get("benchmarks", []))

            # Cache successful extraction
            cache.add_document(model_id, doc_type, url, content_hash, extraction_failed=False)

        except Exception as e:
            logger.warning(f"  ✗ Extraction failed for {doc_type}: {e}")
            # Mark extraction as failed (never retry)
            cache.mark_extraction_failed(model_id, doc_type, url)
            # Still cache the hash to avoid re-downloading
            cache.add_document(model_id, doc_type, url, content_hash, extraction_failed=True)
```

## Benefits
- **Prevents infinite retries** on permanently broken PDFs, corrupted files, or irrelevant documents
- **Improves performance** by skipping failed extractions on subsequent runs
- **Reduces API costs** by not retrying Claude calls that will fail
- **Only retries on content change** - if a document is updated (new content hash), extraction can be attempted again

## Tie-in with P0-2 (PDF Parsing)
When PDF parsing is implemented, the never-retry policy will be especially useful for:
- Corrupted or unreadable PDFs
- Image-only PDFs without text layer
- PDFs that timeout during extraction
- PDFs with <500 chars of extractable text

## Testing
To test P1-7:
1. Manually mark a document as failed: `cache.mark_extraction_failed(model_id, doc_type, url)`
2. Run extraction again - it should be skipped
3. Update the document content (new hash) - extraction should be attempted again
4. Verify that failed extractions are logged and not retried
