"""Basic tests for SQLAlchemy models to verify they work correctly."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Customer, CustomerPII
from src.models.product import Category, Product, ProductPrice


class TestBasicModelOperations:
    """Test basic CRUD operations for key models."""

    @pytest.mark.asyncio
    async def test_database_connection(self, async_session: AsyncSession) -> None:
        """Test that we can connect to the database."""
        result = await async_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_create_customer_with_pii(self, async_session: AsyncSession) -> None:
        """Test creating a customer with PII data."""
        import uuid

        # Create customer with unique email
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        customer = Customer(
            email=unique_email,
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        # Create PII data
        pii = CustomerPII(
            customer_id=customer.id,
            first_name="Test",
            last_name="User",
            phone="+1234567890",
        )
        async_session.add(pii)
        await async_session.commit()

        # Verify
        assert customer.id is not None
        assert pii.customer_id == customer.id

        # Query back
        result = await async_session.execute(
            select(Customer).where(Customer.email == unique_email)
        )
        found = result.scalar_one()
        assert found.id == customer.id

    @pytest.mark.asyncio
    async def test_create_product_with_price(self, async_session: AsyncSession) -> None:
        """Test creating a product with pricing."""
        import uuid

        # Create category first with unique name
        unique_suffix = uuid.uuid4().hex[:8]
        category = Category(
            name=f"Test Category {unique_suffix}",
            slug=f"test-category-{unique_suffix}",
            display_order=1,
        )
        async_session.add(category)
        await async_session.commit()

        # Create product with unique SKU
        product = Product(
            sku=f"TEST-{unique_suffix}",
            name=f"Test Product {unique_suffix}",
            slug=f"test-product-{unique_suffix}",
            category_id=category.id,
            status="active",
        )
        async_session.add(product)
        await async_session.commit()

        # Create price
        price = ProductPrice(
            product_id=product.id,
            currency_code="USD",
            price=99.99,
        )
        async_session.add(price)
        await async_session.commit()

        # Verify
        assert product.id is not None
        assert price.product_id == product.id
        assert float(price.price) == 99.99

    @pytest.mark.asyncio
    async def test_uuid_v7_generation(self, async_session: AsyncSession) -> None:
        """Test that UUID v7 is properly generated."""
        import uuid

        # Create two customers with unique emails
        unique_suffix = uuid.uuid4().hex[:8]
        customer1 = Customer(email=f"uuid1_{unique_suffix}@example.com")
        customer2 = Customer(email=f"uuid2_{unique_suffix}@example.com")

        async_session.add(customer1)
        async_session.add(customer2)
        await async_session.commit()

        # UUIDs should be generated
        assert customer1.id is not None
        assert customer2.id is not None

        # They should be different
        assert customer1.id != customer2.id

    @pytest.mark.asyncio
    async def test_soft_delete(self, async_session: AsyncSession) -> None:
        """Test soft delete functionality."""
        import uuid
        from datetime import UTC, datetime

        # Create customer with unique email
        unique_email = f"delete_{uuid.uuid4().hex[:8]}@example.com"
        customer = Customer(email=unique_email)
        async_session.add(customer)
        await async_session.commit()

        # Soft delete
        customer.deleted_at = datetime.now(UTC)
        customer.is_deleted = True
        await async_session.commit()

        # Should still be queryable
        result = await async_session.execute(
            select(Customer).where(Customer.id == customer.id)
        )
        found = result.scalar_one()
        assert found.deleted_at is not None
        assert found.is_deleted is True

    @pytest.mark.asyncio
    async def test_cascade_relationships(self, async_session: AsyncSession) -> None:
        """Test that cascade delete works properly."""
        # Create customer
        customer = Customer(email="cascade@example.com")
        async_session.add(customer)
        await async_session.commit()

        # Create PII
        pii = CustomerPII(
            customer_id=customer.id,
            first_name="Cascade",
            last_name="Test",
        )
        async_session.add(pii)
        await async_session.commit()

        # Delete customer
        await async_session.delete(customer)
        await async_session.commit()

        # PII should be gone too (CASCADE delete)
        result = await async_session.execute(
            select(CustomerPII).where(CustomerPII.customer_id == customer.id)
        )
        assert result.scalar_one_or_none() is None
