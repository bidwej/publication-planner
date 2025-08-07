"""Pytest configuration and shared fixtures for app tests."""

import pytest
import json
from unittest.mock import Mock


@pytest.fixture
def mock_dash_app():
    """Fixture to provide a mock Dash app for testing."""
    mock_app = Mock()
    mock_app.layout = Mock()
    mock_app.callback = Mock()
    mock_app.run_server = Mock()
    return mock_app


@pytest.fixture
def sample_schedule_data():
    """Fixture to provide sample schedule data for testing."""
    return {
        "paper1": "2024-05-01",
        "paper2": "2024-07-01",
        "paper3": "2024-06-15"
    }


@pytest.fixture
def sample_config_data():
    """Fixture to provide sample config data for testing."""
    return {
        "min_abstract_lead_time_days": 30,
        "min_paper_lead_time_days": 90,
        "max_concurrent_submissions": 3,
        "priority_weights": {
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        },
        "penalty_costs": {
            "default_mod_penalty_per_day": 1000
        }
    }


@pytest.fixture
def mock_storage():
    """Fixture to provide a mock storage object for testing."""
    mock_storage = Mock()
    mock_storage.load_config.return_value = sample_config_data()
    mock_storage.load_schedule.return_value = sample_schedule_data()
    mock_storage.save_schedule = Mock()
    mock_storage.save_config = Mock()
    return mock_storage


@pytest.fixture
def temp_config_file(tmp_path):
    """Fixture to provide a temporary config file for testing."""
    config_data = {
        "min_abstract_lead_time_days": 30,
        "min_paper_lead_time_days": 90,
        "max_concurrent_submissions": 3,
        "priority_weights": {
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        },
        "penalty_costs": {
            "default_mod_penalty_per_day": 1000
        }
    }
    
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    return str(config_file)


@pytest.fixture
def mock_planner():
    """Fixture to provide a mock planner object for testing."""
    mock_planner = Mock()
    mock_planner.generate_schedule.return_value = sample_schedule_data()
    mock_planner.get_schedule_summary.return_value = {
        "total_submissions": 3,
        "schedule_span": 90,
        "penalty_score": 150.50,
        "quality_score": 0.85,
        "efficiency_score": 0.78
    }
    return mock_planner
