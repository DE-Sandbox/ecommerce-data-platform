# Event Schema Evolution Guide

This document describes how to evolve event schemas while maintaining backward compatibility.

## Versioning Strategy

We use semantic versioning for event schemas: `MAJOR.MINOR`

- **MAJOR**: Breaking changes that require consumer updates
- **MINOR**: Backward compatible additions

## Backward Compatible Changes

These changes can be made with a MINOR version bump:

### ✅ Adding Optional Fields

```python
# Version 1.0
class OrderCreatedData(BaseModel):
    order_id: UUID
    customer_id: UUID
    total_amount: Decimal

# Version 1.1 - Added optional field
class OrderCreatedData(BaseModel):
    order_id: UUID
    customer_id: UUID
    total_amount: Decimal
    discount_code: str | None = None  # New optional field
```

### ✅ Adding New Event Types

```python
# Version 1.0
class OrderEvents(str, Enum):
    CREATED = "order.created"
    CANCELLED = "order.cancelled"

# Version 1.1 - Added new event
class OrderEvents(str, Enum):
    CREATED = "order.created"
    CANCELLED = "order.cancelled"
    RETURNED = "order.returned"  # New event type
```

### ✅ Expanding Enums (if handled gracefully)

```python
# Version 1.0
payment_type: Literal["credit_card", "debit_card"]

# Version 1.1 - Added new option
payment_type: Literal["credit_card", "debit_card", "paypal"]
```

## Breaking Changes

These changes require a MAJOR version bump:

### ❌ Removing Fields

```python
# Version 1.0
class OrderCreatedData(BaseModel):
    order_id: UUID
    customer_email: str  # To be removed
    
# Version 2.0 - Field removed
class OrderCreatedData(BaseModel):
    order_id: UUID
    # customer_email removed
```

### ❌ Changing Field Types

```python
# Version 1.0
class PaymentData(BaseModel):
    amount: float  # Using float
    
# Version 2.0 - Type changed
class PaymentData(BaseModel):
    amount: Decimal  # Changed to Decimal
```

### ❌ Renaming Fields

```python
# Version 1.0
class CustomerData(BaseModel):
    user_id: UUID
    
# Version 2.0 - Field renamed
class CustomerData(BaseModel):
    customer_id: UUID  # Renamed from user_id
```

## Migration Patterns

### 1. Dual Write Pattern

When migrating to a new version, emit both versions temporarily:

```python
async def emit_order_created_event(order: Order) -> None:
    # Emit v1.0 for existing consumers
    await publish_event(
        event_type="order.created",
        version="1.0",
        data=order_to_v1_data(order)
    )
    
    # Also emit v2.0 for new consumers
    await publish_event(
        event_type="order.created",
        version="2.0",
        data=order_to_v2_data(order)
    )
```

### 2. Consumer Version Detection

Consumers should handle multiple versions:

```python
def handle_order_event(event: dict[str, object]) -> None:
    version = event["metadata"]["event_version"]
    
    if version == "1.0":
        handle_v1_order(event)
    elif version == "2.0":
        handle_v2_order(event)
    else:
        logger.warning(f"Unknown version: {version}")
```

### 3. Schema Registry Usage

```python
from src.events import get_registry

# Register multiple versions
registry = get_registry()
registry.register_schema("order.created", OrderCreatedDataV1, "1.0")
registry.register_schema("order.created", OrderCreatedDataV2, "2.0")

# Mark old version as deprecated
registry.mark_deprecated(
    "order.created", 
    "1.0",
    migration_notes="Use v2.0 - adds currency_code field"
)
```

## Best Practices

### 1. Plan for Evolution

Always design schemas with evolution in mind:

```python
class OrderData(BaseModel):
    # Required fields - keep minimal
    order_id: UUID
    customer_id: UUID
    
    # Optional fields - easier to evolve
    metadata: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
```

### 2. Use Explicit Versions

Always include version in event metadata:

```python
event = {
    "metadata": {
        "event_version": "1.0",  # Always explicit
        # ...
    }
}
```

### 3. Document Changes

Maintain a changelog for each event type:

```markdown
## order.created

### v2.0 (2025-02-01)
- BREAKING: Removed customer_email (use customer_id to lookup)
- Added currency_code field (required)

### v1.1 (2025-01-15)
- Added discount_code field (optional)
- Added shipping_method field (optional)

### v1.0 (2025-01-01)
- Initial version
```

### 4. Deprecation Timeline

Follow a clear deprecation process:

1. **Announce** deprecation with migration guide
2. **Dual emit** both versions (minimum 30 days)
3. **Monitor** consumer adoption of new version
4. **Remove** old version only after all consumers migrated

### 5. Testing Schema Evolution

```python
def test_schema_backward_compatibility():
    """Test that v1.0 events can be parsed by v1.1 schema."""
    v1_event = {
        "order_id": str(uuid4()),
        "customer_id": str(uuid4()),
        "total_amount": "99.99"
    }
    
    # v1.1 schema should handle v1.0 data
    v1_1_schema = OrderCreatedDataV1_1(**v1_event)
    assert v1_1_schema.discount_code is None  # Default value
```

## Common Pitfalls

1. **Don't reuse version numbers** - Once 1.0 is released, never change it
2. **Don't skip versions** - If you have 1.0 and need breaking changes, use 2.0, not 3.0
3. **Don't change semantics** - If a field means something different, use a new field name
4. **Don't rely on field order** - JSON doesn't guarantee field order