# Week 1 Day 3: CI/CD Pipeline & Comprehensive Testing Framework (2025)

> **Status**: Planned  
> **Prerequisites**: Day 1-2 infrastructure, data models, and migrations complete  
> **Focus**: GitHub Actions CI/CD, comprehensive testing framework, security scanning

## Overview
**Goal**: Establish production-ready CI/CD pipeline and comprehensive testing framework  
**Approach**: Test-driven development with automated quality gates  
**Stack**: GitHub Actions, pytest, testcontainers, coverage.py, security scanners  

---

## Day 3 Morning Session: CI/CD Pipeline Setup

### 1. GitHub Actions Workflow (2 hours)
- [ ] Create multi-stage CI/CD pipeline (.github/workflows/ci.yml)
- [ ] Set up matrix testing (Python 3.11, 3.12, 3.13)
- [ ] Configure caching for dependencies and Docker layers
- [ ] Add branch protection rules
- [ ] Set up environment-specific deployments
- [ ] Create reusable workflow components

### 2. Code Quality Gates (1 hour)
- [ ] Integrate Ruff linting in CI
- [ ] Add mypy type checking
- [ ] Configure SQLFluff for SQL linting
- [ ] Set up pre-commit hooks enforcement
- [ ] Add code coverage requirements (>80%)
- [ ] Create quality badges for README

### 3. Security Scanning (1 hour)
- [ ] Add Dependabot configuration
- [ ] Integrate Trivy for container scanning
- [ ] Set up CodeQL analysis
- [ ] Add secrets scanning with TruffleHog
- [ ] Configure SAST/DAST pipelines
- [ ] Create security policy (SECURITY.md)

---

## Day 3 Afternoon Session: Comprehensive Testing Framework

### 1. Test Infrastructure Setup (1.5 hours) 🎯 **CRITICAL**
Based on test coverage gap analysis:
- [ ] Enhance test fixtures in conftest.py
- [ ] Create test data factories (Factory Boy)
- [ ] Set up testcontainers for integration tests
- [ ] Configure pytest plugins (asyncio, cov, xdist)
- [ ] Add performance test utilities
- [ ] Create test database seeding scripts

### 2. Model Test Coverage (2 hours) 🔴 **HIGH PRIORITY**
Address critical gaps identified by functional testing review:
- [ ] Create tests/models/test_payment.py
  - [ ] Payment method validation (all types)
  - [ ] Payment transaction state machine
  - [ ] Refund processing logic
  - [ ] Currency consistency checks
- [ ] Create tests/models/test_inventory.py
  - [ ] Quantity calculation constraints
  - [ ] Stock reservation workflows
  - [ ] Multi-location tracking
  - [ ] Concurrent adjustment handling
- [ ] Create tests/models/test_shopping.py
  - [ ] Cart session management
  - [ ] Cart item operations
  - [ ] Price consistency validation
  - [ ] Cart expiration logic

### 3. Constraint & Validation Testing (1.5 hours) 🟡 **HIGH PRIORITY**
- [ ] Create tests/models/test_constraints.py
  - [ ] CHECK constraint violations
  - [ ] UNIQUE constraint edge cases
  - [ ] Foreign key cascade behaviors
  - [ ] Soft delete interactions
- [ ] Create tests/models/test_calculations.py
  - [ ] Order total calculations
  - [ ] Line item calculations
  - [ ] Currency precision/rounding
  - [ ] Discount application rules

### 4. Integration Test Foundation (1 hour)
- [ ] Create tests/integration/ directory structure
- [ ] Set up transaction rollback fixtures
- [ ] Create workflow test utilities
- [ ] Add API client test helpers
- [ ] Configure test data isolation

### 5. Items Moved from Day 2 (1.5 hours) 🆕
- [ ] Complete observability stack setup
  - [ ] Add Prometheus + Grafana to docker-compose
  - [ ] Configure PostgreSQL exporter
  - [ ] Create auto-provisioned dashboards
  - [ ] Integrate with FastAPI metrics
- [ ] Data quality metrics collection
  - [ ] Track validation failures
  - [ ] Monitor data completeness
  - [ ] Create quality dashboards
- [ ] Event schema documentation
  - [ ] Document schema evolution approach
  - [ ] Create event flow diagrams
  - [ ] Build event catalog

---

## Deliverables Checklist

### Morning Session
- [ ] GitHub Actions CI/CD pipeline operational
- [ ] All code quality tools integrated
- [ ] Security scanning automated
- [ ] Branch protection configured
- [ ] CI badges added to README

### Afternoon Session
- [ ] Test infrastructure enhanced
- [ ] Payment system tests implemented
- [ ] Inventory management tests created
- [ ] Shopping cart tests operational
- [ ] Constraint validation tests complete
- [ ] Test coverage report generated

---

## Success Criteria
- [ ] CI pipeline runs in < 5 minutes
- [ ] Test coverage > 80% for critical models
- [ ] Zero security vulnerabilities in dependencies
- [ ] All database constraints have tests
- [ ] Integration tests use transactions
- [ ] Parallel test execution working

## Test Implementation Priority

Based on functional tester analysis:

### 🔴 Critical (Day 3)
1. Payment processing tests
2. Inventory calculation tests
3. Order integrity tests
4. Cart functionality tests

### 🟡 High Priority (Day 4-5)
1. Concurrency tests
2. Business workflow tests
3. API contract tests
4. Performance benchmarks

### 🟢 Medium Priority (Week 2)
1. Edge case coverage
2. Security validation
3. Load testing
4. Chaos engineering

## GitHub Actions Pipeline Structure

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint with Ruff
      - name: Type check with mypy
      - name: SQL lint with SQLFluff

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12, 3.13]
    services:
      postgres:
        image: postgres:15
      localstack:
        image: localstack/localstack:latest
    steps:
      - name: Run unit tests
      - name: Run integration tests
      - name: Generate coverage report
      - name: Upload coverage to Codecov

  security:
    runs-on: ubuntu-latest
    steps:
      - name: Run Trivy scanner
      - name: Run CodeQL analysis
      - name: Check for secrets

  build:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker images
      - name: Push to registry
```

## Key Testing Patterns

### 1. Fixture Hierarchy
```python
# Base fixtures for all tests
@pytest.fixture
async def db_session():
    """Transactional test database session."""

@pytest.fixture
async def test_client():
    """FastAPI test client with auth."""

@pytest.fixture
async def test_data_factory():
    """Factory for creating test data."""
```

### 2. Parametrized Tests
```python
@pytest.mark.parametrize("payment_type,valid", [
    ("credit_card", True),
    ("invalid_type", False),
    ("", False),
    (None, False),
])
async def test_payment_type_validation(payment_type, valid):
    """Test all payment type validations."""
```

### 3. Transaction Rollback
```python
@pytest.fixture
async def transactional_db():
    """Auto-rollback database for tests."""
    async with engine.begin() as conn:
        await conn.begin_nested()
        yield conn
        await conn.rollback()
```

---

## Next Steps Preview (Day 4)
- CDC Pipeline with Debezium and Redpanda
- Configure PostgreSQL logical replication
- Set up Redpanda Console monitoring
- Create event streaming topics
- Implement CDC health checks
- Performance testing setup

## References
- Test coverage gaps documented in: docs/test-coverage-gaps.md
- Testing best practices: docs/testing-guide.md
- CI/CD documentation: docs/ci-cd-guide.md