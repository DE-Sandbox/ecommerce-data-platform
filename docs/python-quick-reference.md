# Python Quick Reference Card

## Essential Commands

```bash
# Environment setup
source ~/.zshrc          # Load UV and other tools
uv pip sync             # Sync dependencies

# Running code
uv run python src/main.py
uv run pytest tests/ -v

# Code quality
uv run ruff check . --fix     # Lint and auto-fix
uv run ruff format .          # Format code
uv run mypy src/              # Type check

# Pre-commit
pre-commit install            # Set up hooks
pre-commit run --all-files    # Run all checks
```

## Type Annotations Cheat Sheet

```python
# Modern type syntax (Python 3.12+)
type ConfigValue = str | int | float | bool | None
type ConfigDict = dict[str, ConfigValue]

# Function annotations
def process(data: str) -> bool:
    return True

def save_config(config: ConfigDict) -> None:
    """Procedures return None."""
    pass

# Class methods
class Service:
    def __init__(self, name: str) -> None:
        self.name = name
    
    def get_status(self) -> dict[str, str]:
        return {"status": "running"}
```

## Common Patterns

### Configuration Loading
```python
from src.core.config import load_database_config, get_database_url

# Load config
config = load_database_config("development")
db_url = get_database_url()

# Never hardcode!
# ❌ BAD: DB_URL = "postgresql://localhost:5432/db"
# ✅ GOOD: Use config files
```

### Path Operations
```python
from pathlib import Path

# ❌ OLD: os.path.join(os.path.dirname(__file__), "data")
# ✅ NEW:
data_dir = Path(__file__).parent / "data"
config_file = data_dir / "config.yaml"

with config_file.open() as f:
    data = yaml.safe_load(f)
```

### Error Handling
```python
# Specific exceptions with messages
msg = f"File not found: {file_path}"
raise FileNotFoundError(msg)

# In tests
with pytest.raises(ValueError, match="Invalid input"):
    process_data(None)
```

### Boolean Comparisons
```python
# ✅ Use 'is' for explicit checks
if result is True:
    pass
if error is False:
    pass

# ✅ Or implicit boolean
if result:
    pass
if not error:
    pass
```

## Testing Patterns

```python
import pytest

class TestFeature:
    """Test feature functionality."""
    
    def test_basic_case(self) -> None:
        """Every test returns None."""
        assert True
    
    def test_with_fixture(
        self, 
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Type your fixtures."""
        monkeypatch.setenv("KEY", "value")
        assert os.environ["KEY"] == "value"
```

## Pre-commit Checklist

Before committing:
- [ ] `uv run ruff check .` - No errors
- [ ] `uv run mypy src/` - No type errors  
- [ ] `uv run pytest tests/` - All tests pass
- [ ] No hardcoded values (use config)
- [ ] All functions have type annotations
- [ ] No `Any` types used
- [ ] Docstrings for public functions

## Common Ruff Errors

| Error | Fix |
|-------|-----|
| `ANN201` | Add return type: `-> str`, `-> None` |
| `PTH123` | Use `Path.open()` not `open()` |
| `D200` | Make docstring one line |
| `E712` | Use `is True` not `== True` |
| `TRY003` | Assign error message to variable |
| `UP007` | Use `X \| Y` not `Union[X, Y]` |

## VS Code Settings

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": true,
      "source.organizeImports.ruff": true
    }
  }
}
```