# Database Migrations Guide

This guide explains how database schema is managed in the e-commerce data platform using Alembic and SQLAlchemy.

## Architecture

### Schema Management Strategy

1. **PostgreSQL Dependencies** (Extensions, Functions, Schemas)
   - Managed by `docker/postgres/init_dependencies.sql`
   - Applied automatically when PostgreSQL container starts
   - Includes:
     - Extensions: uuid-ossp, pgcrypto, btree_gin
     - Custom UUID v7 functions
     - Database schemas: ecommerce, audit, archive

2. **Database Tables** (All table DDL)
   - Managed by Alembic migrations
   - SQLAlchemy models in `src/models/` are the source of truth
   - Alembic auto-generates migrations from model changes

### Key Files

- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment setup with async PostgreSQL support
- `src/models/` - SQLAlchemy models defining schema
- `docker/postgres/init_dependencies.sql` - Non-table dependencies

## Common Migration Commands

All migration commands are available through the justfile:

```bash
# Apply all pending migrations
just migrate

# Create a new migration
just migrate-new "add user preferences table"

# Check current migration status
just migrate-status

# Downgrade one migration
just migrate-down

# Go to specific migration
just migrate-to fb847ab39d59

# Show SQL without applying
just migrate-sql

# Verify models match database
just migrate-check
```

## Development Workflow

### 1. Making Schema Changes

```bash
# 1. Modify SQLAlchemy models in src/models/
# 2. Generate migration
just migrate-new "add email index to customers"

# 3. Review generated migration
# 4. Apply migration
just migrate

# 5. Test rollback
just migrate-down
just migrate
```

### 2. Fresh Database Setup

```bash
# Start with clean database
docker-compose down -v
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
sleep 5

# Apply all migrations
just migrate
```

### 3. Resetting Database

```bash
# Complete reset (removes all data)
just db-reset

# Then apply migrations
just migrate
```

## Model Patterns

### Base Classes

- `BaseModel` - Includes id, timestamps, soft delete
- `BaseModelNoSoftDelete` - For tables without soft delete
- `Base` - Direct SQLAlchemy base for custom patterns

### Mixins

- `TimestampMixin` - created_at, updated_at
- `SoftDeleteMixin` - deleted_at, is_deleted  
- `VersionMixin` - version column for optimistic locking

### Example Model

```python
from src.models.base import BaseModel, VersionMixin

class Product(BaseModel, VersionMixin):
    """Product with soft delete and version tracking."""
    
    __tablename__ = "products"
    
    sku: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    __table_args__ = ({"schema": "ecommerce"},)
```

## Best Practices

1. **Always review auto-generated migrations** - Alembic may not detect all changes perfectly
2. **Test migrations** - Always test upgrade and downgrade in development
3. **Keep migrations small** - One logical change per migration
4. **Use descriptive names** - Migration names should clearly indicate what changed
5. **Don't edit applied migrations** - Create new migrations to fix issues

## Troubleshooting

### Migration Conflicts

If you get "Target database is not up to date":

```bash
# Check current state
just migrate-status

# Force to specific revision if needed
docker exec postgres psql -U postgres -d ecommerce -c "UPDATE alembic_version SET version_num='a9eb2b4acc41';"
```

### Clean Slate

For a completely fresh start:

```bash
# Remove all Docker volumes
docker-compose down -v

# Start PostgreSQL
docker-compose up -d postgres

# Apply migrations
just migrate
```

### Connection Issues

If migrations fail with connection errors:

1. Ensure PostgreSQL is running: `docker-compose ps`
2. Check PostgreSQL logs: `just db-logs`
3. Verify connection: `just db-test`