"""Base scheduler implementation."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional, Tuple, Union
from datetime import date, timedelta
from core.models import (
    Config, Submission, SubmissionType, SchedulerStrategy, Conference, Schedule, Interval
)
from core.constants import SCHEDULING_CONSTANTS
from core.dates import is_working_day

# Import existing validation functions
from validation.submission import validate_submission_constraints


class BaseScheduler(ABC):
    """Abstract base scheduler that defines the interface and shared utilities."""
    
    _strategy_registry: Dict[SchedulerStrategy, Type['BaseScheduler']] = {}  # Strategy registry
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}  # Index submissions by ID
        self.conferences = {c.id: c for c in config.conferences}  # Index conferences by ID
    
    @classmethod
    def register_strategy(cls, strategy: SchedulerStrategy):
        """Decorator to register a scheduler class with a strategy."""
        def decorator(scheduler_class: Type['BaseScheduler']) -> Type['BaseScheduler']:
            cls._strategy_registry[strategy] = scheduler_class
            return scheduler_class
        return decorator
    
    @classmethod
    def create_scheduler(cls, strategy: SchedulerStrategy, config: Config) -> 'BaseScheduler':
        """Create a scheduler instance for the given strategy."""
        if strategy not in cls._strategy_registry:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        scheduler_class = cls._strategy_registry[strategy]
        return scheduler_class(config)
    
    @abstractmethod
    def schedule(self) -> Schedule:
        """Generate a schedule for all submissions."""
        pass
    
    # ===== PUBLIC UTILITY METHODS (used by multiple schedulers) =====
    
    def get_dependency_order(self) -> List[str]:
        """Get submissions in proper dependency order (topological sort)."""
        return self._topological_order()
    
    def get_scheduling_window(self) -> Tuple[date, date]:
        """Get the scheduling window (start and end dates)."""
        start_date = date.today()
        
        # Find latest deadline among all conferences
        latest_deadline = start_date
        for conference in self.conferences.values():
            for deadline in conference.deadlines.values():
                if deadline > latest_deadline:
                    latest_deadline = deadline
        
        # Add buffer for conference response time using constants
        response_buffer = SCHEDULING_CONSTANTS.conference_response_time_days
        end_date = latest_deadline + timedelta(days=response_buffer)
        
        return start_date, end_date
    
    def validate_constraints(self, sub: Submission, start: date, schedule: Schedule) -> bool:
        """Validate all constraints for a submission at a given start date."""
        return validate_submission_constraints(sub, start, schedule.to_dict(), self.config)
    
    # ===== PRIVATE HELPER METHODS (internal use only) =====
    
    def _topological_order(self) -> List[str]:
        """Get submissions in topological order based on dependencies."""
        # Simple topological sort implementation
        visited = set()
        temp_visited = set()
        result = []
        
        def dfs(node_id: str):
            if node_id in temp_visited:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected involving {node_id}")
            if node_id in visited:
                return
            
            temp_visited.add(node_id)
            
            # Process dependencies first
            submission = self.submissions[node_id]
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id in self.submissions:
                        dfs(dep_id)
            
            temp_visited.remove(node_id)
            visited.add(node_id)
            result.append(node_id)
        
        # Process all submissions
        for submission_id in self.submissions:
            if submission_id not in visited:
                dfs(submission_id)
        
        return result
    

    

    
    def _apply_early_abstract_scheduling(self, schedule: Schedule) -> None:
        """Apply early abstract scheduling if enabled in config."""
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get(
                "abstract_advance_days", 
                SCHEDULING_CONSTANTS.abstract_advance_days
            )
            self._schedule_early_abstracts(schedule, abstract_advance)
    
    def _get_ready_submissions(self, topo: List[str], schedule: Schedule, current_date: date) -> List[str]:
        """Get list of submissions ready to be scheduled at the current date."""
        ready = []
        for submission_id in topo:
            if submission_id in schedule:
                continue  # Already scheduled
            
            submission = self.submissions[submission_id]
            
            if not submission.are_dependencies_satisfied(schedule.to_dict(), self.submissions, self.config, current_date):
                continue  # Dependencies not satisfied
            
            earliest_start = self._calculate_earliest_start_date(submission, schedule)
            if current_date < earliest_start:
                continue  # Too early to start
            
            ready.append(submission_id)
        
        return ready
    
    def _update_active_submissions(self, active: List[str], schedule: Schedule, current_date: date) -> List[str]:
        """Update list of active submissions by removing finished ones."""
        return [
            submission_id for submission_id in active
            if self._get_end_date(schedule.get_start_date(submission_id) or date.today(), self.submissions[submission_id]) > current_date
        ]
    
    def _schedule_submissions_up_to_limit(self, ready: List[str], schedule: Schedule, 
                                        active: List[str], current_date: date) -> int:
        """Schedule submissions up to the concurrency limit."""
        scheduled_count = 0
        max_concurrent = self.config.max_concurrent_submissions
        
        for submission_id in ready:
            if len(active) >= max_concurrent:
                break  # Reached concurrency limit
            
            # Schedule this submission
            schedule.add_interval(submission_id, current_date)
            active.append(submission_id)
            scheduled_count += 1
        
        return scheduled_count
    
    def _calculate_earliest_start_date(self, submission: Submission, schedule: Schedule) -> date:
        earliest = date.today()
        
        if submission.engineering_ready_date:
            earliest = max(earliest, submission.engineering_ready_date)
        
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in self.submissions:
                    dep = self.submissions[dep_id]
                    if hasattr(dep, 'get_duration_days'):
                        dep_duration = dep.get_duration_days(self.config)
                        dep_start = schedule.get_start_date(dep_id) or date.today()
                        dep_end = dep_start + timedelta(days=dep_duration)
                        earliest = max(earliest, dep_end + timedelta(days=submission.lead_time_from_parents))
        
        return earliest
    
    def _get_end_date(self, start: date, sub: Submission) -> date:
        """Calculate when a submission finishes (start + duration)."""
        duration_days = sub.get_duration_days(self.config)
        return start + timedelta(days=duration_days)
    
    def _schedule_early_abstracts(self, schedule: Schedule, advance_days: int) -> None:
        """Schedule abstracts early if enabled."""
        early_date = date.today() + timedelta(days=advance_days)
        
        for submission in self.submissions.values():
            if (submission.kind == SubmissionType.ABSTRACT and 
                submission.submission_workflow == "abstract_then_paper"):
                # Check if this abstract can be scheduled early
                if validate_submission_constraints(submission, early_date, schedule.to_dict(), self.config):
                    schedule.add_interval(submission.id, early_date)
    
    def _find_next_working_day(self, current_date: date) -> date:
        """Find the next working day (skip blackout dates and weekends)."""
        next_date = current_date + timedelta(days=1)
        
        while not is_working_day(next_date, self.config.blackout_dates):
            next_date += timedelta(days=1)
        
        return next_date
    

    

    

