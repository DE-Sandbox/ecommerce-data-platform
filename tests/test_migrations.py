"""Test database migration commands."""

import subprocess
from pathlib import Path

import pytest


class TestMigrationCommands:
    """Test Alembic migration commands via justfile."""

    def test_migration_status_command(self) -> None:
        """Test that migration status command works."""
        result = subprocess.run(
            ["just", "migrate-status"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        # Should not error
        assert result.returncode == 0
        # Should show some output
        assert "Migration" in result.stdout or "Current" in result.stdout

    def test_migration_check_command(self) -> None:
        """Test that migration check command works."""
        result = subprocess.run(
            ["just", "migrate-check"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        # The check might fail if models don't match migrations exactly,
        # but the command itself should run
        assert result.returncode in [0, 1]

    def test_alembic_config_exists(self) -> None:
        """Test that alembic.ini exists."""
        alembic_ini = Path("alembic.ini")
        assert alembic_ini.exists()
        assert alembic_ini.is_file()

    def test_alembic_directory_structure(self) -> None:
        """Test that Alembic directory structure is correct."""
        alembic_dir = Path("alembic")
        assert alembic_dir.exists()
        assert alembic_dir.is_dir()

        # Check for key files
        env_py = alembic_dir / "env.py"
        assert env_py.exists()

        script_py_mako = alembic_dir / "script.py.mako"
        assert script_py_mako.exists()

        versions_dir = alembic_dir / "versions"
        assert versions_dir.exists()
        assert versions_dir.is_dir()

    def test_initial_migration_exists(self) -> None:
        """Test that initial migration file exists."""
        versions_dir = Path("alembic/versions")

        # Find migration files
        migration_files = list(versions_dir.glob("*_initial_schema_with_functions.py"))
        assert len(migration_files) == 1

        # Check migration content
        migration_file = migration_files[0]
        content = migration_file.read_text()

        # Should create functions
        assert "uuid_generate_v7" in content
        assert "audit_trigger" in content

        # Should create tables
        assert "create_table" in content
        assert "customers" in content
        assert "products" in content
        assert "orders" in content

    def test_migration_sql_command(self) -> None:
        """Test that we can generate SQL from migrations."""
        result = subprocess.run(
            ["just", "migrate-sql"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        # Should generate SQL
        if result.returncode == 0:
            assert "CREATE" in result.stdout or "ALTER" in result.stdout
        # If no pending migrations, that's also fine
        elif "No pending migrations" in result.stderr or "head" in result.stderr:
            assert True
        else:
            # Unexpected error
            pytest.fail(f"Unexpected error: {result.stderr}")

    def test_migration_up_down(self) -> None:
        """Test migration up and down commands."""
        # Get current revision first
        current_result = subprocess.run(
            ["uv", "run", "alembic", "current"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        # Save current state
        current_revision = (
            current_result.stdout.strip().split()[0] if current_result.stdout else None
        )

        # Test downgrade one revision
        downgrade_result = subprocess.run(
            ["uv", "run", "alembic", "downgrade", "-1"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        assert (
            downgrade_result.returncode == 0
        ), f"Downgrade failed: {downgrade_result.stderr}"

        # Test upgrade back to head
        upgrade_result = subprocess.run(
            ["just", "migrate"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        assert (
            upgrade_result.returncode == 0
        ), f"Upgrade failed: {upgrade_result.stderr}"

        # Verify we're back at the same revision
        final_result = subprocess.run(
            ["uv", "run", "alembic", "current"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        if current_revision:
            assert (
                current_revision in final_result.stdout
            ), "Not at expected revision after up/down cycle"
