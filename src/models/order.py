"""Order-related SQLAlchemy models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, Index

from src.models.base import Base, BaseModelNoSoftDelete, VersionMixin

if TYPE_CHECKING:
    # Forward references for relationships - models defined in other files
    from src.models.customer import Customer
    from src.models.payment import Payment
    from src.models.product import Product


class Order(BaseModelNoSoftDelete, VersionMixin):
    """Order model.

    Note: This model has created_at and updated_at but NO deleted_at/is_deleted per schema design.
    """

    __tablename__ = "orders"

    # Note: Order inherits from BaseModel but doesn't use soft delete fields
    # The schema defines orders without deleted_at/is_deleted columns

    customer_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.customers.id"),
        nullable=True,
    )
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    subtotal_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    tax_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    shipping_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    discount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    total_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default=text("'USD'"),
    )
    shipping_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    billing_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )
    placed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    customer: Mapped["Customer | None"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')",
            name="ck_orders_status",
        ),
        CheckConstraint(
            "subtotal_cents >= 0",
            name="ck_orders_subtotal_non_negative",
        ),
        CheckConstraint(
            "tax_cents >= 0",
            name="ck_orders_tax_non_negative",
        ),
        CheckConstraint(
            "shipping_cents >= 0",
            name="ck_orders_shipping_non_negative",
        ),
        CheckConstraint(
            "discount_cents >= 0",
            name="ck_orders_discount_non_negative",
        ),
        CheckConstraint(
            "total_cents = subtotal_cents + tax_cents + shipping_cents - discount_cents",
            name="ck_orders_total_calculation",
        ),
        Index("idx_orders_created_at", "created_at"),
        Index("idx_orders_customer_id", "customer_id"),
        Index("idx_orders_status", "status"),
        {"schema": "ecommerce"},
    )


class OrderItem(Base):
    """Order item model.

    Note: This model only has created_at, no other timestamp/soft delete fields per schema design.
    """

    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("UUID_GENERATE_V7()"),
        nullable=False,
    )
    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.products.id"),
        nullable=False,
    )
    product_variant_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.product_variants.id"),
        nullable=True,
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    tax_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    item_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
        CheckConstraint(
            "unit_price_cents >= 0",
            name="ck_order_items_unit_price_non_negative",
        ),
        CheckConstraint(
            "discount_cents >= 0",
            name="ck_order_items_discount_non_negative",
        ),
        CheckConstraint(
            "tax_cents >= 0",
            name="ck_order_items_tax_non_negative",
        ),
        CheckConstraint(
            "line_total_cents = (quantity * unit_price_cents) - discount_cents + tax_cents",
            name="ck_order_items_line_total_calculation",
        ),
        {"schema": "ecommerce"},
    )
