"""Product-related SQLAlchemy models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, UniqueConstraint

from src.models.base import (
    Base,
    BaseModel,
    SoftDeleteMixin,
    TimestampMixin,
    VersionMixin,
)

if TYPE_CHECKING:
    # Forward references for relationships - models defined in other files
    from src.models.inventory import Inventory
    from src.models.order import OrderItem
    from src.models.review import Review
    from src.models.shopping import CartItem


class Category(BaseModel):
    """Product category model."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.categories.id"),
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )
    category_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    # Self-referential relationship
    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id",
        backref="children",
    )

    # Relationships
    products: Mapped[list["Product"]] = relationship(back_populates="category")

    __table_args__ = ({"schema": "ecommerce"},)


class Product(BaseModel, VersionMixin):
    """Product model."""

    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.categories.id"),
        nullable=True,
    )
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    dimensions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    product_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    # Relationships
    category: Mapped["Category | None"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    prices: Mapped[list["ProductPrice"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="product")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="product")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'discontinued', 'draft')",
            name="ck_products_status",
        ),
        {"schema": "ecommerce"},
    )


class ProductVariant(BaseModel):
    """Product variant model for size, color, etc."""

    __tablename__ = "product_variants"

    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.products.id", ondelete="CASCADE"),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    attributes: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default={},
        server_default=text("'{}'::jsonb"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="variants")
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="variant")

    __table_args__ = ({"schema": "ecommerce"},)


class ProductPrice(Base, TimestampMixin, SoftDeleteMixin):
    """Product pricing model with history tracking.

    Note: This model has created_at but NO updated_at per schema design.
    """

    __tablename__ = "product_prices"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuid_generate_v7()"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.products.id", ondelete="CASCADE"),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default=text("'USD'"),
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    compare_at_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )

    # Override to exclude updated_at
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="prices")

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "currency_code",
            "valid_from",
            name="uq_product_prices_product_currency_valid_from",
        ),
        CheckConstraint(
            "price > 0",
            name="ck_product_prices_price_positive",
        ),
        CheckConstraint(
            "compare_at_price > price OR compare_at_price IS NULL",
            name="ck_product_prices_compare_at_price",
        ),
        {"schema": "ecommerce"},
    )
