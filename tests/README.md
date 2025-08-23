# HealthStash Tests

This directory contains all test files for the HealthStash application.

## Test Structure

```
tests/
├── README.md                    # This file
├── comprehensive_test.py        # Full system integration test
├── test_user_isolation.py      # Security/isolation testing
├── e2e/                        # End-to-end tests
│   ├── auth.spec.js           # Authentication flow tests
│   └── health-records.spec.js # Health records E2E tests
├── backend/                    # Backend unit/integration tests (symlink)
└── frontend/                   # Frontend component tests (symlink)
```

## Running Tests

### System Integration Tests

```bash
# Run comprehensive system test (creates users, records, uploads files)
python tests/comprehensive_test.py

# Test user data isolation and security
python tests/test_user_isolation.py
```

### Backend Tests

```bash
# Run all backend tests
cd backend && pytest tests/

# Run specific test categories
pytest backend/tests/ -m unit        # Unit tests only
pytest backend/tests/ -m integration # Integration tests
pytest backend/tests/ -m security    # Security tests
```

### Frontend Tests

```bash
# Run frontend unit tests
cd frontend && npm test

# Run with coverage
cd frontend && npm run test:coverage
```

### End-to-End Tests

```bash
# Run E2E tests with Playwright
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test tests/e2e/auth.spec.js
```

### Load/Performance Tests

```bash
# Run load tests with Locust
cd backend/tests
locust -f locustfile.py --host http://localhost:8000

# Run headless with specific parameters
locust -f locustfile.py --headless -u 50 -r 5 -t 2m --host http://localhost:8000
```

## Test Categories

### 1. **Unit Tests** (`backend/tests/test_*.py`)
- Test individual functions and methods
- Mock external dependencies
- Fast execution
- Run frequently during development

### 2. **Integration Tests** (`comprehensive_test.py`)
- Test complete workflows
- Use real database and services
- Verify component interactions
- Run before deployments

### 3. **Security Tests** (`test_user_isolation.py`)
- Verify data isolation between users
- Test authentication and authorization
- Check for vulnerabilities
- Critical for medical data compliance

### 4. **E2E Tests** (`e2e/*.spec.js`)
- Test from user perspective
- Full browser automation
- Verify UI workflows
- Run before releases

### 5. **Performance Tests** (`backend/tests/locustfile.py`)
- Load testing
- Stress testing
- Concurrent user simulation
- Run before scaling decisions

## Quick Test Commands

```bash
# Run all tests (requires all services running)
./run-tests.sh --all

# Run specific test suites
./run-tests.sh --unit           # Fast unit tests
./run-tests.sh --integration    # Integration tests
./run-tests.sh --e2e           # End-to-end tests
./run-tests.sh --security      # Security tests
./run-tests.sh --performance   # Performance tests

# Run with coverage
./run-tests.sh --all --coverage
```

## Test Data

Test users created during testing:
- Pattern: `test_[timestamp]@example.com`
- Default password: `TestPassword123!` or as specified
- Admin users: `admin@example.com`, `newadmin_*@example.com`

## Cleanup

Test data is retained for debugging. To clean up:

```sql
-- Remove test users and their data (CASCADE deletes records)
DELETE FROM users WHERE email LIKE '%test_%';
DELETE FROM users WHERE email LIKE '%isolation_test_%';
```

## CI/CD Integration

Tests are automatically run via GitHub Actions on:
- Push to main/develop branches
- Pull requests
- Nightly scheduled runs

See `.github/workflows/ci.yml` for configuration.