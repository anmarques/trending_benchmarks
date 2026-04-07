"""
Test ground truth validation for benchmark extraction.

Tests the complete extraction pipeline against known benchmark data
from real model cards and documents.
"""

import sys
import json
import time
import yaml
from pathlib import Path
from typing import Dict, List, Any, Set

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.benchmark_intelligence.parse_docs import extract_benchmarks_from_model_docs


def load_ground_truth() -> Dict[str, Any]:
    """Load ground truth data from YAML file."""
    ground_truth_path = Path(__file__).parent / "ground_truth" / "ground_truth.yaml"

    with open(ground_truth_path, 'r') as f:
        return yaml.safe_load(f)


def normalize_benchmark_name(name: str) -> str:
    """
    Normalize benchmark name for comparison.

    Removes case differences, dashes, underscores, and spaces.
    """
    return name.lower().replace("-", "").replace("_", "").replace(" ", "")


def extract_benchmark_names(benchmarks: List[Dict[str, Any]]) -> Set[str]:
    """Extract normalized benchmark names from benchmark list."""
    names = set()
    for bench in benchmarks:
        name = bench.get("name", "")
        if name:
            # Split on common separators to handle variants
            # e.g., "MMLU (5-shot)" -> "MMLU"
            base_name = name.split("(")[0].split("[")[0].strip()
            names.add(normalize_benchmark_name(base_name))
    return names


def calculate_extraction_rate(
    extracted_names: Set[str],
    expected_names: Set[str]
) -> Dict[str, Any]:
    """
    Calculate extraction statistics.

    Returns:
        Dictionary with:
            - found: List of expected benchmarks that were found
            - missing: List of expected benchmarks that were not found
            - extra: List of extracted benchmarks not in ground truth
            - rate: Extraction rate (found / expected)
            - precision: found / (found + extra)
            - recall: found / expected
    """
    found = extracted_names & expected_names
    missing = expected_names - extracted_names
    extra = extracted_names - expected_names

    rate = len(found) / len(expected_names) if expected_names else 0.0
    precision = len(found) / len(extracted_names) if extracted_names else 0.0
    recall = len(found) / len(expected_names) if expected_names else 0.0

    return {
        "found": sorted(found),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "found_count": len(found),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "expected_count": len(expected_names),
        "extracted_count": len(extracted_names),
        "rate": rate,
        "precision": precision,
        "recall": recall
    }


def test_model_extraction(
    model_id: str,
    documents: List[Dict[str, Any]],
    expected_benchmarks: List[str]
) -> Dict[str, Any]:
    """
    Test extraction for a single model.

    Args:
        model_id: Model identifier
        documents: List of document specs with URLs
        expected_benchmarks: List of expected benchmark names

    Returns:
        Test results with statistics
    """
    print(f"\n{'=' * 70}")
    print(f"Testing: {model_id}")
    print(f"{'=' * 70}")
    print(f"Expected benchmarks: {len(expected_benchmarks)}")
    print(f"Documents to process: {len(documents)}")

    # Prepare model entry for extraction
    model_entry = {
        "model_id": model_id,
        "documents": documents
    }

    # Measure extraction time
    start_time = time.time()

    try:
        # Run extraction
        result = extract_benchmarks_from_model_docs(model_entry)

        extraction_time = time.time() - start_time

        # Extract results
        extracted_benchmarks = result.get("benchmarks", [])
        docs_processed = result.get("documents_processed", 0)
        errors = result.get("errors", [])

        print(f"\nExtraction complete:")
        print(f"  Time: {extraction_time:.3f} seconds")
        print(f"  Documents processed: {docs_processed}/{len(documents)}")
        print(f"  Benchmarks extracted: {len(extracted_benchmarks)}")

        if errors:
            print(f"  Errors: {len(errors)}")
            for error in errors:
                print(f"    - {error}")

        # Normalize names for comparison
        extracted_names = extract_benchmark_names(extracted_benchmarks)
        expected_names = {normalize_benchmark_name(name) for name in expected_benchmarks}

        # Calculate statistics
        stats = calculate_extraction_rate(extracted_names, expected_names)

        print(f"\nExtraction Statistics:")
        print(f"  Found: {stats['found_count']}/{stats['expected_count']} ({stats['rate']*100:.1f}%)")
        print(f"  Precision: {stats['precision']*100:.1f}%")
        print(f"  Recall: {stats['recall']*100:.1f}%")

        if stats['missing_count'] > 0:
            print(f"\n  Missing ({stats['missing_count']}):")
            for name in stats['missing'][:10]:  # Show first 10
                print(f"    - {name}")
            if stats['missing_count'] > 10:
                print(f"    ... and {stats['missing_count'] - 10} more")

        if stats['extra_count'] > 0:
            print(f"\n  Extra ({stats['extra_count']}):")
            for name in stats['extra'][:10]:  # Show first 10
                print(f"    - {name}")
            if stats['extra_count'] > 10:
                print(f"    ... and {stats['extra_count'] - 10} more")

        # Check performance criteria (SC-002: ≥95% extraction accuracy)
        passed_rate = stats['rate'] >= 0.95
        passed_time = extraction_time < 60.0

        print(f"\nPerformance Criteria:")
        print(f"  Extraction rate ≥95% (SC-002): {'✓ PASS' if passed_rate else '✗ FAIL'} ({stats['rate']*100:.1f}%)")
        print(f"  Time <60 seconds: {'✓ PASS' if passed_time else '✗ FAIL'} ({extraction_time:.3f}s)")

        return {
            "model_id": model_id,
            "success": True,
            "extraction_time": extraction_time,
            "documents_processed": docs_processed,
            "benchmarks_extracted": len(extracted_benchmarks),
            "statistics": stats,
            "passed_rate_test": passed_rate,
            "passed_time_test": passed_time,
            "errors": errors
        }

    except Exception as e:
        extraction_time = time.time() - start_time
        print(f"\n✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            "model_id": model_id,
            "success": False,
            "extraction_time": extraction_time,
            "error": str(e),
            "passed_rate_test": False,
            "passed_time_test": False
        }


def run_ground_truth_validation():
    """Run complete ground truth validation."""
    print("=" * 70)
    print("Ground Truth Validation Test")
    print("=" * 70)

    # Load ground truth
    ground_truth = load_ground_truth()
    models = ground_truth.get("models", [])

    print(f"\nLoaded ground truth:")
    print(f"  Models: {len(models)}")

    # Test each model
    results = []

    for model_data in models:
        model_id = model_data.get("id")  # Changed from model_id to id

        # Extract all benchmark names from all documents
        expected_benchmarks = []
        for doc in model_data.get("documents", []):
            for bench in doc.get("benchmarks", []):
                benchmark_name = bench.get("name")
                if benchmark_name:
                    expected_benchmarks.append(benchmark_name)

        # Prepare document list for extraction
        documents = []
        for doc in model_data.get("documents", []):
            documents.append({
                "type": doc["type"],
                "url": doc["url"],
                "found": True
            })

        # Test extraction
        result = test_model_extraction(model_id, documents, expected_benchmarks)
        results.append(result)

    # Overall summary
    print(f"\n{'=' * 70}")
    print("Overall Summary")
    print(f"{'=' * 70}")

    total_models = len(results)
    successful_models = sum(1 for r in results if r.get("success", False))
    passed_rate_tests = sum(1 for r in results if r.get("passed_rate_test", False))
    passed_time_tests = sum(1 for r in results if r.get("passed_time_test", False))

    print(f"\nModels tested: {total_models}")
    print(f"Successful extractions: {successful_models}/{total_models}")
    print(f"Passed extraction rate test (≥95% SC-002): {passed_rate_tests}/{total_models}")
    print(f"Passed time test (<60s): {passed_time_tests}/{total_models}")

    # Aggregate statistics
    if successful_models > 0:
        avg_rate = sum(
            r.get("statistics", {}).get("rate", 0)
            for r in results if r.get("success", False)
        ) / successful_models

        avg_time = sum(
            r.get("extraction_time", 0)
            for r in results if r.get("success", False)
        ) / successful_models

        total_found = sum(
            r.get("statistics", {}).get("found_count", 0)
            for r in results if r.get("success", False)
        )

        total_expected = sum(
            r.get("statistics", {}).get("expected_count", 0)
            for r in results if r.get("success", False)
        )

        print(f"\nAggregate Statistics:")
        print(f"  Overall extraction rate: {avg_rate*100:.1f}%")
        print(f"  Average extraction time: {avg_time:.3f}s")
        print(f"  Total benchmarks found: {total_found}/{total_expected}")

    # Final verdict
    all_passed = (
        successful_models == total_models and
        passed_rate_tests == total_models and
        passed_time_tests == total_models
    )

    print(f"\n{'=' * 70}")
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print(f"{'=' * 70}")

    return results


if __name__ == "__main__":
    results = run_ground_truth_validation()

    # Exit with appropriate code
    all_passed = all(
        r.get("success", False) and
        r.get("passed_rate_test", False) and
        r.get("passed_time_test", False)
        for r in results
    )

    sys.exit(0 if all_passed else 1)
