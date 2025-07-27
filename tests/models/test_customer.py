"""Test Customer and Address models."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Address, Customer


class TestCustomerModel:
    """Test Customer model functionality."""

    @pytest.mark.asyncio
    async def test_create_customer(self, async_session: AsyncSession) -> None:
        """Test creating a customer."""
        customer = Customer(
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            date_of_birth=datetime(1990, 1, 1).date(),
            customer_segment="premium",
            lifetime_value=1500.00,
            acquisition_channel="organic",
            preferred_language="en",
        )
        async_session.add(customer)
        await async_session.commit()

        # Verify customer was created
        assert customer.id is not None
        assert customer.created_at is not None
        assert customer.is_active is True
        assert customer.email_verified is False

        # Clean up
        await async_session.delete(customer)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_customer_unique_email(self, async_session: AsyncSession) -> None:
        """Test that email must be unique."""
        # Create first customer
        customer1 = Customer(
            email="unique@example.com",
            first_name="First",
            last_name="User",
        )
        async_session.add(customer1)
        await async_session.commit()

        # Try to create second customer with same email
        customer2 = Customer(
            email="unique@example.com",
            first_name="Second",
            last_name="User",
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
            email="delete@example.com",
            first_name="Delete",
            last_name="Me",
        )
        async_session.add(customer)
        await async_session.commit()

        # Soft delete
        customer.deleted_at = datetime.now(UTC)
        await async_session.commit()

        # Query should still find the customer
        result = await async_session.execute(
            select(Customer).where(Customer.email == "delete@example.com")
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.deleted_at is not None

    @pytest.mark.asyncio
    async def test_customer_segments(self, async_session: AsyncSession) -> None:
        """Test different customer segments."""
        segments = ["regular", "premium", "vip"]
        customers = []

        for _i, segment in enumerate(segments):
            customer = Customer(
                email=f"{segment}@example.com",
                first_name=segment.capitalize(),
                last_name="Customer",
                customer_segment=segment,
            )
            customers.append(customer)
            async_session.add(customer)

        await async_session.commit()

        # Query by segment
        result = await async_session.execute(
            select(Customer).where(Customer.customer_segment == "premium")
        )
        premium_customers = result.scalars().all()
        assert len(premium_customers) == 1
        assert premium_customers[0].email == "premium@example.com"

        # Clean up
        for customer in customers:
            await async_session.delete(customer)
        await async_session.commit()


class TestAddressModel:
    """Test Address model functionality."""

    @pytest.mark.asyncio
    async def test_create_address(self, async_session: AsyncSession) -> None:
        """Test creating an address."""
        # First create a customer
        customer = Customer(
            email="address@example.com",
            first_name="Address",
            last_name="Test",
        )
        async_session.add(customer)
        await async_session.commit()

        # Create address
        address = Address(
            customer_id=customer.id,
            address_type="shipping",
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
            email="multi-address@example.com",
            first_name="Multi",
            last_name="Address",
        )
        async_session.add(customer)
        await async_session.commit()

        # Create multiple addresses
        shipping = Address(
            customer_id=customer.id,
            address_type="shipping",
            street_address_1="123 Shipping St",
            city="Ship City",
            state_province="SC",
            postal_code="12345",
            country_code="US",
        )

        billing = Address(
            customer_id=customer.id,
            address_type="billing",
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
                (Address.customer_id == customer.id)
                & (Address.address_type == "shipping")
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
            email="geo@example.com",
            first_name="Geo",
            last_name="Located",
        )
        async_session.add(customer)
        await async_session.commit()

        address = Address(
            customer_id=customer.id,
            address_type="shipping",
            street_address_1="1 Times Square",
            city="New York",
            state_province="NY",
            postal_code="10036",
            country_code="US",
            latitude=40.7580,
            longitude=-73.9855,
        )
        async_session.add(address)
        await async_session.commit()

        # Verify geolocation
        assert address.latitude == 40.7580
        assert address.longitude == -73.9855

        # Clean up
        await async_session.delete(address)
        await async_session.delete(customer)
        await async_session.commit()
