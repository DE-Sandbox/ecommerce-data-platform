#!/bin/bash
# Test database initialization

set -e

echo "Starting PostgreSQL container..."
docker-compose up -d postgres

echo "Waiting for PostgreSQL to be healthy..."
timeout 60 bash -c 'until docker-compose ps postgres | grep -q "healthy"; do sleep 2; done'

echo "Running database initialization tests..."
uv run pytest tests/test_database_init.py -v

echo "Tests completed!"