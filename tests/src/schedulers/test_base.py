"""Tests for the base scheduler."""

import pytest
from datetime import date

from core.models import SubmissionType
from schedulers.greedy import GreedyScheduler


class TestScheduler:
    """Test the base scheduler functionality."""

    def test_scheduler_initialization(self, empty_config):
        """Test scheduler initialization."""
        scheduler = GreedyScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')

    def test_scheduler_with_empty_config(self, empty_config):
        """Test scheduler with empty config."""
        scheduler = GreedyScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert len(scheduler.config.submissions) == 0
        assert len(scheduler.config.conferences) == 0

    def test_scheduler_with_sample_data(self, sample_config):
        """Test scheduler with sample data."""
        scheduler = GreedyScheduler(sample_config)
        
        assert scheduler.config == sample_config
        assert len(scheduler.config.submissions) > 0
        assert len(scheduler.config.conferences) > 0

    def test_schedule_method(self, sample_config):
        """Test the schedule method."""
        scheduler = GreedyScheduler(sample_config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_schedule_with_no_submissions(self, empty_config):
        """Test scheduling with no submissions."""
        scheduler = GreedyScheduler(empty_config)
        
        # Should return empty schedule for no submissions
        result = scheduler.schedule()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_with_no_valid_dates(self):
        """Test scheduling with no valid dates."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create submission with impossible constraints
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1",
            earliest_start_date=date(2024, 12, 1)  # Start after deadline
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        
        # Should return empty schedule
        result = scheduler.schedule()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_with_dependencies(self):
        """Test scheduling with dependencies."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
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
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference])
        
        scheduler = GreedyScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1
        assert "paper1" in result
        
        # If both are scheduled, check dependency constraint
        if "paper2" in result:
            assert result["paper2"] > result["paper1"]

    def test_schedule_respects_earliest_start_date(self, sample_config):
        """Test that schedule respects earliest start dates."""
        scheduler = GreedyScheduler(sample_config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        
        # Check that all scheduled dates are after earliest start dates
        for submission_id, scheduled_date in result.items():
            submission = sample_config.submissions_dict[submission_id]
            if submission.earliest_start_date:
                assert scheduled_date >= submission.earliest_start_date

    def test_schedule_respects_deadlines(self, sample_config):
        """Test that schedule respects deadlines."""
        scheduler = GreedyScheduler(sample_config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        
        # Check that all scheduled dates are before deadlines
        for submission_id, scheduled_date in result.items():
            submission = sample_config.submissions_dict[submission_id]
            conference = sample_config.conferences_dict[submission.conference_id]
            deadline = conference.deadlines[submission.kind]
            assert scheduled_date <= deadline

    def test_schedule_respects_concurrency_limit(self, sample_config):
        """Test that schedule respects concurrency limits."""
        scheduler = GreedyScheduler(sample_config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        
        # Check that no more than max_concurrent_submissions are scheduled on the same day
        scheduled_dates = list(result.values())
        for i, date1 in enumerate(scheduled_dates):
            for j, date2 in enumerate(scheduled_dates):
                if i != j and date1 == date2:
                    same_date_count = sum(1 for d in scheduled_dates if d == date1)
                    assert same_date_count <= sample_config.max_concurrent_submissions
