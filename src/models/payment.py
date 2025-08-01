"""Payment-related SQLAlchemy models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint

from src.models.base import Base, BaseModel, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    # Forward references for relationships - models defined in other files
    from src.models.customer import Customer
    from src.models.order import Order


class PaymentMethod(BaseModel):
    """Customer payment method model."""

    __tablename__ = "payment_methods"

    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)
    expiry_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expiry_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
    )
    payment_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="payment_methods")
    payments: Mapped[list["Payment"]] = relationship(back_populates="payment_method")

    __table_args__ = (
        CheckConstraint(
            "type IN ('credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay')",
            name="ck_payment_methods_type",
        ),
        {"schema": "ecommerce"},
    )


class Payment(Base, TimestampMixin, SoftDeleteMixin):
    """Payment transaction model.

    Note: This model has created_at but NO updated_at per schema design.
    """

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuid_generate_v7()"),
        nullable=False,
    )
    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.orders.id"),
        nullable=False,
    )
    payment_method_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.payment_methods.id"),
        nullable=True,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default=text("'USD'"),
    )
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    # Override to exclude updated_at
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="payments")
    payment_method: Mapped["PaymentMethod | None"] = relationship(
        back_populates="payments"
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('payment', 'refund', 'partial_refund')",
            name="ck_payments_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name="ck_payments_status",
        ),
        CheckConstraint(
            "amount_cents > 0",
            name="ck_payments_amount_positive",
        ),
        {"schema": "ecommerce"},
    )
