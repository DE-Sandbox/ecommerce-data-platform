# Modern task runner for e-commerce data platform
set dotenv-load := true
set export := true

# Default recipe to display help
default:
    @just --list

# Development environment setup
setup:
    @echo "🚀 Setting up development environment..."
    export PATH="$HOME/.local/bin:$PATH" && uv sync --dev
    mise install
    ./scripts/git-hooks/install-hooks.sh
    @echo "✅ Development environment ready!"

# Start all services
up:
    @echo "🐳 Starting Docker services..."
    docker-compose up -d
    @echo "⏳ Waiting for services to be ready..."
    sleep 10
    just init-aws
    @echo "✅ All services running!"

# Stop all services
down:
    docker-compose down
    @echo "🛑 Services stopped"

# Initialize LocalStack AWS resources
init-aws:
    @echo "☁️  Initializing AWS resources in LocalStack..."
    ./scripts/init_aws_resources.sh

# Code quality checks (ultra-fast with Ruff)
lint:
    @echo "🔍 Running linters..."
    export PATH="$HOME/.local/bin:$PATH" && uv run ruff check src/ tests/
    export PATH="$HOME/.local/bin:$PATH" && uv run ruff format --check src/ tests/
    export PATH="$HOME/.local/bin:$PATH" && uv run mypy src/

# Format code
fmt:
    @echo "✨ Formatting code..."
    export PATH="$HOME/.local/bin:$PATH" && uv run ruff check --fix src/ tests/
    export PATH="$HOME/.local/bin:$PATH" && uv run ruff format src/ tests/

# Run tests
test:
    @echo "🧪 Running tests..."
    export PATH="$HOME/.local/bin:$PATH" && uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    @echo "📊 Running tests with coverage..."
    export PATH="$HOME/.local/bin:$PATH" && uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

# Security scan
security:
    @echo "🔐 Running security checks..."
    export PATH="$HOME/.local/bin:$PATH" && uv run bandit -r src/
    export PATH="$HOME/.local/bin:$PATH" && uv run pip-audit
    @echo "✅ Security scan complete"

# Docker security scan
docker-security image="ecommerce-data-platform:latest":
    @echo "🐳 Running Docker security scan..."
    ./scripts/docker-security-scan.sh {{image}}

# Build Docker image
docker-build target="production":
    @echo "🔨 Building Docker image ({{target}} stage)..."
    docker build --target {{target}} -t ecommerce-data-platform:{{target}} .
    @echo "✅ Image built: ecommerce-data-platform:{{target}}"

# Clean everything
clean:
    @echo "🧹 Cleaning up..."
    docker-compose down -v
    rm -rf .cache/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
    find . -type d -name __pycache__ -exec rm -rf {} +
    export PATH="$HOME/.local/bin:$PATH" && uv cache clean
    @echo "✨ Clean!"

# AWS credentials check (no exposure)
check-aws:
    @echo "🔍 Checking AWS configuration..."
    @aws sts get-caller-identity > /dev/null 2>&1 && echo "✅ AWS credentials configured" || echo "❌ AWS credentials not configured"
    @echo "Active profile: ${AWS_PROFILE:-default}"
    @test -f ~/.aws/credentials && echo "⚠️  Warning: Found credentials file. Consider using aws-vault" || echo "✅ No credentials file found (good!)"

# Deploy to AWS (with safety check)
deploy profile="personal":
    @echo "🚀 Deploying to AWS with profile: {{profile}}"
    @echo "⚠️  This will deploy real AWS resources. Continue? [y/N]"
    @read -r response && [ "$$response" = "y" ] || (echo "Cancelled" && exit 1)
    aws-vault exec {{profile}} -- terraform apply

# Local development with hot reload
dev:
    @echo "🔥 Starting development server..."
    export PATH="$HOME/.local/bin:$PATH" && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
migrate:
    @echo "🗄️  Running database migrations..."
    export PATH="$HOME/.local/bin:$PATH" && uv run alembic upgrade head

# Generate synthetic data
generate-data:
    @echo "🎲 Generating synthetic data..."
    export PATH="$HOME/.local/bin:$PATH" && uv run python scripts/generate_data.py

# View logs
logs service="":
    @if [ -z "{{service}}" ]; then \
        docker-compose logs -f; \
    else \
        docker-compose logs -f {{service}}; \
    fi

# AWS CLI with LocalStack
aws-local *args:
    @aws --endpoint-url="${AWS_ENDPOINT_URL:-http://localhost:4566}" {{args}}

# Shell into a service
shell service:
    docker-compose exec {{service}} /bin/bash

# Quick health check
health:
    @echo "🏥 Health Check"
    @echo "==============="
    @docker-compose ps
    @echo ""
    @echo "LocalStack:"
    @curl -s http://localhost:4566/_localstack/health | jq -r '.services' || echo "LocalStack not running"

# Update dependencies
update:
    @echo "📦 Updating dependencies..."
    export PATH="$HOME/.local/bin:$PATH" && uv lock --upgrade
    export PATH="$HOME/.local/bin:$PATH" && uv sync --dev
    @echo "✅ Dependencies updated!"

# Run pre-commit hooks
pre-commit:
    export PATH="$HOME/.local/bin:$PATH" && uv run pre-commit run --all-files

# Git operations for trunk-based development
new branch:
    git checkout main
    git pull --rebase
    git checkout -b {{branch}}

done:
    git checkout main
    git pull --rebase

# Complete development workflow check
check-all: lint test security
    @echo "✅ All checks passed!"

# Terraform commands for LocalStack
tf-init:
    ./scripts/tf-local.sh init

tf-plan:
    ./scripts/tf-local.sh plan

tf-apply:
    ./scripts/tf-local.sh apply

tf-destroy:
    ./scripts/tf-local.sh destroy

# Full infrastructure setup
infra-up: up tf-apply
    @echo "✅ Infrastructure ready!"

# Full infrastructure teardown
infra-down: tf-destroy down
    @echo "🧹 Infrastructure cleaned up!"