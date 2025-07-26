# Multi-stage build for optimal performance and security
FROM python:3.13-slim-bookworm AS base

# Install system dependencies and UV (10-100x faster than pip)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Build stage - install all dependencies including dev tools
FROM base AS builder

# Install all dependencies (including dev) for building
RUN uv sync --all-extras

# Production stage - minimal runtime image
FROM base AS production

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install only production dependencies
RUN uv sync --no-dev

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser scripts/ ./scripts/

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uv", "run", "python", "-m", "src.main"]

# Development stage - includes dev tools and debugging capabilities
FROM builder AS development

# Install additional development tools
RUN uv add --dev \
    ipython \
    jupyter \
    debugpy

# Copy all files for development
COPY . .

# Install pre-commit hooks
RUN uv run pre-commit install

# Expose common development ports
EXPOSE 8000 8888 5678

# Development command with hot reload
CMD ["uv", "run", "python", "-m", "src.main", "--reload"]

# Testing stage - optimized for CI/CD
FROM builder AS testing

# Copy all source code and tests
COPY . .

# Run quality checks
RUN uv run ruff check . && \
    uv run ruff format --check . && \
    uv run mypy src/ && \
    uv run pytest tests/ --cov=src --cov-report=xml

# Data processing stage - optimized for data workloads
FROM base AS data-processor

# Install additional system dependencies for data processing
RUN apt-get update && apt-get install -y \
    postgresql-client \
    awscli \
    && rm -rf /var/lib/apt/lists/*

# Install data processing dependencies
RUN uv sync --group data

# Copy data processing scripts
COPY --chown=appuser:appuser src/data_processing/ ./src/data_processing/
COPY --chown=appuser:appuser models/ ./models/

# Switch to non-root user
USER appuser

# Configure memory settings for data processing
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV MALLOC_ARENA_MAX=2

# Data processing command
CMD ["uv", "run", "python", "-m", "src.data_processing.main"]