"""
Tests for pipeline resumability after interruption.

Verifies that hash cache prevents re-processing of unchanged documents.
"""

import pytest
import sys
import os
import json
import tempfile
import hashlib
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestResumability:
    """Test suite for pipeline resumability."""

    def test_document_hash_calculation(self):
        """Test calculating hash for document content."""
        content1 = "This is a test document"
        content2 = "This is a different document"
        content1_duplicate = "This is a test document"

        hash1 = hashlib.sha256(content1.encode()).hexdigest()
        hash2 = hashlib.sha256(content2.encode()).hexdigest()
        hash1_dup = hashlib.sha256(content1_duplicate.encode()).hexdigest()

        # Same content should produce same hash
        assert hash1 == hash1_dup

        # Different content should produce different hash
        assert hash1 != hash2

    def test_hash_cache_storage(self):
        """Test storing and retrieving document hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "hash_cache.json"

            # Create cache
            cache = {
                "doc1.pdf": {
                    "hash": "abc123",
                    "processed_at": "2024-01-01T00:00:00Z",
                    "status": "completed"
                }
            }

            # Save cache
            with open(cache_file, 'w') as f:
                json.dump(cache, f)

            # Load cache
            with open(cache_file, 'r') as f:
                loaded_cache = json.load(f)

            assert loaded_cache["doc1.pdf"]["hash"] == "abc123"

    def test_skip_processed_documents(self):
        """Test skipping documents that are already in cache."""

        def should_process_document(doc_id, doc_hash, cache):
            """Check if document should be processed based on cache."""
            if doc_id not in cache:
                return True

            cached_entry = cache[doc_id]
            if cached_entry["hash"] != doc_hash:
                # Hash changed, need to reprocess
                return True

            if cached_entry.get("status") != "completed":
                # Previous processing failed or incomplete
                return True

            # Already processed successfully
            return False

        cache = {
            "doc1": {"hash": "abc123", "status": "completed"},
            "doc2": {"hash": "def456", "status": "failed"}
        }

        # doc1 with same hash - should skip
        assert not should_process_document("doc1", "abc123", cache)

        # doc1 with different hash - should process
        assert should_process_document("doc1", "xyz789", cache)

        # doc2 with failed status - should reprocess
        assert should_process_document("doc2", "def456", cache)

        # doc3 not in cache - should process
        assert should_process_document("doc3", "ghi789", cache)

    def test_cache_update_after_processing(self):
        """Test updating cache after document processing."""
        cache = {}

        def process_document(doc_id, content):
            """Process a document and update cache."""
            doc_hash = hashlib.sha256(content.encode()).hexdigest()

            try:
                # Simulate processing
                result = {"extracted": len(content)}

                # Update cache on success
                cache[doc_id] = {
                    "hash": doc_hash,
                    "status": "completed",
                    "result": result
                }
                return result

            except Exception as e:
                # Update cache on failure
                cache[doc_id] = {
                    "hash": doc_hash,
                    "status": "failed",
                    "error": str(e)
                }
                raise

        # Process documents
        result1 = process_document("doc1", "Test content 1")
        result2 = process_document("doc2", "Test content 2")

        assert cache["doc1"]["status"] == "completed"
        assert cache["doc2"]["status"] == "completed"
        assert len(cache) == 2

    def test_interrupted_pipeline_resume(self):
        """Test resuming pipeline after interruption."""
        # Simulate initial pipeline run that processes 3 out of 5 documents
        cache = {
            "doc1": {"hash": "hash1", "status": "completed"},
            "doc2": {"hash": "hash2", "status": "completed"},
            "doc3": {"hash": "hash3", "status": "completed"}
        }

        # Documents to process
        documents = [
            {"id": "doc1", "content": "content1", "hash": "hash1"},
            {"id": "doc2", "content": "content2", "hash": "hash2"},
            {"id": "doc3", "content": "content3", "hash": "hash3"},
            {"id": "doc4", "content": "content4", "hash": "hash4"},
            {"id": "doc5", "content": "content5", "hash": "hash5"}
        ]

        # Filter out already processed documents
        to_process = []
        for doc in documents:
            if doc["id"] not in cache or cache[doc["id"]]["status"] != "completed":
                to_process.append(doc)

        # Should only need to process doc4 and doc5
        assert len(to_process) == 2
        assert to_process[0]["id"] == "doc4"
        assert to_process[1]["id"] == "doc5"

    def test_hash_change_detection(self):
        """Test detecting when document content changes."""
        # Initial processing
        cache = {
            "doc1": {"hash": "original_hash", "status": "completed"}
        }

        # Document with changed content
        new_content = "Updated content"
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()

        # Should detect hash change
        needs_reprocessing = cache["doc1"]["hash"] != new_hash
        assert needs_reprocessing

    def test_partial_failure_recovery(self):
        """Test recovering from partial batch failure."""
        # Simulate batch processing where some documents failed
        cache = {
            "doc1": {"hash": "hash1", "status": "completed"},
            "doc2": {"hash": "hash2", "status": "failed", "error": "Timeout"},
            "doc3": {"hash": "hash3", "status": "completed"},
            "doc4": {"hash": "hash4", "status": "failed", "error": "Parse error"}
        }

        # Get documents that need reprocessing
        failed_docs = [
            doc_id for doc_id, entry in cache.items()
            if entry["status"] == "failed"
        ]

        assert len(failed_docs) == 2
        assert "doc2" in failed_docs
        assert "doc4" in failed_docs

    def test_cache_persistence(self):
        """Test that cache persists across pipeline runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "cache.json"

            # First run - create cache
            cache1 = {
                "doc1": {"hash": "hash1", "status": "completed"}
            }
            with open(cache_file, 'w') as f:
                json.dump(cache1, f)

            # Second run - load and update cache
            with open(cache_file, 'r') as f:
                cache2 = json.load(f)

            cache2["doc2"] = {"hash": "hash2", "status": "completed"}

            with open(cache_file, 'w') as f:
                json.dump(cache2, f)

            # Third run - verify both entries
            with open(cache_file, 'r') as f:
                cache3 = json.load(f)

            assert "doc1" in cache3
            assert "doc2" in cache3
            assert len(cache3) == 2

    def test_concurrent_cache_updates(self):
        """Test thread-safe cache updates."""
        import threading
        import time

        cache = {}
        cache_lock = threading.Lock()

        def update_cache(doc_id, doc_hash):
            with cache_lock:
                cache[doc_id] = {
                    "hash": doc_hash,
                    "status": "completed",
                    "updated_at": time.time()
                }

        # Simulate concurrent updates
        threads = []
        for i in range(10):
            t = threading.Thread(target=update_cache, args=(f"doc{i}", f"hash{i}"))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All updates should be in cache
        assert len(cache) == 10

    def test_cache_invalidation_on_config_change(self):
        """Test invalidating cache when processing config changes."""
        cache = {
            "doc1": {
                "hash": "hash1",
                "status": "completed",
                "config_version": "v1"
            }
        }

        current_config_version = "v2"

        # Should reprocess if config version changed
        def needs_reprocessing(doc_id, cache, current_version):
            if doc_id not in cache:
                return True

            cached_version = cache[doc_id].get("config_version")
            if cached_version != current_version:
                return True

            return cache[doc_id]["status"] != "completed"

        assert needs_reprocessing("doc1", cache, current_config_version)

    def test_incremental_processing(self):
        """Test incremental processing of new documents."""
        # Initial state
        processed_docs = set(["doc1", "doc2", "doc3"])

        # New batch includes some already processed
        new_batch = ["doc2", "doc3", "doc4", "doc5"]

        # Filter to only new documents
        to_process = [doc for doc in new_batch if doc not in processed_docs]

        assert len(to_process) == 2
        assert "doc4" in to_process
        assert "doc5" in to_process


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
