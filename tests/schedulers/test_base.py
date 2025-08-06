"""Tests for scheduler."""

import pytest
from datetime import date
from typing import Dict
from src.schedulers.base import Scheduler
from src.core.models import Config, SchedulerStrategy, Submission, Conference, ConferenceType, ConferenceRecurrence, SubmissionType


class TestScheduler:
    """Test the scheduler class."""
    
    def test_scheduler_initialization(self, minimal_config):
        """Test scheduler initialization."""
        scheduler = Scheduler(minimal_config)
        assert scheduler.config == minimal_config
        assert isinstance(scheduler.submissions, dict)
        assert isinstance(scheduler.conferences, dict)
        
        # Check configuration options
        assert hasattr(scheduler, 'randomness_factor')
        assert hasattr(scheduler, 'lookahead_days')
        assert hasattr(scheduler, 'enable_backtracking')
        assert hasattr(scheduler, 'max_backtracks')
    
    def test_scheduler_with_empty_config(self):
        """Test scheduler with empty config."""
        empty_config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=0,
            min_paper_lead_time_days=60,
            max_concurrent_submissions=1,
            default_paper_lead_time_months=3,
            penalty_costs={},
            priority_weights={},
            scheduling_options={},
            blackout_dates=[],
            data_files={}
        )
        
        scheduler = Scheduler(empty_config)
        assert scheduler.config == empty_config
        assert len(scheduler.submissions) == 0
        assert len(scheduler.conferences) == 0
    
    def test_scheduler_with_sample_data(self, config):
        """Test scheduler with sample data."""
        scheduler = Scheduler(config)
        
        # Should have submissions and conferences
        assert len(scheduler.submissions) > 0
        assert len(scheduler.conferences) > 0
        
        # Test that we can generate a schedule
        schedule = scheduler.schedule()
        assert isinstance(schedule, dict)
        assert len(schedule) > 0
    
    def test_configuration_options(self, minimal_config):
        """Test that configuration options work correctly."""
        # Test with different configuration options
        minimal_config.randomness_factor = 0.1
        minimal_config.lookahead_days = 30
        minimal_config.enable_backtracking = True
        minimal_config.max_backtracks = 10
        
        scheduler = Scheduler(minimal_config)
        
        assert scheduler.randomness_factor == 0.1
        assert scheduler.lookahead_days == 30
        assert scheduler.enable_backtracking is True
        assert scheduler.max_backtracks == 10
    
    def test_default_configuration_options(self, minimal_config):
        """Test default configuration options."""
        scheduler = Scheduler(minimal_config)
        
        # Should have sensible defaults
        assert scheduler.randomness_factor == 0.0
        assert scheduler.lookahead_days == 0
        assert scheduler.enable_backtracking is False
        assert scheduler.max_backtracks == 5
    
    def test_schedule_method(self, config):
        """Test that schedule method returns valid schedule."""
        scheduler = Scheduler(config)
        schedule = scheduler.schedule()
        
        assert isinstance(schedule, dict)
        assert len(schedule) > 0
        
        # Check that all values are dates
        for submission_id, start_date in schedule.items():
            assert isinstance(submission_id, str)
            assert isinstance(start_date, date)
    
    def test_schedule_with_no_submissions(self, minimal_config):
        """Test scheduling with no submissions."""
        scheduler = Scheduler(minimal_config)
        schedule = scheduler.schedule()
        
        # Should return empty schedule
        assert isinstance(schedule, dict)
        assert len(schedule) == 0
    
    def test_schedule_with_dependencies(self, config):
        """Test scheduling with dependencies."""
        scheduler = Scheduler(config)
        schedule = scheduler.schedule()
        
        # Check that dependencies are satisfied
        for submission_id, start_date in schedule.items():
            submission = scheduler.submissions[submission_id]
            if submission.depends_on:
                for parent_id in submission.depends_on:
                    if parent_id in schedule:
                        parent_start = schedule[parent_id]
                        # Child should start after parent
                        assert start_date >= parent_start
