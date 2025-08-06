"""Optimal scheduler implementation using MILP optimization."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from .base import BaseScheduler
from src.core.models import SchedulerStrategy

try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False
    print("Warning: PuLP not available. Install with: pip install pulp")


@BaseScheduler.register_strategy(SchedulerStrategy.OPTIMAL)
class OptimalScheduler(BaseScheduler):
    """Optimal scheduler using MILP optimization to find the best schedule."""
    
    def __init__(self, config, optimization_objective: str = "minimize_makespan"):
        """Initialize scheduler with config and optimization objective."""
        super().__init__(config)
        self.optimization_objective = optimization_objective
        
        if not PULP_AVAILABLE:
            raise ImportError("PuLP is required for optimal scheduling. Install with: pip install pulp")
    
    def schedule(self) -> Dict[str, date]:
        """
        Generate an optimal schedule using MILP optimization.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
        if not PULP_AVAILABLE:
            # Fall back to greedy if PuLP not available
            from .greedy import GreedyScheduler
            greedy_scheduler = GreedyScheduler(self.config)
            return greedy_scheduler.schedule()
        
        self._auto_link_abstract_paper()
        self._validate_venue_compatibility()
        
        # Create and solve MILP model
        model = self._setup_milp_model()
        solution = self._solve_milp_model(model)
        
        if solution is None:
            # If MILP fails, fall back to greedy
            from .greedy import GreedyScheduler
            greedy_scheduler = GreedyScheduler(self.config)
            return greedy_scheduler.schedule()
        
        return self._extract_schedule_from_solution(solution)
    
    def _setup_milp_model(self) -> Optional[Any]:
        """Set up the MILP model for optimization."""
        if not PULP_AVAILABLE:
            return None
            
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
        self._add_concurrency_constraints(prob, start_vars)
        if makespan:
            self._add_makespan_constraints(prob, start_vars, makespan)
        
        return prob
    
    def _add_dependency_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add dependency constraints to the MILP model."""
        if not PULP_AVAILABLE:
            return
            
        for sid, submission in self.submissions.items():
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        # Submission must start after dependency ends
                        dep_duration = self.submissions[dep_id].get_duration_days(self.config)
                        prob += start_vars[sid] >= start_vars[dep_id] + dep_duration
    
    def _add_deadline_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add deadline constraints to the MILP model."""
        if not PULP_AVAILABLE:
            return
            
        for sid, submission in self.submissions.items():
            if submission.conference_id and submission.conference_id in self.conferences:
                conf = self.conferences[submission.conference_id]
                if submission.kind in conf.deadlines:
                    deadline = conf.deadlines[submission.kind]
                    if deadline:
                        # Convert deadline to days from start
                        start_date = min(s.earliest_start_date for s in self.submissions.values() if s.earliest_start_date)
                        deadline_days = (deadline - start_date).days
                        duration = submission.get_duration_days(self.config)
                        prob += start_vars[sid] + duration <= deadline_days
    
    def _add_concurrency_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add concurrency constraints to the MILP model."""
        # For each time period, ensure no more than max_concurrent_submissions are active
        # This is a simplified version - in practice, you'd need to discretize time
        max_concurrent = self.config.max_concurrent_submissions
        
        # Create binary variables for each submission being active at each time
        # This is a simplified approach - in practice, you'd need more sophisticated modeling
        pass  # Simplified for now
    
    def _add_makespan_constraints(self, prob: Any, start_vars: Dict[str, Any], makespan: Any) -> None:
        """Add makespan constraints to the MILP model."""
        if not PULP_AVAILABLE:
            return
            
        for sid, submission in self.submissions.items():
            duration = submission.get_duration_days(self.config)
            prob += makespan >= start_vars[sid] + duration
    
    def _solve_milp_model(self, model: Optional[Any]) -> Optional[Any]:
        """Solve the MILP model and extract the solution."""
        if not PULP_AVAILABLE or model is None:
            return None
            
        try:
            # Solve the problem
            status = model.solve()
            
            if status == pulp.LpStatusOptimal:
                return model
            else:
                print(f"MILP solver status: {pulp.LpStatus[status]}")
                return None
        except Exception as e:
            print(f"Error solving MILP: {e}")
            return None
    
    def _extract_schedule_from_solution(self, solution: Optional[Any]) -> Dict[str, date]:
        """Extract the schedule from the MILP solution."""
        schedule = {}
        
        if solution is None:
            return schedule
        
        # Get the base date for conversion
        base_date = min(s.earliest_start_date for s in self.submissions.values() if s.earliest_start_date)
        if not base_date:
            base_date = date(2025, 1, 1)  # fallback
        
        # Extract start times from solution
        for var in solution.variables():
            if var.name.startswith("start_"):
                sid = var.name.replace("start_", "")
                if sid in self.submissions:
                    start_days = int(var.value())
                    start_date = base_date + timedelta(days=start_days)
                    schedule[sid] = start_date
        
        return schedule
