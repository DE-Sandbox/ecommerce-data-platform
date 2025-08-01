"""Test Customer and Address models."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Address, Customer, CustomerPII


class TestCustomerModel:
    """Test Customer model functionality."""

    @pytest.mark.asyncio
    async def test_create_customer(self, async_session: AsyncSession) -> None:
        """Test creating a customer."""
        # Create customer
        customer = Customer(
            email=f"john.doe_{uuid.uuid4().hex[:8]}@example.com",
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        # Create PII data
        pii = CustomerPII(
            customer_id=customer.id,
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            date_of_birth=datetime(1990, 1, 1).date(),
        )
        async_session.add(pii)
        await async_session.commit()

        # Verify customer was created
        assert customer.id is not None
        assert customer.created_at is not None
        assert customer.status == "active"
        assert customer.email_verified is False
        assert pii.first_name == "John"
        assert pii.last_name == "Doe"

    @pytest.mark.asyncio
    async def test_customer_unique_email(self, async_session: AsyncSession) -> None:
        """Test that email must be unique."""
        # Create first customer
        unique_email = f"unique_{uuid.uuid4().hex[:8]}@example.com"
        customer1 = Customer(
            email=unique_email,
            status="active",
            customer_type="individual",
        )
        async_session.add(customer1)
        await async_session.commit()

        # Try to create second customer with same email
        customer2 = Customer(
            email=unique_email,
            status="active",
            customer_type="individual",
        )
        async_session.add(customer2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

        await async_session.rollback()

        # Clean up
        await async_session.delete(customer1)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_customer_soft_delete(self, async_session: AsyncSession) -> None:
        """Test soft delete functionality."""
        customer = Customer(
            email=f"delete_{uuid.uuid4().hex[:8]}@example.com",
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        # Soft delete
        customer.deleted_at = datetime.now(UTC)
        await async_session.commit()

        # Query should still find the customer
        result = await async_session.execute(
            select(Customer).where(Customer.id == customer.id)
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.deleted_at is not None

    @pytest.mark.asyncio
    async def test_customer_types(self, async_session: AsyncSession) -> None:
        """Test different customer types."""
        types = ["individual", "business"]
        customers = []

        for customer_type in types:
            customer = Customer(
                email=f"{customer_type}_{uuid.uuid4().hex[:8]}@example.com",
                status="active",
                customer_type=customer_type,
            )
            customers.append(customer)
            async_session.add(customer)

        await async_session.commit()

        # Query by type - filter by current test's customers
        result = await async_session.execute(
            select(Customer).where(
                (Customer.customer_type == "business")
                & (Customer.id.in_([c.id for c in customers]))
            )
        )
        business_customers = result.scalars().all()
        assert len(business_customers) == 1
        assert business_customers[0].email.startswith("business_")


class TestAddressModel:
    """Test Address model functionality."""

    @pytest.mark.asyncio
    async def test_create_address(self, async_session: AsyncSession) -> None:
        """Test creating an address."""
        # First create a customer
        customer = Customer(
            email=f"address_{uuid.uuid4().hex[:8]}@example.com",
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        # Create address
        address = Address(
            customer_id=customer.id,
            type="shipping",
            street_address_1="123 Main St",
            street_address_2="Apt 4B",
            city="New York",
            state_province="NY",
            postal_code="10001",
            country_code="US",
            is_default=True,
        )
        async_session.add(address)
        await async_session.commit()

        # Verify address was created
        assert address.id is not None
        assert address.customer_id == customer.id
        assert address.is_default is True

        # Clean up
        await async_session.delete(address)
        await async_session.delete(customer)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_address_types(self, async_session: AsyncSession) -> None:
        """Test different address types."""
        # Create customer
        customer = Customer(
            email=f"multi-address_{uuid.uuid4().hex[:8]}@example.com",
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        # Create multiple addresses
        shipping = Address(
            customer_id=customer.id,
            type="shipping",
            street_address_1="123 Shipping St",
            city="Ship City",
            state_province="SC",
            postal_code="12345",
            country_code="US",
        )

        billing = Address(
            customer_id=customer.id,
            type="billing",
            street_address_1="456 Billing Ave",
            city="Bill City",
            state_province="BC",
            postal_code="67890",
            country_code="US",
        )

        async_session.add(shipping)
        async_session.add(billing)
        await async_session.commit()

        # Query addresses by type
        result = await async_session.execute(
            select(Address).where(
                (Address.customer_id == customer.id) & (Address.type == "shipping")
            )
        )
        shipping_addresses = result.scalars().all()
        assert len(shipping_addresses) == 1
        assert shipping_addresses[0].street_address_1 == "123 Shipping St"

        # Clean up
        await async_session.delete(shipping)
        await async_session.delete(billing)
        await async_session.delete(customer)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_address_geolocation(self, async_session: AsyncSession) -> None:
        """Test address with geolocation data."""
        customer = Customer(
            email=f"geo_{uuid.uuid4().hex[:8]}@example.com",
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        address = Address(
            customer_id=customer.id,
            type="shipping",
            street_address_1="1 Times Square",
            city="New York",
            state_province="NY",
            postal_code="10036",
            country_code="US",
            address_metadata={"latitude": 40.7580, "longitude": -73.9855},
        )
        async_session.add(address)
        await async_session.commit()

        # Verify geolocation in metadata
        assert address.address_metadata["latitude"] == 40.7580
        assert address.address_metadata["longitude"] == -73.9855

        # Clean up
        await async_session.delete(address)
        await async_session.delete(customer)
        await async_session.commit()
