#!/bin/bash
#
# Test Runner for Benchmark Intelligence System
# Phase 10: Testing Suite (T049-T069)
#
# Usage:
#   ./run_tests.sh [OPTIONS]
#
# Options:
#   all          - Run all tests (default)
#   fast         - Run only fast tests (skip slow)
#   unit         - Run only unit tests
#   integration  - Run only integration tests
#   discovery    - Run source discovery tests (Phase 10.1)
#   extraction   - Run benchmark extraction tests (Phase 10.2)
#   taxonomy     - Run taxonomy generation tests (Phase 10.3)
#   report       - Run report generation tests (Phase 10.4)
#   coverage     - Run all tests with coverage report
#   specific     - Run specific test (requires TEST_NAME)
#
# Examples:
#   ./run_tests.sh all
#   ./run_tests.sh fast
#   ./run_tests.sh coverage
#   TEST_NAME=test_huggingface_discovery ./run_tests.sh specific

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")"

# Print banner
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE} Benchmark Intelligence System - Test Suite${NC}"
echo -e "${BLUE} Phase 10: Testing Validation (T049-T069)${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Get test mode (default: all)
MODE="${1:-all}"

# Function to run tests with options
run_pytest() {
    local args=("$@")
    echo -e "${YELLOW}Running: pytest ${args[*]}${NC}"
    echo ""

    if pytest "${args[@]}"; then
        echo ""
        echo -e "${GREEN}✓ Tests passed!${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}✗ Tests failed!${NC}"
        return 1
    fi
}

# Execute based on mode
case "$MODE" in
    all)
        echo -e "${BLUE}Running all tests...${NC}"
        run_pytest tests/ -v
        ;;

    fast)
        echo -e "${BLUE}Running fast tests only (skipping slow)...${NC}"
        run_pytest tests/ -v -m "not slow"
        ;;

    unit)
        echo -e "${BLUE}Running unit tests only...${NC}"
        run_pytest tests/ -v -m "unit"
        ;;

    integration)
        echo -e "${BLUE}Running integration tests only...${NC}"
        run_pytest tests/ -v -m "integration"
        ;;

    discovery)
        echo -e "${BLUE}Running source discovery tests (Phase 10.1)...${NC}"
        run_pytest tests/test_source_discovery.py -v
        ;;

    extraction)
        echo -e "${BLUE}Running benchmark extraction tests (Phase 10.2)...${NC}"
        run_pytest tests/test_benchmark_extraction.py -v
        ;;

    taxonomy)
        echo -e "${BLUE}Running taxonomy generation tests (Phase 10.3)...${NC}"
        run_pytest tests/test_taxonomy_generation.py -v
        ;;

    report)
        echo -e "${BLUE}Running report generation tests (Phase 10.4)...${NC}"
        run_pytest tests/test_report_generation.py -v
        ;;

    coverage)
        echo -e "${BLUE}Running all tests with coverage report...${NC}"
        run_pytest tests/ -v --cov=agents --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;

    specific)
        if [ -z "$TEST_NAME" ]; then
            echo -e "${RED}Error: TEST_NAME environment variable not set${NC}"
            echo "Usage: TEST_NAME=test_name ./run_tests.sh specific"
            exit 1
        fi
        echo -e "${BLUE}Running specific test: $TEST_NAME${NC}"
        run_pytest tests/ -v -k "$TEST_NAME"
        ;;

    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        echo ""
        echo "Available modes:"
        echo "  all          - Run all tests (default)"
        echo "  fast         - Run only fast tests"
        echo "  unit         - Run only unit tests"
        echo "  integration  - Run only integration tests"
        echo "  discovery    - Run source discovery tests"
        echo "  extraction   - Run benchmark extraction tests"
        echo "  taxonomy     - Run taxonomy generation tests"
        echo "  report       - Run report generation tests"
        echo "  coverage     - Run with coverage report"
        echo "  specific     - Run specific test (set TEST_NAME)"
        exit 1
        ;;
esac

# Print summary
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE} Test Suite Complete${NC}"
echo -e "${BLUE}================================================${NC}"
