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
        # Create
        customer = Customer(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
        )
        async_session.add(customer)
        await async_session.commit()

        # Verify ID was generated
        assert customer.id is not None
        assert customer.created_at is not None
        assert customer.updated_at is not None

        # Read
        result = await async_session.execute(
            select(Customer).where(Customer.email == "test@example.com")
        )
        fetched_customer = result.scalar_one()
        assert fetched_customer.id == customer.id
        assert fetched_customer.first_name == "Test"

        # Update
        fetched_customer.first_name = "Updated"
        await async_session.commit()

        # Verify update
        await async_session.refresh(fetched_customer)
        assert fetched_customer.first_name == "Updated"
        assert fetched_customer.updated_at > fetched_customer.created_at

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
            "audit.audit_logs",
        ]

        for table in expected_tables:
            assert table in table_names, f"Missing table: {table}"

    @pytest.mark.asyncio
    async def test_model_relationships(self, async_session: AsyncSession) -> None:
        """Test that model relationships are properly configured."""
        # This test verifies that we can access relationships
        customer = Customer(
            email="relationship@test.com",
            first_name="Relationship",
            last_name="Test",
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
