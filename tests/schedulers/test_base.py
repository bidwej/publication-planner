"""Tests for scheduler."""

import pytest
from datetime import date
from typing import Dict
from src.schedulers.greedy import GreedyScheduler
from src.core.models import Config, SchedulerStrategy, Submission, Conference, ConferenceType, ConferenceRecurrence, SubmissionType


class TestScheduler:
    """Test the scheduler class."""
    
    def test_scheduler_initialization(self, minimal_config):
        """Test scheduler initialization."""
        scheduler = GreedyScheduler(minimal_config)
        assert scheduler.config == minimal_config
        assert isinstance(scheduler.submissions, dict)
        assert isinstance(scheduler.conferences, dict)
    
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
        
        scheduler = GreedyScheduler(empty_config)
        assert scheduler.config == empty_config
        assert len(scheduler.submissions) == 0
        assert len(scheduler.conferences) == 0
    
    def test_scheduler_with_sample_data(self, config):
        """Test scheduler with sample data."""
        scheduler = GreedyScheduler(config)
        
        # Should have submissions and conferences
        assert len(scheduler.submissions) > 0
        assert len(scheduler.conferences) > 0
        
        # Test that we can generate a schedule
        schedule = scheduler.schedule()
        assert isinstance(schedule, dict)
        assert len(schedule) > 0
    
    def test_schedule_method(self, config):
        """Test that schedule method returns valid schedule."""
        scheduler = GreedyScheduler(config)
        schedule = scheduler.schedule()
        
        assert isinstance(schedule, dict)
        assert len(schedule) > 0
        
        # Check that all values are dates
        for submission_id, start_date in schedule.items():
            assert isinstance(submission_id, str)
            assert isinstance(start_date, date)
    
    def test_schedule_with_no_submissions(self, minimal_config):
        """Test scheduling with no submissions."""
        scheduler = GreedyScheduler(minimal_config)
        
        # Should raise RuntimeError when no valid dates found
        with pytest.raises(RuntimeError, match="No valid dates found for scheduling"):
            scheduler.schedule()
    
    def test_schedule_with_dependencies(self, config):
        """Test scheduling with dependencies."""
        scheduler = GreedyScheduler(config)
        schedule = scheduler.schedule()
        
        # Check that dependencies are satisfied
        for sid, start_date in schedule.items():
            sub = scheduler.submissions[sid]
            if sub.depends_on:
                for dep_id in sub.depends_on:
                    if dep_id in schedule:
                        dep_start = schedule[dep_id]
                        # Child should start after parent
                        assert start_date >= dep_start
