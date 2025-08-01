"""Event taxonomy for e-commerce domain.

This module defines all domain events that can occur in the system.
Events follow a consistent naming pattern: {Entity}{Action}
"""

from enum import Enum
from typing import Final


class EventCategory(str, Enum):
    """High-level event categories."""

    ORDER = "order"
    CUSTOMER = "customer"
    PRODUCT = "product"
    PAYMENT = "payment"
    INVENTORY = "inventory"
    CART = "cart"
    REVIEW = "review"


class OrderEvents(str, Enum):
    """Order-related domain events."""

    CREATED = "order.created"
    UPDATED = "order.updated"
    CANCELLED = "order.cancelled"
    CONFIRMED = "order.confirmed"
    PROCESSING = "order.processing"
    SHIPPED = "order.shipped"
    DELIVERED = "order.delivered"
    REFUNDED = "order.refunded"
    ITEM_ADDED = "order.item_added"
    ITEM_REMOVED = "order.item_removed"
    ITEM_UPDATED = "order.item_updated"


class CustomerEvents(str, Enum):
    """Customer-related domain events."""

    REGISTERED = "customer.registered"
    UPDATED = "customer.updated"
    ACTIVATED = "customer.activated"
    DEACTIVATED = "customer.deactivated"
    SUSPENDED = "customer.suspended"
    DELETED = "customer.deleted"
    EMAIL_VERIFIED = "customer.email_verified"
    CREDENTIALS_UPDATED = "customer.credentials_updated"
    ADDRESS_ADDED = "customer.address_added"
    ADDRESS_UPDATED = "customer.address_updated"
    ADDRESS_REMOVED = "customer.address_removed"


class ProductEvents(str, Enum):
    """Product-related domain events."""

    CREATED = "product.created"
    UPDATED = "product.updated"
    ACTIVATED = "product.activated"
    DEACTIVATED = "product.deactivated"
    PRICE_CHANGED = "product.price_changed"
    STOCK_UPDATED = "product.stock_updated"
    CATEGORY_CHANGED = "product.category_changed"
    IMAGE_ADDED = "product.image_added"
    IMAGE_REMOVED = "product.image_removed"


class PaymentEvents(str, Enum):
    """Payment-related domain events."""

    INITIATED = "payment.initiated"
    PROCESSING = "payment.processing"
    COMPLETED = "payment.completed"
    FAILED = "payment.failed"
    CANCELLED = "payment.cancelled"
    REFUND_INITIATED = "payment.refund_initiated"
    REFUND_COMPLETED = "payment.refund_completed"
    REFUND_FAILED = "payment.refund_failed"
    METHOD_ADDED = "payment.method_added"
    METHOD_REMOVED = "payment.method_removed"
    METHOD_UPDATED = "payment.method_updated"


class InventoryEvents(str, Enum):
    """Inventory-related domain events."""

    STOCK_RECEIVED = "inventory.stock_received"
    STOCK_RESERVED = "inventory.stock_reserved"
    STOCK_RELEASED = "inventory.stock_released"
    STOCK_ADJUSTED = "inventory.stock_adjusted"
    LOW_STOCK_ALERT = "inventory.low_stock_alert"
    OUT_OF_STOCK = "inventory.out_of_stock"
    BACK_IN_STOCK = "inventory.back_in_stock"
    LOCATION_TRANSFER = "inventory.location_transfer"


class CartEvents(str, Enum):
    """Shopping cart-related domain events."""

    CREATED = "cart.created"
    ITEM_ADDED = "cart.item_added"
    ITEM_REMOVED = "cart.item_removed"
    ITEM_UPDATED = "cart.item_updated"
    CLEARED = "cart.cleared"
    ABANDONED = "cart.abandoned"
    CONVERTED = "cart.converted"
    MERGED = "cart.merged"


class ReviewEvents(str, Enum):
    """Review-related domain events."""

    SUBMITTED = "review.submitted"
    APPROVED = "review.approved"
    REJECTED = "review.rejected"
    UPDATED = "review.updated"
    DELETED = "review.deleted"
    FLAGGED = "review.flagged"


# Event metadata constants
EVENT_VERSION: Final[str] = "1.0"
EVENT_SOURCE: Final[str] = "ecommerce-platform"

# All events mapping for validation
ALL_EVENTS: Final[dict[EventCategory, type[Enum]]] = {
    EventCategory.ORDER: OrderEvents,
    EventCategory.CUSTOMER: CustomerEvents,
    EventCategory.PRODUCT: ProductEvents,
    EventCategory.PAYMENT: PaymentEvents,
    EventCategory.INVENTORY: InventoryEvents,
    EventCategory.CART: CartEvents,
    EventCategory.REVIEW: ReviewEvents,
}


def get_event_category(event_type: str) -> EventCategory | None:
    """Get the category for a given event type.

    Args:
        event_type: The event type string (e.g., "order.created")

    Returns:
        The event category or None if not found

    """
    prefix = event_type.split(".")[0]
    try:
        return EventCategory(prefix)
    except ValueError:
        return None


def validate_event_type(event_type: str) -> bool:
    """Validate if an event type is registered in the taxonomy.

    Args:
        event_type: The event type to validate

    Returns:
        True if valid, False otherwise

    """
    category = get_event_category(event_type)
    if not category:
        return False

    event_enum = ALL_EVENTS.get(category)
    if not event_enum:
        return False

    return any(event.value == event_type for event in event_enum)
