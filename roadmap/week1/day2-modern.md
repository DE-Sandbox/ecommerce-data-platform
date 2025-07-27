# Week 1 Day 2: Data Models, APIs, Synthetic Data & Monitoring (2025)

> **Status**: In Progress
> **Prerequisites**: Day 1 infrastructure fully operational (LocalStack, Terraform, Docker)

## Overview
**Goal**: Design data models, create APIs, synthetic data generation, and establish monitoring  
**Approach**: Schema-first design with observability from day one  
**Stack**: FastAPI, SQLAlchemy 2.0, Faker, Prometheus, Grafana  

---

## Day 2 Morning Session: Data Modeling & Database Design

### 1. Data Model Design (2 hours) ✅ COMPLETED
- [x] Design comprehensive e-commerce database schema
- [x] Implement PostgreSQL schema with UUID v7
- [x] Add soft delete pattern to all tables
- [x] Configure table relationships and constraints
- [x] Add audit trigger functions
- [x] Set up optimistic locking (version columns)
- [x] Document schema in SQL files

### 2. Migration Framework Setup (1 hour) 🎯 **HIGH PRIORITY**
- [ ] Set up Alembic with async PostgreSQL support
- [ ] Generate initial migration from existing schema
- [ ] Create migration commands in justfile (db-migrate, db-rollback)
- [ ] Test upgrade/downgrade procedures
- [ ] Create seed data migration

### 3. Data Quality Framework (1 hour) ⏸️ **DEFER TO DAY 3**
- [ ] ~~Integrate Great Expectations~~ (complexity not needed yet)
- [x] Define data quality rules (via DB constraints)
- [ ] Create Pydantic validation models
- [ ] Add API request validation
- [ ] Set up data quality metrics

### 4. Event Schema Registry (30 mins)
- [ ] Design event taxonomy
- [ ] Create schema versioning strategy
- [ ] Define core business events
- [ ] Plan schema evolution approach
- [ ] Document event flows

---

## Day 2 Afternoon Session: APIs, Synthetic Data & Monitoring

### 1. FastAPI Application Setup (1.5 hours) 🎯 **HIGH PRIORITY**
- [ ] Create src/api/ structure with routers
- [ ] Set up async SQLAlchemy 2.0 sessions
- [ ] Generate Pydantic v2 models from DB schema
- [ ] Add API versioning via headers (not URL)
- [ ] Create health/readiness endpoints
- [ ] Enable auto-generated OpenAPI docs
- [ ] Add CORS and security middleware

### 2. Synthetic Data Generation (1.5 hours) 🎯 **HIGH PRIORITY**
- [ ] Set up Factory Boy for consistent data
- [ ] Create realistic e-commerce patterns:
  - [ ] Customer personas with behavior
  - [ ] Product catalog with realistic pricing
  - [ ] Order flows with proper state
- [ ] Add temporal patterns (peak hours, seasons)
- [ ] Build REST endpoints:
  - [ ] POST /api/synthetic/generate
  - [ ] POST /api/synthetic/stream
- [ ] Add CLI commands to justfile

### 3. Observability Setup (1 hour) 🚀 **QUICK WIN**
- [ ] Add Prometheus + Grafana to docker-compose
- [ ] Configure PostgreSQL exporter
- [ ] Add FastAPI metrics middleware:
  - [ ] Request duration histogram
  - [ ] Error rate counter
  - [ ] Active connections gauge
- [ ] Create auto-provisioned dashboards
- [ ] Set up structlog for JSON logging
- [ ] Add correlation IDs to requests

### 4. CDC Pipeline Foundation (1 hour) 🔄 **CORE CAPABILITY**
- [ ] Add Redpanda (not Kafka) to docker-compose
- [ ] Configure PostgreSQL for logical replication
- [ ] Set up Debezium PostgreSQL connector
- [ ] Create topics for each table
- [ ] Add Redpanda Console for monitoring
- [ ] Test with sample transactions
- [ ] Add CDC health checks to monitoring

---

## Deliverables Checklist

### Morning Session
- [x] Complete e-commerce data model documentation
- [x] PostgreSQL schema SQL files (sql/schema/001_initial_schema.sql)
- [ ] DynamoDB schema design document
- [ ] Migration scripts ready (Alembic not yet configured)
- [x] Data quality rules defined (via constraints and triggers)
- [ ] Event schema registry design

### Afternoon Session
- [ ] FastAPI application running
- [ ] Synthetic data generation API
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards created
- [ ] Health check endpoints working
- [ ] CDC pipeline capturing changes

---

## Success Criteria
- [ ] Can generate 1000 customers, 5000 orders in < 10 seconds
- [ ] API documentation auto-generated at /docs
- [ ] Database migrations tested with rollback
- [ ] Grafana dashboards show key metrics
- [ ] CDC events visible in Redpanda Console
- [ ] All health checks passing

## Adjusted Execution Order

**Morning (3-4 hours)**:
1. Alembic setup (critical for safe development)
2. FastAPI structure with basic endpoints
3. Start synthetic data framework

**Afternoon (3-4 hours)**:
4. Complete synthetic data with API
5. Add monitoring stack
6. Set up CDC pipeline
7. Test everything together

## Key Architecture Decisions

1. **Use Redpanda instead of Kafka** - Simpler, no Zookeeper, Kafka-compatible
2. **Skip Great Expectations for now** - Pydantic validation is sufficient
3. **Defer DynamoDB** - Focus on PostgreSQL CDC first
4. **API versioning via headers** - More flexible than URL versioning
5. **Factory Boy over Faker alone** - Better referential integrity

---

## Additional Work Completed Today

### Development Environment Improvements
- [x] Added comprehensive database maintenance commands to justfile
- [x] Configured SQL linting with SQLFluff for both raw SQL and dbt
- [x] Set up mypy type checking in pre-commit hooks
- [x] Added optimized test runner for changed files only
- [x] Created GitHub Actions workflow for CI/CD
- [x] Fixed all type annotations to avoid using Any
- [x] Configured trunk-based development workflow

### Testing Infrastructure
- [x] Created comprehensive database initialization tests
- [x] Set up pytest with proper fixtures for database testing
- [x] Added configuration validation tests
- [x] Implemented test optimization for local development

## Dependencies to Add
```toml
# Core
fastapi = "^0.115.0"
uvicorn = "^0.32.0"
pydantic = "^2.10.0"
sqlalchemy = "^2.0.35"
alembic = "^1.14.0"
asyncpg = "^0.30.0"

# Data Generation
faker = "^30.0.0"
factory-boy = "^3.3.1"

# Monitoring
prometheus-client = "^0.21.0"
structlog = "^24.4.0"

# Testing
pytest-asyncio = "^0.24.0"
httpx = "^0.28.0"

# CDC
debezium = "^2.7.0"  # via Docker
confluent-kafka = "^2.6.0"  # for Python client
```

---

## Next Steps Preview (Day 3)
- GitHub Actions CI/CD pipeline
- Comprehensive testing framework
- API contract testing
- Performance benchmarking
- Security scanning integration