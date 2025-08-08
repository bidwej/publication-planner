"""Tests for the heuristic scheduler."""

import pytest
from datetime import date

from core.models import SubmissionType, ConferenceType, Submission, Config
from schedulers.heuristic import HeuristicScheduler
from typing import Dict, List, Any, Optional



class TestHeuristicScheduler:
    """Test the HeuristicScheduler class."""

    def test_heuristic_scheduler_initialization(self, empty_config) -> None:
        """Test heuristic scheduler initialization."""
        scheduler: Any = HeuristicScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self, empty_config) -> None:
        """Test scheduling with empty submissions."""
        scheduler: Any = HeuristicScheduler(empty_config)
        
        # Empty submissions should return empty schedule
        result: Any = scheduler.schedule()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_single_paper(self) -> None:
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
        
        scheduler: Any = HeuristicScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_schedule_multiple_papers(self) -> None:
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
            {SubmissionType.ABSTRACT: date(2024, 8, 1)},
            conf_type=ConferenceType.MEDICAL
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler: Any = HeuristicScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1  # At least one submission should be scheduled
        assert "paper1" in result
        assert isinstance(result["paper1"], date)
        
        # If paper2 is scheduled, verify it's valid
        if "paper2" in result:
            assert isinstance(result["paper2"], date)

    def test_heuristic_algorithm_behavior(self) -> None:
        """Test the heuristic algorithm behavior."""
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
            {SubmissionType.ABSTRACT: date(2024, 8, 1)},
            conf_type=ConferenceType.MEDICAL
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler: Any = HeuristicScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1  # At least one submission should be scheduled
        assert "paper1" in result
        
        # If paper2 is scheduled, verify it's valid
        if "paper2" in result:
            assert isinstance(result["paper2"], date)

    def test_schedule_with_constraints(self) -> None:
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
        
        scheduler: Any = HeuristicScheduler(config)
        
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
        
        scheduler: Any = HeuristicScheduler(config)
        
        with pytest.raises(ValueError, match="Submission paper1 references unknown conference nonexistent_conf"):
            scheduler.schedule()

    def test_schedule_with_priority_ordering(self) -> None:
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
        
        scheduler: Any = HeuristicScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1  # At least one submission should be scheduled
        assert "paper1" in result
        
        # If paper2 is scheduled, verify it's valid
        if "paper2" in result:
            assert isinstance(result["paper2"], date)

    def test_schedule_with_deadline_compliance(self) -> None:
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
        
        scheduler: Any = HeuristicScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that scheduled date is before deadline
        scheduled_date = result["paper1"]
        deadline = conference.deadlines[SubmissionType.PAPER]
        assert scheduled_date <= deadline

    def test_schedule_with_resource_optimization(self) -> None:
        """Test scheduling with resource optimization."""
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
        
        scheduler: Any = HeuristicScheduler(config)
        
        result: Any = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1  # At least one submission should be scheduled
        
        # Check that no more than 2 submissions are scheduled on the same day
        if len(result) > 1:
            scheduled_dates = list(result.values())
            for i, date1 in enumerate(scheduled_dates):
                for j, date2 in enumerate(scheduled_dates):
                    if i != j and date1 == date2:
                        same_date_count = sum(1 for d in scheduled_dates if d == date1)
                        assert same_date_count <= config.max_concurrent_submissions
