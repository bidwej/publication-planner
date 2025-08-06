"""Tests for the backtracking scheduler."""

import pytest
from datetime import date

from src.core.models import Submission, Config, SubmissionType, Conference
from src.schedulers.backtracking import BacktrackingGreedyScheduler as BacktrackingScheduler


def create_mock_submission(submission_id, title, submission_type, conference_id, **kwargs):
    """Create a mock submission with all required attributes."""
    submission = Submission(
        id=submission_id,
        title=title,
        kind=submission_type,
        conference_id=conference_id,
        draft_window_months=kwargs.get('draft_window_months', 3),
        earliest_start_date=kwargs.get('earliest_start_date', date(2024, 1, 1)),
        depends_on=kwargs.get('depends_on', []),
        priority=kwargs.get('priority', 1),
        engineering=kwargs.get('engineering', False),
        estimated_hours=kwargs.get('estimated_hours', 40),
        deadline=kwargs.get('deadline', None)
    )
    return submission


def create_mock_conference(conference_id, name, deadlines):
    """Create a mock conference with all required attributes."""
    conference = Conference(
        id=conference_id,
        name=name,
        deadlines=deadlines,
        conference_type="CONFERENCE",
        recurrence="ANNUAL",
        location="Test Location",
        url="https://test.com"
    )
    return conference


def create_mock_config(submissions, conferences):
    """Create a mock config with all required attributes."""
    config = Config(
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        blackout_dates=set(),
        scheduling_options={"enable_early_abstract_scheduling": False},
        submissions=submissions,
        conferences=conferences,
        submissions_dict={sub.id: sub for sub in submissions},
        conferences_dict={conf.id: conf for conf in conferences}
    )
    return config


class TestBacktrackingScheduler:
    """Test the BacktrackingScheduler class."""

    def test_backtracking_scheduler_initialization(self):
        """Test backtracking scheduler initialization."""
        config = create_mock_config([], [])
        
        scheduler = BacktrackingScheduler(config)
        
        assert scheduler.config == config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self):
        """Test scheduling with empty submissions."""
        config = create_mock_config([], [])
        
        scheduler = BacktrackingScheduler(config)
        
        # Empty submissions should raise RuntimeError
        with pytest.raises(RuntimeError, match="No valid dates found for scheduling"):
            scheduler.schedule()

    def test_schedule_single_paper(self):
        """Test scheduling with single paper."""
        # Create mock submission
        submission = create_mock_submission(
            "sub1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        # Create mock conference
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "sub1" in result
        assert isinstance(result["sub1"], date)

    def test_schedule_multiple_papers(self):
        """Test scheduling with multiple papers."""
        # Create mock submissions
        submission1 = create_mock_submission(
            "sub1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "sub2", "Test Paper 2", SubmissionType.ABSTRACT, "conf2",
            priority=2
        )
        
        # Create mock conferences
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.ABSTRACT: date(2024, 8, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "sub1" in result
        assert "sub2" in result
        assert isinstance(result["sub1"], date)
        assert isinstance(result["sub2"], date)

    def test_schedule_with_constraints(self):
        """Test scheduling with constraints."""
        # Create mock paper with constraints
        submission = create_mock_submission(
            "sub1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        config.blackout_dates = {date(2024, 5, 15), date(2024, 5, 16)}
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "sub1" in result
        
        # Check that scheduled date is not in blackout dates
        scheduled_date = result["sub1"]
        assert scheduled_date not in config.blackout_dates

    def test_schedule_with_insufficient_time(self):
        """Test scheduling when there's insufficient time."""
        # Create mock paper with very short deadline
        submission = create_mock_submission(
            "sub1", "Test Paper", SubmissionType.PAPER, "conf1",
            earliest_start_date=date(2024, 1, 15),  # Start after deadline
            deadline=date(2024, 2, 1),  # Very early deadline
            estimated_hours=200  # Very long paper
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 2, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = BacktrackingScheduler(config)
        
        # Should raise RuntimeError due to insufficient time
        with pytest.raises(RuntimeError, match="No valid dates found for scheduling"):
            scheduler.schedule()

    def test_backtracking_algorithm(self):
        """Test the backtracking algorithm behavior."""
        # Create mock submissions with dependencies
        submission1 = create_mock_submission(
            "sub1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "sub2", "Test Paper 2", SubmissionType.PAPER, "conf1",
            depends_on=["sub1"]
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference])
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "sub1" in result
        assert "sub2" in result
        
        # Check dependency constraint: sub2 should be scheduled after sub1
        assert result["sub2"] > result["sub1"]

    def test_error_handling_invalid_paper(self):
        """Test error handling with invalid paper."""
        # Create mock submission with invalid conference
        submission = create_mock_submission(
            "sub1", "Test Paper", SubmissionType.PAPER, "nonexistent_conf"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = BacktrackingScheduler(config)
        
        # Should raise ValueError due to invalid conference reference
        with pytest.raises(ValueError, match="Submission sub1 references unknown conference nonexistent_conf"):
            scheduler.schedule()

    def test_schedule_with_priority_ordering(self):
        """Test scheduling with priority ordering."""
        # Create mock submissions with different priorities
        submission1 = create_mock_submission(
            "sub1", "Test Paper 1", SubmissionType.PAPER, "conf1",
            priority=2
        )
        
        submission2 = create_mock_submission(
            "sub2", "Test Paper 2", SubmissionType.PAPER, "conf2",
            priority=1
        )
        
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "sub1" in result
        assert "sub2" in result

    def test_schedule_with_resource_constraints(self):
        """Test scheduling with resource constraints."""
        # Create mock submissions that would exceed concurrency limit
        submission1 = create_mock_submission(
            "sub1", "Test Paper 1", SubmissionType.PAPER, "conf1",
            estimated_hours=100
        )
        
        submission2 = create_mock_submission(
            "sub2", "Test Paper 2", SubmissionType.PAPER, "conf1",
            estimated_hours=100
        )
        
        submission3 = create_mock_submission(
            "sub3", "Test Paper 3", SubmissionType.PAPER, "conf1",
            estimated_hours=100
        )
        
        submission4 = create_mock_submission(
            "sub4", "Test Paper 4", SubmissionType.PAPER, "conf1",
            estimated_hours=100
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config(
            [submission1, submission2, submission3, submission4], 
            [conference]
        )
        config.max_concurrent_submissions = 2
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 4
        
        # Check that no more than 2 submissions are scheduled on the same day
        scheduled_dates = list(result.values())
        for i, date1 in enumerate(scheduled_dates):
            for j, date2 in enumerate(scheduled_dates):
                if i != j and date1 == date2:
                    # Count how many submissions are scheduled on this date
                    same_date_count = sum(1 for d in scheduled_dates if d == date1)
                    assert same_date_count <= config.max_concurrent_submissions
