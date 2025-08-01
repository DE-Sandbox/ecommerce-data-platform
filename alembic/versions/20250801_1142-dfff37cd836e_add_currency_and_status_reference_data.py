"""add currency and status reference data

Revision ID: dfff37cd836e
Revises: 500e99a283fd
Create Date: 2025-08-01 11:42:04.386810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'dfff37cd836e'
down_revision: Union[str, Sequence[str], None] = '500e99a283fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reference data demonstrating various currencies and statuses.
    
    This migration adds sample data that showcases the different currency codes
    and status values supported by the system's CHECK constraints.
    """
    
    # Add sample products with different currencies to demonstrate multi-currency support
    op.execute(
        text("""
        -- Get category IDs for reference
        WITH cat_ids AS (
            SELECT 
                id as electronics_id,
                (SELECT id FROM ecommerce.categories WHERE slug = 'clothing') as clothing_id,
                (SELECT id FROM ecommerce.categories WHERE slug = 'books') as books_id
            FROM ecommerce.categories 
            WHERE slug = 'electronics'
        )
        -- Insert sample products with different currencies
        INSERT INTO ecommerce.products (id, sku, name, slug, description, category_id, brand, status, created_at, updated_at)
        SELECT 
            UUID_GENERATE_V7(),
            'DEMO-' || UPPER(SUBSTRING(slug FROM 1 FOR 3)) || '-001',
            name,
            slug,
            description,
            category_id,
            brand,
            'active',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM (
            VALUES 
                ('Smartphone Pro Max', 'smartphone-pro-max', 'Latest flagship smartphone with advanced features', (SELECT electronics_id FROM cat_ids), 'TechCorp'),
                ('Designer Jacket', 'designer-jacket', 'Premium leather jacket from luxury collection', (SELECT clothing_id FROM cat_ids), 'FashionHouse'),
                ('Data Engineering Guide', 'data-engineering-guide', 'Comprehensive guide to modern data engineering', (SELECT books_id FROM cat_ids), 'TechBooks')
        ) AS products(name, slug, description, category_id, brand)
        ON CONFLICT (sku) DO NOTHING;
    """)
    )
    
    # Add product prices in multiple currencies
    op.execute(
        text("""
        -- Insert prices in multiple currencies for demo products
        WITH product_ids AS (
            SELECT id, sku FROM ecommerce.products 
            WHERE sku IN ('DEMO-SMA-001', 'DEMO-DES-001', 'DEMO-DAT-001')
        )
        INSERT INTO ecommerce.product_prices (id, product_id, price, currency_code, valid_from, created_at, updated_at)
        SELECT 
            UUID_GENERATE_V7(),
            p.id,
            price_data.price,
            price_data.currency,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM product_ids p
        CROSS JOIN (
            VALUES 
                -- Smartphone prices
                ('DEMO-SMA-001', 999.99, 'USD'),
                ('DEMO-SMA-001', 899.99, 'EUR'),
                ('DEMO-SMA-001', 799.99, 'GBP'),
                ('DEMO-SMA-001', 1349.99, 'CAD'),
                ('DEMO-SMA-001', 149999, 'JPY'),
                -- Designer Jacket prices  
                ('DEMO-DES-001', 499.99, 'USD'),
                ('DEMO-DES-001', 449.99, 'EUR'),
                ('DEMO-DES-001', 399.99, 'GBP'),
                -- Book prices
                ('DEMO-DAT-001', 49.99, 'USD'),
                ('DEMO-DAT-001', 44.99, 'EUR')
        ) AS price_data(sku, price, currency)
        WHERE p.sku = price_data.sku
        ON CONFLICT (product_id, currency_code, valid_from) DO NOTHING;
    """)
    )
    
    # Add sample customers with different statuses
    op.execute(
        text("""
        -- Insert sample customers demonstrating different statuses
        INSERT INTO ecommerce.customers (id, email, status, customer_type, email_verified, created_at, updated_at)
        VALUES
            (UUID_GENERATE_V7(), 'active.customer@example.com', 'active', 'individual', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'inactive.customer@example.com', 'inactive', 'individual', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'business.customer@example.com', 'active', 'business', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'suspended.customer@example.com', 'suspended', 'individual', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (email) DO NOTHING;
    """)
    )
    
    # Add sample orders with different statuses and currencies
    op.execute(
        text("""
        -- Insert sample orders demonstrating different statuses and currencies
        WITH customer_id AS (
            SELECT id FROM ecommerce.customers WHERE email = 'active.customer@example.com' LIMIT 1
        )
        INSERT INTO ecommerce.orders (id, customer_id, order_number, status, currency_code, subtotal_cents, tax_cents, shipping_cents, total_cents, created_at, updated_at)
        SELECT 
            UUID_GENERATE_V7(),
            (SELECT id FROM customer_id),
            'ORD-DEMO-' || LPAD(row_number::text, 6, '0'),
            status,
            currency,
            subtotal_cents,
            tax_cents,
            shipping_cents,
            subtotal_cents + tax_cents + shipping_cents,
            created_at,
            CURRENT_TIMESTAMP
        FROM (
            VALUES 
                (1, 'pending', 'USD', 10000, 1000, 500, CURRENT_TIMESTAMP - INTERVAL '5 days'),
                (2, 'processing', 'EUR', 20000, 2000, 1000, CURRENT_TIMESTAMP - INTERVAL '4 days'),
                (3, 'shipped', 'GBP', 15000, 1500, 750, CURRENT_TIMESTAMP - INTERVAL '3 days'),
                (4, 'delivered', 'USD', 30000, 3000, 0, CURRENT_TIMESTAMP - INTERVAL '2 days'),
                (5, 'cancelled', 'CAD', 25000, 2500, 1000, CURRENT_TIMESTAMP - INTERVAL '1 day')
        ) AS order_data(row_number, status, currency, subtotal_cents, tax_cents, shipping_cents, created_at)
        ON CONFLICT (order_number) DO NOTHING;
    """)
    )
    
    # Add sample payment methods with different types
    op.execute(
        text("""
        -- Insert sample payment methods demonstrating different types
        WITH customer_id AS (
            SELECT id FROM ecommerce.customers WHERE email = 'active.customer@example.com' LIMIT 1
        )
        INSERT INTO ecommerce.payment_methods (id, customer_id, type, provider, token, last_four, expiry_month, expiry_year, is_default, created_at, updated_at)
        VALUES
            (UUID_GENERATE_V7(), (SELECT id FROM customer_id), 'credit_card', 'visa', 'tok_visa_demo_4242', '4242', 12, 2028, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), (SELECT id FROM customer_id), 'debit_card', 'mastercard', 'tok_mc_demo_5555', '5555', 6, 2027, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), (SELECT id FROM customer_id), 'paypal', 'paypal', 'tok_paypal_demo_001', NULL, NULL, NULL, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), (SELECT id FROM customer_id), 'apple_pay', 'apple', 'tok_apple_demo_001', NULL, NULL, NULL, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT DO NOTHING;
    """)
    )
    
    # Add sample payments with different statuses and types
    op.execute(
        text("""
        -- Insert sample payments demonstrating different statuses and types
        WITH order_payment_data AS (
            SELECT 
                o.id as order_id,
                pm.id as payment_method_id,
                o.total_cents,
                o.currency_code
            FROM ecommerce.orders o
            CROSS JOIN LATERAL (
                SELECT id FROM ecommerce.payment_methods 
                WHERE customer_id = o.customer_id 
                AND is_default = true 
                LIMIT 1
            ) pm
            WHERE o.order_number LIKE 'ORD-DEMO-%'
            AND o.status != 'pending'
            LIMIT 4
        )
        INSERT INTO ecommerce.payments (id, order_id, payment_method_id, amount_cents, currency_code, type, status, created_at, updated_at)
        SELECT 
            UUID_GENERATE_V7(),
            order_id,
            payment_method_id,
            CASE 
                WHEN row_number = 4 THEN total_cents / 2  -- Partial refund
                ELSE total_cents 
            END,
            currency_code,
            CASE 
                WHEN row_number = 3 THEN 'refund'
                WHEN row_number = 4 THEN 'partial_refund'
                ELSE 'payment'
            END,
            CASE 
                WHEN row_number = 1 THEN 'processing'
                WHEN row_number = 2 THEN 'completed'
                WHEN row_number = 3 THEN 'completed'
                WHEN row_number = 4 THEN 'completed'
                ELSE 'pending'
            END,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM (
            SELECT *, row_number() OVER (ORDER BY order_id) as row_number
            FROM order_payment_data
        ) t
        ON CONFLICT DO NOTHING;
    """)
    )


def downgrade() -> None:
    """Remove reference data for currencies and statuses."""
    
    # Remove payments first (foreign key dependencies)
    op.execute(
        text("""
        DELETE FROM ecommerce.payments 
        WHERE order_id IN (
            SELECT id FROM ecommerce.orders 
            WHERE order_number LIKE 'ORD-DEMO-%'
        );
    """)
    )
    
    # Remove payment methods
    op.execute(
        text("""
        DELETE FROM ecommerce.payment_methods 
        WHERE customer_id IN (
            SELECT id FROM ecommerce.customers 
            WHERE email IN (
                'active.customer@example.com',
                'inactive.customer@example.com',
                'business.customer@example.com',
                'suspended.customer@example.com'
            )
        );
    """)
    )
    
    # Remove orders
    op.execute(
        text("""
        DELETE FROM ecommerce.orders 
        WHERE order_number LIKE 'ORD-DEMO-%';
    """)
    )
    
    # Remove customers
    op.execute(
        text("""
        DELETE FROM ecommerce.customers 
        WHERE email IN (
            'active.customer@example.com',
            'inactive.customer@example.com', 
            'business.customer@example.com',
            'suspended.customer@example.com'
        );
    """)
    )
    
    # Remove product prices
    op.execute(
        text("""
        DELETE FROM ecommerce.product_prices 
        WHERE product_id IN (
            SELECT id FROM ecommerce.products 
            WHERE sku IN ('DEMO-SMA-001', 'DEMO-DES-001', 'DEMO-DAT-001')
        );
    """)
    )
    
    # Remove products
    op.execute(
        text("""
        DELETE FROM ecommerce.products 
        WHERE sku IN ('DEMO-SMA-001', 'DEMO-DES-001', 'DEMO-DAT-001');
    """)
    )
