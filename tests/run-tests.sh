#!/bin/bash

# HealthStash Comprehensive Test Runner
# This script automates all testing procedures including unit, integration, E2E, and performance tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
TEST_RESULTS_DIR="$SCRIPT_DIR/test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Test flags
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
RUN_PERFORMANCE=false
RUN_SECURITY=false
RUN_ALL=false
RUN_CONTAINERS=false
VERBOSE=false
COVERAGE=false
PARALLEL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --unit)
            RUN_UNIT=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --e2e)
            RUN_E2E=true
            shift
            ;;
        --performance)
            RUN_PERFORMANCE=true
            shift
            ;;
        --security)
            RUN_SECURITY=true
            shift
            ;;
        --containers)
            RUN_CONTAINERS=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --all           Run all test suites"
            echo "  --unit          Run unit tests only"
            echo "  --integration   Run integration tests only"
            echo "  --e2e           Run end-to-end tests only"
            echo "  --performance   Run performance tests only"
            echo "  --security      Run security tests only"
            echo "  --containers    Run container health checks"
            echo "  --coverage      Generate coverage reports"
            echo "  --verbose       Verbose output"
            echo "  --parallel      Run tests in parallel"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# If no specific tests selected, run all
if [ "$RUN_ALL" = true ]; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_E2E=true
    RUN_PERFORMANCE=true
    RUN_SECURITY=true
    RUN_CONTAINERS=true
fi

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed - some tests may fail"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose is not installed - some tests may fail"
    fi
    
    log_success "Dependencies check completed"
}

setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"
    mkdir -p "$TEST_RESULTS_DIR/backend"
    mkdir -p "$TEST_RESULTS_DIR/frontend"
    mkdir -p "$TEST_RESULTS_DIR/e2e"
    mkdir -p "$TEST_RESULTS_DIR/performance"
    mkdir -p "$TEST_RESULTS_DIR/security"
    
    # Start test containers if needed
    if [ "$RUN_INTEGRATION" = true ] || [ "$RUN_E2E" = true ] || [ "$RUN_CONTAINERS" = true ]; then
        log_info "Starting test containers..."
        docker-compose up -d postgres timescaledb minio
        
        # Wait for services to be ready
        log_info "Waiting for services to be ready..."
        sleep 10
        
        # Check service health
        docker-compose ps
    fi
    
    log_success "Test environment setup completed"
}

run_backend_unit_tests() {
    log_info "Running backend unit tests..."
    
    cd "$BACKEND_DIR"
    
    # Install test dependencies if needed
    pip install -q -r test_requirements.txt
    
    # Run unit tests
    if [ "$COVERAGE" = true ]; then
        pytest tests/ -m unit \
            --cov=app \
            --cov-report=html:$TEST_RESULTS_DIR/backend/coverage \
            --cov-report=xml:$TEST_RESULTS_DIR/backend/coverage.xml \
            --html=$TEST_RESULTS_DIR/backend/unit-tests.html \
            --self-contained-html \
            $([ "$VERBOSE" = true ] && echo "-v") \
            $([ "$PARALLEL" = true ] && echo "-n auto")
    else
        pytest tests/ -m unit \
            --html=$TEST_RESULTS_DIR/backend/unit-tests.html \
            --self-contained-html \
            $([ "$VERBOSE" = true ] && echo "-v") \
            $([ "$PARALLEL" = true ] && echo "-n auto")
    fi
    
    if [ $? -eq 0 ]; then
        log_success "Backend unit tests passed"
    else
        log_error "Backend unit tests failed"
        exit 1
    fi
}

run_backend_integration_tests() {
    log_info "Running backend integration tests..."
    
    cd "$BACKEND_DIR"
    
    # Run integration tests
    pytest tests/ -m integration \
        --html=$TEST_RESULTS_DIR/backend/integration-tests.html \
        --self-contained-html \
        $([ "$VERBOSE" = true ] && echo "-v")
    
    if [ $? -eq 0 ]; then
        log_success "Backend integration tests passed"
    else
        log_error "Backend integration tests failed"
        exit 1
    fi
}

run_frontend_unit_tests() {
    log_info "Running frontend unit tests..."
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        npm ci
    fi
    
    # Run unit tests
    if [ "$COVERAGE" = true ]; then
        npm run test:coverage
        cp -r coverage/* $TEST_RESULTS_DIR/frontend/
    else
        npm test
    fi
    
    if [ $? -eq 0 ]; then
        log_success "Frontend unit tests passed"
    else
        log_error "Frontend unit tests failed"
        exit 1
    fi
}

run_e2e_tests() {
    log_info "Running end-to-end tests..."
    
    # Start all services
    log_info "Starting all services for E2E tests..."
    docker-compose up -d
    
    # Wait for services
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    curl -f http://localhost/health || {
        log_error "Services are not healthy"
        docker-compose logs
        exit 1
    }
    
    # Install Playwright if needed
    if ! command -v playwright &> /dev/null; then
        npm install -g @playwright/test
        npx playwright install --with-deps
    fi
    
    # Run E2E tests
    npx playwright test \
        --reporter=html \
        --output=$TEST_RESULTS_DIR/e2e
    
    if [ $? -eq 0 ]; then
        log_success "E2E tests passed"
    else
        log_error "E2E tests failed"
        # Save logs for debugging
        docker-compose logs > $TEST_RESULTS_DIR/e2e/docker-logs.txt
        exit 1
    fi
}

run_performance_tests() {
    log_info "Running performance tests..."
    
    # Ensure services are running
    docker-compose up -d
    sleep 10
    
    cd "$BACKEND_DIR/tests"
    
    # Install Locust if needed
    pip install -q locust
    
    # Run performance tests
    locust -f locustfile.py \
        --headless \
        --users 50 \
        --spawn-rate 5 \
        --run-time 2m \
        --host http://localhost:8000 \
        --html $TEST_RESULTS_DIR/performance/report.html \
        --csv $TEST_RESULTS_DIR/performance/stats
    
    if [ $? -eq 0 ]; then
        log_success "Performance tests completed"
        
        # Check performance thresholds
        python3 -c "
import csv
import sys

with open('$TEST_RESULTS_DIR/performance/stats_stats.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Name'] == 'Aggregated':
            avg_response = float(row['Average (ms)'])
            failure_rate = float(row['Failure Count']) / float(row['Request Count']) * 100 if float(row['Request Count']) > 0 else 0
            
            print(f'Average Response Time: {avg_response}ms')
            print(f'Failure Rate: {failure_rate:.2f}%')
            
            if avg_response > 500:
                print('WARNING: Average response time exceeds 500ms threshold')
                sys.exit(1)
            if failure_rate > 1:
                print('WARNING: Failure rate exceeds 1% threshold')
                sys.exit(1)
"
    else
        log_error "Performance tests failed"
        exit 1
    fi
}

run_security_tests() {
    log_info "Running security tests..."
    
    cd "$BACKEND_DIR"
    
    # Run Bandit security scanner
    log_info "Running Bandit security scanner..."
    bandit -r app -f json -o $TEST_RESULTS_DIR/security/bandit-report.json
    
    # Run Safety vulnerability scanner
    log_info "Running Safety vulnerability scanner..."
    safety check --json > $TEST_RESULTS_DIR/security/safety-report.json || true
    
    # Run Trivy container scanner
    if command -v trivy &> /dev/null; then
        log_info "Running Trivy container scanner..."
        trivy fs . --format json --output $TEST_RESULTS_DIR/security/trivy-report.json
    fi
    
    log_success "Security tests completed"
}

run_container_health_checks() {
    log_info "Running container health checks..."
    
    cd "$BACKEND_DIR"
    
    # Run container tests
    pytest tests/test_containers.py -v \
        --html=$TEST_RESULTS_DIR/backend/container-tests.html \
        --self-contained-html
    
    if [ $? -eq 0 ]; then
        log_success "Container health checks passed"
    else
        log_error "Container health checks failed"
        exit 1
    fi
}

generate_test_report() {
    log_info "Generating test report..."
    
    # Create summary report
    cat > $TEST_RESULTS_DIR/summary.md << EOF
# Test Results Summary
**Date**: $(date)
**Branch**: $(git branch --show-current)
**Commit**: $(git rev-parse --short HEAD)

## Test Suites Run
- Unit Tests: $([ "$RUN_UNIT" = true ] && echo "✅" || echo "⏭️")
- Integration Tests: $([ "$RUN_INTEGRATION" = true ] && echo "✅" || echo "⏭️")
- E2E Tests: $([ "$RUN_E2E" = true ] && echo "✅" || echo "⏭️")
- Performance Tests: $([ "$RUN_PERFORMANCE" = true ] && echo "✅" || echo "⏭️")
- Security Tests: $([ "$RUN_SECURITY" = true ] && echo "✅" || echo "⏭️")
- Container Health: $([ "$RUN_CONTAINERS" = true ] && echo "✅" || echo "⏭️")

## Results Location
All test results are available in: $TEST_RESULTS_DIR

## Coverage Reports
- Backend: $TEST_RESULTS_DIR/backend/coverage/index.html
- Frontend: $TEST_RESULTS_DIR/frontend/index.html

## Performance Report
$TEST_RESULTS_DIR/performance/report.html

## Security Reports
- Bandit: $TEST_RESULTS_DIR/security/bandit-report.json
- Safety: $TEST_RESULTS_DIR/security/safety-report.json
EOF
    
    log_success "Test report generated: $TEST_RESULTS_DIR/summary.md"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Stop test containers if they were started
    if [ "$RUN_INTEGRATION" = true ] || [ "$RUN_E2E" = true ] || [ "$RUN_CONTAINERS" = true ]; then
        docker-compose down
    fi
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    echo "=========================================="
    echo "   HealthStash Test Suite Runner"
    echo "=========================================="
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Setup test environment
    setup_test_environment
    
    # Run selected test suites
    if [ "$RUN_UNIT" = true ]; then
        run_backend_unit_tests
        run_frontend_unit_tests
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_backend_integration_tests
    fi
    
    if [ "$RUN_E2E" = true ]; then
        run_e2e_tests
    fi
    
    if [ "$RUN_PERFORMANCE" = true ]; then
        run_performance_tests
    fi
    
    if [ "$RUN_SECURITY" = true ]; then
        run_security_tests
    fi
    
    if [ "$RUN_CONTAINERS" = true ]; then
        run_container_health_checks
    fi
    
    # Generate report
    generate_test_report
    
    # Cleanup
    cleanup
    
    echo ""
    echo "=========================================="
    echo "   All Tests Completed Successfully!"
    echo "=========================================="
    echo ""
    echo "View results at: $TEST_RESULTS_DIR/summary.md"
}

# Trap errors and cleanup
trap cleanup EXIT

# Run main function
main