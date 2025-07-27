"""Test Product, Category, and related models."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Category, Product


class TestProductModel:
    """Test Product model functionality."""

    @pytest.mark.asyncio
    async def test_create_product(self, async_session: AsyncSession) -> None:
        """Test creating a product."""
        product = Product(
            sku="TEST-001",
            name="Test Product",
            description="A test product description",
            price=99.99,
            cost=49.99,
            currency="USD",
            weight=1.5,
            weight_unit="kg",
            length=10.0,
            width=20.0,
            height=5.0,
            dimension_unit="cm",
            is_digital=False,
            is_active=True,
            attributes={"color": "blue", "size": "medium"},
            specifications={"material": "cotton", "care": "machine wash"},
        )
        async_session.add(product)
        await async_session.commit()

        # Verify product was created
        assert product.id is not None
        assert product.created_at is not None
        assert product.price == Decimal("99.99")
        assert product.attributes["color"] == "blue"

        # Clean up
        await async_session.delete(product)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_product_unique_sku(self, async_session: AsyncSession) -> None:
        """Test that SKU must be unique."""
        # Create first product
        product1 = Product(
            sku="UNIQUE-SKU",
            name="First Product",
            price=50.00,
        )
        async_session.add(product1)
        await async_session.commit()

        # Try to create second product with same SKU
        product2 = Product(
            sku="UNIQUE-SKU",
            name="Second Product",
            price=60.00,
        )
        async_session.add(product2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

        await async_session.rollback()

        # Clean up
        await async_session.delete(product1)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_digital_product(self, async_session: AsyncSession) -> None:
        """Test digital product attributes."""
        product = Product(
            sku="DIGITAL-001",
            name="Digital Download",
            description="A digital product",
            price=29.99,
            is_digital=True,
            # Digital products shouldn't need physical dimensions
            weight=0,
            attributes={"format": "PDF", "pages": 150},
        )
        async_session.add(product)
        await async_session.commit()

        assert product.is_digital is True
        assert product.weight == 0
        assert product.attributes["format"] == "PDF"

        # Clean up
        await async_session.delete(product)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_product_metadata(self, async_session: AsyncSession) -> None:
        """Test product with metadata fields."""
        product = Product(
            sku="META-001",
            name="SEO Optimized Product",
            price=149.99,
            meta_title="Buy the Best Product | Example Store",
            meta_description="The best product with amazing features and benefits.",
            meta_keywords=["best", "product", "quality"],
        )
        async_session.add(product)
        await async_session.commit()

        assert product.meta_title is not None
        assert "best" in product.meta_keywords

        # Clean up
        await async_session.delete(product)
        await async_session.commit()


class TestCategoryModel:
    """Test Category model functionality."""

    @pytest.mark.asyncio
    async def test_create_category(self, async_session: AsyncSession) -> None:
        """Test creating a category."""
        category = Category(
            name="Electronics",
            slug="electronics",
            description="Electronic products and gadgets",
            is_active=True,
            sort_order=1,
        )
        async_session.add(category)
        await async_session.commit()

        assert category.id is not None
        assert category.slug == "electronics"
        assert category.parent_id is None  # Root category

        # Clean up
        await async_session.delete(category)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_category_hierarchy(self, async_session: AsyncSession) -> None:
        """Test parent-child category relationships."""
        # Create parent category
        parent = Category(
            name="Clothing",
            slug="clothing",
            description="All clothing items",
        )
        async_session.add(parent)
        await async_session.commit()

        # Create child categories
        mens = Category(
            name="Men's Clothing",
            slug="mens-clothing",
            parent_id=parent.id,
            sort_order=1,
        )

        womens = Category(
            name="Women's Clothing",
            slug="womens-clothing",
            parent_id=parent.id,
            sort_order=2,
        )

        async_session.add(mens)
        async_session.add(womens)
        await async_session.commit()

        # Verify hierarchy
        assert mens.parent_id == parent.id
        assert womens.parent_id == parent.id

        # Query children
        result = await async_session.execute(
            select(Category)
            .where(Category.parent_id == parent.id)
            .order_by(Category.sort_order)
        )
        children = result.scalars().all()
        assert len(children) == 2
        assert children[0].slug == "mens-clothing"
        assert children[1].slug == "womens-clothing"

        # Clean up
        await async_session.delete(mens)
        await async_session.delete(womens)
        await async_session.delete(parent)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_category_unique_slug(self, async_session: AsyncSession) -> None:
        """Test that category slug must be unique."""
        cat1 = Category(
            name="Category 1",
            slug="unique-category",
        )
        async_session.add(cat1)
        await async_session.commit()

        cat2 = Category(
            name="Category 2",
            slug="unique-category",
        )
        async_session.add(cat2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

        await async_session.rollback()

        # Clean up
        await async_session.delete(cat1)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_product_with_category(self, async_session: AsyncSession) -> None:
        """Test product with category assignment."""
        # Create category
        electronics = Category(
            name="Electronics",
            slug="electronics-test",
            description="Electronic products",
        )
        async_session.add(electronics)
        await async_session.commit()

        # Create product with category
        product = Product(
            sku="CAT-PROD-001",
            name="Electronic Product",
            price=199.99,
            category_id=electronics.id,
        )
        async_session.add(product)
        await async_session.commit()

        # Verify category assignment
        await async_session.refresh(product)
        assert product.category_id == electronics.id

        # Query products by category
        result = await async_session.execute(
            select(Product).where(Product.category_id == electronics.id)
        )
        products = result.scalars().all()
        assert len(products) == 1
        assert products[0].sku == "CAT-PROD-001"

        # Clean up
        await async_session.delete(product)
        await async_session.delete(electronics)
        await async_session.commit()
