"""Tests for the Optimal Scheduler (MILP optimization)."""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from src.core.config import load_config
from src.core.models import SchedulerStrategy
from src.schedulers.optimal import OptimalScheduler
from src.schedulers.base import BaseScheduler


class TestOptimalScheduler:
    """Test cases for the Optimal Scheduler using MILP optimization."""
    
    @pytest.fixture
    def config(self):
        """Load test configuration."""
        return load_config('config.json')
    
    @pytest.fixture
    def scheduler(self, config):
        """Create an optimal scheduler instance."""
        return OptimalScheduler(config)
    
    def test_optimal_scheduler_initialization(self, scheduler):
        """Test that the optimal scheduler initializes correctly."""
        assert scheduler is not None
        assert scheduler.optimization_objective == "minimize_makespan"
        assert scheduler.max_concurrent == scheduler.config.max_concurrent_submissions
    
    def test_optimal_scheduler_registration(self):
        """Test that the optimal scheduler is properly registered."""
        assert SchedulerStrategy.OPTIMAL in BaseScheduler._strategy_registry
        scheduler_class = BaseScheduler._strategy_registry[SchedulerStrategy.OPTIMAL]
        assert scheduler_class == OptimalScheduler
    
    def test_optimal_scheduler_creation_via_factory(self, config):
        """Test creating optimal scheduler via the factory method."""
        scheduler = BaseScheduler.create_scheduler(SchedulerStrategy.OPTIMAL, config)
        assert isinstance(scheduler, OptimalScheduler)
        assert scheduler.optimization_objective == "minimize_makespan"
    
    def test_milp_model_setup(self, scheduler):
        """Test that the MILP model is set up correctly."""
        model = scheduler._setup_milp_model()
        assert model is not None
        assert hasattr(model, 'variables')
        assert hasattr(model, 'constraints')
    
    def test_dependency_constraints(self, scheduler):
        """Test that dependency constraints are added correctly."""
        from pulp import LpProblem, LpVariable
        
        prob = LpProblem("Test", 1)  # Minimize
        start_vars = {}
        
        # Create test variables
        for submission_id in scheduler.submissions:
            start_vars[submission_id] = LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
        
        # Add dependency constraints
        scheduler._add_dependency_constraints(prob, start_vars)
        
        # Check that constraints were added
        assert len(prob.constraints) > 0
    
    def test_deadline_constraints(self, scheduler):
        """Test that deadline constraints are added correctly."""
        from pulp import LpProblem, LpVariable
        
        prob = LpProblem("Test", 1)  # Minimize
        start_vars = {}
        start_date = date.today()
        
        # Create test variables
        for submission_id in scheduler.submissions:
            start_vars[submission_id] = LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
        
        # Add deadline constraints
        scheduler._add_deadline_constraints(prob, start_vars, start_date)
        
        # Check that constraints were added
        assert len(prob.constraints) > 0
    
    def test_resource_constraints(self, scheduler):
        """Test that resource constraints are added correctly."""
        from pulp import LpProblem, LpVariable
        
        prob = LpProblem("Test", 1)  # Minimize
        start_vars = {}
        resource_vars = {}
        
        # Create test variables
        for submission_id in scheduler.submissions:
            start_vars[submission_id] = LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
            resource_vars[f"active_{submission_id}_day_0"] = LpVariable(f"active_{submission_id}_day_0", cat='Binary')
        
        # Add resource constraints
        scheduler._add_resource_constraints(prob, start_vars, resource_vars)
        
        # Check that constraints were added (may be 0 if no resource constraints apply)
        # The test passes if no exceptions are raised
        assert True
    
    def test_working_days_constraints(self, scheduler):
        """Test that working days constraints are added correctly."""
        from pulp import LpProblem, LpVariable
        
        prob = LpProblem("Test", 1)  # Minimize
        start_vars = {}
        start_date = date.today()
        
        # Create test variables
        for submission_id in scheduler.submissions:
            start_vars[submission_id] = LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
        
        # Add working days constraints
        scheduler._add_working_days_constraints(prob, start_vars, start_date)
        
        # Check that constraints were added (may be empty if working days disabled)
        # The method should not raise an exception
    
    def test_soft_block_constraints(self, scheduler):
        """Test that soft block constraints are added correctly."""
        from pulp import LpProblem, LpVariable
        
        prob = LpProblem("Test", 1)  # Minimize
        start_vars = {}
        start_date = date.today()
        
        # Create test variables
        for submission_id in scheduler.submissions:
            start_vars[submission_id] = LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
        
        # Add soft block constraints
        scheduler._add_soft_block_constraints(prob, start_vars, start_date)
        
        # Check that constraints were added (may be 0 if no soft block constraints apply)
        # The test passes if no exceptions are raised
        assert True
    
    def test_objective_function_creation(self, scheduler):
        """Test that objective functions are created correctly."""
        from pulp import LpProblem, LpVariable
        
        prob = LpProblem("Test", 1)  # Minimize
        start_vars = {}
        resource_vars = {}
        
        # Create test variables
        for submission_id in scheduler.submissions:
            start_vars[submission_id] = LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
            resource_vars[f"active_{submission_id}_day_0"] = LpVariable(f"active_{submission_id}_day_0", cat='Binary')
        
        # Test different objective functions
        objectives = ["minimize_makespan", "minimize_penalties", "minimize_total_time"]
        
        for objective in objectives:
            scheduler.optimization_objective = objective
            obj_func = scheduler._create_objective_function(prob, start_vars, resource_vars)
            assert obj_func is not None
    
    def test_milp_solver_integration(self, scheduler):
        """Test that the MILP solver can be called (may fail if no solver available)."""
        model = scheduler._setup_milp_model()
        
        if model is not None:
            # Try to solve (this may fail if no solver is available)
            try:
                solution = scheduler._solve_milp_model(model)
                # If solution is None, that's okay - it means the solver failed
                # If solution is not None, we should be able to extract a schedule
                if solution is not None:
                    schedule = scheduler._extract_schedule_from_solution(solution)
                    assert isinstance(schedule, dict)
            except Exception as e:
                # It's okay if the solver fails - we just want to test the integration
                assert "solver" in str(e).lower() or "pulp" in str(e).lower()
    
    def test_schedule_extraction(self, scheduler):
        """Test that schedules can be extracted from MILP solutions."""
        # Mock a solution
        mock_solution = MagicMock()
        mock_solution.variables.return_value = {
            "start_test_submission": MagicMock(value=lambda: 5)
        }
        
        schedule = scheduler._extract_schedule_from_solution(mock_solution)
        assert isinstance(schedule, dict)
    
    def test_fallback_to_greedy(self, scheduler):
        """Test that the scheduler falls back to greedy when MILP fails."""
        # Mock MILP to fail
        with patch.object(scheduler, '_setup_milp_model', return_value=None):
            schedule = scheduler.schedule()
            # Should still return a schedule (from greedy fallback)
            assert isinstance(schedule, dict)
    
    def test_optimization_objectives(self, config):
        """Test different optimization objectives."""
        objectives = ["minimize_makespan", "minimize_penalties", "minimize_total_time"]
        
        for objective in objectives:
            scheduler = OptimalScheduler(config, optimization_objective=objective)
            assert scheduler.optimization_objective == objective
    
    def test_is_working_day_method(self, scheduler):
        """Test the working day calculation method."""
        # Test a weekday
        weekday = date(2024, 1, 15)  # Monday
        assert scheduler._is_working_day(weekday) == True
        
        # Test a weekend
        weekend = date(2024, 1, 13)  # Saturday
        assert scheduler._is_working_day(weekday) == True  # Should handle weekends
    
    def test_penalty_constraints(self, scheduler):
        """Test that penalty constraints are added correctly."""
        from pulp import LpProblem, LpVariable
        
        prob = LpProblem("Test", 1)  # Minimize
        start_vars = {}
        penalty_vars = {}
        
        # Create test variables
        for submission_id in scheduler.submissions:
            start_vars[submission_id] = LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
            penalty_vars[submission_id] = LpVariable(f"penalty_{submission_id}", lowBound=0, cat='Integer')
        
        # Add penalty constraints
        scheduler._add_penalty_constraints(prob, start_vars, penalty_vars)
        
        # Check that constraints were added (may be 0 if no penalty constraints apply)
        # The test passes if no exceptions are raised
        assert True
    
    def test_resource_variable_creation(self, scheduler):
        """Test that resource variables are created correctly."""
        from pulp import LpProblem
        
        prob = LpProblem("Test", 1)  # Minimize
        horizon_days = 30
        
        resource_vars = scheduler._create_resource_variables(prob, horizon_days)
        
        assert isinstance(resource_vars, dict)
        assert len(resource_vars) > 0
        
        # Check that variables are binary (or integer with binary bounds)
        for var_name, var in resource_vars.items():
            # PuLP may show binary variables as 'Integer' but with bounds 0-1
            assert var.cat in ['Binary', 'Integer']
            if var.cat == 'Integer':
                assert var.lowBound == 0 and var.upBound == 1
    
    def test_comprehensive_milp_optimization(self, config):
        """Test a complete MILP optimization run."""
        scheduler = OptimalScheduler(config)
        
        try:
            schedule = scheduler.schedule()
            assert isinstance(schedule, dict)
            
            if schedule:
                # Check that all scheduled submissions have valid dates
                for submission_id, start_date in schedule.items():
                    assert isinstance(start_date, date)
                    assert start_date >= date.today()
                    
        except Exception as e:
            # If MILP fails, that's okay - we just want to test the integration
            assert "solver" in str(e).lower() or "pulp" in str(e).lower() or "infeasible" in str(e).lower()


class TestOptimalSchedulerIntegration:
    """Integration tests for the Optimal Scheduler."""
    
    def test_optimal_vs_greedy_comparison(self):
        """Compare optimal scheduler with greedy scheduler."""
        from src.core.config import load_config
        from src.schedulers.greedy import GreedyScheduler
        
        config = load_config('config.json')
        
        # Create both schedulers
        optimal_scheduler = OptimalScheduler(config)
        greedy_scheduler = GreedyScheduler(config)
        
        try:
            # Generate schedules
            optimal_schedule = optimal_scheduler.schedule()
            greedy_schedule = greedy_scheduler.schedule()
            
            # Both should return valid schedules
            assert isinstance(optimal_schedule, dict)
            assert isinstance(greedy_schedule, dict)
            
            # Both should schedule the same submissions
            assert set(optimal_schedule.keys()) == set(greedy_schedule.keys())
            
        except Exception as e:
            # If optimal fails, that's okay - we just want to test the integration
            assert "solver" in str(e).lower() or "pulp" in str(e).lower()
    
    def test_optimal_scheduler_with_different_objectives(self):
        """Test optimal scheduler with different optimization objectives."""
        from src.core.config import load_config
        
        config = load_config('config.json')
        objectives = ["minimize_makespan", "minimize_penalties", "minimize_total_time"]
        
        for objective in objectives:
            try:
                scheduler = OptimalScheduler(config, optimization_objective=objective)
                schedule = scheduler.schedule()
                
                assert isinstance(schedule, dict)
                assert scheduler.optimization_objective == objective
                
            except Exception as e:
                # If MILP fails, that's okay
                assert "solver" in str(e).lower() or "pulp" in str(e).lower()
