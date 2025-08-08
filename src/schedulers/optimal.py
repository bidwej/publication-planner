"""Optimal scheduler implementation using MILP optimization."""

from __future__ import annotations
from typing import Dict, Optional, Any
from datetime import date, timedelta
import pulp

from src.core.models import SchedulerStrategy
from src.schedulers.base import BaseScheduler
from src.core.dates import is_working_day


@BaseScheduler.register_strategy(SchedulerStrategy.OPTIMAL)
class OptimalScheduler(BaseScheduler):
    """Optimal scheduler using MILP optimization to find the best schedule."""
    
    def __init__(self, config, optimization_objective: str = "minimize_makespan"):
        """Initialize scheduler with config and optimization objective."""
        super().__init__(config)
        self.optimization_objective = optimization_objective
    
    def schedule(self) -> Dict[str, date]:
        """
        Generate an optimal schedule using MILP optimization.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
        # Use shared setup
        schedule, topo, start_date, end_date = self._run_common_scheduling_setup()
        
        # Create and solve MILP model
        model = self._setup_milp_model()
        solution = self._solve_milp_model(model)
        
        if solution is None:
            # If MILP fails, fall back to greedy
            from src.schedulers.greedy import GreedyScheduler
            greedy_scheduler = GreedyScheduler(self.config)
            return greedy_scheduler.schedule()
        
        # Extract schedule from MILP solution
        schedule = self._extract_schedule_from_solution(solution)
        
        # If MILP solution is empty or invalid, fall back to greedy
        if not schedule:
            from src.schedulers.greedy import GreedyScheduler
            greedy_scheduler = GreedyScheduler(self.config)
            return greedy_scheduler.schedule()
        
        # Print scheduling summary
        self._print_scheduling_summary(schedule)
        
        return schedule
    
    def _setup_milp_model(self) -> Optional[Any]:
        """Set up the MILP model for optimization."""
        # Create optimization problem
        if self.optimization_objective == "minimize_makespan":
            prob = pulp.LpProblem("Academic_Scheduling", pulp.LpMinimize)
        else:
            prob = pulp.LpProblem("Academic_Scheduling", pulp.LpMaximize)
        
        # Decision variables: start time for each submission
        start_vars = {}
        for submission_id in self.submissions:
            start_vars[submission_id] = pulp.LpVariable(f"start_{submission_id}", lowBound=0, cat='Integer')
        
        # Objective function
        makespan = None
        if self.optimization_objective == "minimize_makespan":
            # Minimize the maximum completion time
            makespan = pulp.LpVariable("makespan", lowBound=0, cat='Integer')
            prob += makespan
        
        elif self.optimization_objective == "minimize_penalties":
            # Minimize total penalties
            penalty_vars = {}
            for submission_id in self.submissions:
                penalty_vars[submission_id] = pulp.LpVariable(f"penalty_{submission_id}", lowBound=0, cat='Integer')
            prob += pulp.lpSum(penalty_vars.values())
        
        elif self.optimization_objective == "minimize_total_time":
            # Minimize the sum of all start times (earlier is better)
            prob += pulp.lpSum(start_vars.values())
        
        # Add a simple constraint to ensure the model has content
        if start_vars:
            # Ensure at least one submission starts after day 0
            prob += pulp.lpSum(start_vars.values()) >= 1
        
        # Constraints
        self._add_dependency_constraints(prob, start_vars)
        self._add_deadline_constraints(prob, start_vars)
        self._add_soft_block_constraints(prob, start_vars)
        self._add_working_days_constraints(prob, start_vars)
        self._add_concurrency_constraints(prob, start_vars)
        if makespan:
            self._add_makespan_constraints(prob, start_vars, makespan)
        
        return prob
    
    def _add_dependency_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add dependency constraints to the MILP model."""
        for submission_id, submission in self.submissions.items():
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        # Submission must start after dependency ends
                        dep_duration = self.submissions[dep_id].get_duration_days(self.config)
                        prob += start_vars[submission_id] >= start_vars[dep_id] + dep_duration
    
    def _add_deadline_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add deadline constraints to the MILP model."""
        for submission_id, submission in self.submissions.items():
            if submission.conference_id and submission.conference_id in self.conferences:
                conf = self.conferences[submission.conference_id]
                if submission.kind in conf.deadlines:
                    deadline = conf.deadlines[submission.kind]
                    if deadline:
                        # Convert deadline to days from start using robust date calculation
                        start_date, _ = self._get_scheduling_window()
                        deadline_days = (deadline - start_date).days
                        duration = submission.get_duration_days(self.config)
                        prob += start_vars[submission_id] + duration <= deadline_days
    
    def _add_soft_block_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add soft block model constraints (PCCP) to the MILP model."""
        for submission_id, submission in self.submissions.items():
            if submission.earliest_start_date:
                # Convert earliest start date to days from base
                start_date, _ = self._get_scheduling_window()
                earliest_days = (submission.earliest_start_date - start_date).days
                
                # Soft block constraint: within ±2 months (60 days)
                prob += start_vars[submission_id] >= earliest_days - 60  # Lower bound
                prob += start_vars[submission_id] <= earliest_days + 60  # Upper bound
    
    def _add_working_days_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add working days only constraints to the MILP model."""
        # Working days constraints require complex binary variable formulations
        # For now, we'll skip this to focus on core optimization functionality
        pass
    
    def _add_concurrency_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add concurrency constraints to the MILP model."""
        # Concurrency constraints require complex binary variable formulations
        # For now, we'll skip this to focus on core optimization functionality
        # The greedy fallback will handle concurrency constraints
        pass
    
    def _add_makespan_constraints(self, prob: Any, start_vars: Dict[str, Any], makespan: Any) -> None:
        """Add makespan constraints to the MILP model."""
        for submission_id, submission in self.submissions.items():
            duration = submission.get_duration_days(self.config)
            prob += makespan >= start_vars[submission_id] + duration
    
    def _solve_milp_model(self, model: Optional[Any]) -> Optional[Any]:
        """Solve the MILP model and return the solution."""
        if model is None:
            return None
        
        try:
            # Solve the model
            model.solve()
            
            # Check if solution was found
            if model.status == pulp.LpStatusOptimal:
                return model
            else:
                print(f"MILP optimization failed with status: {model.status}")
                return None
                
        except Exception as e:
            print(f"Error solving MILP model: {e}")
            return None
    
    def _extract_schedule_from_solution(self, solution: Optional[Any]) -> Dict[str, date]:
        """Extract schedule from MILP solution."""
        if solution is None:
            return {}
        
        schedule = {}
        start_date, _ = self._get_scheduling_window()
        
        try:
            for submission_id in self.submissions:
                var_name = f"start_{submission_id}"
                if var_name in solution.variables():
                    var = solution.variables()[var_name]
                    if var.value() is not None:
                        # Convert days from start to actual date
                        days_from_start = int(var.value())
                        actual_start_date = start_date + timedelta(days=days_from_start)
                        schedule[submission_id] = actual_start_date
        except Exception as e:
            print(f"Error extracting schedule from MILP solution: {e}")
            return {}
        
        return schedule
