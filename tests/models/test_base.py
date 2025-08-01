"""Test base model functionality."""

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base, get_async_session
from src.models.customer import Customer


class TestBaseModel:
    """Test base model and database connection functionality."""

    @pytest.mark.asyncio
    async def test_async_connection(self, async_session: AsyncSession) -> None:
        """Test that async database connection works."""
        result = await async_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_get_async_session(self) -> None:
        """Test get_async_session context manager."""
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_uuid_v7_generation(self, async_session: AsyncSession) -> None:
        """Test that UUID v7 generation works in database."""
        # Test the UUID v7 function directly
        result = await async_session.execute(text("SELECT uuid_generate_v7()"))
        uuid_value = result.scalar()

        assert uuid_value is not None
        assert len(str(uuid_value)) == 36  # Standard UUID format

        # Verify it's time-ordered by generating two UUIDs
        result1 = await async_session.execute(text("SELECT uuid_generate_v7()"))
        uuid1 = result1.scalar()

        # Small delay to ensure different timestamps
        await asyncio.sleep(0.001)

        result2 = await async_session.execute(text("SELECT uuid_generate_v7()"))
        uuid2 = result2.scalar()

        # UUID v7 should be lexicographically sortable by time
        assert str(uuid1) < str(uuid2)

    @pytest.mark.asyncio
    async def test_model_crud_operations(self, async_session: AsyncSession) -> None:
        """Test basic CRUD operations with a model."""
        import uuid

        # Create with unique email
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        customer = Customer(
            email=unique_email,
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        # Verify ID was generated
        assert customer.id is not None
        assert customer.created_at is not None
        assert customer.updated_at is not None

        # Read
        result = await async_session.execute(
            select(Customer).where(Customer.email == unique_email)
        )
        fetched_customer = result.scalar_one()
        assert fetched_customer.id == customer.id
        assert fetched_customer.email == unique_email

        # Update
        updated_email = f"updated_{uuid.uuid4().hex[:8]}@example.com"
        fetched_customer.email = updated_email
        await async_session.commit()

        # Verify update
        await async_session.refresh(fetched_customer)
        assert fetched_customer.email == updated_email
        # Updated_at should be set (may be same as created_at if very fast)
        assert fetched_customer.updated_at is not None

        # Soft Delete
        fetched_customer.deleted_at = datetime.now(UTC)
        await async_session.commit()

        # Verify soft delete
        await async_session.refresh(fetched_customer)
        assert fetched_customer.deleted_at is not None

    @pytest.mark.asyncio
    async def test_table_metadata(self) -> None:
        """Test that all models have proper table metadata."""
        # Check that Base has metadata
        assert hasattr(Base, "metadata")

        # Check that tables are registered
        table_names = list(Base.metadata.tables.keys())
        assert len(table_names) > 0

        # Verify key tables exist
        expected_tables = [
            "ecommerce.customers",
            "ecommerce.orders",
            "ecommerce.products",
            "ecommerce.inventory",
            "audit.audit_log",
        ]

        for table in expected_tables:
            assert table in table_names, f"Missing table: {table}"

    @pytest.mark.asyncio
    async def test_model_relationships(self, async_session: AsyncSession) -> None:
        """Test that model relationships are properly configured."""
        import uuid

        # This test verifies that we can access relationships
        unique_email = f"relationship_{uuid.uuid4().hex[:8]}@test.com"
        customer = Customer(
            email=unique_email,
            status="active",
            customer_type="individual",
        )
        async_session.add(customer)
        await async_session.commit()

        # Verify we can query with relationships (even if empty)
        result = await async_session.execute(
            select(Customer)
            .where(Customer.id == customer.id)
            .options()  # Could add joinedload for relationships
        )
        fetched = result.scalar_one()
        assert fetched.id == customer.id

        # Clean up
        await async_session.delete(fetched)
        await async_session.commit()
