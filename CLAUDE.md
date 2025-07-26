# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Directory Guidelines

**ALWAYS work from the project root directory unless specifically required otherwise:**
- Default working directory: `<project-root>` (where this CLAUDE.md file is located)
- Return to root directory after any subdirectory operations
- Use relative paths from project root in commands and documentation
- Only change to subdirectories when explicitly needed for specific operations

**Directory change examples:**
```bash
# ✅ Good: Run commands from project root
just tf-apply
uv run ruff check src/

# ❌ Avoid: Working from subdirectories unless necessary  
cd terraform/environments/local && terraform apply
```

## Git Commit Guidelines

**NEVER include AI attribution in commit messages:**
- ❌ Do NOT add "Generated with Claude Code" or similar
- ❌ Do NOT add "Co-Authored-By: Claude" lines
- ✅ Write clean, professional commit messages focused on the changes
- ✅ Use conventional commit format when appropriate

## Core Development Principles

### 1. Test-Driven Development (TDD)
**ALWAYS use TDD approach where possible:**
- Write tests BEFORE implementing functionality
- Follow the Red-Green-Refactor cycle:
  1. Write a failing test (Red)
  2. Write minimal code to pass the test (Green)
  3. Refactor while keeping tests passing
- For data pipelines: Write data quality tests before transformations
- For APIs: Write integration tests before implementing endpoints
- For dbt models: Write model tests before creating the SQL

### 2. Documentation Maintenance
**ALWAYS keep documentation up-to-date:**
- Update documentation IMMEDIATELY after code changes
- Run post-processing checks to confirm documentation updates
- Documentation includes:
  - Code comments for complex logic
  - README files for new modules
  - API documentation for new endpoints
  - dbt model descriptions
  - Dagster asset descriptions
- After any code change, verify:
  - CLAUDE.md reflects new patterns or commands
  - README.md includes new setup steps if needed
  - Inline documentation matches implementation

## Project Overview

This is an e-commerce data engineering platform implementing a modern lakehouse architecture on AWS. The project demonstrates CDC streaming, batch processing, and comprehensive orchestration patterns suitable for production deployment.

## Architecture Overview

### Data Flow
- **Source Systems**: PostgreSQL (OLTP), DynamoDB (NoSQL), S3 (Object Storage)
- **Ingestion**: Debezium CDC → Kafka/Kinesis → Delta Lake
- **Processing**: Dagster orchestration with dbt transformations
- **Storage**: Delta Lake on S3 with AWS Glue Catalog
- **Analytics**: Amazon Athena and EMR Serverless

### Technology Stack
- **Local Development**: Docker, LocalStack, Testcontainers
- **Streaming**: Debezium, Kafka/Redpanda (local), Kinesis (AWS)
- **Batch Processing**: dlthub with custom connectors
- **Orchestration**: Dagster with asset-based pipelines
- **Transformation**: dbt Core for data modeling
- **Storage Format**: Delta Lake (with Iceberg migration path)

## Common Commands

### Local Development Setup
```bash
# Start all services
docker-compose up -d

# Initialize databases
docker exec -i postgres psql -U postgres < scripts/init_postgres.sql

# Create S3 buckets in LocalStack
aws --endpoint-url=http://localhost:4566 s3 mb s3://data-lake
aws --endpoint-url=http://localhost:4566 s3 mb s3://staging
```

### Python Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run tests in watch mode (for TDD)
pytest-watch

# Run documentation tests
pytest --doctest-modules src/
```

### Code Quality & Linting
```bash
# Python linting and formatting
black src/ tests/                    # Format Python code
isort src/ tests/                    # Sort imports
flake8 src/ tests/                   # Check style and complexity
mypy src/                            # Type checking
bandit -r src/                       # Security linting

# SQL linting (dbt models)
sqlfluff lint models/                # Lint SQL files
sqlfluff fix models/                 # Auto-fix SQL issues

# YAML/JSON linting
yamllint .                           # Lint YAML files
jsonlint **/*.json                   # Lint JSON files

# Run all linters
make lint                            # Run complete linting suite

# Pre-commit hooks (run automatically on commit)
pre-commit install                   # Install hooks
pre-commit run --all-files          # Run all hooks manually
```

### dbt Commands
```bash
# Run dbt models
dbt run

# Test dbt models
dbt test

# Generate and serve documentation
dbt docs generate && dbt docs serve
```

### Synthetic Data Generation
```bash
# Start synthetic data API
python src/synthetic_data/api.py

# Generate test data
curl -X POST http://localhost:8000/api/generate/customers?count=1000
curl -X POST http://localhost:8000/api/generate/orders?count=5000
```

## Key Directories and Files

### Project Structure
- `src/synthetic_data/` - Synthetic data generation APIs
- `src/ingestion/` - CDC and batch ingestion pipelines
- `src/orchestration/` - Dagster pipeline definitions
- `models/` - dbt transformation models
- `tests/` - Unit, integration, and e2e tests
- `docker/` - Docker configurations and Dockerfiles
- `terraform/` - AWS infrastructure as code

### Important Configuration Files
- `docker-compose.yml` - Local service orchestration
- `.env` - Environment variables (AWS keys, service configs)
- `dagster.yaml` - Dagster configuration
- `dbt_project.yml` - dbt project configuration
- `requirements.txt` - Python dependencies

## Development Workflow

### TDD Development Cycle
1. **Write Test First**: Create failing test for new functionality
2. **Implement Minimal Code**: Make the test pass with simplest solution
3. **Refactor**: Improve code while keeping tests green
4. **Update Documentation**: Immediately update relevant docs
5. **Run Documentation Checks**: Verify all docs are current

### Daily Development Process
1. **Local Services**: Always start with `docker-compose up -d`
2. **Test Watch**: Run `pytest-watch` for continuous testing during TDD
3. **Dagster UI**: Access at http://localhost:3000 for pipeline monitoring
4. **LocalStack**: AWS service emulation at http://localhost:4566
5. **Redpanda Console**: Kafka monitoring at http://localhost:8080


### Post-Development Checklist
After any code change, ALWAYS verify:
- [ ] All tests pass (`pytest tests/`)
- [ ] All linters pass (`make lint` or individual linters)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Security checks pass (`bandit -r src/`)
- [ ] Documentation updated (README, CLAUDE.md, inline docs)
- [ ] dbt documentation regenerated (`dbt docs generate`)
- [ ] No broken links in documentation
- [ ] Code coverage maintained or improved

## Testing Strategy

### TDD Testing Hierarchy
- **Unit Tests**: Test individual functions and transformations (write FIRST)
- **Integration Tests**: Use testcontainers for service integration
- **Data Quality**: dbt tests and Great Expectations checks (define before models)
- **E2E Tests**: Full pipeline validation from source to analytics
- **Documentation Tests**: Verify code examples in docs work

### Testing Best Practices
- Write tests before implementation (TDD)
- Use descriptive test names that explain business value
- Test edge cases and error conditions
- Maintain test data fixtures for consistency
- Mock external dependencies in unit tests
- Use property-based testing for data transformations

## AWS Deployment Notes

The platform is designed for AWS deployment with:
- S3 for data lake storage with lifecycle policies
- Kinesis Data Streams for real-time ingestion
- EMR Serverless for heavy processing
- Athena for interactive queries
- Estimated monthly cost: ~$45-50

## Key Implementation Patterns

1. **CDC Implementation**: Uses Debezium for change data capture with exactly-once processing
2. **Incremental Processing**: dbt incremental models with late-arriving data handling
3. **Asset-Based Orchestration**: Dagster assets with partitioned backfilling
4. **Schema Evolution**: Handled through Delta Lake and careful versioning
5. **Cost Optimization**: Partitioning, compression, and lifecycle policies

## Documentation Maintenance Commands

### Pre-commit Documentation Checks
```bash
# Check for outdated documentation
python scripts/check_docs.py

# Validate code examples in documentation
pytest --doctest-modules docs/

# Check for broken links
markdown-link-check README.md docs/**/*.md

# Regenerate API documentation
sphinx-build -b html docs/ docs/_build/

# Update dbt documentation
dbt docs generate && dbt docs serve --port 8001
```

### Documentation Update Workflow
When making code changes:
1. Update relevant docstrings immediately
2. Regenerate API docs if interfaces changed
3. Update README.md for new features or setup changes
4. Update CLAUDE.md for new commands or patterns
5. Run documentation validation checks
6. Commit documentation changes with code changes