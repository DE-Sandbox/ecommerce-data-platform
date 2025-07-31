# Development Rulebook

A concise guide to development practices for the E-Commerce Data Platform. These rules are derived from industry best practices and team experience.

## 🎯 Core Principles

1. **Test-Driven Development**: Write tests before implementation
2. **Type Safety**: Use strict type annotations everywhere
3. **Configuration Over Code**: Use YAML configs instead of hardcoded values
4. **Documentation Currency**: Update docs immediately with code changes
5. **Trunk-Based Development**: Small, focused commits that maintain working state

## 🐍 Python Standards

### Code Quality (Enforced by CI/CD)
```bash
# Always run before committing
just lint     # Ruff check + format + mypy
just test     # All tests must pass
just security # Bandit security scan
```

### Type Annotations
```python
# ✅ Correct - Always annotate functions
def process_order(order_id: UUID, amount: Decimal) -> OrderResult:
    return OrderResult(...)

# ❌ Wrong - Missing type annotations
def process_order(order_id, amount):
    return result
```

### Modern Python Patterns
```python
# ✅ Use new union syntax
def get_customer(id: UUID) -> Customer | None:
    return session.get(Customer, id)

# ✅ Use pathlib over os.path
config_path = Path("config") / "database.yaml"

# ✅ Use context managers
async with get_async_session() as session:
    # Database operations
```

## 🗄️ Database Development

### Schema Changes
```bash
# 1. Update SQLAlchemy model
# 2. Generate migration
just migrate-new "add customer preferences"

# 3. Review migration file
# 4. Test migration
just migrate      # Apply
just migrate-down # Rollback test
just migrate      # Re-apply

# 5. Commit model + migration together
```

### Model Design
```python
# ✅ Always use base classes
class Customer(BaseModel, VersionMixin):
    email: Mapped[str] = mapped_column(String(255), unique=True)
    
# ✅ Use UUID v7 (time-ordered)
# ✅ Include soft delete (deleted_at, is_deleted)
# ✅ Include audit fields (created_at, updated_at, version)
```

## 🧪 Testing Requirements

### Test Structure
```python
# ✅ Use async fixtures for database tests
@pytest.mark.asyncio
async def test_create_customer(async_session: AsyncSession) -> None:
    customer = Customer(email="test@example.com")
    async_session.add(customer)
    await async_session.commit()
    
    assert customer.id is not None
```

### TDD Workflow
1. **Red**: Write failing test
2. **Green**: Implement minimal code to pass
3. **Refactor**: Improve while keeping tests green
4. **Document**: Update relevant documentation

### Test Categories
- **Unit**: Individual function/method tests
- **Integration**: Service/database interaction tests  
- **E2E**: Full pipeline tests

## 📁 Project Organization

### Configuration
```yaml
# config/database.yaml
development:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}
  user: ${DB_USER:-postgres}
```

### Directory Structure
```
src/
├── core/           # Configuration, utilities
├── models/         # SQLAlchemy models
├── api/           # FastAPI routes
├── services/      # Business logic
└── database/      # DB functions, migrations

tests/
├── unit/          # Fast, isolated tests
├── integration/   # Database/service tests
└── e2e/          # End-to-end tests
```

## 🔧 Development Workflow

### Daily Development
```bash
# 1. Start environment
just up

# 2. Run tests (TDD workflow)
just test

# 3. Make changes following TDD
# 4. Commit frequently
git add . && git commit -m "feat: add customer validation"

# 5. Push regularly
git push origin main
```

### Before Pushing
```bash
# Required checks (automated in CI/CD)
just lint      # Must pass
just test      # Must pass  
just security  # Must pass
```

## 🐳 Docker Standards

### Multi-stage Builds
```dockerfile
# Use explicit stages
FROM python:3.13-slim AS base
FROM base AS development  
FROM base AS production
```

### Environment Variables
```bash
# ✅ Use descriptive names with defaults
DATABASE_URL=${DATABASE_URL:-postgresql://localhost/ecommerce}

# ❌ Don't hardcode sensitive values
```

## 📋 Documentation Rules

### Update Immediately
- Code changes require documentation updates
- New features need usage examples
- Breaking changes need migration guides

### Format Standards
```markdown
# Use consistent formatting
## Section Headers
### Subsection Headers

# Include working examples
```python
# This code actually works
result = process_data(input)
```

## 🚫 Common Pitfalls

### Avoid These Patterns
```python
# ❌ Don't use Any type
def process(data: Any) -> Any:

# ❌ Don't hardcode URLs/credentials  
DATABASE_URL = "postgresql://user:pass@localhost/db"

# ❌ Don't skip tests
# "I'll add tests later" - No, write them first

# ❌ Don't commit uncommented code
# TODO: This is broken, fix later
```

### Security No-Nos
- Never commit credentials to git
- Never log sensitive data
- Never disable SSL in production
- Never use admin privileges unnecessarily

## ✅ Success Metrics

A successful development session includes:
- [ ] All tests passing
- [ ] No linting errors
- [ ] No security warnings
- [ ] Documentation updated
- [ ] Changes deployed successfully

## 🆘 When Things Go Wrong

### Migration Issues
```bash
# Rollback and investigate
just migrate-down
just migrate-status
# Fix migration file
just migrate
```

### Test Failures
```bash
# Run specific failing test
just test tests/path/to/test.py::test_name -v
# Debug with print statements
# Fix and ensure test passes
```

### Linting Errors
```bash
# Auto-fix what's possible
just fmt
# Manually fix remaining issues
# Run lint to verify
just lint
```

Remember: **When in doubt, ask for help. The team is here to support clean, maintainable code.**