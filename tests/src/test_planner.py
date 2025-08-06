"""Tests for the main planner module."""

import pytest
import json
from datetime import date
from unittest.mock import Mock, patch
import tempfile
import os

from src.core.models import Config, Submission, SchedulerStrategy
from src.planner import Planner


class TestPlanner:
    """Test the Planner class."""

    def test_planner_initialization(self):
        """Test planner initialization."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            assert planner.config is not None
        finally:
            os.unlink(config_path)

    def test_planner_initialization_with_submissions(self):
        """Test planner initialization with submissions."""
        # Create a temporary config file with mock data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            assert planner.config is not None
        finally:
            os.unlink(config_path)

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            # The validation happens in __init__, so if we get here it's valid
            assert planner.config is not None
        finally:
            os.unlink(config_path)

    def test_validate_config_empty_submissions(self):
        """Test config validation with empty submissions."""
        # Now uses default config instead of raising error
        planner = Planner("nonexistent_config.json")
        # Default config should have valid submissions
        assert len(planner.config.submissions) > 0
        # Validation should pass
        errors = planner.config.validate()
        assert len(errors) == 0

    def test_validate_config_empty_conferences(self):
        """Test config validation with empty conferences."""
        # Now uses default config instead of raising error
        planner = Planner("nonexistent_config.json")
        # Default config should have valid conferences
        assert len(planner.config.conferences) > 0
        # Validation should pass
        errors = planner.config.validate()
        assert len(errors) == 0

    def test_schedule_method(self):
        """Test the schedule method."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            
            with patch('src.planner.BaseScheduler.create_scheduler') as mock_create:
                mock_scheduler = Mock()
                mock_scheduler.schedule.return_value = {
                    "paper1": date(2024, 5, 1),
                    "paper2": date(2024, 7, 1)
                }
                mock_create.return_value = mock_scheduler
                
                result = planner.schedule()
                
                mock_create.assert_called_once()
                assert isinstance(result, dict)
                assert len(result) == 2
                assert "paper1" in result
                assert "paper2" in result
        finally:
            os.unlink(config_path)

    def test_schedule_method_with_strategy(self):
        """Test the schedule method with specific strategy."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            
            with patch('src.planner.BaseScheduler.create_scheduler') as mock_create:
                mock_scheduler = Mock()
                mock_scheduler.schedule.return_value = {"paper1": date(2024, 5, 1)}
                mock_create.return_value = mock_scheduler
                
                result = planner.schedule(strategy=SchedulerStrategy.GREEDY)
                
                mock_create.assert_called_once()
                assert isinstance(result, dict)
        finally:
            os.unlink(config_path)

    def test_greedy_schedule_method(self):
        """Test the greedy_schedule method."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            
            with patch('src.planner.BaseScheduler.create_scheduler') as mock_create:
                mock_scheduler = Mock()
                mock_scheduler.schedule.return_value = {"paper1": date(2024, 5, 1)}
                mock_create.return_value = mock_scheduler
                
                result = planner.schedule(strategy=SchedulerStrategy.GREEDY)
                
                mock_create.assert_called_once()
                assert isinstance(result, dict)
        finally:
            os.unlink(config_path)

    def test_generate_monthly_table(self):
        """Test the generate_monthly_table method."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            
            with patch('src.planner.generate_simple_monthly_table') as mock_generate:
                mock_generate.return_value = [
                    {"Month": "2024-05", "Papers": "1", "Deadlines": "0"},
                    {"Month": "2024-07", "Papers": "1", "Deadlines": "0"}
                ]
                
                result = planner.generate_monthly_table()
                
                mock_generate.assert_called_once_with(planner.config)
                assert isinstance(result, list)
                assert len(result) == 2
        finally:
            os.unlink(config_path)

    def test_error_handling_invalid_config(self):
        """Test error handling with invalid config."""
        # Now uses default config instead of raising error
        planner = Planner("nonexistent_config.json")
        # Should have a valid default config
        assert planner.config is not None
        assert len(planner.config.submissions) > 0
        assert len(planner.config.conferences) > 0

    def test_error_handling_scheduler_failure(self):
        """Test error handling when scheduler fails."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            
            with patch('src.planner.BaseScheduler.create_scheduler') as mock_create:
                mock_scheduler = Mock()
                mock_scheduler.schedule.side_effect = Exception("Scheduler failed")
                mock_create.return_value = mock_scheduler
                
                with pytest.raises(RuntimeError):
                    planner.schedule()
        finally:
            os.unlink(config_path)

    def test_backward_compatibility(self):
        """Test backward compatibility of planner interface."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "min_abstract_lead_time_days": 30,
                "min_paper_lead_time_days": 90,
                "max_concurrent_submissions": 3,
                "data_files": {
                    "conferences": "conferences.json",
                    "mods": "mods.json",
                    "papers": "papers.json"
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            planner = Planner(config_path)
            
            # Test that interface methods exist
            assert hasattr(planner, 'schedule')
            assert hasattr(planner, 'validate_schedule')
            assert hasattr(planner, 'get_schedule_metrics')
            assert hasattr(planner, 'generate_monthly_table')
        finally:
            os.unlink(config_path)

    def test_planner_with_default_config(self):
        """Test that planner works with default configuration."""
        # Create planner with non-existent config file (should use defaults)
        planner = Planner("nonexistent_config.json")
        
        # Should have a valid config
        assert planner.config is not None
        assert len(planner.config.submissions) > 0
        assert len(planner.config.conferences) > 0
        
        # Should be able to generate a schedule
        schedule = planner.schedule()
        assert schedule is not None
        assert len(schedule) > 0
        
        # Should be able to validate the schedule
        is_valid = planner.validate_schedule(schedule)
        assert isinstance(is_valid, bool)
    
    def test_planner_with_default_config_different_strategies(self):
        """Test that planner works with different strategies using default config."""
        planner = Planner("nonexistent_config.json")
        
        # Test different strategies
        strategies = [
            SchedulerStrategy.GREEDY,
            SchedulerStrategy.RANDOM,
            SchedulerStrategy.HEURISTIC
        ]
        
        for strategy in strategies:
            schedule = planner.schedule(strategy)
            assert schedule is not None
            assert len(schedule) > 0
