"""Payment event schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.events.base import BaseEvent
from src.events.registry import get_registry
from src.events.taxonomy import PaymentEvents


class PaymentInitiatedData(BaseModel):
    """Data payload for payment.initiated event."""

    payment_id: UUID
    order_id: UUID
    payment_method_id: UUID
    amount: Decimal = Field(decimal_places=2, gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    payment_type: str = Field(
        pattern="^(credit_card|debit_card|paypal|bank_transfer|crypto|other)$"
    )
    initiated_at: datetime


class PaymentCompletedData(BaseModel):
    """Data payload for payment.completed event."""

    payment_id: UUID
    order_id: UUID
    transaction_id: str
    amount: Decimal = Field(decimal_places=2, gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    payment_method_type: str
    processing_fee: Decimal = Field(decimal_places=2, ge=0)
    net_amount: Decimal = Field(decimal_places=2)
    completed_at: datetime


class PaymentFailedData(BaseModel):
    """Data payload for payment.failed event."""

    payment_id: UUID
    order_id: UUID
    failure_reason: str
    failure_code: str | None = None
    payment_method_type: str
    amount: Decimal = Field(decimal_places=2, gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    retry_allowed: bool
    failed_at: datetime


class RefundInitiatedData(BaseModel):
    """Data payload for payment.refund_initiated event."""

    refund_id: UUID
    payment_id: UUID
    order_id: UUID
    refund_amount: Decimal = Field(decimal_places=2, gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    refund_reason: str
    initiated_by: str
    initiated_at: datetime


class RefundCompletedData(BaseModel):
    """Data payload for payment.refund_completed event."""

    refund_id: UUID
    payment_id: UUID
    order_id: UUID
    refund_amount: Decimal = Field(decimal_places=2, gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    transaction_id: str
    processing_fee: Decimal = Field(decimal_places=2, ge=0)
    completed_at: datetime


class PaymentMethodAddedData(BaseModel):
    """Data payload for payment.method_added event."""

    payment_method_id: UUID
    customer_id: UUID
    method_type: str = Field(
        pattern="^(credit_card|debit_card|paypal|bank_transfer|crypto|other)$"
    )
    is_default: bool
    last_four: str | None = Field(None, min_length=4, max_length=4)
    expiry_month: int | None = Field(None, ge=1, le=12)
    expiry_year: int | None = Field(None, ge=2024, le=2100)
    added_at: datetime


# Type aliases for events
PaymentInitiatedEvent = BaseEvent[PaymentInitiatedData]
PaymentCompletedEvent = BaseEvent[PaymentCompletedData]
PaymentFailedEvent = BaseEvent[PaymentFailedData]
RefundInitiatedEvent = BaseEvent[RefundInitiatedData]
RefundCompletedEvent = BaseEvent[RefundCompletedData]
PaymentMethodAddedEvent = BaseEvent[PaymentMethodAddedData]


def register_payment_schemas() -> None:
    """Register all payment event schemas with the registry."""
    registry = get_registry()

    registry.register_schema(PaymentEvents.INITIATED.value, PaymentInitiatedData)
    registry.register_schema(PaymentEvents.COMPLETED.value, PaymentCompletedData)
    registry.register_schema(PaymentEvents.FAILED.value, PaymentFailedData)
    registry.register_schema(PaymentEvents.REFUND_INITIATED.value, RefundInitiatedData)
    registry.register_schema(PaymentEvents.REFUND_COMPLETED.value, RefundCompletedData)
    registry.register_schema(PaymentEvents.METHOD_ADDED.value, PaymentMethodAddedData)
