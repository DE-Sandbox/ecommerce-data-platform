"""Customer-related SQLAlchemy models."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint

from src.models.base import (
    Base,
    BaseModel,
    SoftDeleteMixin,
    TimestampMixin,
    VersionMixin,
)

if TYPE_CHECKING:
    # Forward references for relationships - models defined in other files
    from src.models.order import Order
    from src.models.payment import PaymentMethod
    from src.models.review import Review
    from src.models.shopping import Cart


class Customer(BaseModel, VersionMixin):
    """Customer model."""

    __tablename__ = "customers"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("FALSE"))
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    customer_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="individual",
        server_default=text("'individual'"),
    )
    customer_metadata: Mapped[dict] = mapped_column(JSONB, default={}, server_default=text("'{}'::jsonb"))

    # Relationships
    pii: Mapped["CustomerPII"] = relationship(back_populates="customer", uselist=False, cascade="all, delete-orphan")
    addresses: Mapped[list["Address"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    consents: Mapped[list["CustomerConsent"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    payment_methods: Mapped[list["PaymentMethod"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="customer")
    carts: Mapped[list["Cart"]] = relationship(back_populates="customer")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'deleted')",
            name="ck_customers_status",
        ),
        CheckConstraint(
            "customer_type IN ('individual', 'business')",
            name="ck_customers_customer_type",
        ),
        {"schema": "ecommerce"},
    )


class CustomerPII(Base, TimestampMixin, SoftDeleteMixin):
    """Customer PII (Personally Identifiable Information) model."""

    __tablename__ = "customer_pii"
    __table_args__ = ({"schema": "ecommerce"},)

    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.customers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="pii")


class Address(BaseModel, VersionMixin):
    """Customer address model."""

    __tablename__ = "addresses"

    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="shipping",
        server_default=text("'shipping'"),
    )
    recipient_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    street_address_1: Mapped[str] = mapped_column(String(255), nullable=False)
    street_address_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state_province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("FALSE"))
    address_metadata: Mapped[dict] = mapped_column(JSONB, default={}, server_default=text("'{}'::jsonb"))

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="addresses")

    __table_args__ = (
        CheckConstraint(
            "type IN ('shipping', 'billing', 'both')",
            name="ck_addresses_type",
        ),
        {"schema": "ecommerce"},
    )


class CustomerConsent(BaseModel):
    """Customer consent tracking model for GDPR compliance."""

    __tablename__ = "customer_consents"

    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ecommerce.customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="consents")

    __table_args__ = (
        CheckConstraint(
            "consent_type IN ('marketing', 'analytics', 'third_party', 'cookies')",
            name="ck_customer_consents_consent_type",
        ),
        {"schema": "ecommerce"},
    )
