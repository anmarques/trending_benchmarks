"""
Test side-by-side benchmark disambiguation feature.

Tests P2-1: When two similar benchmark names appear in the same document
(e.g., "MMLU" and "MMLU-Pro" in the same table), they should be treated
as distinct benchmarks, not merged during consolidation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.benchmark_intelligence.tools.extract_benchmarks import (
    _detect_cooccurrences,
    _are_potentially_similar,
)
from agents.benchmark_intelligence.tools.consolidate import (
    _apply_cooccurrence_disambiguation,
)


def test_are_potentially_similar():
    """Test the similarity detection function."""
    print("\n=== Testing _are_potentially_similar ===")

    # Should be similar
    assert _are_potentially_similar("MMLU", "MMLU-Pro"), "MMLU and MMLU-Pro should be similar"
    assert _are_potentially_similar("MMLU-Pro", "MMLU"), "MMLU-Pro and MMLU should be similar"
    assert _are_potentially_similar("GSM8K", "GSM-8K"), "GSM8K and GSM-8K should be similar"
    assert _are_potentially_similar("mmlu", "MMLU"), "Case variations should be similar"
    assert _are_potentially_similar("MMLU", "MMLUPro"), "MMLU and MMLUPro should be similar"

    # Should NOT be similar
    assert not _are_potentially_similar("MMLU", "GSM8K"), "MMLU and GSM8K should not be similar"
    assert not _are_potentially_similar("ARC", "MATH"), "ARC and MATH should not be similar"
    assert not _are_potentially_similar("HumanEval", "MBPP"), "HumanEval and MBPP should not be similar"

    print("✓ All similarity tests passed")


def test_detect_cooccurrences():
    """Test co-occurrence detection in extracted benchmarks."""
    print("\n=== Testing _detect_cooccurrences ===")

    # Test case 1: MMLU and MMLU-Pro in same table
    benchmarks_1 = [
        {"name": "MMLU", "source_location": "Table 1"},
        {"name": "MMLU-Pro", "source_location": "Table 1"},
        {"name": "GSM8K", "source_location": "Table 1"},
    ]

    cooccur_1 = _detect_cooccurrences(benchmarks_1)
    print(f"Test 1 - Found {len(cooccur_1)} co-occurrences: {cooccur_1}")

    # Should detect MMLU + MMLU-Pro (similar names in same location)
    assert len(cooccur_1) >= 1, "Should detect at least MMLU + MMLU-Pro"
    assert any(
        (c["benchmark_a"] == "MMLU" and c["benchmark_b"] == "MMLU-Pro") or
        (c["benchmark_a"] == "MMLU-Pro" and c["benchmark_b"] == "MMLU")
        for c in cooccur_1
    ), "Should detect MMLU and MMLU-Pro co-occurrence"

    # Test case 2: Different tables (no co-occurrence expected)
    benchmarks_2 = [
        {"name": "MMLU", "source_location": "Table 1"},
        {"name": "MMLU-Pro", "source_location": "Table 2"},
    ]

    cooccur_2 = _detect_cooccurrences(benchmarks_2)
    print(f"Test 2 - Found {len(cooccur_2)} co-occurrences: {cooccur_2}")

    assert len(cooccur_2) == 0, "Should not detect co-occurrence in different tables"

    # Test case 3: Multiple similar benchmarks in same table
    benchmarks_3 = [
        {"name": "MMLU", "source_location": "Table 1"},
        {"name": "mmlu", "source_location": "Table 1"},
        {"name": "MMLU-Pro", "source_location": "Table 1"},
        {"name": "GSM8K", "source_location": "Table 2"},
        {"name": "GSM-8K", "source_location": "Table 2"},
    ]

    cooccur_3 = _detect_cooccurrences(benchmarks_3)
    print(f"Test 3 - Found {len(cooccur_3)} co-occurrences: {cooccur_3}")

    # Should detect pairs within each table
    assert len(cooccur_3) >= 2, "Should detect multiple co-occurrence pairs"

    print("✓ All co-occurrence detection tests passed")


def test_apply_cooccurrence_disambiguation():
    """Test that consolidation respects co-occurrence constraints."""
    print("\n=== Testing _apply_cooccurrence_disambiguation ===")

    # Test case 1: MMLU variants should be split if they co-occur
    consolidation_before = {
        "consolidations": [
            {
                "canonical_name": "MMLU",
                "variations": ["MMLU", "mmlu", "MMLU-Pro"],
                "benchmark_type": "same",
                "confidence": 0.9,
                "notes": "Case variations"
            }
        ],
        "distinct_benchmarks": [],
        "uncertain_mappings": []
    }

    cooccurrences = [
        {"benchmark_a": "MMLU", "benchmark_b": "MMLU-Pro", "location": "Table 1"}
    ]

    result = _apply_cooccurrence_disambiguation(consolidation_before, cooccurrences)

    print(f"Result has {len(result['consolidations'])} consolidation groups:")
    for cons in result['consolidations']:
        print(f"  - {cons['canonical_name']}: {cons['variations']}")

    # After disambiguation, MMLU and MMLU-Pro should be in separate groups
    assert len(result['consolidations']) >= 2, "Should split into at least 2 groups"

    # Find MMLU-Pro group (should be standalone)
    mmlu_pro_group = [c for c in result['consolidations'] if "MMLU-Pro" in c['variations']]
    assert len(mmlu_pro_group) > 0, "MMLU-Pro should have its own group"

    # MMLU-Pro should NOT be in the same group as MMLU
    for cons in result['consolidations']:
        if "MMLU" in cons['variations'] and "MMLU-Pro" in cons['variations']:
            assert False, "MMLU and MMLU-Pro should be in separate groups"

    # Test case 2: No co-occurrence - should not split
    consolidation_no_split = {
        "consolidations": [
            {
                "canonical_name": "GSM8K",
                "variations": ["GSM8K", "GSM-8K", "gsm8k"],
                "benchmark_type": "same",
                "confidence": 1.0,
                "notes": "Delimiter variations"
            }
        ],
        "distinct_benchmarks": [],
        "uncertain_mappings": []
    }

    no_cooccur = []
    result_no_split = _apply_cooccurrence_disambiguation(consolidation_no_split, no_cooccur)

    print(f"\nNo co-occurrence test - Result has {len(result_no_split['consolidations'])} groups")

    # Should remain as 1 group
    assert len(result_no_split['consolidations']) == 1, "Should not split without co-occurrence"
    assert "GSM8K" in result_no_split['consolidations'][0]['variations'], "Should keep GSM8K"
    assert "GSM-8K" in result_no_split['consolidations'][0]['variations'], "Should keep GSM-8K"

    print("✓ All disambiguation tests passed")


def test_end_to_end_scenario():
    """
    Test a realistic end-to-end scenario with extraction and consolidation.
    """
    print("\n=== Testing End-to-End Scenario ===")

    # Simulate extracted benchmarks from a model card with a table
    # containing both MMLU and MMLU-Pro
    extracted_benchmarks = [
        {"name": "MMLU", "score": 82.5, "source_location": "Table 1, Row 1"},
        {"name": "MMLU-Pro", "score": 65.3, "source_location": "Table 1, Row 2"},
        {"name": "GSM8K", "score": 94.2, "source_location": "Table 1, Row 3"},
        {"name": "HumanEval", "score": 86.6, "source_location": "Table 1, Row 4"},
    ]

    # Another document with case variations (different table)
    extracted_benchmarks_2 = [
        {"name": "mmlu", "score": 83.0, "source_location": "Table 2, Row 1"},
        {"name": "GSM-8K", "score": 92.1, "source_location": "Table 2, Row 2"},
    ]

    # Detect co-occurrences in each document
    cooccur_1 = _detect_cooccurrences(extracted_benchmarks)
    cooccur_2 = _detect_cooccurrences(extracted_benchmarks_2)

    print(f"Document 1 co-occurrences: {len(cooccur_1)}")
    print(f"Document 2 co-occurrences: {len(cooccur_2)}")

    # Combine all co-occurrences
    all_cooccurrences = cooccur_1 + cooccur_2

    # Simulate consolidation result from Claude (without side-by-side awareness)
    naive_consolidation = {
        "consolidations": [
            {
                "canonical_name": "MMLU",
                "variations": ["MMLU", "mmlu", "MMLU-Pro"],  # Incorrectly grouped
                "benchmark_type": "same",
                "confidence": 0.8
            },
            {
                "canonical_name": "GSM8K",
                "variations": ["GSM8K", "GSM-8K"],
                "benchmark_type": "same",
                "confidence": 1.0
            },
            {
                "canonical_name": "HumanEval",
                "variations": ["HumanEval"],
                "benchmark_type": "same",
                "confidence": 1.0
            }
        ],
        "distinct_benchmarks": [],
        "uncertain_mappings": []
    }

    # Apply disambiguation
    final_result = _apply_cooccurrence_disambiguation(naive_consolidation, all_cooccurrences)

    print(f"\nFinal consolidation groups: {len(final_result['consolidations'])}")
    for cons in final_result['consolidations']:
        print(f"  - {cons['canonical_name']}: {cons['variations']}")

    # Verify results
    # Should have at least 4 groups: MMLU (with mmlu), MMLU-Pro (separate), GSM8K (with GSM-8K), HumanEval
    assert len(final_result['consolidations']) >= 4, f"Expected at least 4 groups, got {len(final_result['consolidations'])}"

    # MMLU and MMLU-Pro should be separate
    mmlu_variations = []
    mmlu_pro_variations = []
    for cons in final_result['consolidations']:
        if "MMLU" in cons['variations']:
            mmlu_variations.extend(cons['variations'])
        if "MMLU-Pro" in cons['variations']:
            mmlu_pro_variations.extend(cons['variations'])

    # Should not have both in same group
    if "MMLU-Pro" in mmlu_variations:
        assert False, "MMLU-Pro should not be grouped with MMLU"

    # mmlu (case variation) can be with MMLU, but MMLU-Pro must be separate
    print(f"  MMLU group: {[c['variations'] for c in final_result['consolidations'] if 'MMLU' in c['variations'] and 'MMLU-Pro' not in c['variations']]}")
    print(f"  MMLU-Pro group: {[c['variations'] for c in final_result['consolidations'] if 'MMLU-Pro' in c['variations']]}")

    print("✓ End-to-end scenario test passed")


def test_multiple_cooccurrences():
    """Test handling of multiple co-occurrences in complex scenarios."""
    print("\n=== Testing Multiple Co-occurrences ===")

    # Complex scenario: ARC family with co-occurrences
    consolidation = {
        "consolidations": [
            {
                "canonical_name": "ARC",
                "variations": ["ARC", "ARC-c", "ARC-e", "arc"],
                "benchmark_type": "same",
                "confidence": 0.7
            }
        ],
        "distinct_benchmarks": [],
        "uncertain_mappings": []
    }

    # ARC-c and ARC-e appear together (they are different difficulty levels)
    cooccurrences = [
        {"benchmark_a": "ARC-c", "benchmark_b": "ARC-e", "location": "Table 1"}
    ]

    result = _apply_cooccurrence_disambiguation(consolidation, cooccurrences)

    print(f"Result has {len(result['consolidations'])} groups:")
    for cons in result['consolidations']:
        print(f"  - {cons['canonical_name']}: {cons['variations']}")

    # ARC-c and ARC-e should be in separate groups
    arc_c_in_group = None
    arc_e_in_group = None

    for cons in result['consolidations']:
        if "ARC-c" in cons['variations']:
            arc_c_in_group = cons['canonical_name']
        if "ARC-e" in cons['variations']:
            arc_e_in_group = cons['canonical_name']

    assert arc_c_in_group is not None, "ARC-c should be in some group"
    assert arc_e_in_group is not None, "ARC-e should be in some group"

    # They should not be in the same consolidation
    for cons in result['consolidations']:
        if "ARC-c" in cons['variations']:
            assert "ARC-e" not in cons['variations'], "ARC-c and ARC-e should be separated"

    print("✓ Multiple co-occurrence test passed")


def run_all_tests():
    """Run all test cases."""
    print("=" * 70)
    print("SIDE-BY-SIDE BENCHMARK DISAMBIGUATION TEST SUITE")
    print("=" * 70)

    try:
        test_are_potentially_similar()
        test_detect_cooccurrences()
        test_apply_cooccurrence_disambiguation()
        test_end_to_end_scenario()
        test_multiple_cooccurrences()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        return True

    except AssertionError as e:
        print("\n" + "=" * 70)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 70)
        return False
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
