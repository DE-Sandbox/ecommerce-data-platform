"""Test Product, Category, and related models."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Category, Product, ProductPrice


class TestProductModel:
    """Test Product model functionality."""

    @pytest.mark.asyncio
    async def test_create_product(self, async_session: AsyncSession) -> None:
        """Test creating a product."""
        # Create category first
        category = Category(
            name=f"Test Category {uuid.uuid4().hex[:8]}",
            slug=f"test-category-{uuid.uuid4().hex[:8]}",
            display_order=1,
        )
        async_session.add(category)
        await async_session.commit()

        product = Product(
            sku=f"TEST-{uuid.uuid4().hex[:8]}",
            name="Test Product",
            slug=f"test-product-{uuid.uuid4().hex[:8]}",
            description="A test product description",
            category_id=category.id,
            status="active",
            weight=Decimal("1.5"),
            dimensions={"length": 10.0, "width": 20.0, "height": 5.0},
            product_metadata={"color": "blue", "size": "medium"},
            tags=["new", "featured"],
        )
        async_session.add(product)
        await async_session.commit()

        # Create price
        price = ProductPrice(
            product_id=product.id,
            currency_code="USD",
            price=Decimal("99.99"),
            is_active=True,
        )
        async_session.add(price)
        await async_session.commit()

        # Verify product was created
        assert product.id is not None
        assert product.created_at is not None
        assert product.product_metadata["color"] == "blue"
        assert price.price == Decimal("99.99")

    @pytest.mark.asyncio
    async def test_product_unique_sku(self, async_session: AsyncSession) -> None:
        """Test that SKU must be unique."""
        # Create first product
        unique_sku = f"UNIQUE-{uuid.uuid4().hex[:8]}"
        product1 = Product(
            sku=unique_sku,
            name="First Product",
            slug=f"first-product-{uuid.uuid4().hex[:8]}",
        )
        async_session.add(product1)
        await async_session.commit()

        # Try to create second product with same SKU
        product2 = Product(
            sku=unique_sku,
            name="Second Product",
            slug=f"second-product-{uuid.uuid4().hex[:8]}",
        )
        async_session.add(product2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

        await async_session.rollback()

    @pytest.mark.asyncio
    async def test_product_status(self, async_session: AsyncSession) -> None:
        """Test product status transitions."""
        product = Product(
            sku=f"STATUS-{uuid.uuid4().hex[:8]}",
            name="Status Test Product",
            slug=f"status-test-{uuid.uuid4().hex[:8]}",
            status="draft",
        )
        async_session.add(product)
        await async_session.commit()

        # Test status transitions
        statuses = ["active", "inactive", "discontinued"]
        for status in statuses:
            product.status = status
            await async_session.commit()
            assert product.status == status

    @pytest.mark.asyncio
    async def test_product_metadata(self, async_session: AsyncSession) -> None:
        """Test product metadata storage."""
        product = Product(
            sku=f"META-{uuid.uuid4().hex[:8]}",
            name="Metadata Test",
            slug=f"metadata-test-{uuid.uuid4().hex[:8]}",
            product_metadata={
                "manufacturer": "Test Corp",
                "warranty": "2 years",
                "certifications": ["CE", "FCC"],
            },
            tags=["electronic", "certified"],
        )
        async_session.add(product)
        await async_session.commit()

        # Verify metadata
        assert product.product_metadata["manufacturer"] == "Test Corp"
        assert "CE" in product.product_metadata["certifications"]
        assert "electronic" in product.tags


class TestCategoryModel:
    """Test Category model functionality."""

    @pytest.mark.asyncio
    async def test_create_category(self, async_session: AsyncSession) -> None:
        """Test creating a category."""
        category = Category(
            name=f"Test Category {uuid.uuid4().hex[:8]}",
            slug=f"test-category-{uuid.uuid4().hex[:8]}",
            description="A test category",
            display_order=1,
            is_active=True,
        )
        async_session.add(category)
        await async_session.commit()

        # Verify category was created
        assert category.id is not None
        assert category.created_at is not None
        assert category.is_active is True

    @pytest.mark.asyncio
    async def test_category_hierarchy(self, async_session: AsyncSession) -> None:
        """Test category parent-child relationships."""
        # Create parent category
        parent = Category(
            name=f"Parent Category {uuid.uuid4().hex[:8]}",
            slug=f"parent-{uuid.uuid4().hex[:8]}",
        )
        async_session.add(parent)
        await async_session.commit()

        # Create child categories
        child1 = Category(
            name=f"Child 1 {uuid.uuid4().hex[:8]}",
            slug=f"child-1-{uuid.uuid4().hex[:8]}",
            parent_id=parent.id,
        )
        child2 = Category(
            name=f"Child 2 {uuid.uuid4().hex[:8]}",
            slug=f"child-2-{uuid.uuid4().hex[:8]}",
            parent_id=parent.id,
        )
        async_session.add(child1)
        async_session.add(child2)
        await async_session.commit()

        # Verify relationships
        assert child1.parent_id == parent.id
        assert child2.parent_id == parent.id

        # Query children through parent
        result = await async_session.execute(
            select(Category).where(Category.parent_id == parent.id)
        )
        children = result.scalars().all()
        assert len(children) == 2

    @pytest.mark.asyncio
    async def test_category_unique_slug(self, async_session: AsyncSession) -> None:
        """Test that category slug must be unique."""
        unique_slug = f"unique-slug-{uuid.uuid4().hex[:8]}"

        # Create first category
        category1 = Category(
            name=f"First Category {uuid.uuid4().hex[:8]}",
            slug=unique_slug,
        )
        async_session.add(category1)
        await async_session.commit()

        # Try to create second category with same slug
        category2 = Category(
            name=f"Second Category {uuid.uuid4().hex[:8]}",
            slug=unique_slug,
        )
        async_session.add(category2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_product_with_category(self, async_session: AsyncSession) -> None:
        """Test product-category relationship."""
        # Create category
        category = Category(
            name=f"Electronics {uuid.uuid4().hex[:8]}",
            slug=f"electronics-{uuid.uuid4().hex[:8]}",
            description="Electronic products",
        )
        async_session.add(category)
        await async_session.commit()

        # Create products in category
        products = []
        for i in range(3):
            product = Product(
                sku=f"ELEC-{uuid.uuid4().hex[:8]}",
                name=f"Electronic Product {i}",
                slug=f"electronic-product-{i}-{uuid.uuid4().hex[:8]}",
                category_id=category.id,
            )
            products.append(product)
            async_session.add(product)

        await async_session.commit()

        # Query products by category
        result = await async_session.execute(
            select(Product).where(Product.category_id == category.id)
        )
        category_products = result.scalars().all()
        assert len(category_products) == 3
