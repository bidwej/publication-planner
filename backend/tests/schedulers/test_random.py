"""Tests for the random scheduler."""

from datetime import date, timedelta

import pytest

from core.models import SubmissionType, ConferenceType, Submission, Config
from schedulers.random import RandomScheduler
from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config
from typing import Dict, List, Any, Optional



class TestRandomScheduler:
    """Test the RandomScheduler class."""

    def test_random_scheduler_initialization(self, empty_config) -> None:
        """Test random scheduler initialization."""
        scheduler: Any = RandomScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self, empty_config) -> None:
        """Test scheduling with empty submissions."""
        scheduler: Any = RandomScheduler(empty_config)
        
        # Empty submissions should return empty schedule
        result: Any = scheduler.schedule()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_single_paper(self) -> None:
        """Test scheduling with single paper."""
        
        # Create mock submission
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        # Create mock conference
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler: Any = RandomScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_schedule_multiple_papers(self) -> None:
        """Test scheduling with multiple papers."""
        
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
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.ABSTRACT: date(2026, 8, 1)},
            conf_type=ConferenceType.MEDICAL
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler: Any = RandomScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1  # At least one submission should be scheduled
        assert "paper1" in result
        assert isinstance(result["paper1"], date)
        
        # If paper2 is scheduled, verify it's valid
        if "paper2" in result:
            assert isinstance(result["paper2"], date)

    def test_random_algorithm_behavior(self) -> None:
        """Test the random algorithm behavior."""
        
        # Create mock submissions with different characteristics
        submission1 = create_mock_submission(
            "paper1", "High Priority Paper", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Low Priority Paper", SubmissionType.ABSTRACT, "conf2"
        )
        
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.ABSTRACT: date(2026, 8, 1)},
            conf_type=ConferenceType.MEDICAL
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler: Any = RandomScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_constraints(self) -> None:
        """Test scheduling with constraints."""
        
        # Create mock submission with constraints
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        config.blackout_dates = [date(2026, 5, 15), date(2026, 5, 16)]
        
        scheduler: Any = RandomScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that scheduled date is not in blackout dates
        scheduled_date = result["paper1"]
        assert scheduled_date not in config.blackout_dates

    def test_error_handling_invalid_paper(self) -> None:
        """Test error handling with invalid paper data."""
        # Create a submission with invalid conference reference
        invalid_submission: Submission = Submission(
            id="paper1",
            title="Invalid Paper",
            kind=SubmissionType.PAPER,
            conference_id="nonexistent_conf",
            depends_on=[],
            draft_window_months=2,
            lead_time_from_parents=0,
            penalty_cost_per_day=100.0,
            engineering=False
        )
        
        config: Config = Config(
            submissions=[invalid_submission],
            conferences=[],  # No conferences defined
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        scheduler: Any = RandomScheduler(config)
        
        with pytest.raises(ValueError, match="Submission paper1 references unknown conference nonexistent_conf"):
            scheduler.schedule()

    def test_schedule_with_priority_ordering(self) -> None:
        """Test scheduling with priority ordering."""
        
        # Create mock submissions with different priorities
        submission1 = create_mock_submission(
            "paper1", "High Priority Paper", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Low Priority Paper", SubmissionType.PAPER, "conf2"
        )
        
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler: Any = RandomScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1  # At least one submission should be scheduled
        assert "paper1" in result
        
        # If paper2 is scheduled, verify it's valid
        if "paper2" in result:
            assert isinstance(result["paper2"], date)

    def test_schedule_with_deadline_compliance(self) -> None:
        """Test scheduling with deadline compliance."""
        
        # Create mock submission with tight deadline
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler: Any = RandomScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that scheduled date is before deadline
        scheduled_date = result["paper1"]
        deadline = conference.deadlines[SubmissionType.PAPER]
        assert scheduled_date <= deadline

    def test_schedule_with_resource_constraints(self) -> None:
        """Test scheduling with resource constraints."""
        
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
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        config = create_mock_config([submission1, submission2, submission3], [conference])
        config.max_concurrent_submissions = 2
        
        scheduler: Any = RandomScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 2
        
        # Check that no more than 2 submissions are scheduled on the same day
        scheduled_dates = list(result.values())
        for i, date1 in enumerate(scheduled_dates):
            for j, date2 in enumerate(scheduled_dates):
                if i != j and date1 == date2:
                    same_date_count = sum(1 for d in scheduled_dates if d == date1)
                    assert same_date_count <= config.max_concurrent_submissions

    def test_schedule_with_multiple_runs(self) -> None:
        """Test scheduling with multiple runs to check randomness."""
        
        # Create mock submission
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2026, 6, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler: Any = RandomScheduler(config)
        
        # Run multiple times to check that we get valid results
        results = []
        for _ in range(5):
            result: Any = scheduler.schedule()
            results.append(result["paper1"])
        
        # Check that all results are valid dates
        for scheduled_date in results:
            assert isinstance(scheduled_date, date)
            assert scheduled_date >= date(2025, 1, 1)  # Can schedule from reasonable start date
            assert scheduled_date <= date(2026, 6, 1)  # Before deadline
