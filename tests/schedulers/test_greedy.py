"""Tests for greedy scheduler."""

import pytest
from datetime import date, timedelta
from src.core.models import SubmissionType, Config, Submission, Conference, ConferenceType, ConferenceRecurrence, SchedulerStrategy
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.stochastic import StochasticGreedyScheduler
from src.schedulers.lookahead import LookaheadGreedyScheduler
from src.schedulers.backtracking import BacktrackingGreedyScheduler
from src.core.constraints import validate_all_constraints
from src.scoring.penalty import calculate_penalty_score
from src.scoring.quality import calculate_quality_score
from src.scoring.efficiency import calculate_efficiency_score
from typing import Set

class TestGreedyScheduler:
    """Test the greedy scheduler."""
    
    def test_basic_scheduling(self, greedy_scheduler):
        """Test basic scheduling functionality."""
        schedule = greedy_scheduler.schedule()
        
        assert isinstance(schedule, dict)
        assert len(schedule) > 0
        
        # Check that all scheduled submissions have valid dates
        for sid, start_date in schedule.items():
            assert isinstance(start_date, date)
            assert start_date >= date(2024, 1, 1)  # Reasonable start date
    
    def test_dependency_satisfaction(self, greedy_scheduler):
        """Test that dependencies are satisfied."""
        schedule = greedy_scheduler.schedule()
        
        # Check parent-child relationships
        for sid, start_date in schedule.items():
            sub = greedy_scheduler.submissions[sid]
            if sub.depends_on:
                for parent_id in sub.depends_on:
                    if parent_id in schedule:
                        parent_start = schedule[parent_id]
                        # Child should start after parent
                        assert start_date >= parent_start
    
    def test_concurrency_limit(self, greedy_scheduler):
        """Test that concurrency limits are respected."""
        schedule = greedy_scheduler.schedule()
        
        # Calculate daily workload
        daily_load = {}
        for sid, start_date in schedule.items():
            sub = greedy_scheduler.submissions[sid]
            duration = greedy_scheduler.config.min_paper_lead_time_days if sub.kind == SubmissionType.PAPER else 0
            
            for i in range(duration + 1):
                day = start_date + timedelta(days=i)
                daily_load[day] = daily_load.get(day, 0) + 1
        
        # Check that no day exceeds the concurrency limit
        max_concurrent = greedy_scheduler.config.max_concurrent_submissions
        for day, count in daily_load.items():
            assert count <= max_concurrent
    
    def test_constraint_validation(self, greedy_scheduler):
        """Test constraint validation using the new constraints module."""
        schedule = greedy_scheduler.schedule()
        
        # Use the new constraints module
        validation_result = validate_all_constraints(schedule, greedy_scheduler.config)
        
        # The schedule should be valid
        assert validation_result.is_valid
        assert validation_result.deadlines.is_valid
        assert validation_result.dependencies.is_valid
        assert validation_result.resources.is_valid
    
    def test_constraint_validation_with_invalid_schedule(self, greedy_scheduler):
        """Test constraint validation with an invalid schedule."""
        # Create an invalid schedule (impossible dates)
        invalid_schedule = {
            "paper1": date(2020, 1, 1),  # Too early
            "paper2": date(2020, 1, 1),  # Same day as paper1
        }
        
        # Use the new constraints module
        validation_result = validate_all_constraints(invalid_schedule, greedy_scheduler.config)
        
        # The schedule should be invalid
        assert not validation_result.is_valid
    
    def test_constraint_validation_with_dependency_violation(self, greedy_scheduler):
        """Test constraint validation with dependency violations."""
        # Create a schedule where child starts before parent
        schedule = greedy_scheduler.schedule()
        
        # Find a parent-child pair
        parent_id = None
        child_id = None
        for sid, sub in greedy_scheduler.submissions.items():
            if sub.depends_on:
                parent_id = sub.depends_on[0]
                child_id = sid
                break
        
        if parent_id and child_id and parent_id in schedule and child_id in schedule:
            # Create invalid schedule where child starts before parent
            invalid_schedule = schedule.copy()
            invalid_schedule[child_id] = schedule[parent_id] - timedelta(days=1)
            
            # Use the new constraints module
            validation_result = validate_all_constraints(invalid_schedule, greedy_scheduler.config)
            
            # Should detect dependency violation
            assert not validation_result.dependencies.is_valid
    
    def test_scoring_integration(self, greedy_scheduler):
        """Test integration with scoring functions."""
        schedule = greedy_scheduler.schedule()
        
        # Test penalty scoring
        penalty_breakdown = calculate_penalty_score(schedule, greedy_scheduler.config)
        assert isinstance(penalty_breakdown.total_penalty, (int, float))
        assert penalty_breakdown.total_penalty >= 0
        
        # Test quality scoring
        quality_score = calculate_quality_score(schedule, greedy_scheduler.config)
        assert isinstance(quality_score, float)
        assert 0 <= quality_score <= 1
        
        # Test efficiency scoring
        efficiency_score = calculate_efficiency_score(schedule, greedy_scheduler.config)
        assert isinstance(efficiency_score, float)
        assert 0 <= efficiency_score <= 1


class TestGreedySchedulerStrategyRegistry:
    """Test the strategy registry functionality."""
    
    def test_strategy_registry(self):
        """Test that strategies are properly registered."""
        from schedulers.base import BaseScheduler
        
        # Check that all strategies are registered
        assert SchedulerStrategy.GREEDY in BaseScheduler._strategies
        assert SchedulerStrategy.STOCHASTIC in BaseScheduler._strategies
        assert SchedulerStrategy.LOOKAHEAD in BaseScheduler._strategies
        assert SchedulerStrategy.BACKTRACKING in BaseScheduler._strategies
    
    def test_create_scheduler_via_registry(self, minimal_config):
        """Test creating schedulers via the registry."""
        from schedulers.base import BaseScheduler
        
        # Test each strategy
        for strategy in SchedulerStrategy:
            scheduler = BaseScheduler.create_scheduler(strategy, minimal_config)
            assert isinstance(scheduler, BaseScheduler)
            assert scheduler.config == minimal_config
    
    def test_invalid_strategy(self, minimal_config):
        """Test that invalid strategies raise an error."""
        from schedulers.base import BaseScheduler
        
        with pytest.raises(ValueError, match="Unknown strategy"):
            # Pass a string instead of SchedulerStrategy enum
            BaseScheduler.create_scheduler("invalid_strategy", minimal_config) 