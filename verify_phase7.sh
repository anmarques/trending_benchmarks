#!/bin/bash
# Phase 7 Verification Script

echo "====================================="
echo "Phase 7 Completion Verification"
echo "====================================="
echo

echo "Group 1: API Rate Limiting"
echo "✓ rate_limiter.py exists:"
ls -lh agents/benchmark_intelligence/rate_limiter.py 2>/dev/null && echo "  Found" || echo "  Missing"

echo "✓ config.yaml has rate_limiting:"
grep -q "rate_limiting:" config.yaml && echo "  Found" || echo "  Missing"

echo

echo "Group 2: Testing Infrastructure"
echo "✓ Test files created:"
test_files=(
  "tests/test_connection_pool.py"
  "tests/test_error_aggregator.py"
  "tests/test_progress_tracker.py"
  "tests/test_rate_limiter.py"
  "tests/test_concurrent_processing.py"
  "tests/test_pipeline.py"
  "tests/test_temporal_tracking.py"
  "tests/test_resumability.py"
)

for file in "${test_files[@]}"; do
  [ -f "$file" ] && echo "  ✓ $file" || echo "  ✗ $file"
done

echo "✓ pytest.ini exists:"
[ -f pytest.ini ] && echo "  Found" || echo "  Missing"

echo

echo "Group 3: Ambient Workflows"
echo "✓ ambient.json has workflows:"
workflows=("filter_models" "find_docs" "parse_docs" "consolidate_benchmarks" "categorize_benchmarks" "report" "generate")
for workflow in "${workflows[@]}"; do
  grep -q "\"$workflow\":" .ambient/ambient.json && echo "  ✓ $workflow" || echo "  ✗ $workflow"
done

echo

echo "Group 4: Documentation"
echo "✓ README.md sections:"
grep -q "Execution Modes" README.md && echo "  ✓ Execution Modes" || echo "  ✗ Execution Modes"
grep -q "Concurrency Settings" README.md && echo "  ✓ Concurrency Settings" || echo "  ✗ Concurrency Settings"
grep -q "Common Concurrency Issues" README.md && echo "  ✓ Troubleshooting" || echo "  ✗ Troubleshooting"

echo "✓ Agent README sections:"
grep -q "Pipeline Stages" agents/benchmark_intelligence/README.md && echo "  ✓ Pipeline Stages" || echo "  ✗ Pipeline Stages"
grep -q "rate_limiting:" agents/benchmark_intelligence/README.md && echo "  ✓ Rate Limiting Config" || echo "  ✗ Rate Limiting Config"

echo

echo "====================================="
echo "Completion Summary"
echo "====================================="

# Count completed tasks
total_tasks=35
completed=$(grep -c "^\- \[X\]" specs/001-benchmark-intelligence/tasks.md || echo 0)
blocked=$(grep -c "^\- \[\*\]" specs/001-benchmark-intelligence/tasks.md || echo 0)
pending=$((total_tasks - completed - blocked))

echo "Total Tasks: $total_tasks"
echo "Completed: $completed"
echo "Blocked (requires external resources): $blocked"
echo "Pending: $pending"
echo

if [ $pending -eq 0 ]; then
  echo "✅ Phase 7 COMPLETE (with $blocked tasks blocked by external dependencies)"
else
  echo "⚠️  Phase 7 has $pending pending tasks"
fi

echo
echo "View detailed completion report:"
echo "  cat PHASE7_COMPLETION.md"
echo "  cat PHASE7_FILES.md"

