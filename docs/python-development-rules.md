# Python Development Rules and Standards

This document defines the Python development standards and rules for the e-commerce data platform project.

## Python Version and Tools

### Required Python Version
- **Python 3.13+** (latest stable version)
- Use `mise` for Python version management (not pyenv)
- Use `uv` for package management (not pip/poetry)

### Essential Tools
```bash
# Version management
mise use python@3.13

# Package management
uv pip install <package>
uv run <command>

# Code quality
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

## Type Safety Rules

### 1. NO Any Types
**NEVER use `typing.Any` in code:**
```python
# ❌ BAD
def process_data(data: Any) -> Any:
    return data

# ✅ GOOD - Define specific types
type ConfigValue = str | int | float | bool | list[ConfigValue] | dict[str, ConfigValue] | None

def process_data(data: ConfigValue) -> ConfigValue:
    return data
```

### 2. Use Modern Type Syntax
**Use Python 3.12+ type syntax:**
```python
# ❌ OLD
from typing import Union, Optional, List, Dict, TypeAlias
ConfigValue: TypeAlias = Union[str, int, None]
items: List[str] = []
mapping: Dict[str, int] = {}
value: Optional[str] = None

# ✅ MODERN
type ConfigValue = str | int | None
items: list[str] = []
mapping: dict[str, int] = {}
value: str | None = None
```

### 3. Type All Functions
**Every function must have type annotations:**
```python
# ❌ BAD
def calculate_total(items):
    return sum(item.price for item in items)

# ✅ GOOD
def calculate_total(items: list[OrderItem]) -> Decimal:
    return sum(item.price for item in items)
```

### 4. Type Class Methods
**All class methods including `__init__` must be typed:**
```python
class ConfigLoader:
    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory."""
        self.config_dir = config_dir or Path("config")
```

## Code Style Rules

### 1. Docstrings
**Use Google-style docstrings with proper formatting:**
```python
def load_config(name: str, env: str | None = None) -> dict[str, ConfigValue]:
    """Load configuration from YAML file.

    Args:
        name: Configuration file name without extension
        env: Environment name (development, production)

    Returns:
        Configuration dictionary with substituted values
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
    """
```

### 2. Import Organization
**Imports must follow this order (enforced by Ruff):**
```python
# Standard library
import os
import re
from pathlib import Path

# Third-party packages
import pytest
import yaml

# Local imports
from src.core.config import ConfigLoader
```

### 3. Path Operations
**Always use pathlib, never os.path:**
```python
# ❌ BAD
import os
config_file = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_file) as f:
    data = yaml.safe_load(f)

# ✅ GOOD
from pathlib import Path
config_file = Path(__file__).parent / "config.yaml"
with config_file.open() as f:
    data = yaml.safe_load(f)
```

### 4. String Formatting
**Use f-strings for formatting:**
```python
# ❌ BAD
message = "Config {} not found in {}".format(name, path)
url = "postgresql://" + user + ":" + password + "@" + host

# ✅ GOOD
message = f"Config {name} not found in {path}"
url = f"postgresql://{user}:{password}@{host}"
```

### 5. Boolean Comparisons
**Use `is` for boolean comparisons:**
```python
# ❌ BAD
if config["enabled"] == True:
    pass
if result == False:
    pass

# ✅ GOOD
if config["enabled"] is True:
    pass
if result is False:
    pass
# Or even better
if config["enabled"]:
    pass
if not result:
    pass
```

## Configuration Management

### 1. No Hardcoded Values
**ALWAYS use configuration files:**
```python
# ❌ BAD
DATABASE_URL = "postgresql://localhost:5432/mydb"
API_KEY = "sk-1234567890"

# ✅ GOOD
from src.core.config import load_database_config
config = load_database_config()
database_url = get_database_url()
```

### 2. Environment Variables
**Use ${VAR:-default} syntax in YAML:**
```yaml
database:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}
  name: ${DB_NAME:-ecommerce_dev}
```

### 3. Type-Safe Config Access
**Define config structures with proper types:**
```python
type ConfigDict = dict[str, ConfigValue]

def get_redis_config() -> ConfigDict:
    result = get_config().get("application", "cache.redis", {})
    if isinstance(result, dict):
        return result
    return {}
```

## Testing Rules

### 1. Type Test Functions
**All test functions must have return type annotations:**
```python
def test_config_loading(self) -> None:
    """Test configuration loading."""
    assert True
```

### 2. Use Fixtures Properly
**Type fixture parameters:**
```python
def test_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test with environment variables."""
    monkeypatch.setenv("API_KEY", "test-key")
```

### 3. Avoid Broad Exceptions
**Be specific with exception types:**
```python
# ❌ BAD
with pytest.raises(Exception):
    config.load("invalid")

# ✅ GOOD
with pytest.raises(yaml.YAMLError):
    config.load("invalid")
```

## Project Structure

### 1. Package Structure
**Every package must have `__init__.py`:**
```
src/
├── __init__.py          # "E-commerce data platform source code."
├── core/
│   ├── __init__.py      # "Core utilities and configuration."
│   └── config.py
└── models/
    ├── __init__.py      # "Data models and schemas."
    └── customer.py
```

### 2. Module Docstrings
**Every module must start with a docstring:**
```python
"""Configuration management module.

Loads configuration from YAML files with environment variable substitution.
"""
```

## Error Handling

### 1. Use Specific Exceptions
```python
# ❌ BAD
raise Exception("Something went wrong")

# ✅ GOOD
msg = f"Configuration file not found: {config_file}"
raise FileNotFoundError(msg)
```

### 2. Error Messages in Variables
**Assign error messages to variables (Ruff rule):**
```python
# ❌ BAD
raise ValueError(f"Invalid value: {value}")

# ✅ GOOD
msg = f"Invalid value: {value}"
raise ValueError(msg)
```

## Async/Await Rules

### 1. Type Async Functions
```python
async def fetch_data(url: str) -> dict[str, str]:
    """Fetch data from URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 2. Use AsyncIO Types
```python
from collections.abc import AsyncIterator

async def stream_orders() -> AsyncIterator[Order]:
    """Stream orders from database."""
    async with get_db_connection() as conn:
        async for row in conn.fetch("SELECT * FROM orders"):
            yield Order.from_row(row)
```

## Linting Configuration

### Ruff Settings (pyproject.toml)
```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "DTZ",    # flake8-datetimez
    "T10",    # flake8-debugger
    "EXE",    # flake8-executable
    "ISC",    # flake8-implicit-str-concat
    "PIE",    # flake8-pie
    "T20",    # flake8-print
    "PT",     # flake8-pytest-style
    "Q",      # flake8-quotes
    "RET",    # flake8-return
    "SIM",    # flake8-simplify
    "TID",    # flake8-tidy-imports
    "ARG",    # flake8-unused-arguments
    "ERA",    # eradicate
    "PL",     # pylint
    "TRY",    # tryceratops
    "RUF",    # ruff-specific rules
    "ANN",    # flake8-annotations
    "D",      # pydocstyle
    "PD",     # pandas-vet
    "N",      # pep8-naming
    "COM",    # flake8-commas
    "C90",    # mccabe complexity
    "INP",    # flake8-no-pep420
    "PTH",    # flake8-use-pathlib
]

[tool.ruff.format]
quote-style = "double"
```

### MyPy Settings
```toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_any_explicit = true
disallow_any_generics = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

## Git Pre-commit Hooks

### Required Hooks (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-pyyaml, types-requests]
```

## Development Workflow

1. **Before Writing Code:**
   - Ensure environment is activated: `source ~/.zshrc`
   - Update dependencies: `uv pip sync`

2. **While Writing Code:**
   - Add type annotations for ALL functions and variables
   - Write docstrings for all public functions/classes
   - Use configuration files, never hardcode values

3. **Before Committing:**
   - Run linters: `uv run ruff check . --fix`
   - Run type checker: `uv run mypy src/`
   - Run tests: `uv run pytest tests/`
   - Ensure all hooks pass: `pre-commit run --all-files`

4. **Common Commands:**
   ```bash
   # Development
   uv run python -m src.main
   
   # Testing
   uv run pytest tests/ -v
   uv run pytest tests/ --cov=src
   
   # Linting
   uv run ruff check .
   uv run ruff format .
   uv run mypy src/
   
   # Dependencies
   uv pip install package-name
   uv pip freeze > requirements.txt
   ```

## IDE Configuration

### VS Code Settings
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true,
  "python.analysis.typeCheckingMode": "strict"
}
```

## Summary Checklist

Before submitting any Python code, ensure:
- [ ] All functions have type annotations
- [ ] No `Any` types are used
- [ ] All imports are properly organized
- [ ] Docstrings follow Google style
- [ ] Configuration values are not hardcoded
- [ ] Tests have return type `-> None`
- [ ] Path operations use `pathlib`
- [ ] Boolean comparisons use `is`
- [ ] Error messages use variables
- [ ] All linting passes (`ruff` and `mypy`)