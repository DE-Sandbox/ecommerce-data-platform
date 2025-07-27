-- This script is run when the PostgreSQL container is first created
-- It sets up database dependencies only - tables are managed by Alembic

-- Create development database if it doesn't exist
SELECT 'CREATE DATABASE ecommerce_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ecommerce_dev')\gexec

-- Connect to the main database for dependencies
\c ecommerce

-- Set up extensions, functions, and schemas
\i /docker-entrypoint-initdb.d/init_dependencies.sql

-- Connect to the development database
\c ecommerce_dev

-- Set up extensions, functions, and schemas for dev database too
\i /docker-entrypoint-initdb.d/init_dependencies.sql