"""Test configuration loader functionality."""

from pathlib import Path

import pytest
import yaml

from src.core.config import (
    ConfigLoader,
    ConfigValidationError,
    get_config,
    get_database_url,
    is_feature_enabled,
)


class TestConfigLoader:
    """Test configuration loading and environment variable substitution."""

    def test_load_database_config(self) -> None:
        """Test loading database configuration."""
        loader = ConfigLoader()
        config = loader.load("database", "development")

        assert config["engine"] == "postgresql"
        assert config["database"] == "ecommerce_dev"
        # Check schema names
        schema_names = [s["name"] for s in config["schema"]["schemas"]]
        assert schema_names == ["ecommerce", "audit", "archive"]

    def test_environment_variable_substitution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables are properly substituted."""
        # Set test environment variables
        monkeypatch.setenv("DB_HOST", "test-host")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("DB_USER", "test-user")

        loader = ConfigLoader()
        loader.reload()  # Clear cache
        config = loader.load("database", "development")

        assert config["host"] == "test-host"
        assert config["port"] == "5433"
        assert config["username"] == "test-user"

    def test_default_values(self) -> None:
        """Test that default values work when env vars not set."""
        loader = ConfigLoader()
        config = loader.load("database", "development")

        # Should use defaults from YAML
        assert config["host"] == "localhost"
        assert config["port"] == "5432"

    def test_get_nested_config(self) -> None:
        """Test getting nested configuration values."""
        loader = ConfigLoader()

        # Test nested access
        schemas = loader.get("database", "schema.schemas")
        assert isinstance(schemas, list)
        assert "ecommerce" in [s["name"] for s in schemas]

        # Test default value for non-existent key
        missing = loader.get("database", "non.existent.key", "default-value")
        assert missing == "default-value"

    def test_database_url_generation(self) -> None:
        """Test database URL generation."""
        url = get_database_url("development")
        assert url == "postgresql://postgres:postgres@localhost:5432/ecommerce_dev"

    def test_feature_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test feature flag checking."""
        # Clear any existing environment variables
        monkeypatch.delenv("FEATURE_SDV", raising=False)

        # Test default values
        loader = ConfigLoader()
        loader.reload()  # Clear cache
        assert is_feature_enabled("mimesis_engine") is True
        assert is_feature_enabled("sdv_integration") is False

        # Test with environment override
        monkeypatch.setenv("FEATURE_SDV", "true")
        loader.reload()  # Clear cache again

        # Need to reload the global config instance too
        get_config.cache_clear()

        assert is_feature_enabled("sdv_integration") is True

    def test_multiple_environments(self) -> None:
        """Test loading different environments."""
        loader = ConfigLoader()

        # Development config
        dev_config = loader.load("database", "development")
        assert dev_config["database"] == "ecommerce_dev"
        assert dev_config["log_queries"] is True

        # Test config
        test_config = loader.load("database", "test")
        assert test_config["database"] == "ecommerce_test"
        assert test_config["log_queries"] is False

        # Production config
        prod_config = loader.load("database", "production")
        assert prod_config["database"] == "ecommerce_prod"
        assert prod_config["pool_size"] == "20"

    def test_boolean_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that boolean strings are properly parsed."""
        monkeypatch.setenv("APP_DEBUG", "false")
        monkeypatch.setenv("FEATURE_STREAMING", "true")

        loader = ConfigLoader()
        loader.reload()

        app_config = loader.load("application")
        assert app_config["app"]["debug"] is False
        assert is_feature_enabled("stream_processing") is True


class TestConfigValidation:
    """Test configuration validation and error handling."""

    def test_missing_config_file(self) -> None:
        """Test error when config file doesn't exist."""
        loader = ConfigLoader()

        with pytest.raises(FileNotFoundError):
            loader.load("non_existent_config")

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        """Test error handling for invalid YAML."""
        # Create invalid YAML file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        invalid_yaml = config_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content:")

        loader = ConfigLoader(config_dir)

        with pytest.raises(yaml.YAMLError):
            loader.load("invalid")

    def test_validate_required_fields(self) -> None:
        """Test that required fields are validated."""
        loader = ConfigLoader()

        # Test with actual config - should pass
        required_fields = ["host", "port", "database", "username", "password"]
        loader.validate_required_fields("database", required_fields)

        # Test with missing field - should fail
        with pytest.raises(ConfigValidationError, match="Missing required field: api_key"):
            loader.validate_required_fields("database", [*required_fields, "api_key"])

    def test_validate_field_types(self) -> None:
        """Test that field types are validated."""
        loader = ConfigLoader()

        # Define expected types
        field_types = {
            "port": int,
            "host": str,
            "ssl_mode": str,
            "pool_size": int
        }

        # This should validate types correctly
        config = loader.load("database", "test")

        # Should not raise for valid config
        loader.validate_field_types(config, field_types)

        # Should raise for invalid type
        bad_config = {"port": "not-a-number"}
        with pytest.raises(ConfigValidationError, match="Invalid type for field 'port'"):
            loader.validate_field_types(bad_config, field_types)

    def test_validate_port_range(self) -> None:
        """Test that port numbers are in valid range."""
        loader = ConfigLoader()

        # Valid port
        loader.validate_port(5432)

        # Invalid ports
        with pytest.raises(ConfigValidationError, match="Port must be between 1 and 65535"):
            loader.validate_port(0)

        with pytest.raises(ConfigValidationError, match="Port must be between 1 and 65535"):
            loader.validate_port(70000)

    def test_validate_enum_fields(self) -> None:
        """Test that enum fields only accept valid values."""
        loader = ConfigLoader()

        # Define valid values
        valid_environments = ["development", "test", "production"]

        # Should pass for valid value
        loader.validate_enum("environment", "development", valid_environments)

        # Should fail for invalid value
        with pytest.raises(ConfigValidationError, match="Invalid value 'staging' for field 'environment'"):
            loader.validate_enum("environment", "staging", valid_environments)

