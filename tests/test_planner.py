"""Tests for the main planner module."""

import pytest
from datetime import date
from unittest.mock import Mock, patch

from core.models import Config
from planner import Planner


class TestPlanner:
    """Test the Planner class."""

    def test_planner_initialization(self):
        """Test planner initialization."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        planner = Planner(config)
        
        assert planner.config == config
        assert planner.scheduler is not None

    def test_planner_initialization_with_submissions(self):
        """Test planner initialization with submissions."""
        # Create mock submissions
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        
        paper2 = Mock(spec=Paper)
        paper2.id = "paper2"
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = []
        
        planner = Planner(config)
        
        assert planner.config == config
        assert len(planner.config.submissions) == 2

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = Mock(spec=Config)
        config.submissions = [Mock(spec=Paper)]
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        result = planner.validate_config()
        
        assert result is True

    def test_validate_config_empty_submissions(self):
        """Test config validation with empty submissions."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        result = planner.validate_config()
        
        assert result is False

    def test_validate_config_empty_conferences(self):
        """Test config validation with empty conferences."""
        config = Mock(spec=Config)
        config.submissions = [Mock(spec=Paper)]
        config.conferences = []
        
        planner = Planner(config)
        
        result = planner.validate_config()
        
        assert result is False

    def test_schedule_method(self):
        """Test the schedule method."""
        # Create mock submissions
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        
        paper2 = Mock(spec=Paper)
        paper2.id = "paper2"
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        with patch.object(planner.scheduler, 'schedule') as mock_schedule:
            mock_schedule.return_value = {
                "paper1": date(2024, 5, 1),
                "paper2": date(2024, 7, 1)
            }
            
            result = planner.schedule()
            
            mock_schedule.assert_called_once()
            assert isinstance(result, dict)
            assert len(result) == 2
            assert "paper1" in result
            assert "paper2" in result

    def test_schedule_method_with_strategy(self):
        """Test the schedule method with specific strategy."""
        config = Mock(spec=Config)
        config.submissions = [Mock(spec=Paper)]
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        with patch.object(planner.scheduler, 'schedule') as mock_schedule:
            mock_schedule.return_value = {"paper1": date(2024, 5, 1)}
            
            result = planner.schedule(strategy="greedy")
            
            mock_schedule.assert_called_once()
            assert isinstance(result, dict)

    def test_greedy_schedule_method(self):
        """Test the greedy_schedule method."""
        config = Mock(spec=Config)
        config.submissions = [Mock(spec=Paper)]
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        with patch.object(planner.scheduler, 'schedule') as mock_schedule:
            mock_schedule.return_value = {"paper1": date(2024, 5, 1)}
            
            result = planner.greedy_schedule()
            
            mock_schedule.assert_called_once()
            assert isinstance(result, dict)

    def test_generate_monthly_table(self):
        """Test the generate_monthly_table method."""
        config = Mock(spec=Config)
        config.submissions = [Mock(spec=Paper)]
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        schedule = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        with patch('planner.generate_simple_monthly_table') as mock_generate:
            mock_generate.return_value = [
                {"Month": "2024-05", "Papers": "1", "Deadlines": "0"},
                {"Month": "2024-07", "Papers": "1", "Deadlines": "0"}
            ]
            
            result = planner.generate_monthly_table(schedule)
            
            mock_generate.assert_called_once_with(schedule, config)
            assert isinstance(result, list)
            assert len(result) == 2

    def test_error_handling_invalid_config(self):
        """Test error handling with invalid config."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        planner = Planner(config)
        
        with pytest.raises(ValueError):
            planner.schedule()

    def test_error_handling_scheduler_failure(self):
        """Test error handling when scheduler fails."""
        config = Mock(spec=Config)
        config.submissions = [Mock(spec=Paper)]
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        with patch.object(planner.scheduler, 'schedule') as mock_schedule:
            mock_schedule.side_effect = Exception("Scheduler failed")
            
            with pytest.raises(Exception):
                planner.schedule()

    def test_backward_compatibility(self):
        """Test backward compatibility of planner interface."""
        config = Mock(spec=Config)
        config.submissions = [Mock(spec=Paper)]
        config.conferences = [Mock()]
        
        planner = Planner(config)
        
        # Test that old interface still works
        assert hasattr(planner, 'schedule')
        assert hasattr(planner, 'greedy_schedule')
        assert hasattr(planner, 'generate_monthly_table')
        assert hasattr(planner, 'validate_config')
