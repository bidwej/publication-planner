"""Tests for the random scheduler."""

import pytest
from datetime import date

from src.core.models import SubmissionType
from src.schedulers.random import RandomScheduler


class TestRandomScheduler:
    """Test the RandomScheduler class."""

    def test_random_scheduler_initialization(self, empty_config):
        """Test random scheduler initialization."""
        scheduler = RandomScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self, empty_config):
        """Test scheduling with empty submissions."""
        scheduler = RandomScheduler(empty_config)
        
        # Empty submissions should raise RuntimeError
        with pytest.raises(RuntimeError, match="No valid dates found for scheduling"):
            scheduler.schedule()

    def test_schedule_single_paper(self):
        """Test scheduling with single paper."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submission
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        # Create mock conference
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = RandomScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_schedule_multiple_papers(self):
        """Test scheduling with multiple papers."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submissions
        submission1 = create_mock_submission(
            "paper1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Test Paper 2", SubmissionType.ABSTRACT, "conf2"
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
        
        scheduler = RandomScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
        assert isinstance(result["paper1"], date)
        assert isinstance(result["paper2"], date)

    def test_random_algorithm_behavior(self):
        """Test the random algorithm behavior."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submissions with different characteristics
        submission1 = create_mock_submission(
            "paper1", "High Priority Paper", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Low Priority Paper", SubmissionType.ABSTRACT, "conf2"
        )
        
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.ABSTRACT: date(2024, 8, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler = RandomScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_constraints(self):
        """Test scheduling with constraints."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submission with constraints
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        config.blackout_dates = [date(2024, 5, 15), date(2024, 5, 16)]
        
        scheduler = RandomScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that scheduled date is not in blackout dates
        scheduled_date = result["paper1"]
        assert scheduled_date not in config.blackout_dates

    def test_error_handling_invalid_paper(self):
        """Test error handling with invalid paper."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submission with invalid conference
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "nonexistent_conf"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = RandomScheduler(config)
        
        # Should raise ValueError due to invalid conference reference
        with pytest.raises(ValueError, match="Submission paper1 references unknown conference nonexistent_conf"):
            scheduler.schedule()

    def test_schedule_with_priority_ordering(self):
        """Test scheduling with priority ordering."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submissions with different priorities
        submission1 = create_mock_submission(
            "paper1", "High Priority Paper", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Low Priority Paper", SubmissionType.PAPER, "conf2"
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
        
        scheduler = RandomScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_deadline_compliance(self):
        """Test scheduling with deadline compliance."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submission with tight deadline
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = RandomScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that scheduled date is before deadline
        scheduled_date = result["paper1"]
        deadline = conference.deadlines[SubmissionType.PAPER]
        assert scheduled_date <= deadline

    def test_schedule_with_resource_constraints(self):
        """Test scheduling with resource constraints."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submissions that need resource optimization
        submission1 = create_mock_submission(
            "paper1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Test Paper 2", SubmissionType.PAPER, "conf1"
        )
        
        submission3 = create_mock_submission(
            "paper3", "Test Paper 3", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission1, submission2, submission3], [conference])
        config.max_concurrent_submissions = 2
        
        scheduler = RandomScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 2
        
        # Check that no more than 2 submissions are scheduled on the same day
        scheduled_dates = list(result.values())
        for i, date1 in enumerate(scheduled_dates):
            for j, date2 in enumerate(scheduled_dates):
                if i != j and date1 == date2:
                    same_date_count = sum(1 for d in scheduled_dates if d == date1)
                    assert same_date_count <= config.max_concurrent_submissions

    def test_schedule_with_multiple_runs(self):
        """Test scheduling with multiple runs to check randomness."""
        from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
        
        # Create mock submission
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = RandomScheduler(config)
        
        # Run multiple times to check that we get different results (randomness)
        results = []
        for _ in range(5):
            result = scheduler.schedule()
            results.append(result["paper1"])
        
        # Check that we get at least some different dates (not all the same)
        unique_dates = set(results)
        assert len(unique_dates) > 1
