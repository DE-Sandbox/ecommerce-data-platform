# CLAUDE.md - AI Agent Instructions

## Critical Rules

1. **Working Directory**: Always operate from project root
2. **Commands**: Use `just` (not `make`) - see `justfile` for all commands
3. **Python**: Use `uv` package manager, Python 3.13+, strict typing
4. **Git**: No AI attribution in commits, use trunk-based development
5. **Testing**: Follow TDD - write tests first, then implementation

## Quick Commands

```bash
# Environment
just setup          # Initial setup
just up            # Start services
just down          # Stop services

# Development
just lint          # Run linters (ruff + mypy)
just fmt           # Format code
just test          # Run tests
just test-cov      # Test with coverage

# Database
just migrate       # Apply migrations
just migrate-new "name"  # Create migration
just db-status     # Check database

# Common workflow
just lint && just test  # Before committing
```

## Code Standards

### Python MUST-HAVES

```python
# ✅ ALWAYS
from pathlib import Path         # Never os.path
def process(data: str) -> int:   # Always type hints
async with session:              # Context managers

# ❌ NEVER
def process(data: Any):          # No Any type
os.path.join()                   # Use Path instead
hardcoded_url = "localhost:5432" # Use config files
```

### Configuration

- Store in `config/*.yaml` files
- Use `${ENV_VAR:-default}` syntax
- Load with `src/core/config.py:ConfigLoader`

## Project Context

**E-commerce Data Platform**: AWS lakehouse architecture demonstration

- **Stack**: PostgreSQL, Dagster, dbt, Delta Lake, LocalStack
- **Async**: SQLAlchemy 2.0 with asyncpg
- **Testing**: pytest-asyncio, testcontainers

## File Locations

```text
src/
├── core/          # Config, utilities
├── models/        # SQLAlchemy models
├── database/      # Functions, migrations
└── services/      # Business logic

tests/             # Mirror src structure
config/            # YAML configurations
docs/              # Documentation
```

## Development Workflow

1. **Before coding**: Read existing code patterns
2. **TDD cycle**: Test → Code → Refactor
3. **Code review**: Use data-swe-code-reviewer agent, ALWAYS show summary
4. **Before commit**: `just lint && just test`
5. **Documentation**: Update immediately with code changes

### Code Review Process

**ALWAYS after writing code:**
1. Run data-swe-code-reviewer agent
2. Display summary to user:
   ```
   Code Review Summary:
   
   CRITICAL (must fix):
   - [Issue and fix]
   
   WARNINGS (should fix):
   - [Issue and suggestion]
   
   SUGGESTIONS (nice to have):
   - [Minor improvements]
   ```
3. Wait for user approval before fixing critical issues

## Common Tasks

### Add new model

1. Create test in `tests/models/test_*.py`
2. Create model in `src/models/*.py`
3. Run `just migrate-new "add model"`
4. Review and apply migration

### Fix linting

```bash
just fmt           # Auto-fix formatting
just lint          # Check remaining issues
```

### Debug tests

```bash
just test tests/path/to/test.py::test_name -v
```

## References

- **Detailed rules**: `docs/development-rulebook.md`
- **Local setup**: `docs/local-development.md`
- **All commands**: `justfile`
