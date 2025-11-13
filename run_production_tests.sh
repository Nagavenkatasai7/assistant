#!/bin/bash

# Production Readiness Test Runner
# ATS Resume Generator - Post Kimi K2 + Tavily Migration
# Version: 1.0.0

set -e  # Exit on error

echo "========================================================================"
echo "🚀 ATS RESUME GENERATOR - PRODUCTION READINESS TEST SUITE"
echo "========================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ==============================================================================
# STEP 1: ENVIRONMENT CHECKS
# ==============================================================================

echo "STEP 1: Environment Checks"
echo "------------------------------------------------------------------------"

# Check Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED_VERSION="3.9"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    print_success "Python $PYTHON_VERSION (OK)"
else
    print_error "Python $PYTHON_VERSION < $REQUIRED_VERSION (FAIL)"
    exit 1
fi

# Check API Keys
echo -n "Checking KIMI_API_KEY... "
if [ -z "$KIMI_API_KEY" ]; then
    print_error "Not set"
    exit 1
else
    KEY_LEN=${#KIMI_API_KEY}
    print_success "Set (${KEY_LEN} chars)"
fi

echo -n "Checking TAVILY_API_KEY... "
if [ -z "$TAVILY_API_KEY" ]; then
    print_error "Not set"
    exit 1
else
    KEY_LEN=${#TAVILY_API_KEY}
    print_success "Set (${KEY_LEN} chars)"
fi

# Check Profile.pdf
echo -n "Checking Profile.pdf... "
if [ ! -f "Profile.pdf" ]; then
    print_error "Not found"
    exit 1
else
    FILE_SIZE=$(ls -lh Profile.pdf | awk '{print $5}')
    print_success "Found (${FILE_SIZE})"
fi

# Check database
echo -n "Checking database... "
if [ ! -f "resume_generator.db" ]; then
    print_warning "Not found (will be created)"
else
    RESUME_COUNT=$(sqlite3 resume_generator.db "SELECT COUNT(*) FROM generated_resumes;" 2>/dev/null || echo "0")
    print_success "Found (${RESUME_COUNT} resumes)"
fi

# Check disk space
echo -n "Checking disk space... "
FREE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
print_success "Free: ${FREE_SPACE}"

# Check required packages
echo -n "Checking required packages... "
MISSING_PACKAGES=""
for package in streamlit anthropic pypdf python-docx reportlab requests python-dotenv; do
    if ! pip show $package > /dev/null 2>&1; then
        MISSING_PACKAGES="$MISSING_PACKAGES $package"
    fi
done

if [ -z "$MISSING_PACKAGES" ]; then
    print_success "All packages installed"
else
    print_error "Missing packages:$MISSING_PACKAGES"
    echo ""
    echo "Install missing packages with:"
    echo "pip install$MISSING_PACKAGES"
    exit 1
fi

echo ""
print_success "All environment checks passed!"
echo ""

# ==============================================================================
# STEP 2: CREATE TEST OUTPUT DIRECTORY
# ==============================================================================

echo "STEP 2: Preparing Test Environment"
echo "------------------------------------------------------------------------"

mkdir -p test_output
mkdir -p test_results
print_success "Test directories created"
echo ""

# ==============================================================================
# STEP 3: RUN QUICK SMOKE TEST
# ==============================================================================

echo "STEP 3: Quick Smoke Test"
echo "------------------------------------------------------------------------"

echo "Running quick validation..."
python -c "
import sys
sys.path.insert(0, '.')
from src.clients.kimi_client import KimiK2Client
from src.clients.tavily_client import TavilyClient

try:
    kimi = KimiK2Client()
    print('✅ Kimi K2 client initialized')
    tavily = TavilyClient()
    print('✅ Tavily client initialized')
    print('✅ Quick smoke test passed')
except Exception as e:
    print(f'❌ Quick smoke test failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Smoke test passed"
else
    print_error "Smoke test failed"
    exit 1
fi

echo ""

# ==============================================================================
# STEP 4: RUN TEST SUITE
# ==============================================================================

echo "STEP 4: Running Test Suite"
echo "------------------------------------------------------------------------"

# Ask user which tests to run
echo "Select test suite to run:"
echo "  1) Quick tests (Unit + Critical tests only) - ~15 minutes"
echo "  2) Full test suite (All tests) - ~2 hours"
echo "  3) Specific test (Enter test name)"
echo ""
read -p "Enter choice (1/2/3): " TEST_CHOICE

case $TEST_CHOICE in
    1)
        echo ""
        print_info "Running quick test suite..."
        python -m pytest tests/test_production_readiness.py \
            -k "test_kimi_client_initialization or test_tavily_client_initialization or test_ats_scorer_accuracy or test_resume_structure_validation or test_ats_score_validation" \
            -v --tb=short \
            2>&1 | tee test_results/quick_tests_$(date +%Y%m%d_%H%M%S).txt
        ;;
    2)
        echo ""
        print_info "Running full test suite..."
        python -m pytest tests/test_production_readiness.py \
            -v --tb=short \
            2>&1 | tee test_results/full_tests_$(date +%Y%m%d_%H%M%S).txt
        ;;
    3)
        echo ""
        read -p "Enter test name (e.g., test_end_to_end_resume_generation): " TEST_NAME
        print_info "Running test: $TEST_NAME"
        python -m pytest tests/test_production_readiness.py::TestProductionReadiness::$TEST_NAME \
            -v --tb=short \
            2>&1 | tee test_results/specific_test_$(date +%Y%m%d_%H%M%S).txt
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

TEST_EXIT_CODE=$?

echo ""
echo "========================================================================"

# ==============================================================================
# STEP 5: RESULTS SUMMARY
# ==============================================================================

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    print_success "ALL TESTS PASSED!"
    echo ""
    echo "✅ System is ready for production deployment"
    echo ""
    echo "Next steps:"
    echo "  1. Review test results in test_results/ directory"
    echo "  2. Check generated PDFs in test_output/ directory"
    echo "  3. Review PRODUCTION_READINESS_TEST_PLAN.md for sign-off"
    echo ""
else
    echo ""
    print_error "SOME TESTS FAILED"
    echo ""
    echo "⚠️  System is NOT ready for production"
    echo ""
    echo "Next steps:"
    echo "  1. Review test failures in test_results/ directory"
    echo "  2. Check BUG_TRACKING_TEMPLATE.md for documenting bugs"
    echo "  3. Fix bugs and re-run tests"
    echo ""
    exit 1
fi

echo "========================================================================"
echo ""

# ==============================================================================
# STEP 6: GENERATE SUMMARY REPORT
# ==============================================================================

echo "STEP 6: Generating Summary Report"
echo "------------------------------------------------------------------------"

REPORT_FILE="test_results/test_summary_$(date +%Y%m%d_%H%M%S).txt"

cat > $REPORT_FILE << EOF
======================================================================
ATS RESUME GENERATOR - TEST SUMMARY REPORT
======================================================================

Test Date: $(date)
Test Suite: $TEST_CHOICE
Exit Code: $TEST_EXIT_CODE

Environment:
- Python: $PYTHON_VERSION
- Kimi API Key: Set (${#KIMI_API_KEY} chars)
- Tavily API Key: Set (${#TAVILY_API_KEY} chars)
- Profile.pdf: Present
- Database: Present

Test Results:
$(if [ $TEST_EXIT_CODE -eq 0 ]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)

Production Readiness:
$(if [ $TEST_EXIT_CODE -eq 0 ]; then echo "✅ READY FOR DEPLOYMENT"; else echo "❌ NOT READY - FIX BUGS FIRST"; fi)

Test Artifacts:
- Test results: test_results/
- Generated PDFs: test_output/
- Bug tracking: BUG_TRACKING_TEMPLATE.md

Next Steps:
$(if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "1. Review generated resumes for quality"
    echo "2. Verify ATS scores >= 90"
    echo "3. Check PDF links are clickable"
    echo "4. Sign production readiness document"
else
    echo "1. Review test failures"
    echo "2. Document bugs in BUG_TRACKING_TEMPLATE.md"
    echo "3. Fix bugs"
    echo "4. Re-run test suite"
fi)

======================================================================
EOF

print_success "Summary report generated: $REPORT_FILE"
echo ""

# Display summary
cat $REPORT_FILE

# ==============================================================================
# COMPLETION
# ==============================================================================

echo ""
echo "========================================================================"
echo "🏁 TEST EXECUTION COMPLETE"
echo "========================================================================"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "Production readiness testing completed successfully!"
    exit 0
else
    print_error "Production readiness testing completed with failures"
    exit 1
fi
