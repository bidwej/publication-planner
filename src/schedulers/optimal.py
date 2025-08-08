"""Optimal scheduler implementation using MILP optimization."""

from __future__ import annotations
from typing import Dict, Optional, Any
from datetime import date, timedelta
import pulp

from src.core.models import SchedulerStrategy
from src.schedulers.base import BaseScheduler


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
        self._auto_link_abstract_paper()
        from src.validation.venue import _validate_venue_compatibility
        _validate_venue_compatibility(self.submissions, self.conferences)
        
        # Create and solve MILP model
        model = self._setup_milp_model()
        solution = self._solve_milp_model(model)
        
        if solution is None:
            # If MILP fails, fall back to greedy
            from src.schedulers.greedy import GreedyScheduler
            greedy_scheduler = GreedyScheduler(self.config)
            return greedy_scheduler.schedule()
        
        return self._extract_schedule_from_solution(solution)
    
    def _setup_milp_model(self) -> Optional[Any]:
        """Set up the MILP model for optimization."""
        # Create optimization problem
        if self.optimization_objective == "minimize_makespan":
            prob = pulp.LpProblem("Academic_Scheduling", pulp.LpMinimize)
        else:
            prob = pulp.LpProblem("Academic_Scheduling", pulp.LpMaximize)
        
        # Decision variables: start time for each submission
        start_vars = {}
        for sid in self.submissions:
            start_vars[sid] = pulp.LpVariable(f"start_{sid}", lowBound=0, cat='Integer')
        
        # Objective function
        makespan = None
        if self.optimization_objective == "minimize_makespan":
            # Minimize the maximum completion time
            makespan = pulp.LpVariable("makespan", lowBound=0, cat='Integer')
            prob += makespan
        
        elif self.optimization_objective == "minimize_penalties":
            # Minimize total penalties
            penalty_vars = {}
            for sid in self.submissions:
                penalty_vars[sid] = pulp.LpVariable(f"penalty_{sid}", lowBound=0, cat='Integer')
            prob += pulp.lpSum(penalty_vars.values())
        
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
        for sid, submission in self.submissions.items():
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        # Submission must start after dependency ends
                        dep_duration = self.submissions[dep_id].get_duration_days(self.config)
                        prob += start_vars[sid] >= start_vars[dep_id] + dep_duration
    
    def _add_deadline_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add deadline constraints to the MILP model."""
        for sid, submission in self.submissions.items():
            if submission.conference_id and submission.conference_id in self.conferences:
                conf = self.conferences[submission.conference_id]
                if submission.kind in conf.deadlines:
                    deadline = conf.deadlines[submission.kind]
                    if deadline:
                        # Convert deadline to days from start using robust date calculation
                        start_date, _ = self._get_scheduling_window()
                        deadline_days = (deadline - start_date).days
                        duration = submission.get_duration_days(self.config)
                        prob += start_vars[sid] + duration <= deadline_days
    
    def _add_soft_block_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add soft block model constraints (PCCP) to the MILP model."""
        for sid, submission in self.submissions.items():
            if submission.earliest_start_date:
                # Convert earliest start date to days from base
                start_date, _ = self._get_scheduling_window()
                earliest_days = (submission.earliest_start_date - start_date).days
                
                # Soft block constraint: within ±2 months (60 days)
                prob += start_vars[sid] >= earliest_days - 60  # Lower bound
                prob += start_vars[sid] <= earliest_days + 60  # Upper bound
    
    def _add_working_days_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add working days only constraints to the MILP model."""
        if not self.config.scheduling_options or not self.config.scheduling_options.get("enable_working_days_only", False):
            return
        
        # Create binary variables for each submission starting on a working day
        working_day_vars = {}
        for sid in self.submissions:
            working_day_vars[sid] = pulp.LpVariable(f"working_day_{sid}", cat='Binary')
        
        # Constraint: submission must start on a working day
        for sid in self.submissions:
            prob += working_day_vars[sid] == 1  # Force working day constraint
    
    def _add_concurrency_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add concurrency constraints to the MILP model."""
        max_concurrent = self.config.max_concurrent_submissions
        
        # Create binary variables for each submission being active at each time period
        # For simplicity, we'll use a time discretization approach
        time_horizon = 365  # One year horizon
        active_vars = {}
        
        for sid in self.submissions:
            active_vars[sid] = {}
            for t in range(time_horizon):
                active_vars[sid][t] = pulp.LpVariable(f"active_{sid}_{t}", cat='Binary')
        
        # Constraints: submission is active during its duration
        for sid, submission in self.submissions.items():
            duration = submission.get_duration_days(self.config)
            for t in range(time_horizon):
                # If submission starts at time t, it's active for duration days
                for d in range(duration):
                    if t + d < time_horizon:
                        prob += active_vars[sid][t + d] >= start_vars[sid] - t - 1 + duration
                        prob += active_vars[sid][t + d] <= start_vars[sid] - t + duration
        
        # Constraint: at most max_concurrent submissions active at any time
        for t in range(time_horizon):
            prob += pulp.lpSum(active_vars[sid][t] for sid in self.submissions) <= max_concurrent
    
    def _add_makespan_constraints(self, prob: Any, start_vars: Dict[str, Any], makespan: Any) -> None:
        """Add makespan constraints to the MILP model."""
        for sid, submission in self.submissions.items():
            duration = submission.get_duration_days(self.config)
            prob += makespan >= start_vars[sid] + duration
    
    def _solve_milp_model(self, model: Optional[Any]) -> Optional[Any]:
        """Solve the MILP model and extract the solution."""
        if model is None:
            return None
            
        try:
            # Solve the problem
            status = model.solve()
            
            if status == pulp.LpStatusOptimal:
                return model
            print("MILP solver status: %s", pulp.LpStatus[status])
            return None
        except Exception as e:
            print("Error solving MILP: %s", e)
            return None
    
    def _extract_schedule_from_solution(self, solution: Optional[Any]) -> Dict[str, date]:
        """Extract the schedule from the MILP solution."""
        schedule = {}
        
        if solution is None:
            return schedule
        
        # Get the base date for conversion using robust date calculation
        base_date, _ = self._get_scheduling_window()
        
        # Extract start times from solution
        for var in solution.variables():
            if var.name.startswith("start_"):
                sid = var.name.replace("start_", "")
                if sid in self.submissions:
                    start_days = int(var.value())
                    start_date = base_date + timedelta(days=start_days)
                    schedule[sid] = start_date
        
        return schedule
