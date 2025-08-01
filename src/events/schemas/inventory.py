"""Inventory event schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.events.base import BaseEvent
from src.events.registry import get_registry
from src.events.taxonomy import InventoryEvents


class InventoryStockReceivedData(BaseModel):
    """Data payload for inventory.stock_received event."""

    inventory_id: UUID
    product_id: UUID
    product_sku: str
    location_id: UUID
    quantity_received: int = Field(gt=0)
    quantity_before: int = Field(ge=0)
    quantity_after: int = Field(gt=0)
    unit_cost: float = Field(gt=0)
    supplier_id: UUID | None = None
    purchase_order_number: str | None = None
    received_at: datetime


class InventoryStockReservedData(BaseModel):
    """Data payload for inventory.stock_reserved event."""

    reservation_id: UUID
    product_id: UUID
    product_sku: str
    location_id: UUID
    order_id: UUID
    quantity_reserved: int = Field(gt=0)
    quantity_available_before: int = Field(ge=0)
    quantity_available_after: int = Field(ge=0)
    reservation_expires_at: datetime
    reserved_at: datetime


class InventoryStockReleasedData(BaseModel):
    """Data payload for inventory.stock_released event."""

    reservation_id: UUID
    product_id: UUID
    product_sku: str
    location_id: UUID
    order_id: UUID | None = None
    quantity_released: int = Field(gt=0)
    release_reason: str = Field(
        pattern="^(order_cancelled|reservation_expired|manual_release|order_completed)$"
    )
    released_at: datetime


class InventoryStockAdjustedData(BaseModel):
    """Data payload for inventory.stock_adjusted event."""

    adjustment_id: UUID
    product_id: UUID
    product_sku: str
    location_id: UUID
    quantity_before: int = Field(ge=0)
    quantity_after: int = Field(ge=0)
    adjustment_quantity: int  # Can be negative
    adjustment_reason: str = Field(
        pattern="^(damaged|lost|found|correction|return|theft)$"
    )
    adjusted_by: str
    adjusted_at: datetime
    notes: str | None = None


class InventoryLowStockAlertData(BaseModel):
    """Data payload for inventory.low_stock_alert event."""

    product_id: UUID
    product_sku: str
    location_id: UUID
    current_quantity: int = Field(ge=0)
    reorder_point: int = Field(gt=0)
    reorder_quantity: int = Field(gt=0)
    last_restock_date: datetime | None = None
    average_daily_usage: float = Field(ge=0)
    days_until_stockout: int | None = Field(ge=0)
    alert_generated_at: datetime


class InventoryOutOfStockData(BaseModel):
    """Data payload for inventory.out_of_stock event."""

    product_id: UUID
    product_sku: str
    location_id: UUID
    last_available_at: datetime
    pending_orders_affected: int = Field(ge=0)
    estimated_restock_date: datetime | None = None
    stockout_occurred_at: datetime


# Type aliases for events
InventoryStockReceivedEvent = BaseEvent[InventoryStockReceivedData]
InventoryStockReservedEvent = BaseEvent[InventoryStockReservedData]
InventoryStockReleasedEvent = BaseEvent[InventoryStockReleasedData]
InventoryStockAdjustedEvent = BaseEvent[InventoryStockAdjustedData]
InventoryLowStockAlertEvent = BaseEvent[InventoryLowStockAlertData]
InventoryOutOfStockEvent = BaseEvent[InventoryOutOfStockData]


def register_inventory_schemas() -> None:
    """Register all inventory event schemas with the registry."""
    registry = get_registry()

    registry.register_schema(
        InventoryEvents.STOCK_RECEIVED.value, InventoryStockReceivedData
    )
    registry.register_schema(
        InventoryEvents.STOCK_RESERVED.value, InventoryStockReservedData
    )
    registry.register_schema(
        InventoryEvents.STOCK_RELEASED.value, InventoryStockReleasedData
    )
    registry.register_schema(
        InventoryEvents.STOCK_ADJUSTED.value, InventoryStockAdjustedData
    )
    registry.register_schema(
        InventoryEvents.LOW_STOCK_ALERT.value, InventoryLowStockAlertData
    )
    registry.register_schema(
        InventoryEvents.OUT_OF_STOCK.value, InventoryOutOfStockData
    )
