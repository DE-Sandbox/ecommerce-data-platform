"""Test reference data migration."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Customer
from src.models.order import Order
from src.models.payment import Payment, PaymentMethod
from src.models.product import Product, ProductPrice


@pytest.mark.asyncio
class TestReferenceData:
    """Test that reference data migration created expected records."""

    async def test_demo_products_exist(self, async_session: AsyncSession) -> None:
        """Test that demo products were created."""
        result = await async_session.execute(
            select(Product).where(Product.sku.like("DEMO-%"))
        )
        products = result.scalars().all()

        assert len(products) == 3
        skus = {p.sku for p in products}
        assert skus == {"DEMO-SMA-001", "DEMO-DES-001", "DEMO-DAT-001"}

        # All should be active
        for product in products:
            assert product.status == "active"

    async def test_product_prices_multiple_currencies(
        self, async_session: AsyncSession
    ) -> None:
        """Test that products have prices in multiple currencies."""
        # Get smartphone product
        result = await async_session.execute(
            select(Product).where(Product.sku == "DEMO-SMA-001")
        )
        smartphone = result.scalar_one()

        # Get its prices
        result = await async_session.execute(
            select(ProductPrice).where(ProductPrice.product_id == smartphone.id)
        )
        prices = result.scalars().all()

        # Should have prices in multiple currencies
        currencies = {p.currency_code for p in prices}
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "GBP" in currencies
        assert "CAD" in currencies
        assert "JPY" in currencies

    async def test_demo_customers_with_statuses(
        self, async_session: AsyncSession
    ) -> None:
        """Test that demo customers exist with different statuses."""
        result = await async_session.execute(
            select(Customer).where(Customer.email.like("%@example.com"))
        )
        customers = result.scalars().all()

        assert len(customers) >= 4

        # Check different statuses exist
        statuses = {c.status for c in customers}
        assert "active" in statuses
        assert "inactive" in statuses
        assert "suspended" in statuses

        # Check customer types
        types = {c.customer_type for c in customers}
        assert "individual" in types
        assert "business" in types

    async def test_demo_orders_with_statuses(self, async_session: AsyncSession) -> None:
        """Test that demo orders exist with different statuses."""
        result = await async_session.execute(
            select(Order).where(Order.order_number.like("ORD-DEMO-%"))
        )
        orders = result.scalars().all()

        assert len(orders) == 5

        # Check different order statuses
        statuses = {o.status for o in orders}
        expected_statuses = {
            "pending",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
        }
        assert statuses == expected_statuses

        # Check different currencies
        currencies = {o.currency_code for o in orders}
        assert len(currencies) >= 3  # At least USD, EUR, GBP

    async def test_payment_methods_types(self, async_session: AsyncSession) -> None:
        """Test that different payment method types exist."""
        result = await async_session.execute(
            select(PaymentMethod)
            .join(Customer)
            .where(Customer.email == "active.customer@example.com")
        )
        payment_methods = result.scalars().all()

        assert len(payment_methods) == 4

        # Check different payment types
        types = {pm.type for pm in payment_methods}
        expected_types = {"credit_card", "debit_card", "paypal", "apple_pay"}
        assert types == expected_types

        # One should be default
        default_count = sum(1 for pm in payment_methods if pm.is_default)
        assert default_count == 1

    async def test_payments_with_different_types(
        self, async_session: AsyncSession
    ) -> None:
        """Test that payments exist with different types and statuses."""
        result = await async_session.execute(
            select(Payment).join(Order).where(Order.order_number.like("ORD-DEMO-%"))
        )
        payments = result.scalars().all()

        # Should have some payments
        assert len(payments) > 0

        # Check payment types
        payment_types = {p.type for p in payments}
        assert "payment" in payment_types

        # Check payment statuses
        payment_statuses = {p.status for p in payments}
        assert len(payment_statuses) >= 2  # At least processing and completed
