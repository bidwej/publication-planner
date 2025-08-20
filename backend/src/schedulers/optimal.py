"""Optimal scheduler implementation using MILP optimization."""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, timedelta
from schedulers.base import BaseScheduler
from schedulers.greedy import GreedyScheduler
from core.models import SchedulerStrategy, Schedule, Submission, SubmissionType
from core.constants import EFFICIENCY_CONSTANTS
from core.dates import is_working_day

import pulp


class OptimalScheduler(GreedyScheduler):
    """Optimal scheduler that uses MILP optimization to find the best schedule."""
    
    # ===== INITIALIZATION =====
    
    def __init__(self, config, optimization_objective: str = "minimize_makespan") -> None:
        """Initialize scheduler with config and optimization objective."""
        super().__init__(config)
        self.optimization_objective = optimization_objective
    
    # ===== PUBLIC INTERFACE METHODS =====
    
    def schedule(self) -> Schedule:
        """Generate a schedule using MILP optimization with greedy fallback."""
        # Use shared setup from base class
        self.reset_schedule()
        schedule = self.current_schedule
        start_date, end_date = self.get_scheduling_window()
        
        # Calculate horizon for MILP model
        horizon_days = (end_date - start_date).days + 1
        
        # Safety check: limit horizon to prevent excessive MILP model size
        if horizon_days > EFFICIENCY_CONSTANTS.max_algorithm_iterations:
            print(f"Horizon too large ({horizon_days} days), using greedy fallback")
            return super().schedule()
        
        # Try MILP optimization first
        try:
            # Set up and solve MILP model
            milp_model = self._setup_milp_model(horizon_days, start_date)
            if milp_model is not None:
                solution = self._solve_milp_model(milp_model)
                if solution is not None:
                    # Extract schedule from MILP solution
                    milp_schedule = self._extract_schedule_from_solution(solution, start_date)
                    if milp_schedule.intervals:
                        # Assign conferences and return MILP solution
                        for sub_id in milp_schedule.intervals.keys():
                            submission = self.submissions[sub_id]
                            if not submission.conference_id:
                                self.assign_conference(submission)
                        self.print_scheduling_summary(milp_schedule)
                        return milp_schedule
        except Exception as e:
            print(f"MILP optimization failed: {e}")
            print("Falling back to greedy algorithm...")
        
        # Fallback to greedy algorithm
        print("Using greedy algorithm as fallback...")
        return super().schedule()
    
    # ===== MILP MODEL METHODS =====
    
    def _setup_milp_model(self, horizon_days: int, start_date: date) -> Optional[Any]:
        """Set up the MILP model for optimization."""
        try:
            # Create optimization problem
            prob = pulp.LpProblem("Paper_Scheduling", pulp.LpMinimize)  # type: ignore
            
            # Decision variables
            # x[i,t] = 1 if submission i starts at time t, 0 otherwise
            submissions = list(self.submissions.keys())
            time_periods = range(horizon_days)
            
            x = pulp.LpVariable.dicts("start",  # type: ignore
                                     [(i, t) for i in submissions for t in time_periods],
                                     cat=pulp.LpBinary)  # type: ignore
            
            # Objective function: minimize makespan
            if self.optimization_objective == "minimize_makespan":
                # Minimize the latest completion time
                completion_times = []
                for i in submissions:
                    duration = self.submissions[i].get_duration_days(self.config)
                    for t in time_periods:
                        if t + duration <= horizon_days:
                            completion_times.append((t + duration) * x[i, t])
                
                if completion_times:
                    prob += pulp.lpSum(completion_times)
            else:
                # Default: minimize total penalty
                prob += 0  # Placeholder - implement penalty minimization
            
            # Add constraints
            self._add_dependency_constraints(prob, x, submissions, time_periods)
            self._add_deadline_constraints(prob, x, submissions, time_periods, start_date)
            self._add_resource_constraints(prob, x, submissions, time_periods)
            self._add_working_days_constraints(prob, x, submissions, time_periods, start_date)
            self._add_single_start_constraints(prob, x, submissions, time_periods)
            
            return prob
            
        except Exception as e:
            print(f"Error setting up MILP model: {e}")
            return None
    
    def _add_dependency_constraints(self, prob: pulp.LpProblem, x: Dict, 
                                   submissions: List[str], time_periods: range) -> None:
        """Add dependency constraints to the MILP model."""
        for submission_id in submissions:
            submission = self.submissions[submission_id]
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        dep_duration = self.submissions[dep_id].get_duration_days(self.config)
                        
                        # For each possible start time of the dependent submission
                        for t_dep in time_periods:
                            if t_dep + dep_duration <= len(time_periods):
                                # The dependent submission must complete before this one starts
                                for t_this in time_periods:
                                    if t_this < t_dep + dep_duration:
                                        # If dependent starts at t_dep, this cannot start at t_this
                                        prob += x[dep_id, t_dep] + x[submission_id, t_this] <= 1
    
    def _add_deadline_constraints(self, prob: pulp.LpProblem, x: Dict, 
                                  submissions: List[str], time_periods: range, start_date: date) -> None:
        """Add deadline constraints to the MILP model."""
        for submission_id in submissions:
            submission = self.submissions[submission_id]
            if submission.conference_id:
                conference = self.conferences[submission.conference_id]
                deadline = conference.get_deadline_for_submission(submission)
                if deadline:
                    # Calculate deadline day relative to start_date
                    deadline_day = (deadline - start_date).days
                    
                    # Submission must complete before deadline
                    duration = submission.get_duration_days(self.config)
                    for t in time_periods:
                        if t + duration > deadline_day:
                            # Cannot start at time t if it would exceed deadline
                            prob += x[submission_id, t] == 0
    
    def _add_resource_constraints(self, prob: pulp.LpProblem, x: Dict, 
                                  submissions: List[str], time_periods: range) -> None:
        """Add resource constraints to the MILP model."""
        max_concurrent = self.config.max_concurrent_submissions
        
        # For each time period, limit concurrent submissions
        for t in time_periods:
            concurrent_at_t = []
            for i in submissions:
                duration = self.submissions[i].get_duration_days(self.config)
                # Check if submission i is active at time t
                for start_t in range(max(0, t - duration + 1), t + 1):
                    if start_t < len(time_periods):
                        concurrent_at_t.append(x[i, start_t])
            
            if concurrent_at_t:
                prob += pulp.lpSum(concurrent_at_t) <= max_concurrent
    
    def _add_working_days_constraints(self, prob: pulp.LpProblem, x: Dict, 
                                      submissions: List[str], time_periods: range, start_date: date) -> None:
        """Add working days constraints to the MILP model."""
        if not self.config.enable_working_days_only:
            return
            
        for submission_id in submissions:
            for t in time_periods:
                check_date = start_date + timedelta(days=t)
                # Use the working day function from core.dates
                if not is_working_day(check_date, self.config.blackout_dates):
                    # Cannot start on non-working days
                    prob += x[submission_id, t] == 0
    
    def _add_single_start_constraints(self, prob: pulp.LpProblem, x: Dict, 
                                      submissions: List[str], time_periods: range) -> None:
        """Add constraints that each submission starts exactly once."""
        for i in submissions:
            prob += pulp.lpSum(x[i, t] for t in time_periods) == 1
    
    def _solve_milp_model(self, model: pulp.LpProblem) -> Optional[Dict]:
        """Solve the MILP model."""
        try:
            # Set solver timeout from constants
            solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=EFFICIENCY_CONSTANTS.milp_timeout_seconds)
            status = model.solve(solver)
            
            if status == pulp.LpStatusOptimal:
                print("MILP optimization completed successfully!")
                return {
                    'status': 'optimal',
                    'model': model,
                    'variables': model.variables()
                }
            elif status == pulp.LpStatusInfeasible:
                print("MILP problem is infeasible with current constraints")
                return None
            else:
                print(f"MILP optimization status: {status}")
                return None
                
        except Exception as e:
            print(f"Error solving MILP model: {e}")
            return None
    
    def _extract_schedule_from_solution(self, solution: Dict, start_date: date) -> Schedule:
        """Extract schedule from MILP solution."""
        schedule = Schedule()
        
        try:
            model = solution['model']
            variables = solution['variables']
            
            # Extract start times from solution
            for var in variables:
                if var.name.startswith('start_') and var.varValue == 1:
                    # Parse variable name: start_submission_id_time
                    parts = var.name.split('_')
                    if len(parts) >= 3:
                        submission_id = parts[1]
                        start_day = int(parts[2])
                        
                        if submission_id in self.submissions:
                            start_date_actual = start_date + timedelta(days=start_day)
                            duration = self.submissions[submission_id].get_duration_days(self.config)
                            
                            # Add to schedule
                            schedule.add_interval(submission_id, start_date_actual, duration_days=duration)
            
            return schedule
            
        except Exception as e:
            print(f"Error extracting schedule from MILP solution: {e}")
            return Schedule()
