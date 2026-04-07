# Quick Reference - Benchmark Intelligence System

## Execution Commands

### Python Execution
```bash
# Full pipeline (all 6 stages)
python -m agents.benchmark_intelligence.main generate

# Individual stages
python -m agents.benchmark_intelligence.main filter_models
python -m agents.benchmark_intelligence.main find_docs
python -m agents.benchmark_intelligence.main parse_docs --concurrency 20
python -m agents.benchmark_intelligence.main consolidate_benchmarks
python -m agents.benchmark_intelligence.main categorize_benchmarks
python -m agents.benchmark_intelligence.main report
```

### Ambient Execution
```bash
# Full pipeline
/benchmark_intelligence.generate

# Individual stages
/benchmark_intelligence.filter_models
/benchmark_intelligence.find_docs
/benchmark_intelligence.parse_docs --concurrency 30
/benchmark_intelligence.consolidate_benchmarks --from-db
/benchmark_intelligence.categorize_benchmarks
/benchmark_intelligence.report
```

## Configuration

### Key Settings in config.yaml

```yaml
# Discovery
discovery:
  models_per_lab: 15
  date_filter_months: 12

# Concurrency (default: 20 workers)
parallelization:
  max_concurrent_document_fetches: 5
  timeout_per_document_seconds: 60

# Rate Limiting (prevents 429 errors)
rate_limiting:
  huggingface:
    requests_per_minute: 60
  anthropic:
    requests_per_minute: 50
  arxiv:
    requests_per_minute: 30
```

### Adjust Concurrency
```bash
# Low (safer, slower)
--concurrency 10

# Medium (default)
--concurrency 20

# High (faster, may hit rate limits)
--concurrency 50
```

## Output Files

All outputs in `agents/benchmark_intelligence/outputs/`:

| Stage | Output File |
|-------|-------------|
| filter_models | `filtered_models/models_YYYYMMDD_HHMMSS.json` |
| find_docs | `docs/docs_YYYYMMDD_HHMMSS.json` |
| parse_docs | `parsed/parsed_YYYYMMDD_HHMMSS.json` |
| consolidate | `consolidated/benchmarks_YYYYMMDD_HHMMSS.json` |
| categorize | `categorized/categorized_YYYYMMDD_HHMMSS.json` |
| report | `reports/report_YYYYMMDD_HHMMSS.md` |

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/test_rate_limiter.py -v

# Run with coverage
python3 -m pytest tests/ --cov=agents.benchmark_intelligence --cov-report=term-missing

# Run ground truth validation
python3 -m pytest tests/test_ground_truth_validation.py -v
```

## Troubleshooting

### 429 Rate Limit Errors
1. Reduce concurrency: `--concurrency 10`
2. Adjust in config.yaml: `requests_per_minute: 30`
3. Rate limiter automatically retries with backoff

### Timeout Errors
1. Increase timeout: `timeout_per_document_seconds: 120`
2. Reduce concurrent fetches: `max_concurrent_document_fetches: 3`

### Memory Issues
1. Lower concurrency: `--concurrency 5`
2. Process stages individually instead of full pipeline

### Resuming After Interruption
- Just re-run the same command
- Hash cache automatically skips processed documents

## Environment Variables

```bash
# Required
export HF_TOKEN="hf_your_token"

# Optional (not needed on Ambient)
export ANTHROPIC_API_KEY="your_key"
```

## Documentation

- **Main README**: `/workspace/repos/trending_benchmarks/README.md`
- **Agent README**: `/workspace/repos/trending_benchmarks/agents/benchmark_intelligence/README.md`
- **Phase 7 Report**: `/workspace/repos/trending_benchmarks/PHASE7_COMPLETION.md`
- **File Inventory**: `/workspace/repos/trending_benchmarks/PHASE7_FILES.md`

## Key Features

✅ **Rate Limiting**: Automatic 429 error prevention with exponential backoff  
✅ **High Concurrency**: 20-50 workers supported  
✅ **Resumability**: Hash cache prevents re-processing  
✅ **Temporal Tracking**: 12-month rolling window  
✅ **Status Classification**: Emerging/extinct benchmark detection  

## Production Checklist

Before deploying:
1. [ ] Run ground truth validation (≥95% accuracy)
2. [ ] Run coverage analysis (≥80% coverage)
3. [ ] Test resumability (interrupt + restart)
4. [ ] Verify Ambient workflows (if using Ambient)
5. [ ] Stress test with high concurrency

---

**Quick Help**: Run `bash verify_phase7.sh` to verify Phase 7 completion
