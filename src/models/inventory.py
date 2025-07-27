"""Inventory-related SQLAlchemy models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, UniqueConstraint

from src.models.base import BaseModel, VersionMixin

if TYPE_CHECKING:
    # Forward references for relationships - models defined in other files
    from src.models.product import Product, ProductVariant


class Location(BaseModel):
    """Warehouse/store location model."""

    __tablename__ = "locations"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="warehouse",
        server_default=text("'warehouse'"),
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )
    location_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    # Relationships
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="location")

    __table_args__ = (
        CheckConstraint(
            "type IN ('warehouse', 'store', 'dropship')",
            name="ck_locations_type",
        ),
        {"schema": "ecommerce"},
    )


class Inventory(BaseModel, VersionMixin):
    """Inventory tracking model."""

    __tablename__ = "inventory"

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
    location_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.locations.id"),
        nullable=False,
    )
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    quantity_available: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    reorder_point: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reorder_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_counted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="inventory")
    variant: Mapped["ProductVariant | None"] = relationship(back_populates="inventory")
    location: Mapped["Location"] = relationship(back_populates="inventory")

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "product_variant_id",
            "location_id",
            name="uq_inventory_product_variant_location",
        ),
        CheckConstraint(
            "quantity_on_hand >= 0",
            name="ck_inventory_quantity_on_hand_non_negative",
        ),
        CheckConstraint(
            "quantity_reserved >= 0",
            name="ck_inventory_quantity_reserved_non_negative",
        ),
        CheckConstraint(
            "quantity_available = quantity_on_hand - quantity_reserved",
            name="ck_inventory_quantity_available_calculation",
        ),
        {"schema": "ecommerce"},
    )
