# Event Catalog

This document describes all domain events in the e-commerce platform.

## Event Structure

All events follow a standard structure:

```json
{
  "metadata": {
    "event_id": "uuid",
    "event_type": "order.created",
    "event_version": "1.0",
    "event_source": "ecommerce-platform",
    "timestamp": "2025-01-01T12:00:00Z",
    "correlation_id": "uuid",
    "causation_id": "uuid",
    "actor_id": "user:12345"
  },
  "data": {
    // Event-specific data
  }
}
```

## Event Categories

### Order Events

| Event Type | Description | Key Data |
|------------|-------------|----------|
| `order.created` | New order placed | order_id, customer_id, items, total_amount |
| `order.updated` | Order details modified | order_id, fields_updated, old/new values |
| `order.cancelled` | Order cancelled | order_id, cancellation_reason, refund_amount |
| `order.confirmed` | Payment confirmed | order_id, confirmation_time |
| `order.processing` | Order being processed | order_id, estimated_completion |
| `order.shipped` | Order shipped | order_id, tracking_number, carrier |
| `order.delivered` | Order delivered | order_id, delivered_at, signed_by |
| `order.refunded` | Order refunded | order_id, refund_amount, reason |

### Customer Events

| Event Type | Description | Key Data |
|------------|-------------|----------|
| `customer.registered` | New customer signup | customer_id, email, registration_source |
| `customer.updated` | Profile updated | customer_id, fields_updated |
| `customer.activated` | Account activated | customer_id, activation_method |
| `customer.deactivated` | Account deactivated | customer_id, reason |
| `customer.suspended` | Account suspended | customer_id, reason, duration |
| `customer.email_verified` | Email verified | customer_id, email, method |
| `customer.password_changed` | Password changed | customer_id, changed_by |
| `customer.address_added` | New address added | customer_id, address_id, type |

### Payment Events

| Event Type | Description | Key Data |
|------------|-------------|----------|
| `payment.initiated` | Payment started | payment_id, order_id, amount |
| `payment.processing` | Payment being processed | payment_id, processor |
| `payment.completed` | Payment successful | payment_id, transaction_id |
| `payment.failed` | Payment failed | payment_id, failure_reason |
| `payment.refund_initiated` | Refund started | refund_id, payment_id, amount |
| `payment.refund_completed` | Refund successful | refund_id, transaction_id |
| `payment.method_added` | Payment method added | method_id, customer_id, type |

### Inventory Events

| Event Type | Description | Key Data |
|------------|-------------|----------|
| `inventory.stock_received` | New stock received | product_id, quantity_received, location_id |
| `inventory.stock_reserved` | Stock reserved for order | product_id, quantity_reserved, order_id |
| `inventory.stock_released` | Reserved stock released | reservation_id, quantity_released, reason |
| `inventory.stock_adjusted` | Manual adjustment | product_id, adjustment_quantity, reason |
| `inventory.low_stock_alert` | Low stock warning | product_id, current_quantity, reorder_point |
| `inventory.out_of_stock` | Product out of stock | product_id, location_id |

## Event Versioning

Events use semantic versioning (MAJOR.MINOR):
- **MAJOR**: Breaking changes (field removal, type changes)
- **MINOR**: Backward compatible changes (new optional fields)

Current version: **1.0**

### Version Compatibility Rules

1. Events must be backward compatible within the same major version
2. New fields must be optional with sensible defaults
3. Field types cannot change without a major version bump
4. Field removal requires a major version bump

### Migration Strategy

When introducing breaking changes:
1. Deploy new version alongside old version
2. Update producers to emit both versions
3. Migrate consumers to handle new version
4. Phase out old version after all consumers updated

## Event Flow Examples

### Order Lifecycle

```
1. cart.created
2. cart.item_added (multiple)
3. order.created
4. payment.initiated
5. inventory.stock_reserved
6. payment.completed
7. order.confirmed
8. order.processing
9. order.shipped
10. order.delivered
```

### Failed Payment Flow

```
1. order.created
2. payment.initiated
3. payment.failed
4. inventory.stock_released
5. order.cancelled
```

## Implementation

All event schemas are implemented in:
- `src/events/taxonomy.py` - Event type definitions
- `src/events/schemas/` - Pydantic models for each event type
- `src/events/registry.py` - Schema registry for validation

## Usage Example

```python
from src.events import get_registry, OrderEvents
from src.events.schemas.order import OrderCreatedData
from uuid import uuid4

# Get the registry
registry = get_registry()

# Create an event
event_data = {
    "metadata": {
        "event_id": str(uuid4()),
        "event_type": OrderEvents.CREATED.value,
        "event_version": "1.0",
        "event_source": "ecommerce-platform",
        "timestamp": "2025-01-01T12:00:00Z"
    },
    "data": {
        "order_id": str(uuid4()),
        "order_number": "ORD-2025-0001",
        # ... other fields
    }
}

# Validate the event
validated_event = registry.validate_event(event_data)
```