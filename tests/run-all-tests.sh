#!/bin/bash
# Quick test runner for common test scenarios

set -e

echo "🧪 HealthStash Test Suite"
echo "========================"
echo ""

# Default to running integration tests
TEST_TYPE=${1:-integration}

case $TEST_TYPE in
    quick)
        echo "Running quick tests..."
        cd ../backend && python -m pytest tests/ -m "unit and not slow" -v
        ;;
    
    integration)
        echo "Running integration tests..."
        python comprehensive_test.py
        ;;
    
    security)
        echo "Running security tests..."
        python test_user_isolation.py
        ;;
    
    backend)
        echo "Running backend tests..."
        cd ../backend && python -m pytest tests/ -v
        ;;
    
    frontend)
        echo "Running frontend tests..."
        cd ../frontend && npm test
        ;;
    
    e2e)
        echo "Running E2E tests..."
        npx playwright test --config=playwright.config.js
        ;;
    
    all)
        echo "Running all tests..."
        ./run-tests.sh --all
        ;;
    
    *)
        echo "Usage: $0 [quick|integration|security|backend|frontend|e2e|all]"
        echo ""
        echo "  quick       - Run fast unit tests only"
        echo "  integration - Run comprehensive integration test (default)"
        echo "  security    - Run user isolation security tests"
        echo "  backend     - Run all backend tests"
        echo "  frontend    - Run all frontend tests"
        echo "  e2e         - Run end-to-end browser tests"
        echo "  all         - Run complete test suite"
        exit 1
        ;;
esac

echo ""
echo "✅ Tests completed!"