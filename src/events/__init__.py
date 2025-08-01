"""Event schema registry for e-commerce domain events.

This package provides:
- Event taxonomy with all domain events
- Schema versioning and registry
- Type-safe event definitions using Pydantic
- Event validation and serialization
"""

from src.events.base import BaseEvent, EventMetadata
from src.events.registry import (
    InMemoryEventRegistry,
    ensure_schemas_registered,
    get_registry,
    set_registry,
)
from src.events.schemas import register_all_schemas
from src.events.taxonomy import (
    CartEvents,
    CustomerEvents,
    EventCategory,
    InventoryEvents,
    OrderEvents,
    PaymentEvents,
    ProductEvents,
    ReviewEvents,
    get_event_category,
    validate_event_type,
)

# Don't auto-register on import - let applications control this

__all__ = [
    # Base classes
    "BaseEvent",
    "CartEvents",
    "CustomerEvents",
    # Taxonomy
    "EventCategory",
    "EventMetadata",
    # Registry
    "InMemoryEventRegistry",
    "InventoryEvents",
    "OrderEvents",
    "PaymentEvents",
    "ProductEvents",
    "ReviewEvents",
    "ensure_schemas_registered",
    "get_event_category",
    "get_registry",
    "register_all_schemas",
    "set_registry",
    "validate_event_type",
]
