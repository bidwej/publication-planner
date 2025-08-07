"""Pytest configuration and shared fixtures for all tests."""

import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture
def test_root_dir():
    """Fixture to provide the test root directory."""
    return Path(__file__).parent


@pytest.fixture
def project_root_dir():
    """Fixture to provide the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture to provide a temporary directory for testing."""
    return tmp_path