-- This script is run when the PostgreSQL container is first created
-- It sources our main schema file

-- Create development database if it doesn't exist
SELECT 'CREATE DATABASE ecommerce_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ecommerce_dev')\gexec

-- Connect to the development database
\c ecommerce_dev

-- Run our main schema
\i /docker-entrypoint-initdb.d/001_initial_schema.sql