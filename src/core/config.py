"""Configuration management module.

Loads configuration from YAML files with environment variable substitution.
"""

import os
import re
from functools import cache
from pathlib import Path
from typing import Final

import yaml

# Type definitions for configuration values
type ConfigValue = str | int | float | bool | list[ConfigValue] | dict[str, ConfigValue] | None
type ConfigDict = dict[str, ConfigValue]

# Constants
MAX_PORT: Final[int] = 65535
MIN_PORT: Final[int] = 1


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""



class ConfigLoader:
    """Load and manage application configuration."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize configuration loader.

        Args:
            config_dir: Directory containing configuration files.
                       Defaults to project_root/config

        """
        if config_dir is None:
            # Find project root (where pyproject.toml is)
            current = Path(__file__).resolve()
            while current != current.parent:
                if (current / "pyproject.toml").exists():
                    config_dir = current / "config"
                    break
                current = current.parent
            else:
                config_dir = Path("config")

        self.config_dir = Path(config_dir)
        self._cache: dict[str, ConfigDict] = {}

    def _substitute_env_vars(self, value: ConfigValue) -> ConfigValue:
        """Recursively substitute environment variables in configuration values.

        Supports ${VAR_NAME:-default_value} syntax.

        Args:
            value: Configuration value to process

        Returns:
            Value with environment variables substituted

        """
        if isinstance(value, str):
            # Pattern to match ${VAR:-default}
            pattern = re.compile(r"\$\{([^}]+)\}")

            def replacer(match: re.Match[str]) -> str:
                var_expr = match.group(1)
                if ":-" in var_expr:
                    var_name, default = var_expr.split(":-", 1)
                    return os.environ.get(var_name.strip(), default)
                return os.environ.get(var_expr, match.group(0))

            # Handle boolean strings
            result = pattern.sub(replacer, value)
            if result.lower() in ("true", "false"):
                return result.lower() == "true"
            return result

        if isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._substitute_env_vars(v) for v in value]

        return value

    def load(self, config_name: str, environment: str | None = None) -> ConfigDict:
        """Load configuration from YAML file.

        Args:
            config_name: Name of configuration file (without .yaml extension)
            environment: Environment to load (e.g., 'development', 'production')
                        If None, uses APP_ENV or defaults to 'development'

        Returns:
            Configuration dictionary with environment variables substituted

        """
        cache_key = f"{config_name}:{environment}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        config_file = self.config_dir / f"{config_name}.yaml"
        if not config_file.exists():
            msg = f"Configuration file not found: {config_file}"
            raise FileNotFoundError(msg)

        with config_file.open() as f:
            config = yaml.safe_load(f)

        # Apply environment-specific overrides
        if environment is None:
            environment = os.environ.get("APP_ENV", "development")

        # Get base configuration
        result = config.get("default", {}).copy()

        # Apply environment-specific configuration
        if environment in config:
            result.update(config[environment])

        # Add non-environment sections
        for key, value in config.items():
            if key not in ["default", "development", "test", "production", "localstack"]:
                result[key] = value

        # Substitute environment variables
        result = self._substitute_env_vars(result)  # type: ignore[assignment]

        # Cache the result (we know result is a dict at this point)
        self._cache[cache_key] = result  # type: ignore[assignment]

        return result  # type: ignore[return-value]

    def get(self, config_name: str, key_path: str, default: ConfigValue = None) -> ConfigValue:
        """Get a specific configuration value using dot notation.

        Args:
            config_name: Name of configuration file
            key_path: Dot-separated path to configuration value (e.g., 'api.rate_limit.enabled')
            default: Default value if key not found

        Returns:
            Configuration value or default

        """
        config = self.load(config_name)

        keys = key_path.split(".")
        value: ConfigValue = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def reload(self) -> None:
        """Clear configuration cache to force reload."""
        self._cache.clear()

    def validate_required_fields(self, config_name: str, required_fields: list[str]) -> None:
        """Validate that all required fields are present in configuration.

        Args:
            config_name: Name of configuration to validate
            required_fields: List of required field names

        Raises:
            ConfigValidationError: If required field is missing

        """
        config = self.load(config_name)
        for field in required_fields:
            if field not in config:
                msg = f"Missing required field: {field}"
                raise ConfigValidationError(msg)

    def validate_field_types(self, config: ConfigDict, field_types: dict[str, type]) -> None:
        """Validate that fields have correct types.

        Args:
            config: Configuration dictionary to validate
            field_types: Mapping of field names to expected types

        Raises:
            ConfigValidationError: If field has incorrect type

        """
        for field, expected_type in field_types.items():
            if field in config:
                value = config[field]
                # Handle string to int conversion from environment variables
                if expected_type is int and isinstance(value, str) and value.isdigit():
                    continue
                if not isinstance(value, expected_type):
                    msg = f"Invalid type for field '{field}': expected {expected_type.__name__}, got {type(value).__name__}"
                    raise ConfigValidationError(msg)

    def validate_port(self, port: int | str) -> None:
        """Validate that port number is in valid range.

        Args:
            port: Port number to validate

        Raises:
            ConfigValidationError: If port is invalid

        """
        port_num = int(port) if isinstance(port, str) else port
        if not MIN_PORT <= port_num <= MAX_PORT:
            msg = f"Port must be between {MIN_PORT} and {MAX_PORT}"
            raise ConfigValidationError(msg)

    def validate_enum(self, field_name: str, value: str, valid_values: list[str]) -> None:
        """Validate that field value is in allowed set.

        Args:
            field_name: Name of field being validated
            value: Value to validate
            valid_values: List of allowed values

        Raises:
            ConfigValidationError: If value is not allowed

        """
        if value not in valid_values:
            msg = f"Invalid value '{value}' for field '{field_name}'. Must be one of: {', '.join(valid_values)}"
            raise ConfigValidationError(msg)


# Global configuration instance
@cache
def get_config() -> ConfigLoader:
    """Get global configuration loader instance."""
    return ConfigLoader()


# Convenience functions
def load_database_config(environment: str | None = None) -> ConfigDict:
    """Load database configuration."""
    return get_config().load("database", environment)


def load_application_config(environment: str | None = None) -> ConfigDict:
    """Load application configuration."""
    return get_config().load("application", environment)


def get_database_url(environment: str | None = None) -> str:
    """Get database connection URL."""
    config = load_database_config(environment)

    return (
        f"postgresql://{config['username']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )


def get_s3_config() -> ConfigDict:
    """Get S3 configuration."""
    result = get_config().get("application", "storage.s3", {})
    if isinstance(result, dict):
        return result
    return {}


def get_redis_config() -> ConfigDict:
    """Get Redis configuration."""
    result = get_config().get("application", "cache.redis", {})
    if isinstance(result, dict):
        return result
    return {}


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature flag is enabled."""
    result = get_config().get("application", f"features.{feature_name}", False)
    return bool(result)
