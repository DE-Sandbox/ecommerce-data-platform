"""Tests for event schema registry."""

from uuid import uuid4

import pytest
from pydantic import BaseModel

from src.events.registry import (
    InMemoryEventRegistry,
    ensure_schemas_registered,
    get_registry,
)
from src.events.schemas.order import OrderCreatedData
from src.events.taxonomy import OrderEvents


class TestEventRegistry:
    """Test the event schema registry functionality."""

    def test_register_and_get_schema(self) -> None:
        """Test registering and retrieving schemas."""
        registry = InMemoryEventRegistry()

        # Register a schema
        registry.register_schema(OrderEvents.CREATED.value, OrderCreatedData, "1.0")

        # Retrieve the schema
        schema = registry.get_schema(OrderEvents.CREATED.value, "1.0")
        assert schema is OrderCreatedData

        # Get latest version
        latest_schema = registry.get_schema(OrderEvents.CREATED.value)
        assert latest_schema is OrderCreatedData

    def test_register_duplicate_schema_fails(self) -> None:
        """Test that registering duplicate schemas fails."""
        registry = InMemoryEventRegistry()

        # Register once
        registry.register_schema(OrderEvents.CREATED.value, OrderCreatedData, "1.0")

        # Try to register again
        with pytest.raises(ValueError, match="Schema already registered"):
            registry.register_schema(OrderEvents.CREATED.value, OrderCreatedData, "1.0")

    def test_invalid_event_type_fails(self) -> None:
        """Test that invalid event types are rejected."""
        registry = InMemoryEventRegistry()

        with pytest.raises(ValueError, match="Invalid event type"):
            registry.register_schema("invalid.event", OrderCreatedData)

    def test_validate_event(self) -> None:
        """Test event validation."""
        registry = InMemoryEventRegistry()
        registry.register_schema(OrderEvents.CREATED.value, OrderCreatedData, "1.0")

        # Create a valid event
        event_data = {
            "metadata": {
                "event_id": str(uuid4()),
                "event_type": OrderEvents.CREATED.value,
                "event_version": "1.0",
                "event_source": "test",
                "timestamp": "2025-01-01T12:00:00Z",
            },
            "data": {
                "order_id": str(uuid4()),
                "order_number": "ORD-001",
                "customer_id": str(uuid4()),
                "customer_email": "test@example.com",
                "currency_code": "USD",
                "subtotal_amount": "100.00",
                "tax_amount": "10.00",
                "shipping_amount": "5.00",
                "discount_amount": "0.00",
                "total_amount": "115.00",
                "shipping_address": {
                    "street_address_1": "123 Main St",
                    "city": "New York",
                    "state_province": "NY",
                    "postal_code": "10001",
                    "country_code": "US",
                },
                "billing_address": {
                    "street_address_1": "123 Main St",
                    "city": "New York",
                    "state_province": "NY",
                    "postal_code": "10001",
                    "country_code": "US",
                },
                "items": [
                    {
                        "item_id": str(uuid4()),
                        "product_id": str(uuid4()),
                        "product_sku": "PROD-001",
                        "product_name": "Test Product",
                        "quantity": 1,
                        "unit_price": "100.00",
                        "total_amount": "100.00",
                    }
                ],
                "payment_method_type": "credit_card",
                "created_at": "2025-01-01T12:00:00Z",
            },
        }

        # Validate the event
        validated_event = registry.validate_event(event_data)
        assert validated_event.metadata.event_type == OrderEvents.CREATED.value
        assert isinstance(validated_event.data, OrderCreatedData)

    def test_validate_event_missing_schema_fails(self) -> None:
        """Test that validation fails for unregistered schemas."""
        registry = InMemoryEventRegistry()

        event_data: dict[str, object] = {
            "metadata": {
                "event_id": str(uuid4()),
                "event_type": OrderEvents.CREATED.value,
                "event_version": "1.0",
            },
            "data": {},
        }

        with pytest.raises(ValueError, match="No schema found"):
            registry.validate_event(event_data)

    def test_schema_evolution_path(self) -> None:
        """Test getting schema evolution paths."""
        registry = InMemoryEventRegistry()

        # Register multiple versions
        class V1(BaseModel):
            field1: str

        class V2(BaseModel):
            field1: str
            field2: str | None = None

        class V3(BaseModel):
            field1: str
            field2: str | None = None
            field3: int = 0

        registry.register_schema(OrderEvents.UPDATED.value, V1, "1.0")
        registry.register_schema(OrderEvents.UPDATED.value, V2, "1.1")
        registry.register_schema(OrderEvents.UPDATED.value, V3, "1.2")

        # Get evolution path
        path = registry.get_schema_evolution_path(
            OrderEvents.UPDATED.value, "1.0", "1.2"
        )
        assert path == ["1.0", "1.1", "1.2"]

        # Reverse path should be empty
        reverse_path = registry.get_schema_evolution_path(
            OrderEvents.UPDATED.value, "1.2", "1.0"
        )
        assert reverse_path == []

    def test_list_operations(self) -> None:
        """Test listing event types and versions."""
        # Use the global registry with schemas registered once
        ensure_schemas_registered()
        registry = get_registry()

        # List event types
        event_types = registry.list_event_types()
        assert OrderEvents.CREATED.value in event_types
        assert OrderEvents.UPDATED.value in event_types

        # List versions
        versions = registry.list_versions(OrderEvents.CREATED.value)
        assert "1.0" in versions

    def test_mark_deprecated(self) -> None:
        """Test marking schemas as deprecated."""
        registry = InMemoryEventRegistry()
        registry.register_schema(OrderEvents.CREATED.value, OrderCreatedData, "1.0")

        # Mark as deprecated
        registry.mark_deprecated(
            OrderEvents.CREATED.value,
            "1.0",
            "Use version 2.0 instead",
        )

        # Verify it's marked (would need to expose this in the API)
        assert OrderEvents.CREATED.value in registry._schemas
        schema_version = registry._schemas[OrderEvents.CREATED.value]["1.0"]
        assert schema_version.deprecated is True
        assert schema_version.migration_notes == "Use version 2.0 instead"

    def test_version_comparison(self) -> None:
        """Test version comparison logic."""
        registry = InMemoryEventRegistry()

        # Test version comparison
        assert registry._compare_versions("1.0", "1.1") == -1
        assert registry._compare_versions("1.1", "1.0") == 1
        assert registry._compare_versions("1.0", "1.0") == 0
        assert registry._compare_versions("2.0", "1.9") == 1
        assert registry._compare_versions("1.10", "1.9") == 1
