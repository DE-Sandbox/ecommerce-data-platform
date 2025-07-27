"""Review-related SQLAlchemy models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint

from src.models.base import BaseModel

if TYPE_CHECKING:
    # Forward references for relationships - models defined in other files
    from src.models.customer import Customer
    from src.models.product import Product


class Review(BaseModel):
    """Product review model."""

    __tablename__ = "reviews"

    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.products.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.customers.id"),
        nullable=True,
    )
    order_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.orders.id"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified_purchase: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
    )
    helpful_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    unhelpful_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    moderation_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="reviews")
    customer: Mapped["Customer | None"] = relationship(back_populates="reviews")

    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_reviews_rating_range",
        ),
        CheckConstraint(
            "moderation_status IN ('pending', 'approved', 'rejected', 'flagged')",
            name="ck_reviews_moderation_status",
        ),
        {"schema": "ecommerce"},
    )
