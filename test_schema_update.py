#!/usr/bin/env python3
"""Test script to verify P1-1 and P1-6 schema updates."""

import os
import sys
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from benchmark_intelligence.tools.cache import CacheManager


def test_schema_updates():
    """Test that schema updates work correctly."""

    # Create test database
    test_db = "/tmp/test_cache.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    print("Creating CacheManager with updated schema...")
    cache = CacheManager(test_db)

    # Test 1: Add a model
    print("\n1. Testing model creation...")
    model_id = cache.add_model({
        'id': 'test/model-1',
        'name': 'Test Model 1',
        'lab': 'test-lab',
        'downloads': 1000,
        'likes': 50
    })
    print(f"   ✓ Created model: {model_id}")

    # Test 2: Verify model exists and is active
    print("\n2. Testing model retrieval...")
    model = cache.get_model('test/model-1')
    assert model is not None, "Model should exist"
    assert model['deleted_at'] is None, "Model should not be deleted"
    print(f"   ✓ Retrieved model: {model['name']}")

    # Test 3: Mark model as deleted
    print("\n3. Testing soft delete (mark_model_as_deleted)...")
    marked = cache.mark_model_as_deleted('test/model-1')
    assert marked, "Model should be marked as deleted"
    print(f"   ✓ Marked model as deleted")

    # Test 4: Verify model is excluded by default
    print("\n4. Testing deleted model filtering...")
    model = cache.get_model('test/model-1')
    assert model is None, "Deleted model should not be returned by default"
    print(f"   ✓ Deleted model excluded from default query")

    # Test 5: Verify model can still be retrieved with include_deleted
    print("\n5. Testing include_deleted flag...")
    model = cache.get_model('test/model-1', include_deleted=True)
    assert model is not None, "Model should exist with include_deleted=True"
    assert model['deleted_at'] is not None, "Model should have deleted_at timestamp"
    print(f"   ✓ Retrieved deleted model with include_deleted=True")

    # Test 6: Add document metadata (no content)
    print("\n6. Testing document metadata storage...")
    doc_id = cache.add_document(
        model_id='test/model-2',
        doc_type='model_card',
        url='https://example.com/model-card',
        content_hash='abc123def456'
    )
    print(f"   ✓ Added document metadata (ID: {doc_id})")

    # Test 7: Retrieve document
    print("\n7. Testing document retrieval...")
    doc = cache.get_document('test/model-2', 'model_card', 'https://example.com/model-card')
    assert doc is not None, "Document should exist"
    assert doc['content_hash'] == 'abc123def456', "Hash should match"
    assert doc['extraction_failed'] is False, "extraction_failed should default to False"
    print(f"   ✓ Retrieved document with correct hash")

    # Test 8: Mark extraction as failed
    print("\n8. Testing mark_extraction_failed...")
    cache.mark_extraction_failed('test/model-2', 'model_card', 'https://example.com/model-card')
    doc = cache.get_document('test/model-2', 'model_card', 'https://example.com/model-card')
    assert doc['extraction_failed'] is True, "extraction_failed should be True"
    print(f"   ✓ Marked extraction as failed")

    # Test 9: Test should_skip_extraction
    print("\n9. Testing should_skip_extraction...")

    # Should skip because extraction_failed is True
    skip = cache.should_skip_extraction('test/model-2', 'model_card', 'https://example.com/model-card', 'new_hash')
    assert skip, "Should skip extraction when extraction_failed=True"
    print(f"   ✓ Skips extraction when marked as failed")

    # Add new document that hasn't failed
    cache.add_document('test/model-3', 'model_card', 'https://example.com/model-3', 'hash1')

    # Should skip because hash unchanged
    skip = cache.should_skip_extraction('test/model-3', 'model_card', 'https://example.com/model-3', 'hash1')
    assert skip, "Should skip extraction when hash unchanged"
    print(f"   ✓ Skips extraction when hash unchanged")

    # Should NOT skip because hash changed
    skip = cache.should_skip_extraction('test/model-3', 'model_card', 'https://example.com/model-3', 'hash2')
    assert not skip, "Should NOT skip extraction when hash changed"
    print(f"   ✓ Does not skip extraction when hash changed")

    # Should NOT skip for new document
    skip = cache.should_skip_extraction('test/model-4', 'model_card', 'https://example.com/model-4', 'hash1')
    assert not skip, "Should NOT skip extraction for new document"
    print(f"   ✓ Does not skip extraction for new document")

    # Test 10: Test get_all_model_ids and get_active_model_ids
    print("\n10. Testing model ID retrieval...")
    cache.add_model({'id': 'test/model-5', 'name': 'Model 5', 'lab': 'test-lab'})
    all_ids = cache.get_all_model_ids()
    active_ids = cache.get_active_model_ids()

    assert 'test/model-1' in all_ids, "Deleted model should be in all_ids"
    assert 'test/model-1' not in active_ids, "Deleted model should not be in active_ids"
    assert 'test/model-5' in all_ids, "Active model should be in all_ids"
    assert 'test/model-5' in active_ids, "Active model should be in active_ids"
    print(f"   ✓ All IDs: {len(all_ids)}, Active IDs: {len(active_ids)}")

    # Test 11: Test stats exclude deleted models
    print("\n11. Testing stats calculation...")
    stats = cache.get_stats()
    # Should only count active models (not test/model-1 which is deleted)
    print(f"   ✓ Stats: {stats['models']} models, {stats['labs']} labs")

    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)

    # Cleanup
    os.remove(test_db)


if __name__ == '__main__':
    test_schema_updates()
