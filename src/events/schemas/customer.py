"""Customer event schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.events.base import BaseEvent
from src.events.registry import get_registry
from src.events.taxonomy import CustomerEvents


class CustomerRegisteredData(BaseModel):
    """Data payload for customer.registered event."""

    customer_id: UUID
    email: EmailStr
    customer_type: str = Field(pattern="^(individual|business)$")
    registration_source: str
    ip_address: str | None = None
    referral_code: str | None = None
    created_at: datetime


class CustomerUpdatedData(BaseModel):
    """Data payload for customer.updated event."""

    customer_id: UUID
    fields_updated: list[str]
    old_values: dict[str, str | bool | int]
    new_values: dict[str, str | bool | int]
    updated_by: str | None = None
    updated_at: datetime


class CustomerDeactivatedData(BaseModel):
    """Data payload for customer.deactivated event."""

    customer_id: UUID
    reason: str
    deactivated_by: str | None = None
    deactivated_at: datetime
    scheduled_deletion_date: datetime | None = None


class CustomerAddressData(BaseModel):
    """Address data for customer address events."""

    address_id: UUID
    address_type: str = Field(pattern="^(billing|shipping|both)$")
    is_default: bool
    street_address_1: str
    street_address_2: str | None = None
    city: str
    state_province: str
    postal_code: str
    country_code: str = Field(min_length=2, max_length=2)
    phone_number: str | None = None


class CustomerAddressAddedData(BaseModel):
    """Data payload for customer.address_added event."""

    customer_id: UUID
    address: CustomerAddressData
    added_at: datetime


class CustomerEmailVerifiedData(BaseModel):
    """Data payload for customer.email_verified event."""

    customer_id: UUID
    email: EmailStr
    verified_at: datetime
    verification_method: str = Field(pattern="^(email|sms|manual)$")


class CustomerPasswordChangedData(BaseModel):
    """Data payload for customer.password_changed event."""

    customer_id: UUID
    changed_by: str = Field(pattern="^(customer|admin|system)$")
    changed_at: datetime
    require_logout_all_devices: bool = True
    notification_sent: bool = True


# Type aliases for events
CustomerRegisteredEvent = BaseEvent[CustomerRegisteredData]
CustomerUpdatedEvent = BaseEvent[CustomerUpdatedData]
CustomerDeactivatedEvent = BaseEvent[CustomerDeactivatedData]
CustomerAddressAddedEvent = BaseEvent[CustomerAddressAddedData]
CustomerEmailVerifiedEvent = BaseEvent[CustomerEmailVerifiedData]
CustomerPasswordChangedEvent = BaseEvent[CustomerPasswordChangedData]


def register_customer_schemas() -> None:
    """Register all customer event schemas with the registry."""
    registry = get_registry()

    registry.register_schema(CustomerEvents.REGISTERED.value, CustomerRegisteredData)
    registry.register_schema(CustomerEvents.UPDATED.value, CustomerUpdatedData)
    registry.register_schema(CustomerEvents.DEACTIVATED.value, CustomerDeactivatedData)
    registry.register_schema(
        CustomerEvents.ADDRESS_ADDED.value, CustomerAddressAddedData
    )
    registry.register_schema(
        CustomerEvents.EMAIL_VERIFIED.value, CustomerEmailVerifiedData
    )
    registry.register_schema(
        CustomerEvents.CREDENTIALS_UPDATED.value, CustomerPasswordChangedData
    )
