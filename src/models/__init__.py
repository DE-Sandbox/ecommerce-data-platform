"""SQLAlchemy models for the e-commerce platform."""

from src.models.audit import AuditLog
from src.models.base import Base
from src.models.customer import Address, Customer, CustomerConsent, CustomerPII
from src.models.inventory import Inventory, Location
from src.models.order import Order, OrderItem
from src.models.payment import Payment, PaymentMethod
from src.models.product import Category, Product, ProductPrice, ProductVariant
from src.models.review import Review
from src.models.shopping import Cart, CartItem

__all__ = [
    "Address",
    "AuditLog",
    "Base",
    # Shopping models
    "Cart",
    "CartItem",
    # Product models
    "Category",
    # Customer models
    "Customer",
    "CustomerConsent",
    "CustomerPII",
    "Inventory",
    # Inventory models
    "Location",
    # Order models
    "Order",
    "OrderItem",
    "Payment",
    # Payment models
    "PaymentMethod",
    "Product",
    "ProductPrice",
    "ProductVariant",
    # Review models
    "Review",
]
