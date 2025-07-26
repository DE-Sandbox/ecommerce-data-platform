# Modern Python Development Setup (2025)

This guide covers the modern Python development setup using cutting-edge tools that provide 10-100x performance improvements over traditional approaches.

## UV: The Modern Python Package Manager

**UV** is a Rust-powered Python package manager that replaces pip, Poetry, and even pyenv in most use cases. It provides installation speeds that are 10-100x faster than traditional tools.

### Installation

```bash
# Install UV (works on macOS, Linux, Windows)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip (if you must)
pip install uv

# Or via Homebrew (macOS)
brew install uv
```

### Basic Usage

```bash
# Create a new project
uv init my-project
cd my-project

# Install dependencies from pyproject.toml
uv sync                             # Install all dependencies
uv sync --dev                       # Include development dependencies  
uv sync --no-dev                    # Production dependencies only
uv sync --all-extras                # Include all optional dependencies

# Add new dependencies
uv add pandas                       # Add to production dependencies
uv add --dev pytest                 # Add to development dependencies
uv add --optional data "dask[array]" # Add to optional dependency group

# Remove dependencies
uv remove pandas
uv remove --dev pytest

# Run commands in the environment
uv run python script.py
uv run pytest
uv run black src/

# Create and manage Python environments
uv python install 3.13             # Install Python 3.13
uv python list                      # List installed Python versions
uv venv                            # Create virtual environment
uv venv --python 3.13              # Create venv with specific Python version
```

### UV vs Traditional Tools

| Task | Traditional | UV Command | Speed Improvement |
|------|-------------|------------|-------------------|
| Install dependencies | `pip install -r requirements.txt` | `uv sync` | 10-100x faster |
| Add dependency | `pip install pandas && pip freeze > requirements.txt` | `uv add pandas` | Instant |
| Create environment | `python -m venv venv && source venv/bin/activate` | `uv venv` | 10x faster |
| Lock dependencies | `pip-tools compile` | `uv lock` | 50x faster |

## Ruff: Ultra-Fast Python Linter and Formatter

**Ruff** consolidates multiple tools (Black, isort, flake8, bandit, etc.) into a single, ultra-fast solution running at 10-100x the speed of traditional linters.

### Key Features

- **800+ built-in rules** covering style, complexity, security, and more
- **Format and lint** in a single tool
- **Compatible** with existing Black, isort, and flake8 configurations
- **Automatic fixes** for many rule violations

### Usage

```bash
# Lint code
uv run ruff check src/              # Check for issues
uv run ruff check --fix src/        # Check and auto-fix issues

# Format code  
uv run ruff format src/             # Format code (replaces Black)
uv run ruff format --check src/     # Check formatting without changes

# Combined workflow
uv run ruff check --fix src/ && uv run ruff format src/
```

### Configuration

Ruff is configured in `pyproject.toml` with comprehensive rule selection:

```toml
[tool.ruff]
target-version = "py313"
line-length = 88
select = ["ALL"]  # Enable all available rules
ignore = [
    "D",      # pydocstyle (use only when needed)
    "ANN",    # flake8-annotations (mypy handles this)
    "COM",    # flake8-commas (formatter handles this)
    # ... see pyproject.toml for full list
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

## Type Checking with Mypy

**Mypy** remains the gold standard for Python type checking, now optimized for modern Python versions.

### Usage

```bash
# Type check source code
uv run mypy src/

# Type check with specific options
uv run mypy --strict src/
uv run mypy --show-error-codes src/
```

### Configuration

```toml
[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
```

## Development Workflow

### Daily Development Commands

```bash
# Start development
uv sync --dev                       # Install all dependencies
uv run pre-commit install           # Install git hooks

# Code quality checks (fast with Ruff)
uv run ruff check --fix src/        # Lint and auto-fix
uv run ruff format src/             # Format code
uv run mypy src/                    # Type checking

# Testing
uv run pytest                      # Run tests
uv run pytest --cov=src            # Run with coverage
uv run pytest-watch                # Continuous testing (TDD)

# All-in-one quality check
make check                          # Uses Makefile for combined checks
```

### Pre-commit Integration

UV works seamlessly with pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Performance Comparisons

### Dependency Installation

```bash
# Traditional approach
time pip install -r requirements.txt
# Real: 45.2s, User: 12.3s, Sys: 4.1s

# UV approach  
time uv sync
# Real: 1.8s, User: 0.3s, Sys: 0.2s
# 25x faster!
```

### Linting and Formatting

```bash
# Traditional approach (Black + isort + flake8)
time (black src/ && isort src/ && flake8 src/)
# Real: 8.4s, User: 7.2s, Sys: 1.1s

# Ruff approach
time ruff check --fix src/ && ruff format src/
# Real: 0.2s, User: 0.1s, Sys: 0.1s  
# 42x faster!
```

## Migration Guide

### From pip + requirements.txt

```bash
# Convert requirements.txt to pyproject.toml
uv add --requirements requirements.txt
uv add --dev --requirements requirements-dev.txt

# Remove old files
rm requirements.txt requirements-dev.txt
```

### From Poetry

```bash
# UV can read Poetry's pyproject.toml directly
uv sync

# Remove Poetry-specific files
rm poetry.lock
```

### From pip-tools

```bash
# Convert from requirements.in
uv add --requirements requirements.in
uv add --dev --requirements requirements-dev.in

# UV's uv.lock replaces requirements.txt
rm requirements.in requirements-dev.in requirements.txt requirements-dev.txt
```

## Best Practices

1. **Always use `uv sync`** instead of manual pip installs
2. **Pin Python version** in pyproject.toml: `requires-python = ">=3.13"`
3. **Use dependency groups** for optional features: `uv add --optional data pandas`
4. **Commit uv.lock** to ensure reproducible builds
5. **Use `uv run`** for all script execution to ensure environment consistency
6. **Configure Ruff comprehensively** to replace multiple tools
7. **Enable all Ruff rules** then selectively ignore what you don't need

## Troubleshooting

### Common Issues

```bash
# UV not found after installation
source ~/.bashrc  # or restart terminal

# Permission issues
uv cache clean    # Clear UV cache

# Dependency conflicts
uv lock --upgrade  # Regenerate lock file

# Environment issues
rm -rf .venv && uv sync  # Recreate environment
```

### Performance Tips

```bash
# Use UV cache for faster subsequent installs
export UV_CACHE_DIR="$HOME/.cache/uv"

# Parallel installs (default, but can be tuned)
export UV_CONCURRENT_INSTALLS=8

# Skip unnecessary steps in CI
uv sync --frozen  # Don't update lock file
```

This modern Python setup provides dramatic performance improvements while maintaining compatibility with existing tools and workflows.