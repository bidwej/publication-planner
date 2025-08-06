"""Tests for scheduler."""

import pytest
from datetime import date
from typing import Dict
from schedulers.greedy import GreedyScheduler
from core.models import Config, SchedulerStrategy, Submission, Conference, ConferenceType, ConferenceRecurrence, SubmissionType


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
        # Should schedule all submissions
        assert len(schedule) == len(scheduler.submissions)
    
    def test_schedule_method(self, config):
        """Test that schedule method returns valid schedule."""
        scheduler = GreedyScheduler(config)
        schedule = scheduler.schedule()
        
        assert isinstance(schedule, dict)
        assert len(schedule) == len(scheduler.submissions)
        
        # Check that all values are dates
        for submission_id, start_date in schedule.items():
            assert isinstance(submission_id, str)
            assert isinstance(start_date, date)
            assert submission_id in scheduler.submissions
    
    def test_schedule_with_no_submissions(self, minimal_config):
        """Test scheduling with no submissions."""
        scheduler = GreedyScheduler(minimal_config)
        
        # Should raise RuntimeError when no valid dates found
        with pytest.raises(RuntimeError, match="No valid dates found for scheduling"):
            scheduler.schedule()
    
    def test_schedule_with_no_valid_dates(self):
        """Test scheduling when submissions have no valid dates."""
        # Create submissions without earliest_start_date and conferences without deadlines
        submissions = [
            Submission(
                id="test-pap",
                title="Test Paper",
                kind=SubmissionType.PAPER,
                conference_id="ICML",
                depends_on=[],
                draft_window_months=2,
                lead_time_from_parents=0,
                penalty_cost_per_day=500,
                engineering=True,
                earliest_start_date=None  # No earliest start date
            )
        ]
        
        conferences = [
            Conference(
                id="ICML",
                name="ICML",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={}  # No deadlines
            )
        ]
        
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=60,
            max_concurrent_submissions=1,
            default_paper_lead_time_months=3,
            penalty_costs={},
            priority_weights={},
            scheduling_options={},
            blackout_dates=[],
            data_files={}
        )
        
        scheduler = GreedyScheduler(config)
        
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
                        dep_end = scheduler._get_end_date(dep_start, scheduler.submissions[dep_id])
                        # Child should start after parent finishes
                        assert start_date >= dep_end
    
    def test_schedule_respects_earliest_start_date(self, config):
        """Test that schedule respects earliest_start_date constraints."""
        scheduler = GreedyScheduler(config)
        schedule = scheduler.schedule()
        
        for sid, start_date in schedule.items():
            sub = scheduler.submissions[sid]
            if sub.earliest_start_date:
                assert start_date >= sub.earliest_start_date
    
    def test_schedule_respects_deadlines(self, config):
        """Test that schedule respects conference deadlines."""
        scheduler = GreedyScheduler(config)
        schedule = scheduler.schedule()
        
        for sid, start_date in schedule.items():
            sub = scheduler.submissions[sid]
            if sub.conference_id and sub.conference_id in scheduler.conferences:
                conf = scheduler.conferences[sub.conference_id]
                if sub.kind in conf.deadlines:
                    deadline = conf.deadlines[sub.kind]
                    end_date = scheduler._get_end_date(start_date, sub)
                    assert end_date <= deadline
    
    def test_schedule_respects_concurrency_limit(self, config):
        """Test that schedule respects max_concurrent_submissions limit."""
        scheduler = GreedyScheduler(config)
        schedule = scheduler.schedule()
        
        # Group submissions by start date
        date_to_submissions = {}
        for sid, start_date in schedule.items():
            if start_date not in date_to_submissions:
                date_to_submissions[start_date] = []
            date_to_submissions[start_date].append(sid)
        
        # Check that no date has more than max_concurrent_submissions active
        for start_date, submission_ids in date_to_submissions.items():
            active_count = 0
            for sid in submission_ids:
                sub = scheduler.submissions[sid]
                end_date = scheduler._get_end_date(start_date, sub)
                # Count how many submissions are active on this date
                for other_sid, other_start in schedule.items():
                    other_sub = scheduler.submissions[other_sid]
                    other_end = scheduler._get_end_date(other_start, other_sub)
                    if other_start <= start_date < other_end:
                        active_count += 1
                        break
            
            assert active_count <= scheduler.config.max_concurrent_submissions
