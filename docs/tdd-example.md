# Test-Driven Development (TDD) Example

This document shows how we SHOULD have developed the configuration module using TDD, versus how we actually did it.

## What We Did Wrong ❌

1. **Wrote implementation first** (`src/core/config.py`)
2. **Created tests afterward** (`tests/test_config.py`)  
3. **Fixed issues reactively** (linting, type safety)

This is NOT TDD! This is "test-after" development.

## The Correct TDD Approach ✅

### 1. RED Phase - Write Failing Tests First

```python
# tests/test_config_tdd.py
"""Test configuration loader functionality."""

import pytest
from src.core.config import ConfigLoader  # This doesn't exist yet!

def test_load_configuration() -> None:
    """Test basic configuration loading."""
    # This test MUST fail because ConfigLoader doesn't exist
    loader = ConfigLoader()
    config = loader.load("database")
    
    assert isinstance(config, dict)
    assert "host" in config
```

Run test → **FAIL** (ImportError: cannot import ConfigLoader)

### 2. GREEN Phase - Write Minimal Code to Pass

```python
# src/core/config.py
"""Configuration management module."""

class ConfigLoader:
    """Load application configuration."""
    
    def load(self, name: str) -> dict[str, str]:
        """Load configuration."""
        return {"host": "localhost"}  # Minimal implementation!
```

Run test → **PASS** ✅

### 3. REFACTOR Phase - Improve Code Quality

Now that tests pass, refactor while keeping tests green:

```python
# src/core/config.py
"""Configuration management module."""

from pathlib import Path
import yaml

type ConfigDict = dict[str, str | int | bool | None]

class ConfigLoader:
    """Load application configuration."""
    
    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize loader."""
        self.config_dir = config_dir or Path("config")
    
    def load(self, name: str) -> ConfigDict:
        """Load configuration from YAML."""
        config_file = self.config_dir / f"{name}.yaml"
        if not config_file.exists():
            return {"host": "localhost"}  # Default
        
        with config_file.open() as f:
            return yaml.safe_load(f)
```

Run test → **STILL PASSES** ✅

## TDD Cycle for Each Feature

### Example: Adding Environment Variable Support

#### 1. RED - Test First
```python
def test_environment_variable_substitution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test env var substitution."""
    monkeypatch.setenv("DB_HOST", "prod-server")
    
    loader = ConfigLoader()
    config = loader.load("database")
    
    assert config["host"] == "prod-server"  # Will FAIL
```

#### 2. GREEN - Minimal Implementation
```python
def _substitute_env_vars(self, value: str) -> str:
    """Substitute environment variables."""
    if value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        return os.environ.get(var_name, value)
    return value
```

#### 3. REFACTOR - Improve
```python
def _substitute_env_vars(self, value: ConfigValue) -> ConfigValue:
    """Recursively substitute environment variables."""
    if isinstance(value, str):
        pattern = re.compile(r"\$\{([^}]+)\}")
        # ... full implementation
```

## Benefits of True TDD

1. **Better Design**: Writing tests first forces you to think about the API
2. **100% Coverage**: Every line exists because a test required it
3. **Confidence**: Changes don't break existing functionality
4. **Documentation**: Tests document how to use the code
5. **No Over-Engineering**: Only write code that's actually needed

## TDD Rules

1. **Never write production code without a failing test**
2. **Write only enough test code to fail**
3. **Write only enough production code to pass**
4. **Refactor only when tests are green**
5. **One test, one assertion (when possible)**

## Red-Green-Refactor Rhythm

```bash
# 1. Write test
uv run pytest tests/test_new_feature.py  # RED ❌

# 2. Write code
# ... implement minimal solution ...

# 3. Run test
uv run pytest tests/test_new_feature.py  # GREEN ✅

# 4. Refactor
# ... improve code quality ...

# 5. Run all tests
uv run pytest tests/  # ALL GREEN ✅

# 6. Commit
git add -A && git commit -m "feat: add new feature using TDD"
```

## Common TDD Mistakes

1. **Writing too much test**: Test one behavior at a time
2. **Writing implementation details**: Test behavior, not implementation
3. **Not refactoring**: The third step is crucial!
4. **Skipping RED**: If test passes immediately, it's not testing anything
5. **Writing code "just in case"**: YAGNI - You Aren't Gonna Need It

## VS Code TDD Workflow

1. Split screen: test file (left), implementation (right)
2. Use `pytest-watch` for continuous testing:
   ```bash
   uv run pytest-watch tests/test_feature.py
   ```
3. Use VS Code tasks for quick test runs:
   ```json
   {
     "label": "Run Current Test",
     "type": "shell",
     "command": "uv run pytest ${file} -v",
     "problemMatcher": ["$python"]
   }
   ```

## Conclusion

We built our config module backwards:
- ❌ Implementation → Tests → Fixes
- ✅ Should be: Tests → Implementation → Refactor

Going forward, ALWAYS:
1. Write the test first
2. See it fail
3. Make it pass with minimal code
4. Refactor for quality
5. Keep tests green

This is the discipline of TDD!