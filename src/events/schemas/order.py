"""Order event schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.events.base import BaseEvent
from src.events.registry import get_registry
from src.events.taxonomy import OrderEvents


class OrderAddress(BaseModel):
    """Address information for order events."""

    street_address_1: str
    street_address_2: str | None = None
    city: str
    state_province: str
    postal_code: str
    country_code: str


class OrderItemData(BaseModel):
    """Order item information."""

    item_id: UUID
    product_id: UUID
    product_sku: str
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(decimal_places=2)
    discount_amount: Decimal = Field(decimal_places=2, default=Decimal("0.00"))
    tax_amount: Decimal = Field(decimal_places=2, default=Decimal("0.00"))
    total_amount: Decimal = Field(decimal_places=2)


class OrderCreatedData(BaseModel):
    """Data payload for order.created event."""

    order_id: UUID
    order_number: str
    customer_id: UUID
    customer_email: str
    currency_code: str = Field(min_length=3, max_length=3)
    subtotal_amount: Decimal = Field(decimal_places=2)
    tax_amount: Decimal = Field(decimal_places=2)
    shipping_amount: Decimal = Field(decimal_places=2)
    discount_amount: Decimal = Field(decimal_places=2)
    total_amount: Decimal = Field(decimal_places=2)
    shipping_address: OrderAddress
    billing_address: OrderAddress
    items: list[OrderItemData] = Field(min_length=1)
    payment_method_type: str
    created_at: datetime


class OrderUpdatedData(BaseModel):
    """Data payload for order.updated event."""

    order_id: UUID
    order_number: str
    fields_updated: list[str]
    old_values: dict[str, str | int | float]
    new_values: dict[str, str | int | float]
    updated_by: str | None = None
    updated_at: datetime


class OrderCancelledData(BaseModel):
    """Data payload for order.cancelled event."""

    order_id: UUID
    order_number: str
    cancellation_reason: str
    cancelled_by: str | None = None
    cancelled_at: datetime
    refund_amount: Decimal = Field(decimal_places=2)
    refund_initiated: bool = False


class OrderShippedData(BaseModel):
    """Data payload for order.shipped event."""

    order_id: UUID
    order_number: str
    tracking_number: str
    carrier: str
    shipped_at: datetime
    estimated_delivery_date: datetime | None = None
    shipping_cost: Decimal = Field(decimal_places=2)


class OrderDeliveredData(BaseModel):
    """Data payload for order.delivered event."""

    order_id: UUID
    order_number: str
    delivered_at: datetime
    delivery_confirmation: str | None = None
    signed_by: str | None = None


# Type aliases for events
OrderCreatedEvent = BaseEvent[OrderCreatedData]
OrderUpdatedEvent = BaseEvent[OrderUpdatedData]
OrderCancelledEvent = BaseEvent[OrderCancelledData]
OrderShippedEvent = BaseEvent[OrderShippedData]
OrderDeliveredEvent = BaseEvent[OrderDeliveredData]


def register_order_schemas() -> None:
    """Register all order event schemas with the registry."""
    registry = get_registry()

    registry.register_schema(OrderEvents.CREATED.value, OrderCreatedData)
    registry.register_schema(OrderEvents.UPDATED.value, OrderUpdatedData)
    registry.register_schema(OrderEvents.CANCELLED.value, OrderCancelledData)
    registry.register_schema(OrderEvents.SHIPPED.value, OrderShippedData)
    registry.register_schema(OrderEvents.DELIVERED.value, OrderDeliveredData)
