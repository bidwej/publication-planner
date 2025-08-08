"""Tests for the stochastic scheduler."""

from datetime import date, timedelta

import pytest

from src.core.models import SubmissionType, ConferenceType
from src.schedulers.stochastic import StochasticGreedyScheduler
from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config


class TestStochasticScheduler:
    """Test the stochastic scheduler functionality."""

    def test_stochastic_scheduler_initialization(self, empty_config):
        """Test stochastic scheduler initialization."""
        scheduler = StochasticGreedyScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')
        assert hasattr(scheduler, 'randomness_factor')

    def test_schedule_empty_submissions(self, empty_config):
        """Test scheduling with empty submissions."""
        scheduler = StochasticGreedyScheduler(empty_config)
        
        result = scheduler.schedule()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_single_paper(self):
        """Test scheduling with a single paper."""
        # Create mock submission
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        # Create mock conference
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = StochasticGreedyScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_schedule_multiple_papers(self):
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
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.ABSTRACT: date(2025, 10, 1)},
            conf_type=ConferenceType.MEDICAL
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler = StochasticGreedyScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
        assert isinstance(result["paper1"], date)
        assert isinstance(result["paper2"], date)

    def test_stochastic_algorithm_behavior(self):
        """Test the stochastic algorithm behavior."""
        # Create mock submissions with different characteristics
        submission1 = create_mock_submission(
            "paper1", "High Priority Paper", SubmissionType.PAPER, "conf1"
        )
        
        submission2 = create_mock_submission(
            "paper2", "Low Priority Paper", SubmissionType.ABSTRACT, "conf2"
        )
        
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.ABSTRACT: date(2025, 10, 1)},
            conf_type=ConferenceType.MEDICAL
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler = StochasticGreedyScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_constraints(self):
        """Test scheduling with constraints."""
        # Create mock submission with constraints
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = StochasticGreedyScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_error_handling_invalid_paper(self):
        """Test error handling for invalid paper."""
        # Create mock submission with invalid conference reference
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "nonexistent_conf"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = StochasticGreedyScheduler(config)
        
        # Should handle gracefully without raising an error
        result = scheduler.schedule()
        assert isinstance(result, dict)

    def test_schedule_with_priority_ordering(self):
        """Test scheduling with priority ordering."""
        # Create mock submissions with different priorities
        submission1 = create_mock_submission(
            "paper1", "High Priority Paper", SubmissionType.PAPER, "conf1",
            engineering=True
        )
        
        submission2 = create_mock_submission(
            "paper2", "Low Priority Paper", SubmissionType.PAPER, "conf2",
            engineering=False
        )
        
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler = StochasticGreedyScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_deadline_compliance(self):
        """Test scheduling with deadline compliance."""
        # Create mock submission with tight deadline
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        
        config = create_mock_config([submission], [conference])
        
        scheduler = StochasticGreedyScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that the scheduled date meets the deadline
        scheduled_date = result["paper1"]
        end_date = scheduled_date + timedelta(days=config.min_paper_lead_time_days)
        assert end_date <= date(2025, 12, 1)
