"""Tests for the base scheduler."""

from datetime import date, timedelta

import pytest

from core.models import SubmissionType, Schedule
from schedulers.greedy import GreedyScheduler
from conftest import create_mock_submission, create_mock_conference, create_mock_config
from typing import Dict, List, Any, Optional



class TestScheduler:
    """Test the base scheduler functionality."""

    def test_scheduler_initialization(self, empty_config) -> None:
        """Test scheduler initialization."""
        scheduler: Any = GreedyScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')

    def test_scheduler_with_empty_config(self, empty_config) -> None:
        """Test scheduler with empty config."""
        scheduler: Any = GreedyScheduler(empty_config)
        
        result: Any = scheduler.schedule()
        assert isinstance(result, Schedule)
        assert len(result.intervals) == 0

    def test_scheduler_with_sample_data(self, sample_config) -> None:
        """Test scheduler with sample data."""
        scheduler: Any = GreedyScheduler(sample_config)
        
        assert scheduler.config == sample_config
        assert len(scheduler.config.submissions) > 0
        assert len(scheduler.config.conferences) > 0

    def test_schedule_method(self, sample_config) -> None:
        """Test the schedule method."""
        scheduler: Any = GreedyScheduler(sample_config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, Schedule)
        assert len(result.intervals) > 0

    def test_schedule_with_no_submissions(self, empty_config) -> None:
        """Test scheduling with no submissions."""
        scheduler: Any = GreedyScheduler(empty_config)
        
        # Should return empty schedule for no submissions
        result: Any = scheduler.schedule()
        assert isinstance(result, Schedule)
        assert len(result.intervals) == 0

    def test_schedule_with_no_valid_dates(self) -> None:
        """Test scheduling with no valid dates."""
        # Create submission with impossible constraints
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1",
            earliest_start_date=date(2025, 12, 1)  # Start after deadline
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler: Any = GreedyScheduler(config)
        
        # Should return empty schedule
        result: Any = scheduler.schedule()
        assert isinstance(result, Schedule)
        assert len(result.intervals) == 0

    def test_schedule_with_dependencies(self) -> None:
        """Test scheduling with dependencies."""
        # Create submissions with dependencies
        submission1 = create_mock_submission(
            "paper1", "Dependency Paper", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Dependent Paper", SubmissionType.PAPER, "conf1",
            depends_on=["paper1"]
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference])
        
        scheduler: Any = GreedyScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, Schedule)
        assert len(result.intervals) >= 1
        assert "paper1" in result.intervals
        
        # If both are scheduled, check dependency constraint
        if "paper2" in result.intervals:
            assert result.intervals["paper2"].start_date > result.intervals["paper1"].start_date

    def test_schedule_respects_earliest_start_date(self, sample_config) -> None:
        """Test that schedule respects earliest start dates."""
        scheduler: Any = GreedyScheduler(sample_config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, Schedule)
        
        # Check that all scheduled dates are after earliest start dates
        for submission_id, interval in result.intervals.items():
            submission = next(s for s in sample_config.submissions if s.id == submission_id)
            if submission.earliest_start_date:
                assert interval.start_date >= submission.earliest_start_date

    def test_schedule_respects_deadlines(self, sample_config) -> None:
        """Test that schedule respects deadlines."""
        scheduler: Any = GreedyScheduler(sample_config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, Schedule)
        
        # Check that all scheduled dates meet deadlines
        for submission_id, interval in result.intervals.items():
            submission = next(s for s in sample_config.submissions if s.id == submission_id)
            if submission.conference_id:
                conf = next(c for c in sample_config.conferences if c.id == submission.conference_id)
                if conf and submission.kind in conf.deadlines:
                    deadline = conf.deadlines[submission.kind]
                    end_date = interval.start_date + timedelta(days=sample_config.min_paper_lead_time_days)
                    assert end_date <= deadline

    def test_schedule_respects_concurrency_limit(self, sample_config) -> None:
        """Test that schedule respects concurrency limits."""
        scheduler: Any = GreedyScheduler(sample_config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, Schedule)
        
        # Check that no more than max_concurrent_submissions are scheduled on the same day
        scheduled_dates = [interval.start_date for interval in result.intervals.values()]
        for i, date1 in enumerate(scheduled_dates):
            same_date_count = sum(1 for d in scheduled_dates if d == date1)
            assert same_date_count <= sample_config.max_concurrent_submissions
