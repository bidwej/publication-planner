"""Pytest configuration for Dash app tests."""

import pytest
from pathlib import Path

# Dash-specific fixtures
@pytest.fixture
def dash_app_dir() -> Path:
    """Fixture to provide the Dash app directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def dash_components_dir() -> Path:
    """Fixture to provide the Dash components directory."""
    return Path(__file__).parent.parent / "components"

# Re-export all core fixtures so they're available in Dash tests
__all__ = [
    'dash_app_dir',
    'dash_components_dir'
]
