"""Test Order and OrderItem models."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Address, Customer
from src.models.order import Order, OrderItem
from src.models.product import Product


class TestOrderModel:
    """Test Order model functionality."""

    @pytest.fixture
    async def test_customer(self, async_session: AsyncSession) -> Customer:
        """Create a test customer."""
        customer = Customer(
            email="order-test@example.com",
            first_name="Order",
            last_name="Test",
            phone="+1234567890",
        )
        async_session.add(customer)
        await async_session.commit()
        return customer

    @pytest.fixture
    async def test_address(
        self, async_session: AsyncSession, test_customer: Customer
    ) -> Address:
        """Create a test address."""
        address = Address(
            customer_id=test_customer.id,
            address_type="shipping",
            street_address_1="123 Test St",
            city="Test City",
            state_province="TC",
            postal_code="12345",
            country_code="US",
        )
        async_session.add(address)
        await async_session.commit()
        return address

    @pytest.fixture
    async def test_product(self, async_session: AsyncSession) -> Product:
        """Create a test product."""
        product = Product(
            sku="ORDER-TEST-001",
            name="Test Product for Orders",
            price=50.00,
            cost=25.00,
        )
        async_session.add(product)
        await async_session.commit()
        return product

    @pytest.mark.asyncio
    async def test_create_order(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test creating an order."""
        order = Order(
            order_number="ORD-2025-001",
            customer_id=test_customer.id,
            status="pending",
            currency="USD",
            subtotal=100.00,
            tax_amount=8.50,
            shipping_amount=10.00,
            discount_amount=5.00,
            total_amount=113.50,
            shipping_address_id=test_address.id,
            billing_address_id=test_address.id,
            customer_notes="Please handle with care",
        )
        async_session.add(order)
        await async_session.commit()

        # Verify order was created
        assert order.id is not None
        assert order.created_at is not None
        assert order.order_number == "ORD-2025-001"
        assert order.status == "pending"
        assert order.total_amount == Decimal("113.50")

    @pytest.mark.asyncio
    async def test_order_status_transitions(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test order status transitions."""
        order = Order(
            order_number="ORD-STATUS-001",
            customer_id=test_customer.id,
            status="pending",
            total_amount=100.00,
            shipping_address_id=test_address.id,
            billing_address_id=test_address.id,
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
            order_number="ORD-ITEMS-001",
            customer_id=test_customer.id,
            status="pending",
            subtotal=150.00,
            total_amount=150.00,
            shipping_address_id=test_address.id,
            billing_address_id=test_address.id,
        )
        async_session.add(order)
        await async_session.commit()

        # Create order items
        item1 = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            quantity=2,
            unit_price=50.00,
            subtotal=100.00,
            discount_amount=0.00,
            tax_amount=0.00,
            total_amount=100.00,
        )

        item2 = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            quantity=1,
            unit_price=50.00,
            subtotal=50.00,
            discount_amount=0.00,
            tax_amount=0.00,
            total_amount=50.00,
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
        total_amount = sum(item.total_amount for item in items)
        assert total_quantity == 3
        assert total_amount == Decimal("150.00")

    @pytest.mark.asyncio
    async def test_order_cancellation(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test order cancellation."""
        order = Order(
            order_number="ORD-CANCEL-001",
            customer_id=test_customer.id,
            status="processing",
            total_amount=200.00,
            shipping_address_id=test_address.id,
            billing_address_id=test_address.id,
        )
        async_session.add(order)
        await async_session.commit()

        # Cancel order
        order.status = "cancelled"
        order.cancelled_at = datetime.now(UTC)
        order.cancellation_reason = "Customer requested cancellation"
        await async_session.commit()

        # Verify cancellation
        await async_session.refresh(order)
        assert order.status == "cancelled"
        assert order.cancelled_at is not None
        assert order.cancellation_reason is not None

    @pytest.mark.asyncio
    async def test_order_with_promo_code(
        self,
        async_session: AsyncSession,
        test_customer: Customer,
        test_address: Address,
    ) -> None:
        """Test order with promotional code."""
        order = Order(
            order_number="ORD-PROMO-001",
            customer_id=test_customer.id,
            status="pending",
            subtotal=100.00,
            discount_amount=20.00,  # 20% off
            total_amount=80.00,
            promo_code="SAVE20",
            shipping_address_id=test_address.id,
            billing_address_id=test_address.id,
        )
        async_session.add(order)
        await async_session.commit()

        assert order.promo_code == "SAVE20"
        assert order.discount_amount == Decimal("20.00")
        assert order.total_amount == Decimal("80.00")


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
            order_number="ORD-CALC-001",
            customer_id=test_customer.id,
            status="pending",
            total_amount=0,
            shipping_address_id=test_address.id,
            billing_address_id=test_address.id,
        )
        async_session.add(order)
        await async_session.commit()

        # Create order item with discount
        item = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            quantity=5,
            unit_price=50.00,  # $50 per item
            subtotal=250.00,  # 5 * $50
            discount_amount=25.00,  # $25 discount
            discount_percentage=10.0,  # 10% discount
            tax_amount=22.50,  # 9% tax on discounted amount
            total_amount=247.50,  # $250 - $25 + $22.50
        )
        async_session.add(item)
        await async_session.commit()

        # Verify calculations
        assert item.subtotal == Decimal("250.00")
        assert item.discount_amount == Decimal("25.00")
        assert item.tax_amount == Decimal("22.50")
        assert item.total_amount == Decimal("247.50")

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
            order_number="ORD-FULFILL-001",
            customer_id=test_customer.id,
            status="processing",
            total_amount=100.00,
            shipping_address_id=test_address.id,
            billing_address_id=test_address.id,
        )
        async_session.add(order)
        await async_session.commit()

        # Create order item
        item = OrderItem(
            order_id=order.id,
            product_id=test_product.id,
            quantity=2,
            unit_price=50.00,
            total_amount=100.00,
            fulfillment_status="pending",
        )
        async_session.add(item)
        await async_session.commit()

        # Update fulfillment
        item.fulfillment_status = "shipped"
        item.tracking_number = "TRACK123456"
        item.shipped_at = datetime.now(UTC)
        await async_session.commit()

        # Verify fulfillment
        await async_session.refresh(item)
        assert item.fulfillment_status == "shipped"
        assert item.tracking_number == "TRACK123456"
        assert item.shipped_at is not None
