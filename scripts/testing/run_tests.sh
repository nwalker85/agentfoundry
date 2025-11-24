#!/bin/bash
# Run Tests for Engineering Department
# Usage: ./run_tests.sh [suite] [options]
#   suite: all|unit|integration|e2e|uat (default: all)
#   options: any pytest options (e.g., -v, --cov)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🧪 Engineering Department Test Suite"
echo "====================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "   Create it with: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Parse test suite argument
SUITE=${1:-all}
shift || true  # Remove first argument, ignore error if no args

# Determine which tests to run
case $SUITE in
    unit)
        echo "📦 Running Unit Tests..."
        TEST_PATH="tests/unit/"
        ;;
    integration)
        echo "🔗 Running Integration Tests..."
        TEST_PATH="tests/integration/"
        # Check if MCP server is running for integration tests
        if ! curl -s http://localhost:8001/ > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  MCP server not running!${NC}"
            echo "   Start it in another terminal with: ./start_server.sh"
            echo "   Or: python mcp_server.py"
            exit 1
        fi
        echo -e "${GREEN}✅ MCP server detected at http://localhost:8001${NC}"
        ;;
    e2e)
        echo "🔄 Running End-to-End Tests..."
        TEST_PATH="tests/e2e/"
        # Check if MCP server is running for E2E tests
        if ! curl -s http://localhost:8001/ > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  MCP server not running!${NC}"
            echo "   Start it in another terminal with: ./start_server.sh"
            echo "   Or: python mcp_server.py"
            exit 1
        fi
        echo -e "${GREEN}✅ MCP server detected at http://localhost:8001${NC}"
        ;;
    uat)
        echo "✅ Running User Acceptance Tests..."
        TEST_PATH="tests/uat/"
        # Check if MCP server is running for UAT
        if ! curl -s http://localhost:8001/ > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  MCP server not running!${NC}"
            echo "   Start it in another terminal with: ./start_server.sh"
            echo "   Or: python mcp_server.py"
            exit 1
        fi
        echo -e "${GREEN}✅ MCP server detected at http://localhost:8001${NC}"
        ;;
    all)
        echo "🎯 Running All Tests..."
        TEST_PATH="tests/"
        # Note: Server check happens in individual test suites
        ;;
    *)
        echo -e "${RED}❌ Unknown test suite: $SUITE${NC}"
        echo "Usage: ./run_tests.sh [suite] [options]"
        echo "  Suites: all|unit|integration|e2e|uat (default: all)"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh              # Run all tests"
        echo "  ./run_tests.sh unit         # Run unit tests only"
        echo "  ./run_tests.sh e2e -v       # Run E2E tests with verbose output"
        echo "  ./run_tests.sh all --cov    # Run all tests with coverage"
        exit 1
        ;;
esac

echo ""

# Run pytest with the specified path and any additional options
pytest $TEST_PATH "$@"

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
fi

exit $EXIT_CODE
