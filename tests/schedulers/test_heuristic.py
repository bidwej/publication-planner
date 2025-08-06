"""Tests for the heuristic scheduler."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock

from core.models import Paper, Schedule, ScheduleItem, Config
from schedulers.heuristic import HeuristicScheduler


class TestHeuristicScheduler:
    """Test the HeuristicScheduler class."""

    def test_heuristic_scheduler_initialization(self):
        """Test heuristic scheduler initialization."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        scheduler = HeuristicScheduler(config)
        
        assert scheduler.config == config
        assert hasattr(scheduler, 'schedule')

    def test_schedule_empty_submissions(self):
        """Test scheduling with empty submissions."""
        config = Mock(spec=Config)
        config.submissions = []
        config.conferences = []
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_single_paper(self):
        """Test scheduling with single paper."""
        # Create mock paper
        paper = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_schedule_multiple_papers(self):
        """Test scheduling with multiple papers."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
        assert isinstance(result["paper1"], date)
        assert isinstance(result["paper2"], date)

    def test_heuristic_algorithm_behavior(self):
        """Test the heuristic algorithm behavior."""
        # Create mock papers with different deadlines
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Early Deadline Paper"
        paper1.deadline = date(2024, 4, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
        
        # Heuristic should prioritize early deadlines
        if result["paper1"] and result["paper2"]:
            # Early deadline paper should be scheduled before late deadline paper
            assert result["paper1"] <= result["paper2"]

    def test_schedule_with_constraints(self):
        """Test scheduling with constraints."""
        # Create mock paper with constraints
        paper = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        
        # Check that scheduled date is not in blackout dates
        scheduled_date = result["paper1"]
        assert scheduled_date not in config.blackout_dates

    def test_schedule_with_heuristic_rules(self):
        """Test scheduling with different heuristic rules."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        # Test with different heuristic rules
        result_earliest_deadline = scheduler.schedule(rule="earliest_deadline")
        result_shortest_processing = scheduler.schedule(rule="shortest_processing")
        result_priority_weighted = scheduler.schedule(rule="priority_weighted")
        
        assert isinstance(result_earliest_deadline, dict)
        assert isinstance(result_shortest_processing, dict)
        assert isinstance(result_priority_weighted, dict)
        assert len(result_earliest_deadline) == 2
        assert len(result_shortest_processing) == 2
        assert len(result_priority_weighted) == 2

    def test_error_handling_invalid_paper(self):
        """Test error handling with invalid paper data."""
        # Create mock paper with invalid data
        paper = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        # Should handle invalid data gracefully
        result = scheduler.schedule()
        
        assert isinstance(result, dict)

    def test_schedule_with_priority_ordering(self):
        """Test scheduling with priority-based ordering."""
        # Create mock papers with different priorities
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "High Priority Paper"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        paper1.priority = "high"
        
        paper2 = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_deadline_compliance(self):
        """Test scheduling with deadline compliance focus."""
        # Create mock papers with tight deadlines
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Tight Deadline Paper"
        paper1.deadline = date(2024, 3, 1)
        paper1.estimated_hours = 80
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
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
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Resource Intensive Paper"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 200
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result

    def test_schedule_with_heuristic_weights(self):
        """Test scheduling with heuristic weights."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
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
        
        scheduler = HeuristicScheduler(config)
        
        # Test with different weight combinations
        result_balanced = scheduler.schedule(deadline_weight=0.5, processing_weight=0.5)
        result_deadline_focused = scheduler.schedule(deadline_weight=0.8, processing_weight=0.2)
        result_processing_focused = scheduler.schedule(deadline_weight=0.2, processing_weight=0.8)
        
        assert isinstance(result_balanced, dict)
        assert isinstance(result_deadline_focused, dict)
        assert isinstance(result_processing_focused, dict)
        assert len(result_balanced) == 2
        assert len(result_deadline_focused) == 2
        assert len(result_processing_focused) == 2

    def test_schedule_with_complex_heuristics(self):
        """Test scheduling with complex heuristic combinations."""
        # Create mock papers with complex characteristics
        paper1 = Mock(spec=Paper)
        paper1.id = "paper1"
        paper1.title = "Complex Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        paper1.priority = "high"
        
        paper2 = Mock(spec=Paper)
        paper2.id = "paper2"
        paper2.title = "Complex Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="PAPER")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 3
        paper2.priority = "low"
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences = [Mock()]
        config.start_date = date(2024, 1, 1)
        config.end_date = date(2024, 12, 31)
        config.min_paper_lead_time_days = 90
        config.blackout_dates = [date(2024, 5, 15), date(2024, 5, 16)]
        config.max_hours_per_day = 8
        config.max_papers_per_month = 2
        
        scheduler = HeuristicScheduler(config)
        
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paper1" in result
        assert "paper2" in result
