# Benchmark Intelligence System - Test Suite

Comprehensive testing suite for Phase 10 of the Benchmark Intelligence System implementation.

## Overview

This test suite validates all 21 test tasks across 4 testing phases:

- **Phase 10.1: Source Discovery Validation** (T049-T053) - 5 tests
- **Phase 10.2: Benchmark Extraction Validation** (T054-T058) - 5 tests
- **Phase 10.3: Taxonomy Generation Validation** (T059-T062) - 4 tests
- **Phase 10.4: Report Generation Validation** (T063-T069) - 7 tests

## Test Files

### 1. `test_source_discovery.py` (Phase 10.1)
- **T049**: Test harness setup
- **T050**: HuggingFace discovery (15 models per lab)
- **T051**: Model filtering (type/date/lab)
- **T052**: Model sorting (downloads/trending)
- **T053**: Document fetching with URL validation

### 2. `test_benchmark_extraction.py` (Phase 10.2)
- **T054**: Test harness setup
- **T055**: Ground truth coverage (target: ≥90% recall)
- **T056**: Extraction precision (target: ≥85% precision)
- **T057**: Variant detection (shots/subset/method)
- **T058**: Name consolidation with fuzzy matching

### 3. `test_taxonomy_generation.py` (Phase 10.3)
- **T059**: Test harness setup
- **T060**: Category assignment accuracy
- **T061**: Taxonomy evolution with version tracking
- **T062**: Multi-label benchmarks (e.g., MMLU)

### 4. `test_report_generation.py` (Phase 10.4)
- **T063**: Test harness setup
- **T064**: All 7 sections presence
- **T065**: Temporal trends with snapshots
- **T066**: Emerging benchmarks (≤3 months)
- **T067**: Almost extinct (≥9 months)
- **T068**: Markdown validity
- **T069**: End-to-end pipeline

## Running Tests

### Run All Tests
```bash
cd /workspace/repos/trending_benchmarks
pytest tests/ -v
```

### Run Specific Test Suite
```bash
# Source discovery tests
pytest tests/test_source_discovery.py -v

# Benchmark extraction tests
pytest tests/test_benchmark_extraction.py -v

# Taxonomy generation tests
pytest tests/test_taxonomy_generation.py -v

# Report generation tests
pytest tests/test_report_generation.py -v
```

### Run Specific Test Function
```bash
pytest tests/test_source_discovery.py::TestSourceDiscovery::test_huggingface_discovery -v
```

### Run with Coverage
```bash
pytest tests/ --cov=agents --cov-report=html --cov-report=term
```

### Run Fast Tests Only (Skip Slow)
```bash
pytest tests/ -v -m "not slow"
```

### Run Integration Tests Only
```bash
pytest tests/ -v -m integration
```

## Test Markers

Tests are marked with the following markers:

- `slow` - Tests that take longer to run (API calls, etc.)
- `integration` - End-to-end integration tests
- `unit` - Fast unit tests
- `source_discovery` - Source discovery phase tests
- `benchmark_extraction` - Benchmark extraction phase tests
- `taxonomy_generation` - Taxonomy generation phase tests
- `report_generation` - Report generation phase tests

## Expected Results

### Target Metrics

- **Ground Truth Coverage**: ≥90% recall
- **Extraction Precision**: ≥85% precision
- **Model Discovery**: 15 models per lab
- **All Report Sections**: 7 sections present
- **Taxonomy Categories**: 10+ categories

### Success Criteria

All tests should pass with:
- ✓ Source discovery finding models from all configured labs
- ✓ Benchmark extraction meeting recall/precision targets
- ✓ Taxonomy properly categorizing benchmarks
- ✓ Reports containing all required sections
- ✓ End-to-end pipeline executing without errors

## Ground Truth Data

Ground truth data is located at: `tests/ground_truth/ground_truth.yaml`

This file contains:
- 2 models (Llama-3.1-8B, Qwen2.5-72B-Instruct)
- 181 total benchmarks across 3-4 documents per model
- 75 unique benchmark names
- Expected consolidation behavior
- Expected category classifications

## Troubleshooting

### API Rate Limits
If you encounter HuggingFace API rate limits:
```bash
export HF_TOKEN=your_token_here
pytest tests/ -v
```

### Slow Tests
To skip slow tests during development:
```bash
pytest tests/ -v -m "not slow"
```

### Mock vs Real Tests
Some tests use mocks for speed. To run with real API calls, set:
```bash
export USE_REAL_API=true
pytest tests/ -v
```

## Test Data

Test data and fixtures are organized as:
- `tests/ground_truth/` - Ground truth validation data
- `tests/test_data/` - Generated test data (created during test runs)
- `tests/conftest.py` - Shared pytest fixtures

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Add appropriate markers (`@pytest.mark.slow`, etc.)
3. Document expected behavior
4. Update this README with new test descriptions
5. Ensure tests are independent and can run in any order

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-cov
    pytest tests/ -v --cov=agents --cov-report=xml
```

## Contact

For questions or issues with the test suite, refer to:
- Main README: `/workspace/repos/trending_benchmarks/README.md`
- Specifications: `/workspace/repos/trending_benchmarks/SPECIFICATIONS.md`
- Phase 10 Tasks: Tasks T049-T069
