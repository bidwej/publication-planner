"""Tests for the backtracking scheduler."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.core.models import Submission, Config, SubmissionType
from src.schedulers.backtracking import BacktrackingScheduler


class TestBacktrackingScheduler:
    """Test the BacktrackingScheduler class."""

    def test_backtracking_scheduler_initialization(self):
        """Test backtracking scheduler initialization."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        scheduler = BacktrackingScheduler(config)
        
        assert scheduler.config == config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self):
        """Test scheduling with empty submissions."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_single_paper(self):
        """Test scheduling with single paper."""
        # Create mock submission
        submission = Mock(spec=Submission)
        submission.id = "sub1"
        submission.title = "Test Paper"
        submission.kind = SubmissionType.PAPER
        submission.conference_id = "conf1"
        submission.draft_window_months = 3
        submission.earliest_start_date = date(2024, 1, 1)
        
        config = Mock(spec=Config)
        config.submissions = [submission]
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "sub1" in result
        assert isinstance(result["sub1"], date)

    def test_schedule_multiple_papers(self):
        """Test scheduling with multiple papers."""
        # Create mock submissions
        submission1 = Mock(spec=Submission)
        submission1.id = "sub1"
        submission1.title = "Test Paper 1"
        submission1.kind = SubmissionType.PAPER
        submission1.conference_id = "conf1"
        submission1.draft_window_months = 3
        submission1.earliest_start_date = date(2024, 1, 1)
        
        submission2 = Mock(spec=Submission)
        submission2.id = "sub2"
        submission2.title = "Test Paper 2"
        submission2.kind = SubmissionType.ABSTRACT
        submission2.conference_id = "conf2"
        submission2.draft_window_months = 0
        submission2.earliest_start_date = date(2024, 1, 1)
        
        config = Mock(spec=Config)
        config.submissions = [submission1, submission2]
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
        
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
        submission = Mock(spec=Submission)
        submission.id = "sub1"
        submission.title = "Test Paper"
        submission.kind = SubmissionType.PAPER
        submission.conference_id = "conf1"
        submission.draft_window_months = 3
        submission.earliest_start_date = date(2024, 1, 1)
        
        config = Mock(spec=Config)
        config.submissions = [submission]
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
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
        # Create mock paper with very short deadline
        submission = Mock(spec=Submission)
        submission.id = "sub1"
        submission.title = "Test Paper"
        submission.kind = SubmissionType.PAPER
        submission.conference_id = "conf1"
        submission.draft_window_months = 3
        submission.earliest_start_date = date(2024, 1, 15)  # Start after deadline
        submission.deadline = date(2024, 2, 1)  # Very early deadline
        submission.estimated_hours = 200  # Very long paper
        
        config = Mock(spec=Config)
        config.submissions = [submission]
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
        
        scheduler = BacktrackingScheduler(config)
        
        # Should handle insufficient time gracefully
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        # May return empty dict or handle the constraint

    def test_backtracking_algorithm(self):
        """Test the backtracking algorithm behavior."""
        # Create mock papers with conflicting deadlines
        submission1 = Mock(spec=Submission)
        submission1.id = "sub1"
        submission1.title = "Test Paper 1"
        submission1.kind = SubmissionType.PAPER
        submission1.conference_id = "conf1"
        submission1.draft_window_months = 3
        submission1.earliest_start_date = date(2024, 1, 1)
        submission1.deadline = date(2024, 6, 1)
        submission1.estimated_hours = 80
        
        submission2 = Mock(spec=Submission)
        submission2.id = "sub2"
        submission2.title = "Test Paper 2"
        submission2.kind = SubmissionType.PAPER
        submission2.conference_id = "conf2"
        submission2.draft_window_months = 3
        submission2.earliest_start_date = date(2024, 1, 1)
        submission2.deadline = date(2024, 6, 15)
        submission2.estimated_hours = 60
        
        config = Mock(spec=Config)
        config.submissions = [submission1, submission2]
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "sub1" in result
        assert "sub2" in result
        
        # Check that papers are scheduled before their deadlines
        if result["sub1"]:
            assert result["sub1"] <= submission1.deadline
        if result["sub2"]:
            assert result["sub2"] <= submission2.deadline

    def test_error_handling_invalid_paper(self):
        """Test error handling with invalid paper data."""
        # Create mock paper with invalid data
        submission = Mock(spec=Submission)
        submission.id = "sub1"
        submission.title = "Test Paper"
        submission.kind = SubmissionType.PAPER
        submission.conference_id = "conf1"
        submission.draft_window_months = 3
        submission.earliest_start_date = date(2024, 1, 1)
        submission.deadline = None  # Invalid deadline
        submission.estimated_hours = 40
        
        config = Mock(spec=Config)
        config.submissions = [submission]
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
        
        scheduler = BacktrackingScheduler(config)
        
        # Should handle invalid data gracefully
        result = scheduler.schedule()
        
        assert isinstance(result, dict)

    def test_schedule_with_priority_ordering(self):
        """Test scheduling with priority-based ordering."""
        # Create mock papers with different priorities
        submission1 = Mock(spec=Submission)
        submission1.id = "sub1"
        submission1.title = "High Priority Paper"
        submission1.kind = SubmissionType.PAPER
        submission1.conference_id = "conf1"
        submission1.draft_window_months = 3
        submission1.earliest_start_date = date(2024, 1, 1)
        submission1.deadline = date(2024, 6, 1)
        submission1.estimated_hours = 40
        submission1.priority = "high"
        
        submission2 = Mock(spec=Submission)
        submission2.id = "sub2"
        submission2.title = "Low Priority Paper"
        submission2.kind = SubmissionType.ABSTRACT
        submission2.conference_id = "conf2"
        submission2.draft_window_months = 0
        submission2.earliest_start_date = date(2024, 1, 1)
        submission2.deadline = date(2024, 8, 1)
        submission2.estimated_hours = 60
        submission2.priority = "low"
        
        config = Mock(spec=Config)
        config.submissions = [submission2, submission1]  # Low priority first
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "sub1" in result
        assert "sub2" in result

    def test_schedule_with_resource_constraints(self):
        """Test scheduling with resource constraints."""
        # Create mock papers that require significant resources
        submission1 = Mock(spec=Submission)
        submission1.id = "sub1"
        submission1.title = "Resource Intensive Paper"
        submission1.kind = SubmissionType.PAPER
        submission1.conference_id = "conf1"
        submission1.draft_window_months = 3
        submission1.earliest_start_date = date(2024, 1, 1)
        submission1.deadline = date(2024, 6, 1)
        submission1.estimated_hours = 200  # Very resource intensive
        
        submission2 = Mock(spec=Submission)
        submission2.id = "sub2"
        submission2.title = "Light Paper"
        submission2.kind = SubmissionType.ABSTRACT
        submission2.conference_id = "conf2"
        submission2.draft_window_months = 0
        submission2.earliest_start_date = date(2024, 1, 1)
        submission2.deadline = date(2024, 8, 1)
        submission2.estimated_hours = 20  # Light paper
        
        config = Mock(spec=Config)
        config.submissions = [submission1, submission2]
        config.conferences = [Mock()]
        config.min_paper_lead_time_days = 90
        config.max_hours_per_day = 8  # Resource constraint
        
        scheduler = BacktrackingScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "sub1" in result
        assert "sub2" in result
