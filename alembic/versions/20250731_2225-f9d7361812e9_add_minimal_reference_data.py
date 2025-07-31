"""add minimal reference data

Revision ID: f9d7361812e9
Revises: 18bd19b54443
Create Date: 2025-07-31 22:25:29.116279

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "f9d7361812e9"
down_revision: str | Sequence[str] | None = "18bd19b54443"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add minimal reference data for e-commerce platform."""
    # Insert root product categories - minimal set for testing
    # Use DO UPDATE to handle existing rows with same name but different slug
    op.execute(
        text("""
        INSERT INTO ecommerce.categories (id, name, slug, description, display_order, is_active, created_at, updated_at)
        VALUES
            (UUID_GENERATE_V7(), 'Electronics', 'electronics', 'Electronic devices and accessories', 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'Clothing', 'clothing', 'Apparel and fashion items', 2, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'Books', 'books', 'Physical and digital books', 3, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'Home & Garden', 'home-garden', 'Home improvement and garden supplies', 4, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'Sports & Outdoors', 'sports-outdoors', 'Sporting goods and outdoor equipment', 5, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (slug) DO UPDATE SET
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP;
    """)
    )

    # Insert warehouse/store locations - not geographic locations
    # The Location model is for warehouses and stores, not countries
    op.execute(
        text("""
        INSERT INTO ecommerce.locations (id, name, type, code, address, is_active, created_at, updated_at)
        VALUES
            -- Sample warehouses
            (UUID_GENERATE_V7(), 'Main Distribution Center', 'warehouse', 'WH-001', '123 Logistics Way, Newark, NJ 07102', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'West Coast Fulfillment', 'warehouse', 'WH-002', '456 Shipping Blvd, Los Angeles, CA 90013', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            -- Sample retail stores
            (UUID_GENERATE_V7(), 'Downtown Flagship Store', 'store', 'ST-001', '789 Main St, New York, NY 10001', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (UUID_GENERATE_V7(), 'Mall Location', 'store', 'ST-002', '321 Shopping Center Dr, Chicago, IL 60601', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (code) DO NOTHING;
    """)
    )

    # Note: PaymentMethod is customer-specific, not a reference table
    # Note: Order statuses are handled by the OrderStatus enum in the model
    # Note: Payment types and statuses are handled by check constraints

    # Note: We intentionally do NOT add:
    # - Test users (should be created via API)
    # - Test products (should be created via synthetic data generation)
    # - Any business data that could change


def downgrade() -> None:
    """Remove reference data."""
    # Delete in reverse order to respect foreign key constraints
    op.execute(
        text("""
        DELETE FROM ecommerce.locations
        WHERE code IN ('WH-001', 'WH-002', 'ST-001', 'ST-002');
    """)
    )

    op.execute(
        text("""
        DELETE FROM ecommerce.categories
        WHERE slug IN ('electronics', 'clothing', 'books', 'home-garden', 'sports-outdoors');
    """)
    )
