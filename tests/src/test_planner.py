"""Tests for the main planner module."""

import pytest
import json
from datetime import date
from unittest.mock import Mock, patch
import tempfile
import os

from core.models import SchedulerStrategy
from planner import Planner


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
            
            with patch('planner.BaseScheduler.create_scheduler') as mock_create:
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
            
            with patch('planner.BaseScheduler.create_scheduler') as mock_create:
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
            
            with patch('planner.BaseScheduler.create_scheduler') as mock_create:
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
            
            with patch('planner.generate_simple_monthly_table') as mock_generate:
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
            
            with patch('planner.BaseScheduler.create_scheduler') as mock_create:
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

    def test_complete_planner_workflow(self):
        """Test complete workflow from config loading to schedule generation."""
        planner = Planner("nonexistent_config.json")
        
        # Generate schedule with different strategies
        strategies = [SchedulerStrategy.GREEDY, SchedulerStrategy.STOCHASTIC]
        
        for strategy in strategies:
            # Generate schedule
            schedule = planner.schedule(strategy)
            
            # Verify schedule is not empty
            assert schedule is not None
            assert len(schedule) > 0
            
            # Verify schedule structure
            for submission_id, start_date in schedule.items():
                assert isinstance(submission_id, str)
                assert isinstance(start_date, date)
            
            # Validate schedule
            is_valid = planner.validate_schedule(schedule)
            assert isinstance(is_valid, bool)
            
            # Get metrics
            metrics = planner.get_schedule_metrics(schedule)
            assert isinstance(metrics, dict)
            assert 'total_submissions' in metrics
            assert 'duration_days' in metrics
            assert 'penalty_score' in metrics
            assert 'quality_score' in metrics
            assert 'efficiency_score' in metrics

    def test_comprehensive_result_generation(self):
        """Test comprehensive result generation with all metrics."""
        planner = Planner("nonexistent_config.json")
        
        # Generate schedule
        schedule = planner.schedule(SchedulerStrategy.GREEDY)
        
        # Get comprehensive result
        result = planner.get_comprehensive_result(schedule, SchedulerStrategy.GREEDY)
        
        # Verify result structure
        assert result.schedule == schedule
        assert isinstance(result.summary.total_submissions, int)
        assert isinstance(result.summary.schedule_span, int)
        assert isinstance(result.summary.penalty_score, (int, float))
        assert isinstance(result.summary.quality_score, (int, float))
        assert isinstance(result.summary.efficiency_score, (int, float))
        
        # Verify validation result
        assert hasattr(result.validation, 'is_valid')
        assert hasattr(result.validation, 'violations')
        
        # Verify scoring result
        assert hasattr(result.scoring, 'penalty_score')
        assert hasattr(result.scoring, 'quality_score')
        assert hasattr(result.scoring, 'efficiency_score')
        assert hasattr(result.scoring, 'overall_score')
        
        # Verify metrics
        assert hasattr(result.metrics, 'makespan')
        assert hasattr(result.metrics, 'avg_utilization')
        assert hasattr(result.metrics, 'peak_utilization')
        assert hasattr(result.metrics, 'total_penalty')
        assert hasattr(result.metrics, 'compliance_rate')
        assert hasattr(result.metrics, 'quality_score')

    def test_all_scheduler_strategies(self):
        """Test that all scheduler strategies can generate valid schedules."""
        planner = Planner("nonexistent_config.json")
        
        strategies = list(SchedulerStrategy)
        
        for strategy in strategies:
            # Generate schedule
            schedule = planner.schedule(strategy)
            
            # Verify schedule is generated
            assert schedule is not None
            assert len(schedule) > 0
            
            # Verify schedule structure
            for submission_id, start_date in schedule.items():
                assert isinstance(submission_id, str)
                assert isinstance(start_date, date)
            
            # Get metrics
            metrics = planner.get_schedule_metrics(schedule)
            assert isinstance(metrics, dict)
            assert 'total_submissions' in metrics

    def test_schedule_validation_workflow(self):
        """Test complete schedule validation workflow."""
        planner = Planner("nonexistent_config.json")
        
        # Generate schedule
        schedule = planner.schedule(SchedulerStrategy.GREEDY)
        
        # Validate schedule
        is_valid = planner.validate_schedule(schedule)
        
        # Verify validation result
        assert isinstance(is_valid, bool)
        
        # Get detailed validation
        validation_result = planner.validate_schedule_comprehensive(schedule)
        
        # Verify validation structure
        assert 'summary' in validation_result
        assert 'constraints' in validation_result
        assert 'deadlines' in validation_result
        assert 'dependencies' in validation_result
        assert 'resources' in validation_result
        
        # Verify summary structure
        summary = validation_result['summary']
        assert 'is_feasible' in summary
        assert 'total_violations' in summary
        assert 'summary' in summary

    def test_schedule_metrics_calculation(self):
        """Test comprehensive schedule metrics calculation."""
        planner = Planner("nonexistent_config.json")
        
        # Generate schedule
        schedule = planner.schedule(SchedulerStrategy.GREEDY)
        
        # Get metrics
        metrics = planner.get_schedule_metrics(schedule)
        
        # Verify all required metrics are present
        required_metrics = [
            'total_submissions',
            'duration_days',
            'penalty_score',
            'quality_score',
            'efficiency_score',
            'penalty_breakdown'
        ]
        
        for metric in required_metrics:
            assert metric in metrics
        
        # Verify penalty breakdown structure
        penalty_breakdown = metrics['penalty_breakdown']
        assert 'deadline_penalties' in penalty_breakdown
        assert 'dependency_penalties' in penalty_breakdown
        assert 'resource_penalties' in penalty_breakdown
        
        # Verify metric types
        assert isinstance(metrics['total_submissions'], int)
        assert isinstance(metrics['duration_days'], int)
        assert isinstance(metrics['penalty_score'], (int, float))
        assert isinstance(metrics['quality_score'], (int, float))
        assert isinstance(metrics['efficiency_score'], (int, float))

    def test_schedule_date_consistency(self):
        """Test that schedule dates are consistent and valid."""
        planner = Planner("nonexistent_config.json")
        
        # Generate schedule
        schedule = planner.schedule(SchedulerStrategy.GREEDY)
        
        if schedule:
            # Get date range
            start_date = min(schedule.values())
            end_date = max(schedule.values())
            
            # Verify dates are within config range
            assert start_date >= planner.config.start_date
            assert end_date <= planner.config.end_date
            
            # Verify all dates are valid
            for submission_id, schedule_date in schedule.items():
                assert isinstance(schedule_date, date)
                assert schedule_date >= planner.config.start_date
                assert schedule_date <= planner.config.end_date

    def test_multiple_strategy_comparison(self):
        """Test comparing results from multiple strategies."""
        planner = Planner("nonexistent_config.json")
        
        strategies = [SchedulerStrategy.GREEDY, SchedulerStrategy.STOCHASTIC]
        results = {}
        
        for strategy in strategies:
            # Generate schedule
            schedule = planner.schedule(strategy)
            
            # Get comprehensive result
            result = planner.get_comprehensive_result(schedule, strategy)
            
            results[strategy] = result
        
        # Verify all strategies produced results
        assert len(results) == len(strategies)
        
        # Verify all results have required attributes
        for strategy, result in results.items():
            assert result.schedule is not None
            assert len(result.schedule) > 0
            assert result.summary.total_submissions > 0
            assert result.summary.schedule_span >= 0
