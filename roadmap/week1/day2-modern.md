# Week 1 Day 2: Data Models, APIs, Synthetic Data & Monitoring (2025)

> **Status**: Partially Complete (Morning: 90%, Afternoon: 10%)  
> **Last Updated**: 2025-07-31
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

### 2. Migration Framework Setup (1 hour) ✅ COMPLETED
- [x] Set up Alembic with async PostgreSQL support
- [x] Generate initial migration from existing schema
- [x] Create migration commands in justfile (migrate, migrate-new, migrate-down, etc.)
- [x] Test upgrade/downgrade procedures
- [x] Refactor to use Alembic as single source of truth for tables
- [x] Create documentation for migration workflow
- [x] Create minimal reference data migration (currencies, statuses only)

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

### 0. Architect-Recommended Data Strategy 🏗️ **NEW APPROACH**


Implement layered data strategy:
- [ ] **Reference Data** (via migration): Currencies, order statuses, payment types
- [ ] **Bootstrap Service**: Minimal operational data endpoint
- [ ] **Synthetic Data API**: Full test data generation
- [ ] **Scenario-Based Generators**: Complex e-commerce patterns
- [ ] 

### 1. FastAPI Application Setup (1.5 hours) 🎯 **HIGH PRIORITY**
- [ ] Create src/api/ structure with routers
- [ ] Set up async SQLAlchemy 2.0 sessions
- [ ] Generate Pydantic v2 models from DB schema
- [ ] Add API versioning via headers (not URL)
- [ ] Create health/readiness endpoints
- [ ] Enable auto-generated OpenAPI docs
- [ ] Add CORS and security middleware

### 2. Synthetic Data Generation (1.5 hours) 🎯 **ARCHITECT-ALIGNED**
- [ ] Create layered data generation framework:
  - [ ] Base `DataGenerator` abstract class
  - [ ] Model-specific generators (CustomerGenerator, ProductGenerator)
  - [ ] Scenario-based generators (BlackFridayScenario, SeasonalScenario)
- [ ] Implement Factory Boy patterns for consistency
- [ ] Build REST endpoints:
  - [ ] POST /api/synthetic/reference-data (minimal bootstrap)
  - [ ] POST /api/synthetic/generate/{model}
  - [ ] POST /api/synthetic/scenarios/{scenario}
  - [ ] POST /api/synthetic/bulk-generate
- [ ] Add progress tracking for large datasets
- [ ] Create CLI commands in justfile

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
- [x] Migration scripts ready (Alembic fully configured with justfile commands)
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

## Architect-Recommended Execution Order

**Phase 1: Foundation (1 hour)**
1. Create minimal reference data migration (currencies, statuses)
2. Set up FastAPI project structure with proper layering

**Phase 2: Core API (2 hours)**
3. Build FastAPI with async SQLAlchemy sessions
4. Generate Pydantic models from SQLAlchemy
5. Create health/readiness endpoints

**Phase 3: Data Generation Framework (2 hours)**
6. Implement base DataGenerator classes
7. Create model-specific generators
8. Build synthetic data API endpoints

**Phase 4: Advanced Features (2 hours)**
9. Add scenario-based generators
10. Implement bulk generation with progress tracking
11. Set up monitoring stack (if time permits)

## Key Architecture Decisions

1. **Use Redpanda instead of Kafka** - Simpler, no Zookeeper, Kafka-compatible
2. **Skip Great Expectations for now** - Pydantic validation is sufficient
3. **Defer DynamoDB** - Focus on PostgreSQL CDC first
4. **API versioning via headers** - More flexible than URL versioning
5. **Factory Boy over Faker alone** - Better referential integrity

---

## Actual Completion Status (2025-07-31)

### ✅ Fully Completed
- **Data Model Design**: All SQLAlchemy models with UUID v7, soft delete, audit fields
- **Migration Framework**: Alembic fully configured with async support and alembic_utils
- **Testing Infrastructure**: Comprehensive model tests, fixtures, pytest-asyncio
- **Database Commands**: Full suite of db commands in justfile
- **Type Safety**: Strict typing enforced, no Any types allowed
- **Documentation**: Consolidated docs, development rulebook, optimized CLAUDE.md

### ⚠️ Partially Completed  
- **CDC Infrastructure**: Redpanda in docker-compose but no Debezium connector
- **Monitoring**: Metrics endpoint exists but no Prometheus/Grafana stack

### ❌ Not Started
- **FastAPI Application**: No src/api/ structure created
- **Synthetic Data Generation**: No implementation
- **Pydantic Models**: Not generated from DB schema
- **Event Schema Registry**: Design not completed
- **DynamoDB Integration**: Deferred to later

### 📊 Completion Metrics
- Morning Session: 75% complete (missing seed data, event registry)
- Afternoon Session: 10% complete (only docker-compose updates)
- Overall Day 2: ~40% complete

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