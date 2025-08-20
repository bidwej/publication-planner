"""Base scheduler implementation."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional, Tuple, Union
from datetime import date, timedelta
from core.models import (
    Config, Submission, SubmissionType, SchedulerStrategy, Conference, Schedule, Interval
)

from core.dates import is_working_day

# Validation imports
from validation.submission import validate_submission_constraints
from validation.scheduler import validate_scheduler_constraints, validate_scheduling_window
# No need to import validate_dependencies_satisfied - using submission.are_dependencies_satisfied() method


class BaseScheduler(ABC):
    """Abstract base scheduler that defines the interface and shared utilities."""
    
    _strategy_registry: Dict[SchedulerStrategy, Type['BaseScheduler']] = {}  # Strategy registry
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}  # Index submissions by ID
        self.conferences = {c.id: c for c in config.conferences}  # Index conferences by ID
        self._schedule: Optional[Schedule] = None
        self._topo: Optional[List[str]] = None
        self._start_date: Optional[date] = None
        self._end_date: Optional[date] = None
    
    # ===== PUBLIC UTILITY METHODS (used by multiple schedulers) =====
    
    @classmethod
    def create_scheduler(cls, strategy: SchedulerStrategy, config: Config) -> 'BaseScheduler':
        """Create a scheduler instance for the given strategy."""
        if strategy not in cls._strategy_registry:
            # Try to auto-register the strategy by looking for scheduler classes
            cls._auto_register_strategy(strategy)
            
            # If still not found, raise error
            if strategy not in cls._strategy_registry:
                raise ValueError(f"Unknown strategy: {strategy}. No scheduler class found.")
        
        scheduler_class = cls._strategy_registry[strategy]
        return scheduler_class(config)
    
    @classmethod
    def _auto_register_strategy(cls, strategy: SchedulerStrategy) -> None:
        """Auto-register scheduler classes by looking for them in the schedulers module."""
        try:
            # Import the scheduler classes directly
            from schedulers.greedy import GreedyScheduler
            from schedulers.random import RandomScheduler
            from schedulers.stochastic import StochasticGreedyScheduler
            from schedulers.lookahead import LookaheadGreedyScheduler
            from schedulers.heuristic import HeuristicScheduler
            from schedulers.backtracking import BacktrackingGreedyScheduler
            from schedulers.optimal import OptimalScheduler
            
            # Map strategies to scheduler classes
            strategy_mapping = {
                SchedulerStrategy.GREEDY: GreedyScheduler,
                SchedulerStrategy.STOCHASTIC: StochasticGreedyScheduler,
                SchedulerStrategy.LOOKAHEAD: LookaheadGreedyScheduler,
                SchedulerStrategy.BACKTRACKING: BacktrackingGreedyScheduler,
                SchedulerStrategy.RANDOM: RandomScheduler,
                SchedulerStrategy.HEURISTIC: HeuristicScheduler,
                SchedulerStrategy.OPTIMAL: OptimalScheduler
            }
            
            if strategy in strategy_mapping:
                cls._strategy_registry[strategy] = strategy_mapping[strategy]
                
        except ImportError:
            # If import fails, try to find classes dynamically
            import importlib
            import inspect
            
            # Get the module where this class is defined
            module = inspect.getmodule(cls)
            if not module:
                return
                
            # Look for scheduler classes in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseScheduler) and 
                    obj != BaseScheduler and
                    hasattr(obj, '__module__') and
                    obj.__module__ == module.__name__):
                    
                    # Try to determine the strategy from the class name
                    if strategy.value in name.lower():
                        cls._strategy_registry[strategy] = obj
                        return
            
            # If not found by name, try to register based on common patterns
            strategy_mapping = {
                SchedulerStrategy.GREEDY: 'GreedyScheduler',
                SchedulerStrategy.STOCHASTIC: 'StochasticScheduler',
                SchedulerStrategy.LOOKAHEAD: 'LookaheadScheduler',
                SchedulerStrategy.BACKTRACKING: 'BacktrackingGreedyScheduler',
                SchedulerStrategy.RANDOM: 'RandomScheduler',
                SchedulerStrategy.HEURISTIC: 'HeuristicScheduler',
                SchedulerStrategy.OPTIMAL: 'OptimalScheduler'
            }
            
            if strategy in strategy_mapping:
                class_name = strategy_mapping[strategy]
                if hasattr(module, class_name):
                    cls._strategy_registry[strategy] = getattr(module, class_name)
    
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
        return validate_scheduling_window(self.config)
    
    def validate_constraints(self, sub: Submission, start: date, schedule: Schedule) -> bool:
        """Validate all constraints for a submission at a given start date."""
        validation_result = validate_scheduler_constraints(sub, start, schedule, self.config)
        return validation_result.is_valid
    
    def reset_schedule(self) -> None:
        """Reset the scheduler to start with a fresh schedule."""
        self._topo = self.get_dependency_order()
        self._start_date, self._end_date = self.get_scheduling_window()
        self._schedule = Schedule()
    
    def _ensure_schedule_initialized(self) -> None:
        """Ensure schedule is initialized before use."""
        if self._schedule is None:
            self.reset_schedule()
    
    @property
    def current_schedule(self) -> Schedule:
        """Get the current schedule, initializing if needed."""
        self._ensure_schedule_initialized()
        assert self._schedule is not None  # Type guard
        return self._schedule
    
    @property
    def dependency_order(self) -> List[str]:
        """Get the dependency order, initializing if needed."""
        self._ensure_schedule_initialized()
        assert self._topo is not None  # Type guard
        return self._topo
    
    @property
    def start_date(self) -> date:
        """Get the start date, initializing if needed."""
        self._ensure_schedule_initialized()
        assert self._start_date is not None  # Type guard
        return self._start_date
    
    @property
    def end_date(self) -> date:
        """Get the end date, initializing if needed."""
        self._ensure_schedule_initialized()
        assert self._end_date is not None  # Type guard
        return self._end_date
    
    def _print_scheduling_summary(self, schedule: Schedule) -> None:
        """Print a summary of the scheduling results."""
        if not schedule:
            print("No schedule generated")
            return
        
        scheduled_count = len(schedule.intervals)
        total_count = len(self.submissions)
        
        print(f"Successfully scheduled {scheduled_count} out of {total_count} submissions")
        
        if scheduled_count > 0:
            start_date = schedule.start_date
            end_date = schedule.end_date
            if start_date and end_date:
                duration = (end_date - start_date).days
                print(f"Schedule spans {duration} days from {start_date} to {end_date}")
    
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
    
    def _get_ready_submissions(self, topo: List[str], schedule: Schedule, current_date: date) -> List[str]:
        """Get list of submissions ready to be scheduled at the current date."""
        ready = []
        for submission_id in topo:
            if submission_id in schedule:
                continue  # Already scheduled
            
            submission = self.submissions[submission_id]
            
            if not submission.are_dependencies_satisfied(schedule, self.config, current_date):
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
            if submission_id in schedule.intervals and 
            self._get_end_date(schedule.intervals[submission_id].start_date, self.submissions[submission_id]) > current_date
        ]
    
    def _schedule_submissions_up_to_limit(self, ready: List[str], schedule: Schedule, 
                                        active: List[str], current_date: date) -> int:
        """Schedule submissions up to the concurrency limit."""
        scheduled_count = 0
        max_concurrent = self.config.max_concurrent_submissions
        
        for submission_id in ready:
            if len(active) >= max_concurrent:
                break  # Reached concurrency limit
            
            # Get submission object to calculate duration
            submission = self.submissions[submission_id]
            
            # Schedule this submission
            schedule.add_interval(submission_id, current_date, duration_days=submission.get_duration_days(self.config))
            active.append(submission_id)
            scheduled_count += 1
        
        return scheduled_count
    
    def _calculate_earliest_start_date(self, submission: Submission, schedule: Schedule) -> date:
        # Use a reasonable reference date instead of date.today() to avoid future failures
        # This allows for historical data and resubmissions
        earliest = date.today() - timedelta(days=365)  # Allow scheduling up to 1 year in the past
        
        if submission.engineering_ready_date:
            earliest = max(earliest, submission.engineering_ready_date)
        
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in self.submissions:
                    dep = self.submissions[dep_id]
                    if hasattr(dep, 'get_duration_days'):
                        dep_duration = dep.get_duration_days(self.config)
                        # Use the correct Schedule.intervals structure
                        if dep_id in schedule.intervals:
                            dep_start = schedule.intervals[dep_id].start_date
                            dep_end = dep_start + timedelta(days=dep_duration)
                            earliest = max(earliest, dep_end + timedelta(days=submission.lead_time_from_parents))
        
        return earliest
    
    def _get_end_date(self, start: date, sub: Submission) -> date:
        """Calculate when a submission finishes (start + duration)."""
        duration_days = sub.get_duration_days(self.config)
        return start + timedelta(days=duration_days)
    
    def _find_next_working_day(self, current_date: date) -> date:
        """Find the next working day (skip blackout dates and weekends)."""
        next_date = current_date + timedelta(days=1)
        
        while not is_working_day(next_date, self.config.blackout_dates):
            next_date += timedelta(days=1)
        
        return next_date
    

    

    

    

