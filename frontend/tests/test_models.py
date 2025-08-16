"""Tests for app.models module."""

import pytest
from datetime import datetime
from typing import Dict, Any

from app.models import WebAppState
from src.core.models import ScheduleState, SchedulerStrategy


class TestWebAppState:
    """Test cases for WebAppState model."""
    
    def test_web_app_state_creation_defaults(self) -> None:
        """Test WebAppState creation with default values."""
        state = WebAppState()
        
        assert state.current_schedule is None
        assert state.available_strategies is not None
        assert len(state.available_strategies) > 0
        assert SchedulerStrategy.GREEDY in state.available_strategies
        assert state.config_path == "config.json"
    
    def test_web_app_state_creation_custom(self, empty_config) -> None:
        """Test WebAppState creation with custom values."""
        mock_schedule = ScheduleState(
            schedule={},
            config=empty_config,
            strategy=SchedulerStrategy.GREEDY,
            timestamp=datetime.now().isoformat()
        )
        
        custom_strategies = [SchedulerStrategy.GREEDY, SchedulerStrategy.OPTIMAL]
        custom_config_path = "custom_config.json"
        
        state = WebAppState(
            current_schedule=mock_schedule,
            available_strategies=custom_strategies,
            config_path=custom_config_path
        )
        
        assert state.current_schedule == mock_schedule
        assert state.available_strategies == custom_strategies
        assert state.config_path == custom_config_path
    
    def test_web_app_state_init_sets_default_strategies(self) -> None:
        """Test that __init__ sets default strategies when None."""
        state = WebAppState(available_strategies=None)
        
        assert state.available_strategies is not None
        assert len(state.available_strategies) > 0
        assert all(isinstance(s, SchedulerStrategy) for s in state.available_strategies)
    
    def test_web_app_state_with_schedule(self, empty_config) -> None:
        """Test WebAppState with a schedule."""
        mock_schedule = ScheduleState(
            schedule={"paper1": "2024-01-01"},
            config=empty_config,
            strategy=SchedulerStrategy.GREEDY,
            timestamp=datetime.now().isoformat()
        )
        
        state = WebAppState(current_schedule=mock_schedule)
        
        assert state.current_schedule == mock_schedule
        assert state.current_schedule.schedule == {"paper1": "2024-01-01"}
        assert state.current_schedule.strategy == SchedulerStrategy.GREEDY
    
    def test_web_app_state_serialization(self) -> None:
        """Test WebAppState serialization methods."""
        state = WebAppState(config_path="test_config.json")
        
        # Test to_dict
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["config_path"] == "test_config.json"
        
        # Test from_dict
        new_state = WebAppState.from_dict(state_dict)
        assert new_state.config_path == "test_config.json"
        assert new_state.available_strategies is not None
    
    def test_web_app_state_field_modification(self) -> None:
        """Test that WebAppState fields can be modified."""
        state = WebAppState()
        
        # Should be able to modify fields
        state.config_path = "new_config.json"
        
        assert state.config_path == "new_config.json"
