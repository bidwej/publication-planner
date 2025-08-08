"""Optimal scheduler implementation using MILP optimization."""

from __future__ import annotations
from typing import Dict, Optional, Any, List, Tuple
from datetime import date, timedelta
import pulp
import math

from src.core.models import SchedulerStrategy
from src.schedulers.base import BaseScheduler


@BaseScheduler.register_strategy(SchedulerStrategy.OPTIMAL)
class OptimalScheduler(BaseScheduler):
    """Optimal scheduler using MILP optimization to find the best schedule."""
    
    def __init__(self, config, optimization_objective: str = "minimize_makespan"):
        """Initialize scheduler with config and optimization objective."""
        super().__init__(config)
        self.optimization_objective = optimization_objective
        self.max_concurrent = config.max_concurrent_submissions
    
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
        
        # Check if MILP is feasible for this problem size
        if len(self.submissions) > 20:
            print(f"MILP optimization: Too many submissions ({len(self.submissions)}) for MILP, falling back to greedy")
            from src.schedulers.greedy import GreedyScheduler
            greedy_scheduler = GreedyScheduler(self.config)
            return greedy_scheduler.schedule()
        
        # Create and solve MILP model
        model = self._setup_milp_model()
        solution = self._solve_milp_model(model)
        
        if solution is None:
            # If MILP fails, fall back to greedy
            print("MILP optimization failed, falling back to greedy scheduler")
            from src.schedulers.greedy import GreedyScheduler
            greedy_scheduler = GreedyScheduler(self.config)
            return greedy_scheduler.schedule()
        
        # Extract schedule from MILP solution
        schedule = self._extract_schedule_from_solution(solution)
        
        # If MILP solution is empty or invalid, fall back to greedy
        if not schedule:
            print("MILP solution is empty, falling back to greedy scheduler")
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
            prob = pulp.LpProblem("Academic_Scheduling", pulp.LpMinimize)
        
        # Get scheduling window
        start_date, end_date = self._get_scheduling_window()
        horizon_days = (end_date - start_date).days
        
        # Decision variables: start time for each submission
        start_vars = {}
        for submission_id in self.submissions:
            start_vars[submission_id] = pulp.LpVariable(
                f"start_{submission_id}", 
                lowBound=0, 
                upBound=horizon_days,
                cat='Integer'
            )
        
        # Binary variables for resource constraints
        resource_vars = self._create_resource_variables(prob, horizon_days)
        
        # Penalty variables for optimization
        penalty_vars = {}
        for submission_id in self.submissions:
            penalty_vars[submission_id] = pulp.LpVariable(
                f"penalty_{submission_id}", 
                lowBound=0,
                cat='Integer'
            )
        
        # Objective function
        objective = self._create_objective_function(prob, start_vars, resource_vars)
        prob += objective
        
        # Constraints
        self._add_dependency_constraints(prob, start_vars)
        self._add_deadline_constraints(prob, start_vars, start_date)
        self._add_resource_constraints(prob, start_vars, resource_vars)
        self._add_working_days_constraints(prob, start_vars, start_date)
        self._add_soft_block_constraints(prob, start_vars, start_date)
        self._add_penalty_constraints(prob, start_vars, penalty_vars)
        
        return prob
    
    def _create_resource_variables(self, prob: Any, horizon_days: int) -> Dict[str, Any]:
        """Create resource constraint variables."""
        resource_vars = {}
        # Simplified resource variables - just track if submission is active on each day
        for submission_id in self.submissions:
            for day in range(horizon_days):
                var_name = f"resource_{submission_id}_{day}"
                resource_vars[var_name] = pulp.LpVariable(var_name, cat=pulp.LpBinary)
        return resource_vars
    
    def _create_objective_function(self, prob: Any, start_vars: Dict[str, Any], 
                                 resource_vars: Dict[str, Any]) -> Any:
        """Create the objective function for MILP optimization."""
        if self.optimization_objective == "minimize_makespan":
            # Minimize the maximum completion time
            makespan = pulp.LpVariable("makespan", lowBound=0)
            for submission_id, submission in self.submissions.items():
                duration = submission.get_duration_days(self.config)
                prob += makespan >= start_vars[submission_id] + duration
            return makespan
        else:
            # Default: minimize total completion time
            total_time = pulp.lpSum([
                start_vars[submission_id] + submission.get_duration_days(self.config)
                for submission_id, submission in self.submissions.items()
            ])
            return total_time
    
    def _add_dependency_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add dependency constraints to the MILP model."""
        for submission_id, submission in self.submissions.items():
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        dep = self.submissions[dep_id]
                        dep_duration = dep.get_duration_days(self.config)
                        # Submission must start after dependency ends
                        prob += start_vars[submission_id] >= start_vars[dep_id] + dep_duration
    
    def _add_deadline_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                                start_date: date) -> None:
        """Add deadline constraints to the MILP model."""
        for submission_id, submission in self.submissions.items():
            if submission.conference_id and submission.conference_id in self.conferences:
                conf = self.conferences[submission.conference_id]
                if submission.kind in conf.deadlines:
                    deadline = conf.deadlines[submission.kind]
                    if deadline:
                        deadline_days = (deadline - start_date).days
                        duration = submission.get_duration_days(self.config)
                        # Submission must complete before deadline
                        prob += start_vars[submission_id] + duration <= deadline_days
    
    def _add_resource_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                                resource_vars: Dict[str, Any]) -> None:
        """Add resource constraints to the MILP model."""
        start_date, end_date = self._get_scheduling_window()
        horizon_days = (end_date - start_date).days
        
        # Resource constraints: limit concurrent submissions per day
        for day in range(horizon_days):
            active_submissions = []
            for submission_id, submission in self.submissions.items():
                duration = submission.get_duration_days(self.config)
                # Check if submission is active on this day
                var_name = f"resource_{submission_id}_{day}"
                if var_name in resource_vars:
                    # Submission is active if it starts before or on this day and ends after this day
                    prob += resource_vars[var_name] <= 1
                    prob += resource_vars[var_name] >= start_vars[submission_id] - day
                    prob += resource_vars[var_name] >= day - start_vars[submission_id] - duration + 1
                    active_submissions.append(resource_vars[var_name])
            
            # Limit concurrent submissions
            if active_submissions:
                prob += pulp.lpSum(active_submissions) <= self.max_concurrent
    
    def _add_working_days_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                                    start_date: date) -> None:
        """Add working days constraints to the MILP model."""
        if not (self.config.scheduling_options and 
                self.config.scheduling_options.get("enable_working_days_only", False)):
            return
        
        # Create binary variables for working days
        working_day_vars = {}
        horizon_days = max((end - start).days for start, end in [self._get_scheduling_window()])
        
        for day in range(horizon_days + 1):
            working_day_vars[f"working_day_{day}"] = pulp.LpVariable(
                f"working_day_{day}", cat=pulp.LpBinary
            )
        
        # Link working day variables to actual dates
        for day in range(horizon_days + 1):
            actual_date = start_date + timedelta(days=day)
            is_working = self._is_working_day(actual_date)
            
            if is_working:
                prob += working_day_vars[f"working_day_{day}"] == 1
            else:
                prob += working_day_vars[f"working_day_{day}"] == 0
        
        # Ensure submissions start on working days
        for submission_id in self.submissions:
            prob += start_vars[submission_id] >= 0  # Start day must be valid
    
    def _add_soft_block_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                                  start_date: date) -> None:
        """Add soft block model constraints (PCCP) to the MILP model."""
        for submission_id, submission in self.submissions.items():
            if submission.earliest_start_date:
                # Convert earliest start date to days from base
                earliest_days = (submission.earliest_start_date - start_date).days
                
                # Soft block constraint: within ±2 months (60 days)
                prob += start_vars[submission_id] >= max(0, earliest_days - 60)  # Lower bound
                prob += start_vars[submission_id] <= earliest_days + 60  # Upper bound
    
    def _add_penalty_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                               penalty_vars: Dict[str, Any]) -> None:
        """Add penalty constraints to the MILP model."""
        start_date, _ = self._get_scheduling_window()
        
        for submission_id, submission in self.submissions.items():
            # Deadline penalty
            if submission.conference_id and submission.conference_id in self.conferences:
                conf = self.conferences[submission.conference_id]
                if submission.kind in conf.deadlines:
                    deadline = conf.deadlines[submission.kind]
                    if deadline:
                        deadline_days = (deadline - start_date).days
                        duration = submission.get_duration_days(self.config)
                        
                        # Penalty if submission completes after deadline
                        prob += penalty_vars[submission_id] >= (
                            start_vars[submission_id] + duration - deadline_days
                        ) * 100  # 100 points per day late
            
            # Resource penalty (simplified)
            # This would require more complex modeling for exact resource violations
            # For now, we'll use a simplified approach
            prob += penalty_vars[submission_id] >= 0
    
    def _is_working_day(self, date_obj: date) -> bool:
        """Check if a date is a working day."""
        from src.core.dates import is_working_day
        return is_working_day(date_obj, self.config.blackout_dates)
    
    def _solve_milp_model(self, model: Optional[Any]) -> Optional[Any]:
        """Solve the MILP model and return the solution."""
        if model is None:
            return None
        
        try:
            # Solve the model with a shorter time limit to prevent hanging
            solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=30)  # 30 second time limit
            model.solve(solver)
            
            # Check if solution was found
            if model.status == pulp.LpStatusOptimal:
                print(f"MILP optimization successful with objective value: {pulp.value(model.objective)}")
                return model
            elif model.status == pulp.LpStatusInfeasible:
                print("MILP optimization: No feasible solution found")
                return None
            elif model.status == pulp.LpStatusUnbounded:
                print("MILP optimization: Problem is unbounded")
                return None
            elif model.status == pulp.LpStatusNotSolved:
                print("MILP optimization: Time limit exceeded or solver failed")
                return None
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
                if hasattr(solution, 'variables') and var_name in solution.variables():
                    var = solution.variables()[var_name]
                    if hasattr(var, 'value') and var.value() is not None:
                        # Convert days from start to actual date
                        days_from_start = int(var.value())
                        actual_start_date = start_date + timedelta(days=days_from_start)
                        schedule[submission_id] = actual_start_date
                else:
                    # If variable not found, try alternative access method
                    try:
                        var = getattr(solution, var_name)
                        if hasattr(var, 'value') and var.value() is not None:
                            days_from_start = int(var.value())
                            actual_start_date = start_date + timedelta(days=days_from_start)
                            schedule[submission_id] = actual_start_date
                    except AttributeError:
                        # Variable not accessible, skip this submission
                        continue
        except Exception as e:
            print(f"Error extracting schedule from MILP solution: {e}")
            return {}
        
        return schedule
