"""Test database initialization and schema creation."""

import time
from typing import Generator

import pytest
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.exc import OperationalError

from src.core.config import ConfigLoader, get_database_url


@pytest.fixture(scope="module")
def db_engine() -> Generator[Engine, None, None]:
    """Create database engine with connection retry logic.
    
    This fixture runs once per module (before all tests in this file).
    """
    url = get_database_url("development")
    engine = create_engine(url)
    
    # Wait for database to be ready (Docker startup)
    max_retries = 5
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                break
        except OperationalError:
            if i == max_retries - 1:
                raise
            time.sleep(2)
    
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def db_config() -> dict[str, any]:
    """Load database configuration from YAML."""
    loader = ConfigLoader()
    return loader.load("database", "development")


class TestDatabaseInitialization:
    """Test that database is properly initialized with schema."""

    def test_database_connection(self, db_engine: Engine) -> None:
        """Test that we can connect to the database."""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_schemas_exist(self, db_engine: Engine, db_config: dict[str, any]) -> None:
        """Test that all required schemas from config are created."""
        # Get expected schemas from configuration
        expected_schemas = {
            schema["name"] 
            for schema in db_config["schema"]["schemas"]
        }
        
        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = ANY(:schemas)"
                ),
                {"schemas": list(expected_schemas)}
            )
            actual_schemas = {row[0] for row in result}
            
            missing_schemas = expected_schemas - actual_schemas
            assert not missing_schemas, f"Missing schemas: {missing_schemas}"

    def test_uuid_v7_function_exists(self, db_engine: Engine) -> None:
        """Test that UUID v7 function is created."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT routine_name FROM information_schema.routines "
                    "WHERE routine_name = 'uuid_generate_v7' "
                    "AND routine_schema = 'public'"
                )
            )
            functions = [row[0] for row in result]
            
            assert "uuid_generate_v7" in functions

    def test_all_tables_exist(self, db_engine: Engine, db_config: dict[str, any]) -> None:
        """Test that all tables from config are created."""
        # Get expected tables from configuration
        expected_tables_by_schema = db_config["schema"]["tables"]
        
        inspector = inspect(db_engine)
        
        # Check each schema has its expected tables
        for schema, expected_tables in expected_tables_by_schema.items():
            if not expected_tables:  # Skip empty schemas like archive
                continue
                
            actual_tables = set(inspector.get_table_names(schema=schema))
            expected_set = set(expected_tables)
            
            missing_tables = expected_set - actual_tables
            assert not missing_tables, f"Missing tables in {schema}: {missing_tables}"

    def test_table_structure(self, db_engine: Engine) -> None:
        """Test that tables have correct structure with UUID v7 defaults."""
        inspector = inspect(db_engine)
        
        # Check customers table structure as an example
        columns = inspector.get_columns("customers", schema="ecommerce")
        column_dict = {col["name"]: col for col in columns}
        
        # Check standard columns that should exist on most tables
        assert "id" in column_dict
        assert "UUID" in str(column_dict["id"]["type"])
        assert column_dict["id"]["default"] is not None
        
        # Check audit columns
        assert "created_at" in column_dict
        assert "updated_at" in column_dict
        assert "deleted_at" in column_dict
        assert "is_deleted" in column_dict

    def test_indexes_exist(self, db_engine: Engine) -> None:
        """Test that performance indexes are created."""
        inspector = inspect(db_engine)
        
        # Check orders table indexes as an example
        indexes = inspector.get_indexes("orders", schema="ecommerce")
        index_names = {idx["name"] for idx in indexes}
        
        # Should have indexes on commonly queried fields
        expected_indexes = {
            "idx_orders_customer_id",
            "idx_orders_status",
            "idx_orders_created_at"
        }
        
        missing_indexes = expected_indexes - index_names
        assert not missing_indexes, f"Missing indexes: {missing_indexes}"

    def test_foreign_keys_exist(self, db_engine: Engine) -> None:
        """Test that foreign key constraints are properly set up."""
        inspector = inspect(db_engine)
        
        # Check order_items foreign keys
        fks = inspector.get_foreign_keys("order_items", schema="ecommerce")
        fk_columns = {fk["constrained_columns"][0] for fk in fks}
        
        assert "order_id" in fk_columns
        assert "product_variant_id" in fk_columns

    def test_audit_trigger_functions(self, db_engine: Engine) -> None:
        """Test that audit trigger functions are created."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT routine_name FROM information_schema.routines "
                    "WHERE routine_name LIKE 'audit_%' "
                    "AND routine_schema = 'audit'"
                )
            )
            functions = [row[0] for row in result]
            
            assert "audit_trigger" in functions

    def test_database_matches_config(self, db_engine: Engine, db_config: dict[str, any]) -> None:
        """Test that database name matches configuration."""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            current_db = result.scalar()
            
            assert current_db == db_config["database"]