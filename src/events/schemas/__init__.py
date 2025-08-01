"""Event schemas package.

This module provides all event schemas and registration functions.
"""

from src.events.schemas.customer import (
    CustomerAddressAddedEvent,
    CustomerDeactivatedEvent,
    CustomerEmailVerifiedEvent,
    CustomerPasswordChangedEvent,
    CustomerRegisteredEvent,
    CustomerUpdatedEvent,
    register_customer_schemas,
)
from src.events.schemas.inventory import (
    InventoryLowStockAlertEvent,
    InventoryOutOfStockEvent,
    InventoryStockAdjustedEvent,
    InventoryStockReceivedEvent,
    InventoryStockReleasedEvent,
    InventoryStockReservedEvent,
    register_inventory_schemas,
)
from src.events.schemas.order import (
    OrderCancelledEvent,
    OrderCreatedEvent,
    OrderDeliveredEvent,
    OrderShippedEvent,
    OrderUpdatedEvent,
    register_order_schemas,
)
from src.events.schemas.payment import (
    PaymentCompletedEvent,
    PaymentFailedEvent,
    PaymentInitiatedEvent,
    PaymentMethodAddedEvent,
    RefundCompletedEvent,
    RefundInitiatedEvent,
    register_payment_schemas,
)


def register_all_schemas() -> None:
    """Register all event schemas with the global registry."""
    register_order_schemas()
    register_customer_schemas()
    register_payment_schemas()
    register_inventory_schemas()


__all__ = [
    "CustomerAddressAddedEvent",
    "CustomerDeactivatedEvent",
    "CustomerEmailVerifiedEvent",
    "CustomerPasswordChangedEvent",
    # Customer events
    "CustomerRegisteredEvent",
    "CustomerUpdatedEvent",
    "InventoryLowStockAlertEvent",
    "InventoryOutOfStockEvent",
    "InventoryStockAdjustedEvent",
    # Inventory events
    "InventoryStockReceivedEvent",
    "InventoryStockReleasedEvent",
    "InventoryStockReservedEvent",
    "OrderCancelledEvent",
    # Order events
    "OrderCreatedEvent",
    "OrderDeliveredEvent",
    "OrderShippedEvent",
    "OrderUpdatedEvent",
    "PaymentCompletedEvent",
    "PaymentFailedEvent",
    # Payment events
    "PaymentInitiatedEvent",
    "PaymentMethodAddedEvent",
    "RefundCompletedEvent",
    "RefundInitiatedEvent",
    # Registration functions
    "register_all_schemas",
    "register_customer_schemas",
    "register_inventory_schemas",
    "register_order_schemas",
    "register_payment_schemas",
]
