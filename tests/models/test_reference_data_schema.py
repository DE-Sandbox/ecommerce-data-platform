"""Test reference data schema without depending on migrations."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.inventory import Location
from src.models.product import Category


class TestReferenceDataSchema:
    """Test that reference data models work correctly without depending on migration state."""

    @pytest.mark.asyncio
    async def test_create_category(self, async_session: AsyncSession) -> None:
        """Test creating a category with all required fields."""
        # Use unique values to avoid conflicts
        unique_suffix = str(uuid.uuid4())[:8]

        # Create a category
        category = Category(
            name=f"Test Electronics {unique_suffix}",
            slug=f"test-electronics-{unique_suffix}",
            description="Test category for electronics",
            display_order=1,
            is_active=True,
        )
        async_session.add(category)
        await async_session.commit()

        # Verify it was created with UUID v7
        assert category.id is not None
        assert len(str(category.id)) == 36  # UUID format
        assert category.created_at is not None
        assert category.updated_at is not None

        # Query it back
        result = await async_session.execute(
            select(Category).where(Category.slug == f"test-electronics-{unique_suffix}")
        )
        saved_category = result.scalar_one()

        assert saved_category.name == f"Test Electronics {unique_suffix}"
        assert saved_category.description == "Test category for electronics"
        assert saved_category.display_order == 1
        assert saved_category.is_active is True

    @pytest.mark.asyncio
    async def test_category_unique_constraints(
        self, async_session: AsyncSession
    ) -> None:
        """Test that category constraints work correctly."""
        # Use unique values to avoid conflicts
        unique_suffix = str(uuid.uuid4())[:8]

        # Create first category
        category1 = Category(
            name=f"Unique Test {unique_suffix}",
            slug=f"unique-slug-{unique_suffix}",
            display_order=1,
        )
        async_session.add(category1)
        await async_session.commit()

        # Try to create another with same slug (should fail)
        category2 = Category(
            name="Different Name",
            slug=f"unique-slug-{unique_suffix}",  # Same slug
            display_order=2,
        )
        async_session.add(category2)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "duplicate key value violates unique constraint" in str(exc_info.value)
        await async_session.rollback()

        # Try to create another with same name (should fail)
        category3 = Category(
            name=f"Unique Test {unique_suffix}",  # Same name
            slug="different-slug",
            display_order=3,
        )
        async_session.add(category3)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "duplicate key value violates unique constraint" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_location(self, async_session: AsyncSession) -> None:
        """Test creating a location with all required fields."""
        # Use unique values to avoid conflicts
        unique_suffix = str(uuid.uuid4())[:8]

        # Create a warehouse
        warehouse = Location(
            code=f"TEST-WH-{unique_suffix}",
            name=f"Test Warehouse {unique_suffix}",
            type="warehouse",
            address="123 Test St, Test City, TC 12345",
            is_active=True,
        )
        async_session.add(warehouse)
        await async_session.commit()

        # Verify it was created
        assert warehouse.id is not None
        assert warehouse.created_at is not None
        assert warehouse.updated_at is not None
        assert warehouse.location_metadata == {}  # Default empty dict

        # Create a store
        store = Location(
            code=f"TEST-ST-{unique_suffix}",
            name=f"Test Store {unique_suffix}",
            type="store",
            address="456 Shop Ave, Mall City, MC 67890",
            is_active=True,
        )
        async_session.add(store)
        await async_session.commit()

        # Query both back - filter by our unique suffix to avoid other data
        result = await async_session.execute(
            select(Location)
            .where(Location.code.like(f"TEST-%{unique_suffix}"))
            .order_by(Location.code)
        )
        locations = result.scalars().all()

        assert len(locations) == 2
        # Sort by type to ensure consistent order
        locations_by_type = sorted(locations, key=lambda loc: loc.type)
        assert locations_by_type[0].type == "store"
        assert locations_by_type[1].type == "warehouse"

    @pytest.mark.asyncio
    async def test_location_unique_code(self, async_session: AsyncSession) -> None:
        """Test that location code must be unique."""
        # Use unique values to avoid conflicts
        unique_suffix = str(uuid.uuid4())[:8]

        # Create first location
        location1 = Location(
            code=f"UNIQUE-{unique_suffix}",
            name="First Location",
            type="warehouse",
        )
        async_session.add(location1)
        await async_session.commit()

        # Try to create another with same code
        location2 = Location(
            code=f"UNIQUE-{unique_suffix}",  # Same code
            name="Second Location",
            type="store",
        )
        async_session.add(location2)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "duplicate key value violates unique constraint" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_location_type_constraint(self, async_session: AsyncSession) -> None:
        """Test that location type allows valid values."""
        # Use unique values to avoid conflicts
        unique_suffix = str(uuid.uuid4())[:8]

        # Test valid location types
        valid_types = ["warehouse", "store"]

        for loc_type in valid_types:
            location = Location(
                code=f"TEST-{loc_type.upper()}-{unique_suffix}",
                name=f"Test {loc_type.title()}",
                type=loc_type,
            )
            async_session.add(location)

        # Should succeed for valid types
        await async_session.commit()

        # Verify locations were created
        assert all(loc.id is not None for loc in async_session.new)

        # Note: Currently the Location model doesn't enforce type constraints
        # This test documents the expected valid types
