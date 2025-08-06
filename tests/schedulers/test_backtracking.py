"""Tests for the backtracking scheduler."""

import pytest
from datetime import date

from src.core.models import SubmissionType
from src.schedulers.backtracking import BacktrackingGreedyScheduler as BacktrackingScheduler


class TestBacktrackingScheduler:
    """Test the BacktrackingScheduler class."""

    def test_backtracking_scheduler_initialization(self, empty_config):
        """Test backtracking scheduler initialization."""
        scheduler = BacktrackingScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self, empty_config):
        """Test scheduling with empty submissions."""
        scheduler = BacktrackingScheduler(empty_config)
        
        # Empty submissions should raise RuntimeError
        with pytest.raises(RuntimeError, match="No valid dates found for scheduling"):
            scheduler.schedule()

    def test_schedule_single_paper(self):
        """Test scheduling with single paper."""
        # Create mock submission
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
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
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submissions
        submission1 = create_mock_submission(
            "sub1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "sub2", "Test Paper 2", SubmissionType.ABSTRACT, "conf2"
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
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock paper with constraints
        submission = create_mock_submission(
            "sub1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        config.blackout_dates = [date(2024, 5, 15), date(2024, 5, 16)]
        
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
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock paper with very short deadline
        submission = create_mock_submission(
            "sub1", "Test Paper", SubmissionType.PAPER, "conf1",
            earliest_start_date=date(2024, 1, 15)  # Start after deadline
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 2, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = BacktrackingScheduler(config)
        
        # Should return empty schedule due to insufficient time
        result = scheduler.schedule()
        assert isinstance(result, dict)
        assert len(result) == 0  # No submissions scheduled

    def test_backtracking_algorithm(self):
        """Test the backtracking algorithm behavior."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
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
        # May schedule only one submission if dependency can't be satisfied
        assert len(result) >= 1
        assert "sub1" in result
        
        # If both are scheduled, check dependency constraint
        if "sub2" in result:
            assert result["sub2"] > result["sub1"]

    def test_error_handling_invalid_paper(self):
        """Test error handling with invalid paper."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
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
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submissions with different priorities
        submission1 = create_mock_submission(
            "sub1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "sub2", "Test Paper 2", SubmissionType.PAPER, "conf2"
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
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submissions that would exceed concurrency limit
        submission1 = create_mock_submission(
            "sub1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "sub2", "Test Paper 2", SubmissionType.PAPER, "conf1"
        )
        
        submission3 = create_mock_submission(
            "sub3", "Test Paper 3", SubmissionType.PAPER, "conf1"
        )
        
        submission4 = create_mock_submission(
            "sub4", "Test Paper 4", SubmissionType.PAPER, "conf1"
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
        # May schedule fewer than 4 due to resource constraints
        assert len(result) >= 2
        
        # Check that no more than 2 submissions are scheduled on the same day
        scheduled_dates = list(result.values())
        for i, date1 in enumerate(scheduled_dates):
            for j, date2 in enumerate(scheduled_dates):
                if i != j and date1 == date2:
                    # Count how many submissions are scheduled on this date
                    same_date_count = sum(1 for d in scheduled_dates if d == date1)
                    assert same_date_count <= config.max_concurrent_submissions
