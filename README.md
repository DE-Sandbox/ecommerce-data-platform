# E-Commerce Data Platform (2025)

A modern e-commerce data engineering platform implementing lakehouse architecture with cutting-edge 2025 tooling. Demonstrates CDC streaming, batch processing, and comprehensive orchestration patterns suitable for production deployment.

## 🚀 Quick Start

```bash
# 1. Set up development environment
just setup

# 2. Start LocalStack + PostgreSQL
just up

# 3. Use the awslocal script for LocalStack AWS CLI
./scripts/awslocal s3 ls
./scripts/awslocal dynamodb list-tables

# Or add to PATH for convenience
export PATH="$PWD/scripts:$PATH"
awslocal s3 ls
```

### Alternative AWS CLI usage:
```bash
# Source environment and use alias
source scripts/localstack-env.sh
awslocal s3 ls

# Or manually with environment variables
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
aws --endpoint-url=http://localhost:4566 s3 ls
```

## 📋 Project Structure

```
ecommerce-data-platform/
├── docs/                           # Technical documentation
│   ├── python-setup.md             # UV & Ruff modern Python setup
│   ├── docker-guide.md             # Multi-stage containerization
│   ├── local-development.md        # LocalStack AWS emulation
│   └── modern-data-engineering-setup.md # 2025 best practices
├── roadmap/                        # Project planning
│   ├── initial-roadmap.md          # 2-month implementation plan
│   ├── project-basic-roadmap.md    # Basic roadmap
│   └── week1-todo-list.md          # Week 1 tasks
├── CLAUDE.md                       # AI assistant guidance
├── pyproject.toml                  # Modern Python 3.13+ configuration
├── Dockerfile                      # Multi-stage optimized builds
└── Makefile                        # UV-powered development commands
```

## 🛠 Modern Technology Stack (2025)

### Core Technologies
- **Python 3.13+** - Latest stable with performance improvements
- **UV** - Rust-powered dependency management (10-100x faster than pip)
- **Ruff** - Ultra-fast linter/formatter (replaces Black, isort, flake8, bandit)
- **LocalStack** - Complete AWS emulation (90+ services locally)

### Data Platform
- **Dagster 1.11.3+** - Modern orchestration with Components
- **dbt Core 1.10.5+** - Data transformations with Fusion engine
- **Delta Lake** - Lakehouse storage format
- **PostgreSQL** - OLTP workloads
- **Redpanda** - Kafka-compatible streaming

## 🔧 Development Commands

```bash
# Code quality (Rust-powered, ultra-fast)
make format                         # Format with Ruff
make lint                          # Lint with Ruff + mypy
make check                         # Run all quality checks

# Testing
make test                          # Run all tests
make test-watch                    # Continuous testing (TDD)

# Data platform
make docs                          # Generate dbt documentation
awslocal s3 ls                     # Interact with local AWS
```

## 📖 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Quick reference and AI assistant guidance
- **[docs/](docs/)** - Comprehensive technical documentation
- **[roadmap/](roadmap/)** - Project planning and implementation roadmaps

## 🎯 Key Features

- **10-100x faster development** with UV and Ruff
- **Complete local AWS environment** with LocalStack
- **Production-identical code** for local and cloud
- **Modern containerization** with multi-stage Docker builds
- **Comprehensive testing** with Testcontainers
- **Enterprise-grade security** and best practices

## 💰 Cost Optimization

- **85-95% development cost reduction** using LocalStack vs cloud ($25/month vs $500-2000/month)
- **~$45-50/month estimated production costs** on AWS
- **Optimized resource usage** with lifecycle policies and efficient architectures
