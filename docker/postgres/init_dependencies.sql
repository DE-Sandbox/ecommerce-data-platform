-- PostgreSQL Dependencies Setup
-- This file sets up required extensions and schemas
-- Functions, triggers, and tables are managed by Alembic migrations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ecommerce;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS archive;

-- Set default search path
SET search_path TO ecommerce, public;