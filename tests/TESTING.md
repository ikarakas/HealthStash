# HealthStash Testing Documentation

## Overview

This document provides comprehensive information about the testing infrastructure for the HealthStash application. Our testing strategy ensures code quality, reliability, and performance across all components.

## Testing Architecture

```
┌─────────────────────────────────────────────────┐
│                   CI/CD Pipeline                 │
├─────────────────────────────────────────────────┤
│  Code Quality → Unit Tests → Integration Tests   │
│       ↓            ↓              ↓              │
│  Security Scan → E2E Tests → Performance Tests  │
│       ↓            ↓              ↓              │
│   Build Images → Deploy Staging → Production    │
└─────────────────────────────────────────────────┘
```

## Test Categories

### 1. Unit Tests
- **Location**: `backend/tests/test_*.py`, `frontend/tests/unit/`
- **Coverage Target**: 80%
- **Execution Time**: < 5 minutes
- **Run Command**: 
  ```bash
  # Backend
  cd backend && pytest -m unit
  
  # Frontend
  cd frontend && npm run test
  ```

### 2. Integration Tests
- **Location**: `backend/tests/test_*.py` (marked with `@pytest.mark.integration`)
- **Coverage Target**: 70%
- **Execution Time**: < 10 minutes
- **Run Command**: 
  ```bash
  cd backend && pytest -m integration
  ```

### 3. End-to-End Tests
- **Location**: `tests/e2e/`
- **Framework**: Playwright
- **Browsers**: Chrome, Firefox, Safari, Mobile
- **Run Command**: 
  ```bash
  npx playwright test
  ```

### 4. Performance Tests
- **Location**: `backend/tests/locustfile.py`
- **Framework**: Locust
- **Metrics**: Response time, throughput, error rate
- **Run Command**: 
  ```bash
  locust -f backend/tests/locustfile.py --host http://localhost:8000
  ```

### 5. Container Health Checks
- **Location**: `backend/tests/test_containers.py`
- **Checks**: Service availability, resource usage, restart resilience
- **Run Command**: 
  ```bash
  pytest backend/tests/test_containers.py
  ```

## Test Execution Guide

### Quick Start

1. **Install Dependencies**
   ```bash
   # Backend
   pip install -r backend/test_requirements.txt
   
   # Frontend
   cd frontend && npm install
   
   # E2E
   npx playwright install
   ```

2. **Run All Tests**
   ```bash
   ./run-tests.sh --all
   ```

3. **Run Specific Test Suite**
   ```bash
   # Unit tests only
   ./run-tests.sh --unit
   
   # E2E tests only
   ./run-tests.sh --e2e
   
   # Performance tests
   ./run-tests.sh --performance
   ```

### Docker-Based Testing

```bash
# Run tests in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific test suite
docker-compose -f docker-compose.test.yml run backend-tests
docker-compose -f docker-compose.test.yml run frontend-tests
docker-compose -f docker-compose.test.yml run e2e-tests
```

## Test Coverage

### Backend Coverage
- **Current**: Tracking via pytest-cov
- **Reports**: HTML, XML, Terminal
- **View Report**: `open backend/htmlcov/index.html`

### Frontend Coverage
- **Current**: Tracking via Vitest/V8
- **Reports**: HTML, LCOV, JSON
- **View Report**: `open frontend/coverage/index.html`

### Coverage Requirements
- New code must have >80% coverage
- Critical paths must have >90% coverage
- Security-related code must have 100% coverage

## Performance Benchmarks

### API Response Times
| Endpoint | Target | Current |
|----------|--------|---------|
| GET /health | <100ms | ✅ 45ms |
| POST /auth/login | <200ms | ✅ 120ms |
| GET /health-records | <300ms | ✅ 180ms |
| POST /files/upload | <1000ms | ✅ 650ms |

### Load Test Targets
- **Concurrent Users**: 100
- **Requests/Second**: 500
- **Error Rate**: <1%
- **P95 Response Time**: <500ms

## Security Testing

### Automated Security Checks
1. **Dependency Scanning**: Safety, Snyk
2. **Code Analysis**: Bandit, Semgrep
3. **Container Scanning**: Trivy, Grype
4. **SAST**: CodeQL, SonarQube

### Security Test Categories
- SQL Injection prevention
- XSS protection
- CSRF protection
- Authentication bypass attempts
- Rate limiting verification
- File upload validation
- Path traversal prevention

## Test Data Management

### Fixtures and Factories
- **Location**: `backend/tests/factories.py`
- **Purpose**: Generate consistent test data
- **Usage**:
  ```python
  from tests.factories import UserFactory, HealthRecordFactory
  
  user = UserFactory()
  record = HealthRecordFactory(user=user)
  ```

### Test Database
- **Reset**: Before each test run
- **Seeding**: Via factories and fixtures
- **Cleanup**: Automatic after tests

## Continuous Integration

### GitHub Actions Workflow
- **Trigger**: Push, PR, Schedule
- **Stages**: Lint → Test → Build → Deploy
- **Artifacts**: Coverage reports, test results, performance metrics

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: backend-tests
        name: Backend Tests
        entry: pytest backend/tests -m "unit and not slow"
        language: system
        pass_filenames: false
      
      - id: frontend-tests
        name: Frontend Tests
        entry: npm test
        language: system
        pass_filenames: false
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Ensure test database is running
   docker-compose up -d postgres
   
   # Reset test database
   ./scripts/reset-test-db.sh
   ```

2. **Port Conflicts**
   ```bash
   # Check for port usage
   lsof -i :8000
   lsof -i :3000
   
   # Kill conflicting processes
   kill -9 <PID>
   ```

3. **Flaky E2E Tests**
   ```bash
   # Run with debug mode
   npx playwright test --debug
   
   # Increase timeouts
   npx playwright test --timeout=60000
   ```

## Test Monitoring

### Metrics Dashboard
- **URL**: http://localhost:3000/tests/dashboard
- **Metrics**: Test execution time, pass rate, coverage trends
- **Alerts**: Failed tests, coverage drops, performance degradation

### Test Reports
- **Location**: `test-results/`
- **Formats**: HTML, JSON, JUnit XML
- **Retention**: 30 days

## Best Practices

### Writing Tests

1. **Follow AAA Pattern**
   - Arrange: Set up test data
   - Act: Execute the function
   - Assert: Verify the result

2. **Use Descriptive Names**
   ```python
   def test_user_can_upload_pdf_file_successfully():
       # Not: test_upload()
   ```

3. **Isolate Tests**
   - No shared state between tests
   - Use fixtures for setup/teardown
   - Mock external dependencies

4. **Test Edge Cases**
   - Null/empty inputs
   - Boundary values
   - Error conditions
   - Concurrent operations

### Performance Testing

1. **Baseline Measurements**
   - Establish performance baselines
   - Track trends over time
   - Alert on degradation

2. **Realistic Scenarios**
   - Use production-like data
   - Simulate real user behavior
   - Test at expected scale

## Maintenance

### Weekly Tasks
- Review failed tests in CI
- Update test dependencies
- Archive old test reports

### Monthly Tasks
- Review and update test coverage targets
- Performance baseline review
- Security scan review

### Quarterly Tasks
- Full E2E test suite review
- Load test scenario updates
- Disaster recovery testing

## Contact

For testing-related questions:
- **Email**: qa@healthstash.example.com
- **Slack**: #testing-support
- **Documentation**: https://docs.healthstash.example.com/testing