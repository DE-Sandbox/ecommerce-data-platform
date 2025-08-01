"""Shared fixtures for model tests."""

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_database_url
from src.models.base import Base
from src.models.customer import Address, Customer, CustomerPII
from src.models.product import Category, Product, ProductPrice


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine]:
    """Create async engine for testing."""
    url = get_database_url("test", async_driver=True)
    engine = create_async_engine(url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Create async session for testing."""
    # Create tables if they don't exist

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create a session for the test
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_customer(async_session: AsyncSession) -> Customer:
    """Create a test customer with PII."""
    unique_suffix = uuid.uuid4().hex[:8]

    # Create customer
    customer = Customer(
        email=f"test_{unique_suffix}@example.com",
        status="active",
        customer_type="individual",
    )
    async_session.add(customer)
    await async_session.commit()

    # Create PII
    pii = CustomerPII(
        customer_id=customer.id,
        first_name="Test",
        last_name="Customer",
        phone="+1234567890",
    )
    async_session.add(pii)
    await async_session.commit()

    return customer


@pytest_asyncio.fixture
async def test_address(async_session: AsyncSession, test_customer: Customer) -> Address:
    """Create a test address."""
    address = Address(
        customer_id=test_customer.id,
        type="shipping",
        street_address_1="123 Test St",
        city="Test City",
        state_province="TC",
        postal_code="12345",
        country_code="US",
        is_default=True,
    )
    async_session.add(address)
    await async_session.commit()
    return address


@pytest_asyncio.fixture
async def test_category(async_session: AsyncSession) -> Category:
    """Create a test category."""
    unique_suffix = uuid.uuid4().hex[:8]

    category = Category(
        name=f"Test Category {unique_suffix}",
        slug=f"test-category-{unique_suffix}",
        display_order=1,
        is_active=True,
    )
    async_session.add(category)
    await async_session.commit()
    return category


@pytest_asyncio.fixture
async def test_product(async_session: AsyncSession, test_category: Category) -> Product:
    """Create a test product with price."""
    unique_suffix = uuid.uuid4().hex[:8]

    # Create product
    product = Product(
        sku=f"TEST-{unique_suffix}",
        name=f"Test Product {unique_suffix}",
        slug=f"test-product-{unique_suffix}",
        category_id=test_category.id,
        status="active",
        weight=Decimal("1.0"),
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

    return product
