"""Test Order and OrderItem models."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Address, Customer
from src.models.order import Order, OrderItem
from src.models.product import Product


class TestOrderModel:
    """Test Order model functionality."""

    @pytest.mark.asyncio
    async def test_create_order(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test creating an order."""
        order = Order(
            order_number=f"ORD-{uuid.uuid4().hex[:8]}",
            customer_id=test_customer.id,
            status="pending",
            currency_code="USD",
            subtotal_cents=10000,  # $100.00
            tax_cents=850,  # $8.50
            shipping_cents=1000,  # $10.00
            discount_cents=500,  # $5.00
            total_cents=11350,  # $113.50
            shipping_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            billing_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            notes="Please handle with care",
        )
        async_session.add(order)
        await async_session.commit()

        # Verify order was created
        assert order.id is not None
        assert order.created_at is not None
        assert order.order_number.startswith("ORD-")
        assert order.status == "pending"
        assert order.total_cents == 11350

    @pytest.mark.asyncio
    async def test_order_status_transitions(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test order status transitions."""
        order = Order(
            order_number=f"ORD-STATUS-{uuid.uuid4().hex[:8]}",
            customer_id=test_customer.id,
            status="pending",
            subtotal_cents=10000,  # $100.00
            tax_cents=0,
            shipping_cents=0,
            discount_cents=0,
            total_cents=10000,  # $100.00
            shipping_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            billing_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
        )
        async_session.add(order)
        await async_session.commit()

        # Test status transitions
        statuses = ["processing", "shipped", "delivered"]
        for status in statuses:
            order.status = status
            if status == "shipped":
                order.shipped_at = datetime.now(UTC)
            elif status == "delivered":
                order.delivered_at = datetime.now(UTC)
            await async_session.commit()

            # Verify status change
            await async_session.refresh(order)
            assert order.status == status

        assert order.shipped_at is not None
        assert order.delivered_at is not None

    @pytest.mark.asyncio
    async def test_order_with_items(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
        test_product: Product,
    ) -> None:
        """Test order with line items."""
        # Create order
        order = Order(
            order_number=f"ORD-ITEMS-{uuid.uuid4().hex[:8]}",
            customer_id=test_customer.id,
            status="pending",
            subtotal_cents=15000,  # $150.00
            total_cents=15000,  # $150.00
            shipping_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            billing_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
        )
        async_session.add(order)
        await async_session.commit()

        # Create order items
        item1 = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            sku=test_product.sku,
            name=test_product.name,
            quantity=2,
            unit_price_cents=5000,  # $50.00
            discount_cents=0,
            tax_cents=0,
            line_total_cents=10000,  # 2 * $50.00
        )

        item2 = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            sku=test_product.sku,
            name=test_product.name,
            quantity=1,
            unit_price_cents=5000,  # $50.00
            discount_cents=0,
            tax_cents=0,
            line_total_cents=5000,  # 1 * $50.00
        )

        async_session.add(item1)
        async_session.add(item2)
        await async_session.commit()

        # Query order items
        result = await async_session.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        items = result.scalars().all()
        assert len(items) == 2

        # Verify totals
        total_quantity = sum(item.quantity for item in items)
        total_amount = sum(item.line_total_cents for item in items)
        assert total_quantity == 3
        assert total_amount == 15000  # $150.00

    @pytest.mark.asyncio
    async def test_order_cancellation(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test order cancellation."""
        order = Order(
            order_number=f"ORD-CANCEL-{uuid.uuid4().hex[:8]}",
            customer_id=test_customer.id,
            status="processing",
            subtotal_cents=20000,  # $200.00
            tax_cents=0,
            shipping_cents=0,
            discount_cents=0,
            total_cents=20000,  # $200.00
            shipping_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            billing_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
        )
        async_session.add(order)
        await async_session.commit()

        # Cancel order
        order.status = "cancelled"
        order.cancelled_at = datetime.now(UTC)
        # Store cancellation reason in metadata - update dict in place
        metadata = dict(order.order_metadata)
        metadata["cancellation_reason"] = "Customer requested cancellation"
        order.order_metadata = metadata
        await async_session.commit()

        # Verify cancellation
        await async_session.refresh(order)
        assert order.status == "cancelled"
        assert order.cancelled_at is not None
        assert "cancellation_reason" in order.order_metadata

    @pytest.mark.asyncio
    async def test_order_with_promo_code(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test order with promotional code."""
        order = Order(
            order_number=f"ORD-PROMO-{uuid.uuid4().hex[:8]}",
            customer_id=test_customer.id,
            status="pending",
            subtotal_cents=10000,  # $100.00
            discount_cents=2000,  # $20.00 (20% off)
            total_cents=8000,  # $80.00
            order_metadata={"promo_code": "SAVE20"},
            shipping_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            billing_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
        )
        async_session.add(order)
        await async_session.commit()

        assert order.order_metadata["promo_code"] == "SAVE20"
        assert order.discount_cents == 2000
        assert order.total_cents == 8000


class TestOrderItemModel:
    """Test OrderItem model functionality."""

    @pytest.mark.asyncio
    async def test_order_item_calculations(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
        test_product: Product,
    ) -> None:
        """Test order item price calculations."""
        # Create order
        order = Order(
            order_number=f"ORD-CALC-{uuid.uuid4().hex[:8]}",
            customer_id=test_customer.id,
            status="pending",
            total_cents=0,
            shipping_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            billing_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
        )
        async_session.add(order)
        await async_session.commit()

        # Create order item with discount
        item = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            sku=test_product.sku,
            name=test_product.name,
            quantity=5,
            unit_price_cents=5000,  # $50 per item
            discount_cents=2500,  # $25 discount
            tax_cents=2250,  # $22.50 tax
            line_total_cents=24750,  # (5 * $50) - $25 + $22.50 = $247.50
        )
        async_session.add(item)
        await async_session.commit()

        # Verify calculations
        # Verify calculations
        assert item.quantity * item.unit_price_cents == 25000  # $250.00
        assert item.discount_cents == 2500  # $25.00
        assert item.tax_cents == 2250  # $22.50
        assert item.line_total_cents == 24750  # $247.50

    @pytest.mark.asyncio
    async def test_order_item_fulfillment(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
        test_product: Product,
    ) -> None:
        """Test order item fulfillment status."""
        # Create order
        order = Order(
            order_number=f"ORD-FULFILL-{uuid.uuid4().hex[:8]}",
            customer_id=test_customer.id,
            status="processing",
            subtotal_cents=10000,  # $100.00
            tax_cents=0,
            shipping_cents=0,
            discount_cents=0,
            total_cents=10000,  # $100.00
            shipping_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
            billing_address={
                "street_address_1": test_address.street_address_1,
                "city": test_address.city,
                "state_province": test_address.state_province,
                "postal_code": test_address.postal_code,
                "country_code": test_address.country_code,
            },
        )
        async_session.add(order)
        await async_session.commit()

        # Create order item
        item = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            sku=test_product.sku,
            name=test_product.name,
            quantity=2,
            unit_price_cents=5000,  # $50.00
            discount_cents=0,
            tax_cents=0,
            line_total_cents=10000,  # 2 * $50.00
        )
        async_session.add(item)
        await async_session.commit()

        # Verify item was created
        await async_session.refresh(item)
        assert item.id is not None
        assert item.quantity == 2
        assert item.line_total_cents == 10000
