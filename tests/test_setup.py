"""Test to verify the project setup is working correctly."""

import sys

import src


def test_import() -> None:
    """Test that we can import the main package."""
    assert src.__version__ == "0.1.0"


def test_environment() -> None:
    """Test that the environment is set up correctly."""
    assert sys.version_info >= (3, 11)
