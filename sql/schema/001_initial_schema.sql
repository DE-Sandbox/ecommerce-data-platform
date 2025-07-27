-- E-commerce Platform PostgreSQL Schema
-- Version: 1.0.0
-- Features: UUID v7, JSONB, Partitioning, RLS, Generated Columns

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Create UUID v7 function (pure SQL implementation)
-- Based on best practices from PostgreSQL community (2024)
-- This implementation provides time-ordered UUIDs without requiring compilation or superuser privileges
CREATE OR REPLACE FUNCTION UUID_GENERATE_V7()
RETURNS uuid
LANGUAGE sql
VOLATILE
PARALLEL SAFE
AS $$
  -- Generate UUID v7 using current timestamp
  -- Structure: unix_ts_ms (48 bits) | ver (4 bits) | rand_a (12 bits) | var (2 bits) | rand_b (62 bits)
  SELECT encode(
    set_bit(
      set_bit(
        overlay(
          uuid_send(gen_random_uuid())
          placing substring(int8send(floor(extract(epoch from clock_timestamp()) * 1000)::bigint) from 3)
          from 1 for 6
        ),
        52, 1
      ),
      53, 1
    ),
    'hex'
  )::uuid
$$;

-- Alternative UUID v7 with sub-millisecond precision (for high-throughput scenarios)
CREATE OR REPLACE FUNCTION UUID_GENERATE_V7_PRECISE()
RETURNS uuid
LANGUAGE sql
VOLATILE
PARALLEL SAFE
AS $$
  -- Extract timestamp with microsecond precision
  WITH ts AS (
    SELECT extract(epoch from clock_timestamp()) AS epoch_seconds
  )
  SELECT encode(
    set_bit(
      set_bit(
        overlay(
          overlay(
            uuid_send(gen_random_uuid())
            placing substring(int8send(floor(ts.epoch_seconds * 1000)::bigint) from 3)
            from 1 for 6
          )
          -- Add sub-millisecond precision in rand_a field (12 bits)
          placing substring(int8send(((ts.epoch_seconds * 1000000)::bigint % 1000) << 2) from 7)
          from 7 for 2
        ),
        52, 1
      ),
      53, 1
    ),
    'hex'
  )::uuid
  FROM ts
$$;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ecommerce;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS archive;

SET search_path TO ecommerce, public;

-- =====================================================
-- CUSTOMER DOMAIN
-- =====================================================

-- Customers table (main identity)
CREATE TABLE customers (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    email varchar(255) UNIQUE NOT NULL,
    email_verified boolean DEFAULT FALSE,
    status varchar(50) NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'inactive', 'suspended', 'deleted')
    ),
    customer_type varchar(50) NOT NULL DEFAULT 'individual' CHECK (
        customer_type IN ('individual', 'business')
    ),
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    version integer DEFAULT 1 NOT NULL
);

-- Customer PII table (GDPR compliance)
CREATE TABLE customer_pii (
    customer_id uuid PRIMARY KEY REFERENCES customers (id) ON DELETE CASCADE,
    first_name varchar(100),
    last_name varchar(100),
    phone varchar(50),
    date_of_birth date,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL
);

-- Customer addresses
CREATE TABLE addresses (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    customer_id uuid NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    type varchar(50) NOT NULL DEFAULT 'shipping' CHECK (
        type IN ('shipping', 'billing', 'both')
    ),
    recipient_name varchar(200),
    street_address_1 varchar(255) NOT NULL,
    street_address_2 varchar(255),
    city varchar(100) NOT NULL,
    state_province varchar(100),
    postal_code varchar(20),
    country_code char(2) NOT NULL,
    phone varchar(50),
    is_default boolean DEFAULT FALSE,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    version integer DEFAULT 1 NOT NULL
);

-- Customer consent tracking (GDPR)
CREATE TABLE customer_consents (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    customer_id uuid NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    consent_type varchar(100) NOT NULL CHECK (
        consent_type IN ('marketing', 'analytics', 'third_party', 'cookies')
    ),
    granted boolean NOT NULL,
    granted_at timestamptz,
    revoked_at timestamptz,
    ip_address inet,
    user_agent text,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL
);

-- =====================================================
-- PRODUCT DOMAIN
-- =====================================================

-- Product categories
CREATE TABLE categories (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    parent_id uuid REFERENCES categories (id),
    slug varchar(100) UNIQUE NOT NULL,
    name varchar(200) NOT NULL,
    description text,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL
);

-- Products (master catalog)
CREATE TABLE products (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    sku varchar(100) UNIQUE NOT NULL,
    name varchar(500) NOT NULL,
    description text,
    category_id uuid REFERENCES categories (id),
    brand varchar(200),
    attributes jsonb DEFAULT '{}',
    tags text [],
    status varchar(50) NOT NULL DEFAULT 'active' CHECK (
        status IN ('draft', 'active', 'discontinued', 'deleted')
    ),
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    version integer DEFAULT 1 NOT NULL
);

-- Product variants (SKUs)
CREATE TABLE product_variants (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    product_id uuid NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    sku varchar(100) UNIQUE NOT NULL,
    name varchar(500) NOT NULL,
    attributes jsonb DEFAULT '{}', -- size, color, material, etc.
    weight_grams integer,
    dimensions_cm jsonb, -- {length, width, height}
    barcode varchar(100),
    status varchar(50) NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'discontinued', 'deleted')
    ),
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL
);

-- Temporal pricing table
CREATE TABLE product_prices (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    product_variant_id uuid NOT NULL REFERENCES product_variants (
        id
    ) ON DELETE CASCADE,
    price_cents integer NOT NULL CHECK (price_cents >= 0),
    compare_at_price_cents integer CHECK (compare_at_price_cents >= 0),
    cost_cents integer CHECK (cost_cents >= 0),
    currency char(3) NOT NULL DEFAULT 'USD',
    valid_from timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to timestamptz,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_price_range CHECK (
        valid_to IS NULL OR valid_to > valid_from
    )
);

-- =====================================================
-- INVENTORY DOMAIN
-- =====================================================

-- Warehouse locations
CREATE TABLE locations (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    code varchar(50) UNIQUE NOT NULL,
    name varchar(200) NOT NULL,
    type varchar(50) NOT NULL DEFAULT 'warehouse' CHECK (
        type IN ('warehouse', 'store', 'dropship')
    ),
    address jsonb NOT NULL,
    metadata jsonb DEFAULT '{}',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL
);

-- Inventory tracking with optimistic locking
CREATE TABLE inventory (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    product_variant_id uuid NOT NULL REFERENCES product_variants (
        id
    ) ON DELETE CASCADE,
    location_id uuid NOT NULL REFERENCES locations (id) ON DELETE CASCADE,
    quantity_available integer NOT NULL DEFAULT 0 CHECK (
        quantity_available >= 0
    ),
    quantity_reserved integer NOT NULL DEFAULT 0 CHECK (quantity_reserved >= 0),
    quantity_allocated integer NOT NULL DEFAULT 0 CHECK (
        quantity_allocated >= 0
    ),
    reorder_point integer,
    reorder_quantity integer,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    UNIQUE (product_variant_id, location_id)
);

-- =====================================================
-- ORDER DOMAIN
-- =====================================================

-- Orders table (partitioning removed due to foreign key constraints)
CREATE TABLE orders (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    order_number varchar(50) UNIQUE NOT NULL,
    customer_id uuid NOT NULL REFERENCES customers (id),
    status varchar(50) NOT NULL DEFAULT 'draft' CHECK (
        status IN (
            'draft',
            'pending',
            'confirmed',
            'processing',
            'shipped',
            'delivered',
            'cancelled',
            'refunded'
        )
    ),

    -- Address snapshots (denormalized for immutability)
    billing_address jsonb NOT NULL,
    shipping_address jsonb NOT NULL,

    -- Financial
    subtotal_cents integer NOT NULL DEFAULT 0 CHECK (subtotal_cents >= 0),
    tax_cents integer NOT NULL DEFAULT 0 CHECK (tax_cents >= 0),
    shipping_cents integer NOT NULL DEFAULT 0 CHECK (shipping_cents >= 0),
    discount_cents integer NOT NULL DEFAULT 0 CHECK (discount_cents >= 0),
    total_cents integer NOT NULL DEFAULT 0 CHECK (total_cents >= 0),
    currency char(3) NOT NULL DEFAULT 'USD',

    -- Metadata
    channel varchar(50) DEFAULT 'web' CHECK (
        channel IN ('web', 'mobile', 'api', 'phone', 'store')
    ),
    notes text,
    tags text [],
    metadata jsonb DEFAULT '{}',

    -- Timestamps
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    confirmed_at timestamptz,
    shipped_at timestamptz,
    delivered_at timestamptz,
    cancelled_at timestamptz,

    -- Version for optimistic locking
    version integer DEFAULT 1 NOT NULL
);

-- Note: Partitioning removed due to foreign key constraints
-- Consider implementing partitioning at application level or using inheritance-based partitioning

-- Order items
CREATE TABLE order_items (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    order_id uuid NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    product_variant_id uuid NOT NULL REFERENCES product_variants (id),

    -- Snapshot product info (denormalized for history)
    product_name varchar(500) NOT NULL,
    variant_name varchar(500) NOT NULL,
    sku varchar(100) NOT NULL,

    -- Quantities and pricing
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price_cents integer NOT NULL CHECK (unit_price_cents >= 0),
    discount_cents integer NOT NULL DEFAULT 0 CHECK (discount_cents >= 0),
    tax_cents integer NOT NULL DEFAULT 0 CHECK (tax_cents >= 0),
    total_cents integer NOT NULL CHECK (total_cents >= 0),

    -- Fulfillment
    fulfilled_quantity integer DEFAULT 0 CHECK (fulfilled_quantity >= 0),
    returned_quantity integer DEFAULT 0 CHECK (returned_quantity >= 0),

    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =====================================================
-- PAYMENT DOMAIN
-- =====================================================

-- Payment methods (tokenized)
CREATE TABLE payment_methods (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    customer_id uuid NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    type varchar(50) NOT NULL CHECK (
        type IN ('card', 'bank', 'paypal', 'wallet')
    ),
    provider varchar(50) NOT NULL, -- stripe, paypal, etc.
    token varchar(255) NOT NULL, -- Provider token, never store actual card numbers
    last_four varchar(4),
    brand varchar(50),
    expiry_month integer CHECK (expiry_month BETWEEN 1 AND 12),
    expiry_year integer CHECK (expiry_year >= EXTRACT(YEAR FROM NOW())),
    is_default boolean DEFAULT FALSE,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL
);

-- Payments
CREATE TABLE payments (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    order_id uuid NOT NULL REFERENCES orders (id),
    payment_method_id uuid REFERENCES payment_methods (id),
    amount_cents integer NOT NULL CHECK (amount_cents > 0),
    currency char(3) NOT NULL DEFAULT 'USD',
    status varchar(50) NOT NULL DEFAULT 'pending' CHECK (
        status IN (
            'pending',
            'processing',
            'succeeded',
            'failed',
            'cancelled',
            'refunded'
        )
    ),
    provider varchar(50) NOT NULL,
    provider_transaction_id varchar(255) UNIQUE,
    failure_reason text,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processed_at timestamptz,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    -- Idempotency key to prevent duplicate charges
    idempotency_key varchar(255) UNIQUE NOT NULL
);

-- =====================================================
-- CART DOMAIN
-- =====================================================

-- Shopping carts (with TTL support)
CREATE TABLE carts (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    session_id varchar(255) UNIQUE NOT NULL,
    customer_id uuid REFERENCES customers (id),
    status varchar(50) DEFAULT 'active' CHECK (
        status IN ('active', 'abandoned', 'converted', 'expired')
    ),
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    expires_at timestamptz DEFAULT (
        CURRENT_TIMESTAMP + interval '7 days'
    ) NOT NULL
);

-- Cart items
CREATE TABLE cart_items (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    cart_id uuid NOT NULL REFERENCES carts (id) ON DELETE CASCADE,
    product_variant_id uuid NOT NULL REFERENCES product_variants (id),
    quantity integer NOT NULL CHECK (quantity > 0),
    price_cents integer NOT NULL CHECK (price_cents >= 0),
    metadata jsonb DEFAULT '{}',
    added_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL
);

-- =====================================================
-- REVIEW DOMAIN
-- =====================================================

-- Product reviews
CREATE TABLE reviews (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    product_id uuid NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    customer_id uuid NOT NULL REFERENCES customers (id),
    order_id uuid REFERENCES orders (id), -- For verified purchase
    rating integer NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title varchar(200),
    comment text,
    is_verified_purchase boolean DEFAULT FALSE,
    helpful_count integer DEFAULT 0,
    unhelpful_count integer DEFAULT 0,
    status varchar(50) DEFAULT 'pending' CHECK (
        status IN ('pending', 'approved', 'rejected', 'deleted')
    ),
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamptz,
    is_deleted boolean DEFAULT FALSE NOT NULL,
    published_at timestamptz
);

-- =====================================================
-- INDEXES (Optimized for UUID v7)
-- =====================================================

-- Customer indexes
CREATE INDEX idx_customers_email ON customers (email);
CREATE INDEX idx_customers_status ON customers (status) WHERE status = 'active';
CREATE INDEX idx_customer_pii_customer_id ON customer_pii (customer_id);
CREATE INDEX idx_addresses_customer_id ON addresses (customer_id);
CREATE INDEX idx_addresses_default ON addresses (customer_id) WHERE is_default
= TRUE;

-- Product indexes
CREATE INDEX idx_products_sku ON products (sku);
CREATE INDEX idx_products_status ON products (status) WHERE status = 'active';
CREATE INDEX idx_products_category ON products (category_id);
CREATE INDEX idx_products_attributes ON products USING gin (attributes);
CREATE INDEX idx_products_tags ON products USING gin (tags);
CREATE INDEX idx_variants_product_id ON product_variants (product_id);
CREATE INDEX idx_variants_sku ON product_variants (sku);
CREATE INDEX idx_prices_product_variant_id ON product_prices (
    product_variant_id
);
CREATE INDEX idx_prices_valid ON product_prices (
    product_variant_id, valid_from, valid_to
);

-- Order indexes (optimized for time-based queries with UUID v7)
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_created_at ON orders (created_at);
-- CREATE INDEX idx_orders_year_month ON orders(year_month); -- Removed with generated column
CREATE INDEX idx_order_items_order_id ON order_items (order_id);
CREATE INDEX idx_order_items_product_variant_id ON order_items (
    product_variant_id
);

-- Inventory indexes
CREATE INDEX idx_inventory_variant_location ON inventory (
    product_variant_id, location_id
);
CREATE INDEX idx_inventory_low_stock ON inventory (
    product_variant_id
) WHERE quantity_available
< reorder_point;

-- Cart indexes
CREATE INDEX idx_carts_session_id ON carts (session_id);
CREATE INDEX idx_carts_customer_id ON carts (customer_id);
CREATE INDEX idx_carts_expires_at ON carts (expires_at) WHERE status = 'active';
CREATE INDEX idx_cart_items_cart_id ON cart_items (cart_id);

-- Payment indexes
CREATE INDEX idx_payments_order_id ON payments (order_id);
CREATE INDEX idx_payments_status ON payments (status);
CREATE INDEX idx_payment_methods_customer_id ON payment_methods (
    customer_id
) WHERE deleted_at IS NULL;

-- Review indexes
CREATE INDEX idx_reviews_product_id ON reviews (product_id);
CREATE INDEX idx_reviews_customer_id ON reviews (customer_id);
CREATE INDEX idx_reviews_status ON reviews (status) WHERE status = 'approved';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION UPDATE_UPDATED_AT_COLUMN()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_customer_pii_updated_at BEFORE UPDATE ON customer_pii
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_product_variants_updated_at BEFORE UPDATE ON product_variants
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_inventory_updated_at BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_carts_updated_at BEFORE UPDATE ON carts
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION UPDATE_UPDATED_AT_COLUMN();

-- Optimistic locking trigger
CREATE OR REPLACE FUNCTION INCREMENT_VERSION()
RETURNS trigger AS $$
BEGIN
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply version increment triggers
CREATE TRIGGER increment_customers_version BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION INCREMENT_VERSION();
CREATE TRIGGER increment_products_version BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION INCREMENT_VERSION();
CREATE TRIGGER increment_orders_version BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION INCREMENT_VERSION();
CREATE TRIGGER increment_inventory_version BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION INCREMENT_VERSION();
CREATE TRIGGER increment_addresses_version BEFORE UPDATE ON addresses
    FOR EACH ROW EXECUTE FUNCTION INCREMENT_VERSION();

-- =====================================================
-- ROW LEVEL SECURITY (Multi-tenancy ready)
-- =====================================================

-- Enable RLS on sensitive tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_pii ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_methods ENABLE ROW LEVEL SECURITY;

-- Example RLS policies (to be customized based on auth strategy)
-- CREATE POLICY customer_isolation ON customers
--     FOR ALL
--     TO application_user
--     USING (id = current_setting('app.current_customer_id')::uuid);

-- =====================================================
-- AUDIT TABLES
-- =====================================================

-- Audit log table
CREATE TABLE audit.audit_log (
    id uuid DEFAULT UUID_GENERATE_V7() PRIMARY KEY,
    table_name varchar(100) NOT NULL,
    record_id uuid NOT NULL,
    action varchar(20) NOT NULL CHECK (
        action IN ('INSERT', 'UPDATE', 'DELETE')
    ),
    old_data jsonb,
    new_data jsonb,
    changed_by varchar(255),
    changed_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address inet,
    user_agent text
);

CREATE INDEX idx_audit_log_table_record ON audit.audit_log (
    table_name, record_id
);
CREATE INDEX idx_audit_log_changed_at ON audit.audit_log (changed_at);

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Function to check UUID v7 validity and extract timestamp
CREATE OR REPLACE FUNCTION EXTRACT_TIMESTAMP_FROM_UUIDV7(uuid_value uuid)
RETURNS timestamptz AS $$
    SELECT to_timestamp(
        (
            ('x' || substring(uuid_value::text, 1, 8) || substring(uuid_value::text, 10, 4))::bit(48)::bigint
        )::double precision / 1000
    );
$$ LANGUAGE sql IMMUTABLE PARALLEL SAFE;

-- Sequence for order numbers
CREATE SEQUENCE order_number_seq START WITH 1;

-- Function to generate order numbers
CREATE OR REPLACE FUNCTION GENERATE_ORDER_NUMBER()
RETURNS varchar AS $$
    SELECT 'ORD-' || to_char(CURRENT_TIMESTAMP, 'YYYYMMDD') || '-' || 
           lpad(nextval('order_number_seq')::text, 6, '0');
$$ LANGUAGE sql;

-- Sequence already created above

-- =====================================================
-- AUDIT FUNCTIONS
-- =====================================================

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit.audit_trigger()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (table_name, record_id, action, new_data, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, to_jsonb(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (table_name, record_id, action, old_data, new_data, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, to_jsonb(OLD), to_jsonb(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (table_name, record_id, action, old_data, changed_by)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, to_jsonb(OLD), current_user);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE customers IS 'Core customer identity table with minimal PII';
COMMENT ON TABLE customer_pii IS 'Separated PII for GDPR compliance and data protection';
COMMENT ON TABLE orders IS 'Order table with UUID v7 for time-based ordering';
COMMENT ON TABLE inventory IS 'Real-time inventory tracking with optimistic locking';
COMMENT ON COLUMN inventory.version IS 'Optimistic lock version to prevent race conditions';
COMMENT ON FUNCTION UUID_GENERATE_V7() IS 'Generates time-ordered UUIDs for better index performance (pure SQL implementation)';
COMMENT ON FUNCTION UUID_GENERATE_V7_PRECISE() IS 'Generates UUID v7 with sub-millisecond precision for high-throughput scenarios';
COMMENT ON FUNCTION EXTRACT_TIMESTAMP_FROM_UUIDV7(
    uuid
) IS 'Extracts creation timestamp from UUID v7 values';
