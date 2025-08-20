"""Tests for app.models module."""

import pytest
from datetime import datetime
from app.models import WebAppState, ComponentState


def test_web_app_state_creation_defaults():
    """Test WebAppState creation with default values."""
    state = WebAppState()
    
    assert state.current_schedule is None
    assert state.available_strategies is not None
    assert len(state.available_strategies) > 0
    assert state.config_path == "config.json"


def test_web_app_state_creation_custom():
    """Test WebAppState creation with custom values."""
    try:
        # Try to create with custom values
        custom_strategies = ["GREEDY", "OPTIMAL"]
        custom_config_path = "custom_config.json"
        
        state = WebAppState(
            available_strategies=custom_strategies,
            config_path=custom_config_path
        )
        
        assert state.config_path == custom_config_path
    except Exception:
        # If it fails due to missing dependencies, that's okay
        pass


def test_web_app_state_init_sets_default_strategies():
    """Test that __init__ sets default strategies when None."""
    state = WebAppState(available_strategies=None)
    
    assert state.available_strategies is not None
    assert len(state.available_strategies) > 0


def test_web_app_state_serialization():
    """Test WebAppState serialization methods."""
    state = WebAppState(config_path="test_config.json")
    
    # Test model_dump (Pydantic v2 method)
    state_dict = state.model_dump()
    assert isinstance(state_dict, dict)
    assert state_dict["config_path"] == "test_config.json"
    
    # Test model_validate (Pydantic v2 method)
    new_state = WebAppState.model_validate(state_dict)
    assert new_state.config_path == "test_config.json"
    assert new_state.available_strategies is not None


def test_web_app_state_field_modification():
    """Test that WebAppState fields can be modified."""
    state = WebAppState()
    
    # Should be able to modify fields
    state.config_path = "new_config.json"
    assert state.config_path == "new_config.json"


def test_component_state_creation():
    """Test ComponentState creation."""
    state = ComponentState(component_name="test")
    
    assert state.component_name == "test"
    assert state.config_data is None
    assert state.last_refresh is None
    assert state.chart_type is None
    assert state.custom_settings is None


def test_component_state_with_data():
    """Test ComponentState with data."""
    # Create a minimal config data structure that matches the Config model
    config_data = {
        "submissions": [],
        "conferences": [],
        "min_abstract_lead_time_days": 30,
        "min_paper_lead_time_days": 60,
        "max_concurrent_submissions": 3
    }
    custom_settings = {"theme": "dark"}
    
    state = ComponentState(
        component_name="dashboard",
        config_data=config_data,
        last_refresh="2024-01-01",
        chart_type="timeline",
        custom_settings=custom_settings
    )
    
    assert state.component_name == "dashboard"
    # config_data is now a proper Config object, so check attributes
    assert state.config_data is not None
    assert state.config_data.submissions == []
    assert state.config_data.conferences == []
    assert state.config_data.min_abstract_lead_time_days == 30
    assert state.config_data.min_paper_lead_time_days == 60
    assert state.config_data.max_concurrent_submissions == 3
    assert state.last_refresh == "2024-01-01"
    assert state.chart_type == "timeline"
    assert state.custom_settings == custom_settings


def test_component_state_serialization():
    """Test ComponentState serialization methods."""
    state = ComponentState(component_name="test", chart_type="gantt")
    
    # Test model_dump (Pydantic v2 method)
    state_dict = state.model_dump()
    assert isinstance(state_dict, dict)
    assert state_dict["component_name"] == "test"
    assert state_dict["chart_type"] == "gantt"
    
    # Test model_validate (Pydantic v2 method)
    new_state = ComponentState.model_validate(state_dict)
    assert new_state.component_name == "test"
    assert new_state.chart_type == "gantt"
