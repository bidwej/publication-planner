"""Pytest configuration for Dash app tests."""

import pytest
from pathlib import Path
import sys

# Add the backend tests directories to the path so we can import from them
backend_tests_dir = Path(__file__).parent.parent.parent / "backend" / "tests"
backend_src_tests_dir = Path(__file__).parent.parent.parent / "backend" / "tests" / "src"
sys.path.insert(0, str(backend_tests_dir))
sys.path.insert(0, str(backend_src_tests_dir))

# Import core fixtures from backend tests
from conftest import (
    test_root_dir,
    project_root_dir, 
    temp_dir,
    create_mock_submission,
    create_flexible_submission,
    create_mock_conference,
    create_mock_config,
    empty_config,
    empty_schedule
)

# Import fixtures from backend src tests
from conftest import (
    test_data_dir,
    test_config_path,
    config,
    mock_schedule_summary,
    sample_schedule
)

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
    'test_root_dir',
    'project_root_dir', 
    'temp_dir',
    'create_mock_submission',
    'create_flexible_submission',
    'create_mock_conference',
    'create_mock_config',
    'empty_config',
    'empty_schedule',
    'test_data_dir',
    'test_config_path',
    'config',
    'mock_schedule_summary',
    'sample_schedule',
    'dash_app_dir',
    'dash_components_dir'
]
