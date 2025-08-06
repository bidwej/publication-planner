"""Tests for the optimal scheduler."""

from datetime import date
from unittest.mock import Mock

from src.core.models import Submission, Config
from src.schedulers.optimal import OptimalScheduler


class TestOptimalScheduler:
    """Test the OptimalScheduler class."""

    def test_optimal_scheduler_initialization(self):
        """Test optimal scheduler initialization."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        scheduler = OptimalScheduler(config)
        
        assert scheduler.config == config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self):
        """Test scheduling with empty submissions."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_single_paper(self):
        """Test scheduling with single paper."""
        # Create mock paper
        paper = Mock(spec=Submission)
        paper.id = "paper1"
        paper.title = "Test Paper"
        paper.deadline = date(2024, 6, 1)
        paper.estimated_hours = 40
        paper.kind = Mock(value="PAPER")
        paper.conference_id = "conf1"
        paper.draft_window_months = 3
        
        config = Mock(spec=Config)
        config.submissions = [paper]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_schedule_multiple_papers(self):
        """Test scheduling with multiple papers."""
        # Create mock papers
        paper1 = Mock(spec=Submission)
        paper1.id = "paper1"
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Submission)
        paper2.id = "paper2"
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="ABSTRACT")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 0
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
        assert isinstance(result["paper1"], date)
        assert isinstance(result["paper2"], date)

    def test_optimal_algorithm_behavior(self):
        """Test the optimal algorithm behavior."""
        # Create mock papers with different deadlines
        paper1 = Mock(spec=Submission)
        paper1.id = "paper1"
        paper1.title = "Early Deadline Paper"
        paper1.deadline = date(2024, 4, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Submission)
        paper2.id = "paper2"
        paper2.title = "Late Deadline Paper"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="PAPER")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 3
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
        
        # Optimal should prioritize early deadlines
        if result["paper1"] and result["paper2"]:
            # Early deadline paper should be scheduled before late deadline paper
            assert result["paper1"] <= result["paper2"]

    def test_schedule_with_constraints(self):
        """Test scheduling with constraints."""
        # Create mock paper with constraints
        paper = Mock(spec=Submission)
        paper.id = "paper1"
        paper.title = "Test Paper"
        paper.deadline = date(2024, 6, 1)
        paper.estimated_hours = 40
        paper.kind = Mock(value="PAPER")
        paper.conference_id = "conf1"
        paper.draft_window_months = 3
        
        config = Mock(spec=Config)
        config.submissions = [paper]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        config.blackout_dates = [date(2024, 5, 15), date(2024, 5, 16)]
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that scheduled date is not in blackout dates
        scheduled_date = result["paper1"]
        assert scheduled_date not in config.blackout_dates

    def test_schedule_with_optimization_objective(self):
        """Test scheduling with different optimization objectives."""
        # Create mock papers
        paper1 = Mock(spec=Submission)
        paper1.id = "paper1"
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Submission)
        paper2.id = "paper2"
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="PAPER")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 3
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        
        scheduler = OptimalScheduler(config)
        
        # Test with different optimization objectives
        result_min_makespan = scheduler.schedule(objective="min_makespan")
        result_min_penalty = scheduler.schedule(objective="min_penalty")
        
        assert isinstance(result_min_makespan, dict)
        assert isinstance(result_min_penalty, dict)
        assert len(result_min_makespan) == 2
        assert len(result_min_penalty) == 2

    def test_error_handling_invalid_paper(self):
        """Test error handling with invalid paper data."""
        # Create mock paper with invalid data
        paper = Mock(spec=Submission)
        paper.id = "paper1"
        paper.title = "Test Paper"
        paper.deadline = None  # Invalid deadline
        paper.estimated_hours = 40
        paper.kind = Mock(value="PAPER")
        paper.conference_id = "conf1"
        paper.draft_window_months = 3
        
        config = Mock(spec=Config)
        config.submissions = [paper]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        
        scheduler = OptimalScheduler(config)
        
        # Should handle invalid data gracefully
        result = scheduler.schedule()
        
        assert isinstance(result, dict)

    def test_schedule_with_priority_ordering(self):
        """Test scheduling with priority-based ordering."""
        # Create mock papers with different priorities
        paper1 = Mock(spec=Submission)
        paper1.id = "paper1"
        paper1.title = "High Priority Paper"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        paper1.priority = "high"
        
        paper2 = Mock(spec=Submission)
        paper2.id = "paper2"
        paper2.title = "Low Priority Paper"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="ABSTRACT")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 0
        paper2.priority = "low"
        
        config = Mock(spec=Config)
        config.submissions = [paper2, paper1]  # Low priority first
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_deadline_compliance(self):
        """Test scheduling with deadline compliance focus."""
        # Create mock papers with tight deadlines
        paper1 = Mock(spec=Submission)
        paper1.id = "paper1"
        paper1.title = "Tight Deadline Paper"
        paper1.deadline = date(2024, 3, 1)
        paper1.estimated_hours = 80
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Submission)
        paper2.id = "paper2"
        paper2.title = "Flexible Deadline Paper"
        paper2.deadline = date(2024, 12, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="PAPER")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 3
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
        
        # Check that tight deadline paper is scheduled before its deadline
        if result["paper1"]:
            assert result["paper1"] <= paper1.deadline

    def test_schedule_with_resource_optimization(self):
        """Test scheduling with resource optimization."""
        # Create mock papers with different resource requirements
        paper1 = Mock(spec=Submission)
        paper1.id = "paper1"
        paper1.title = "Resource Intensive Paper"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 200
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Submission)
        paper2.id = "paper2"
        paper2.title = "Light Paper"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 20
        paper2.kind = Mock(value="ABSTRACT")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 0
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        config.max_hours_per_day = 8
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_complex_constraints(self):
        """Test scheduling with complex constraints."""
        # Create mock papers with complex constraints
        paper1 = Mock(spec=Submission)
        paper1.id = "paper1"
        paper1.title = "Complex Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Submission)
        paper2.id = "paper2"
        paper2.title = "Complex Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="PAPER")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 3
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        config.blackout_dates = [date(2024, 5, 15), date(2024, 5, 16)]
        config.max_hours_per_day = 8
        config.max_papers_per_month = 2
        
        scheduler = OptimalScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
