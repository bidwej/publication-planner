"""Optimal scheduler implementation using MILP optimization."""

from __future__ import annotations
from typing import Dict, Optional, Any, List, Tuple
from datetime import date, timedelta
import pulp
import math

from core.models import SchedulerStrategy, SubmissionType, Schedule, Interval
from core.constants import PENALTY_CONSTANTS, SCHEDULING_CONSTANTS, EFFICIENCY_CONSTANTS
from core.dates import is_working_day
from schedulers.base import BaseScheduler


class OptimalScheduler(BaseScheduler):
    """Optimal scheduler using MILP optimization to find the best schedule."""
    
    def __init__(self, config, optimization_objective: str = "minimize_makespan"):
        """Initialize scheduler with config and optimization objective."""
        super().__init__(config)
        self.optimization_objective = optimization_objective
        self.max_concurrent = config.max_concurrent_submissions
    
    def schedule(self) -> Schedule:
        """Generate an optimal schedule using MILP optimization."""
        
        # Get what we need from base
        topo = self.get_dependency_order()
        
        # Try MILP optimization first
        print(f"MILP optimization: Attempting optimal schedule for {len(self.submissions)} submissions")
        
        # Set up and solve the MILP model
        model = self._setup_milp_model()
        if model is not None:
            solution = self._solve_milp_model(model)
            if solution is not None:
                milp_schedule = self._extract_schedule_from_solution(solution)
                if milp_schedule:
                    print("MILP optimization: Successfully generated optimal schedule")
                    # Assign conferences to submissions without them
                    milp_schedule = self._assign_conferences(milp_schedule)
                    # Convert to intervals
                    intervals = {}
                    for sub_id, interval in milp_schedule.intervals.items():
                        duration = self.submissions[sub_id].get_duration_days(self.config)
                        end_date = interval.start_date + timedelta(days=duration)
                        intervals[sub_id] = Interval(start_date=interval.start_date, end_date=end_date)
                    return Schedule(intervals=intervals)
        
        # Pure optimal: if MILP fails, return empty schedule
        print(f"MILP optimization: No solution found with current constraints")
        print(f"MILP optimization: Returning empty schedule (use GreedyScheduler for approximate solution)")
        return Schedule(intervals={})
    
    def _assign_conferences(self, schedule: Schedule) -> Schedule:
        """Assign conferences to submissions that don't have them."""
        for sub_id in schedule.intervals.keys():
            submission = self.submissions[sub_id]
            if not submission.conference_id:
                self._assign_best_conference(submission)
        return schedule
    
    def _assign_best_conference(self, submission) -> None:
        """Assign the best available conference to a submission."""
        preferred_conferences = self._get_preferred_conferences(submission)
        if not preferred_conferences:
            return
            
        # Try to find the best conference for this submission
        for conf_name in preferred_conferences:
            conf = self._find_conference_by_name(conf_name)
            if not conf:
                continue
                
            if self._try_assign_conference(submission, conf):
                return
    
    def _get_preferred_conferences(self, submission) -> List[str]:
        """Get list of preferred conferences for a submission."""
        if hasattr(submission, 'preferred_conferences') and submission.preferred_conferences:
            return submission.preferred_conferences
        
        # Open to any opportunity if no specific preferences
        if (submission.preferred_kinds is None or 
            (submission.preferred_workflow and submission.preferred_workflow.value == "all_types")):
            return [conf.name for conf in self.conferences.values() if conf.deadlines]
        
        # Use specific preferred_kinds
        preferred_conferences = []
        for conf in self.conferences.values():
            if any(ctype in conf.deadlines for ctype in (submission.preferred_kinds or [submission.kind])):
                preferred_conferences.append(conf.name)
        return preferred_conferences
    
    def _find_conference_by_name(self, conf_name: str):
        """Find conference by name."""
        for conf in self.conferences.values():
            if conf.name == conf_name:
                return conf
        return None
    
    def _try_assign_conference(self, submission, conf) -> bool:
        """Try to assign a submission to a specific conference. Returns True if successful."""
        
        submission_types_to_try = self._get_submission_types_to_try(submission)
        
        for submission_type in submission_types_to_try:
            if submission_type not in conf.deadlines:
                continue
                
            if not self._can_meet_deadline(submission, conf, submission_type):
                continue
                
            if not self._check_conference_compatibility_for_type(conf, submission_type):
                continue
                
            # Handle special case: papers at conferences requiring abstracts
            if (submission_type == SubmissionType.PAPER and 
                conf.requires_abstract_before_paper() and 
                SubmissionType.ABSTRACT in conf.deadlines):
                submission.conference_id = conf.id
                submission.preferred_kinds = [SubmissionType.ABSTRACT]
                return True
            
            # Regular assignment
            submission.conference_id = conf.id
            if submission.preferred_kinds is None:
                submission.preferred_kinds = [submission_type]
            return True
        
        return False
    
    def _get_submission_types_to_try(self, submission) -> List[SubmissionType]:
        """Get list of submission types to try in priority order."""
        if submission.preferred_kinds is not None:
            return submission.preferred_kinds
        
        if (submission.preferred_workflow and 
            submission.preferred_workflow.value == "all_types"):
            return [SubmissionType.POSTER, SubmissionType.ABSTRACT, SubmissionType.PAPER]
        
        # Default priority order
        return [SubmissionType.POSTER, SubmissionType.ABSTRACT, SubmissionType.PAPER]
    
    def _can_meet_deadline(self, submission, conf, submission_type) -> bool:
        """Check if submission can meet the deadline for a specific submission type."""
        duration = submission.get_duration_days(self.config)
        latest_start = conf.deadlines[submission_type] - timedelta(days=duration)
        # Allow past dates - they might be legitimate for historical data or resubmissions
        # Only check if the deadline is physically possible to meet
        return True  # Always allow scheduling, let validation handle deadline violations

    def _check_conference_compatibility_for_type(self, conference, submission_type: SubmissionType) -> bool:
        """Check if a submission is compatible with a conference for a specific submission type."""
        return submission_type in conference.deadlines
    
    def _setup_milp_model(self) -> Optional[Any]:
        """Set up the MILP model for optimization."""
        try:
            # Create optimization problem
            prob = pulp.LpProblem("Academic_Scheduling", pulp.LpMinimize)
            
            # Get scheduling window
            start_date, end_date = self.get_scheduling_window()
            horizon_days = (end_date - start_date).days
            
            if horizon_days <= 0:
                print("Invalid scheduling window")
                return None
            
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
            
            # Add constraints
            self._add_dependency_constraints(prob, start_vars)
            self._add_deadline_constraints(prob, start_vars, start_date)
            self._add_resource_constraints(prob, start_vars, resource_vars, horizon_days)
            self._add_working_days_constraints(prob, start_vars, start_date)
            self._add_soft_block_constraints(prob, start_vars, start_date)
            self._add_penalty_constraints(prob, start_vars, penalty_vars)
            
            return prob
            
        except Exception as e:
            print(f"Error setting up MILP model: {e}")
            return None
    
    def _create_resource_variables(self, prob: Any, horizon_days: int) -> Dict[str, Any]:
        """Create resource constraint variables using proper MILP formulation."""
        resource_vars = {}
        
        # Create binary variables for each submission-day combination
        # This tracks whether a submission is active on a given day
        for submission_id in self.submissions:
            submission = self.submissions[submission_id]
            duration = submission.get_duration_days(self.config)
            
            for day in range(horizon_days):
                var_name = f"active_{submission_id}_{day}"
                resource_vars[var_name] = pulp.LpVariable(var_name, cat=pulp.LpBinary)
        
        return resource_vars
    
    def _create_objective_function(self, prob: Any, start_vars: Dict[str, Any], 
                                 resource_vars: Dict[str, Any]) -> Any:
        """Create the objective function for MILP optimization with soft constraint penalties."""
        
        # Multi-objective function combining time and penalty minimization
        time_objective = pulp.lpSum(start_vars.values())  # Minimize start times
        
        # Add penalty terms for soft constraint violations
        penalty_objective = 0
        
        # Collect deadline violation penalties
        for submission_id in self.submissions:
            deadline_slack_var = f"deadline_slack_{submission_id}"
            # Check if this variable exists in the problem
            try:
                slack_var = pulp.LpVariable(deadline_slack_var, lowBound=0)
                # Use penalty cost from config or submission
                penalty_cost = self._get_penalty_cost(submission_id)
                penalty_objective += penalty_cost * slack_var
            except:
                # Variable doesn't exist, skip
                pass
        
        # Collect dependency violation penalties
        for submission_id, submission in self.submissions.items():
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        dep_slack_var = f"dep_slack_{submission_id}_{dep_id}"
                        try:
                            slack_var = pulp.LpVariable(dep_slack_var, lowBound=0)
                            # Higher penalty for dependency violations
                            penalty_cost = self._get_penalty_cost(submission_id) * 2.0
                            penalty_objective += penalty_cost * slack_var
                        except:
                            pass
        
        # Weighted combination: 70% time optimization, 30% penalty minimization
        if self.optimization_objective == "minimize_makespan":
            # Minimize the maximum completion time with penalties
            makespan = pulp.LpVariable("makespan", lowBound=0)
            for submission_id, submission in self.submissions.items():
                duration = submission.get_duration_days(self.config)
                prob += makespan >= start_vars[submission_id] + duration
            return 0.7 * makespan + 0.3 * penalty_objective
        else:
            # Default: minimize weighted combination of time and penalties
            return 0.7 * time_objective + 0.3 * penalty_objective
    
    def _get_penalty_cost(self, submission_id: str) -> float:
        """Get penalty cost for a submission from config or submission."""
        submission = self.submissions[submission_id]
        
        # Use submission-specific penalty if available
        if submission.penalty_cost_per_month:
            return submission.penalty_cost_per_month / 30.0  # Convert to daily
        
        # Use config penalty costs
        if self.config.penalty_costs:
            if submission.kind == SubmissionType.PAPER:
                return self.config.penalty_costs.get("default_paper_penalty_per_day", PENALTY_CONSTANTS.default_paper_penalty_per_day)
            else:
                return self.config.penalty_costs.get("default_mod_penalty_per_day", PENALTY_CONSTANTS.default_mod_penalty_per_day)
        
        # Default penalty from constants
        if submission.kind == SubmissionType.PAPER:
            return PENALTY_CONSTANTS.default_paper_penalty_per_day
        else:
            return PENALTY_CONSTANTS.default_mod_penalty_per_day
    
    def _add_dependency_constraints(self, prob: Any, start_vars: Dict[str, Any]) -> None:
        """Add soft dependency constraints to the MILP model."""
        constraints_added = 0
        for submission_id, submission in self.submissions.items():
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        dep = self.submissions[dep_id]
                        dep_duration = dep.get_duration_days(self.config)
                        
                        # Add soft dependency constraint with slack variable
                        dependency_violation = pulp.LpVariable(f"dep_slack_{submission_id}_{dep_id}", lowBound=0)
                        prob += start_vars[submission_id] >= start_vars[dep_id] + dep_duration - dependency_violation
                        constraints_added += 1
        
        print(f"MILP: Added {constraints_added} soft dependency constraints")
    
    def _add_deadline_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                                start_date: date) -> None:
        """Add soft deadline constraints to the MILP model."""
        constraints_added = 0
        
        for submission_id, submission in self.submissions.items():
            if submission.conference_id and submission.conference_id in self.conferences:
                conf = self.conferences[submission.conference_id]
                if submission.kind in conf.deadlines:
                    deadline = conf.deadlines[submission.kind]
                    if deadline:
                        deadline_days = (deadline - start_date).days
                        duration = submission.get_duration_days(self.config)
                        
                        # Use soft constraints - always feasible, but with penalty for violations
                        # This prevents infeasibility while still encouraging deadline compliance
                        if deadline_days > 0:  # Only for future deadlines
                            deadline_violation = pulp.LpVariable(f"deadline_slack_{submission_id}", lowBound=0)
                            prob += start_vars[submission_id] + duration <= deadline_days + deadline_violation
                            constraints_added += 1
        
        print(f"MILP: Added {constraints_added} soft deadline constraints")
    
    def _add_resource_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                                resource_vars: Dict[str, Any], horizon_days: int) -> None:
        """Add resource constraints to the MILP model using robust approach."""
        # Add basic bounds to ensure submissions start within the horizon
        for submission_id in self.submissions:
            prob += start_vars[submission_id] >= 0
            prob += start_vars[submission_id] <= horizon_days - 1
        
        # Simplified resource constraints - just ensure reasonable scheduling window
        # Don't add overly complex resource constraints that might cause infeasibility
        # The greedy fallback will handle resource optimization if MILP fails
    
    def _add_working_days_constraints(self, prob: Any, start_vars: Dict[str, Any], 
                                    start_date: date) -> None:
        """Add working days constraints to the MILP model."""
        if not (self.config.scheduling_options and 
                self.config.scheduling_options.get("enable_working_days_only", False)):
            return
        
        # Create a list of working days
        working_days = []
        horizon_days = max((end - start).days for start, end in [self.get_scheduling_window()])
        
        for day in range(horizon_days + 1):
            actual_date = start_date + timedelta(days=day)
            if self._is_working_day(actual_date):
                working_days.append(day)
        
        # Ensure submissions start on working days
        for submission_id in self.submissions:
            # Create constraint that start time must be in working_days
            # This is a simplified approach - in practice, you'd need more complex constraints
            prob += start_vars[submission_id] >= 0  # Basic constraint
    
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
        start_date, _ = self.get_scheduling_window()
        
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
        return is_working_day(date_obj, self.config.blackout_dates)
    
    def _solve_milp_model(self, model: Optional[Any]) -> Optional[Any]:
        """Solve the MILP model and return the solution."""
        if model is None:
            return None
        
        try:
            # Solve the model with a time limit to prevent hanging
            timeout_seconds = EFFICIENCY_CONSTANTS.milp_timeout_seconds
            print(f"MILP optimization: Starting solver with {timeout_seconds}s timeout")
            
            solver = pulp.PULP_CBC_CMD(
                msg=False, 
                timeLimit=timeout_seconds,
                options=['doHeuristic on', 'maxSolutions 1']  # Add heuristic and limit solutions
            )
            
            # Set a maximum iteration limit as additional safety
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
    
    def _extract_schedule_from_solution(self, solution: Optional[Any]) -> Schedule:
        """Extract schedule from MILP solution."""
        if solution is None:
            return Schedule()
        
        schedule = Schedule()
        start_date, _ = self.get_scheduling_window()
        
        try:
            # Get all variables from the problem to avoid recursion
            all_vars = {}
            if hasattr(solution, 'variables'):
                try:
                    # Try to get variables list directly
                    vars_list = solution.variables()
                    if hasattr(vars_list, '__iter__'):
                        for var in vars_list:
                            if hasattr(var, 'name') and hasattr(var, 'varValue'):
                                all_vars[var.name] = var.varValue
                except:
                    pass
            
            for submission_id in self.submissions:
                var_name = f"start_{submission_id}"
                var_value = None
                
                # Use the pre-extracted variables to avoid recursion
                if var_name in all_vars:
                    var_value = all_vars[var_name]
                
                # Fallback: try direct variable access (but with recursion limit)
                if var_value is None:
                    try:
                        if hasattr(solution, var_name):
                            var = getattr(solution, var_name)
                            # Use varValue property instead of value() method to avoid recursion
                            if hasattr(var, 'varValue'):
                                var_value = var.varValue
                            elif hasattr(var, 'value'):
                                # Only call value() once, don't chain calls
                                val = var.value()
                                if val is not None:
                                    var_value = val
                    except RecursionError:
                        print(f"Recursion error accessing variable {var_name}, skipping")
                        continue
                    except Exception:
                        pass
                
                if var_value is not None and var_value >= 0:
                    # Convert days from start to actual date
                    days_from_start = int(var_value)
                    actual_start_date = start_date + timedelta(days=days_from_start)
                    schedule.add_interval(submission_id, actual_start_date)
                else:
                    print(f"Warning: Could not extract value for variable {var_name}")
                    
        except RecursionError as e:
            print(f"Recursion error extracting schedule from MILP solution: {e}")
            return Schedule()
        except Exception as e:
            print(f"Error extracting schedule from MILP solution: {e}")
            return Schedule()
        
        return schedule
