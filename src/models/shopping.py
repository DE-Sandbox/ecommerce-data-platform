"""Shopping cart-related SQLAlchemy models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint

from src.models.base import Base, BaseModel, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    # Forward references for relationships - models defined in other files
    from src.models.customer import Customer
    from src.models.product import Product


class Cart(BaseModel):
    """Shopping cart model."""

    __tablename__ = "carts"

    customer_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.customers.id"),
        nullable=True,
    )
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cart_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    # Relationships
    customer: Mapped["Customer | None"] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'abandoned', 'converted', 'merged')",
            name="ck_carts_status",
        ),
        CheckConstraint(
            "(customer_id IS NOT NULL) OR (session_id IS NOT NULL)",
            name="ck_carts_customer_or_session",
        ),
        {"schema": "ecommerce"},
    )


class CartItem(Base, TimestampMixin, SoftDeleteMixin):
    """Cart item model.

    Note: This model has both created_at (added_at) and updated_at per schema design.
    """

    __tablename__ = "cart_items"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("UUID_GENERATE_V7()"),
        nullable=False,
    )
    cart_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.carts.id", ondelete="CASCADE"),
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
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    cart_item_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    # Custom timestamp names per schema
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Note: Schema uses 'added_at' instead of 'created_at' for cart_items
    # The TimestampMixin's created_at is not used in this table

    # Relationships
    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_cart_items_quantity_positive",
        ),
        CheckConstraint(
            "price_cents >= 0",
            name="ck_cart_items_price_non_negative",
        ),
        {"schema": "ecommerce"},
    )
