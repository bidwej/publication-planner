"""Base scheduler implementation."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional, Tuple, Any
from datetime import date, timedelta
from core.models import (
    Config, Submission, SubmissionType, SchedulerStrategy, Conference, Schedule, Interval
)
from core.constants import PRIORITY_CONSTANTS, SCHEDULING_CONSTANTS

from core.dates import is_working_day

# Validation imports
from validation.submission import validate_submission_constraints
from validation.scheduler import validate_scheduler_constraints, validate_scheduling_window


class SchedulingConfig:
    """Configuration constants for scheduling algorithms."""
    MAX_ITERATIONS = 1000
    DEFAULT_TIMEOUT_SECONDS = 60
    MIN_DEADLINE_BUFFER_DAYS = 7
    MAX_BACKTRACK_ATTEMPTS = 5


class BaseScheduler(ABC):
    """Abstract base scheduler that defines the interface and shared utilities."""
    
    _strategy_registry: Dict[SchedulerStrategy, Type['BaseScheduler']] = {}  # Strategy registry
    
    def __init__(self, config: Config) -> None:
        """Initialize scheduler with configuration.
        
        Args:
            config: Configuration object containing submissions, conferences, and settings
        """
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}  # Index submissions by ID
        self.conferences = {c.id: c for c in config.conferences}  # Index conferences by ID
        self._schedule: Optional[Schedule] = None
        self._topo: Optional[List[str]] = None
        self._start_date: Optional[date] = None
        self._end_date: Optional[date] = None
    
    # ===== PUBLIC INTERFACE METHODS =====
    
    @abstractmethod
    def schedule(self) -> Schedule:
        """Generate a schedule for all submissions.
        
        Returns:
            Schedule object with intervals for all submissions
            
        Raises:
            ValueError: If scheduling fails due to invalid configuration
            RuntimeError: If scheduling algorithm fails to converge
        """
        pass
    
    # ===== PUBLIC UTILITY METHODS (used by multiple schedulers) =====
    
    @classmethod
    def create_scheduler(cls, strategy: SchedulerStrategy, config: Config) -> 'BaseScheduler':
        """Create a scheduler instance for the given strategy.
        
        Args:
            strategy: Scheduling strategy to use
            config: Configuration object
            
        Returns:
            Configured scheduler instance
            
        Raises:
            ValueError: If strategy is unknown or scheduler creation fails
        """
        if strategy not in cls._strategy_registry:
            # Try to auto-register the strategy by looking for scheduler classes
            cls._auto_register_strategy(strategy)
            
            # If still not found, raise error
            if strategy not in cls._strategy_registry:
                raise ValueError(f"Unknown strategy: {strategy}. No scheduler class found.")
        
        scheduler_class = cls._strategy_registry[strategy]
        return scheduler_class(config)
    
    def get_dependency_order(self) -> List[str]:
        """Get submissions in proper dependency order (topological sort).
        
        Returns:
            List of submission IDs in dependency order
            
        Raises:
            ValueError: If circular dependencies are detected
        """
        return self._topological_order()
    
    def get_scheduling_window(self) -> Tuple[date, date]:
        """Get the scheduling window (start and end dates).
        
        Returns:
            Tuple of (start_date, end_date) for scheduling window
        """
        return validate_scheduling_window(self.config)
    
    def validate_constraints(self, submission: Submission, start: date, schedule: Schedule) -> bool:
        """Validate all constraints for a submission at a given start date.
        
        Args:
            submission: Submission to validate
            start: Proposed start date
            schedule: Current schedule
            
        Returns:
            True if all constraints are satisfied, False otherwise
        """
        validation_result = validate_scheduler_constraints(submission, start, schedule, self.config)
        return validation_result.is_valid
    
    def reset_schedule(self) -> None:
        """Reset the scheduler to start with a fresh schedule."""
        self._topo = self.get_dependency_order()
        self._start_date, self._end_date = self.get_scheduling_window()
        self._schedule = Schedule()
    
    def print_scheduling_summary(self, schedule: Schedule) -> None:
        """Print a summary of the scheduling results.
        
        Args:
            schedule: Schedule to summarize
        """
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
    
    # ===== STANDARDIZED SCHEDULING INTERFACE =====
    
    def get_priority(self, submission: Submission) -> float:
        """Calculate standard priority score for a submission.
        
        Args:
            submission: Submission to calculate priority for
            
        Returns:
            Priority score (higher = more important)
        """
        base_priority = 0.0
        
        # Priority based on submission type
        if submission.kind == SubmissionType.PAPER:
            base_priority += PRIORITY_CONSTANTS.engineering_paper_weight
        elif submission.kind == SubmissionType.ABSTRACT:
            base_priority += PRIORITY_CONSTANTS.abstract_weight
        elif submission.kind == SubmissionType.POSTER:
            base_priority += 1.0  # Default poster weight
        
        # Priority based on dependencies
        if submission.depends_on:
            base_priority += 10.0
        
        # Priority based on deadline proximity
        if submission.conference_id and submission.conference_id in self.conferences:
            conf = self.conferences[submission.conference_id]
            if submission.kind in conf.deadlines:
                deadline = conf.deadlines[submission.kind]
                if deadline:
                    days_until_deadline = (deadline - date.today()).days
                    if days_until_deadline > 0:
                        base_priority += 100.0 / days_until_deadline  # Closer deadline = higher priority
                    else:
                        base_priority -= abs(days_until_deadline) * 0.1  # Past deadlines get penalty
        
        return base_priority
    
    def sort_ready_submissions(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority (default implementation).
        
        Args:
            ready: List of submission IDs ready to be scheduled
            
        Returns:
            Sorted list of submission IDs (highest priority first)
        """
        # Default: sort by priority score
        return sorted(ready, key=lambda sid: self.get_priority(self.submissions[sid]), reverse=True)
    
    def can_schedule(self, submission: Submission, start_date: date, schedule: Schedule) -> bool:
        """Check if a submission can be scheduled at a given date (default implementation).
        
        Args:
            submission: Submission to check
            start_date: Proposed start date
            schedule: Current schedule
            
        Returns:
            True if submission can be scheduled, False otherwise
        """
        # Default: use comprehensive validation
        return self.validate_constraints(submission, start_date, schedule)
    
    def assign_conference(self, submission: Submission) -> bool:
        """Assign a conference to a submission (default implementation).
        
        Args:
            submission: Submission to assign conference to
            
        Returns:
            True if conference was assigned, False otherwise
        """
        # Default: try to assign based on preferences
        preferred_conferences = self._get_preferred_conferences(submission)
        if not preferred_conferences:
            return False
            
        for conf_name in preferred_conferences:
            conf = self._find_conference_by_name(conf_name)
            if not conf:
                continue
                
            if self._try_assign_conference(submission, conf):
                return True
        
        return False
    
    # ===== SHARED UTILITY METHODS =====
    
    def get_ready_submissions(self, topo: List[str], schedule: Schedule, current_date: date) -> List[str]:
        """Get list of submissions ready to be scheduled at the current date.
        
        Args:
            topo: Topological order of submissions
            schedule: Current schedule
            current_date: Current date for scheduling
            
        Returns:
            List of submission IDs ready to be scheduled
        """
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
    
    def update_active_submissions(self, active: List[str], schedule: Schedule, current_date: date) -> List[str]:
        """Update list of active submissions by removing finished ones.
        
        Args:
            active: Current list of active submission IDs
            schedule: Current schedule
            current_date: Current date
            
        Returns:
            Updated list of active submission IDs
        """
        return [
            submission_id for submission_id in active
            if submission_id in schedule.intervals and 
            self._get_end_date(schedule.intervals[submission_id].start_date, self.submissions[submission_id]) > current_date
        ]
    
    def schedule_submissions_up_to_limit(self, ready: List[str], schedule: Schedule, 
                                        active: List[str], current_date: date) -> int:
        """Schedule submissions up to the concurrency limit.
        
        Args:
            ready: List of submission IDs ready to be scheduled
            schedule: Schedule to add intervals to
            active: Current list of active submission IDs
            current_date: Date to schedule submissions on
            
        Returns:
            Number of submissions successfully scheduled
        """
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
    
    # ===== PROPERTY ACCESSORS =====
    
    @property
    def current_schedule(self) -> Schedule:
        """Get the current schedule, initializing if needed.
        
        Returns:
            Current schedule object
            
        Raises:
            RuntimeError: If schedule initialization fails
        """
        self._ensure_schedule_initialized()
        assert self._schedule is not None  # Type guard
        return self._schedule
    
    @property
    def dependency_order(self) -> List[str]:
        """Get the dependency order, initializing if needed.
        
        Returns:
            List of submission IDs in dependency order
        """
        self._ensure_schedule_initialized()
        assert self._topo is not None  # Type guard
        return self._topo
    
    @property
    def start_date(self) -> date:
        """Get the start date, initializing if needed.
        
        Returns:
            Scheduling start date
        """
        self._ensure_schedule_initialized()
        assert self._start_date is not None  # Type guard
        return self._start_date
    
    @property
    def end_date(self) -> date:
        """Get the end date, initializing if needed.
        
        Returns:
            Scheduling end date
        """
        self._ensure_schedule_initialized()
        assert self._end_date is not None  # Type guard
        return self._end_date
    
    # ===== PRIVATE HELPER METHODS =====
    
    def _ensure_schedule_initialized(self) -> None:
        """Ensure schedule is initialized before use.
        
        Raises:
            RuntimeError: If schedule initialization fails
        """
        if self._schedule is None:
            self.reset_schedule()
    
    @classmethod
    def _auto_register_strategy(cls, strategy: SchedulerStrategy) -> None:
        """Auto-register scheduler classes by looking for them in the schedulers module.
        
        Args:
            strategy: Strategy to register
        """
        try:
            # Import the scheduler classes directly
            from schedulers.greedy import GreedyScheduler
            from schedulers.random import RandomScheduler
            from schedulers.stochastic import StochasticScheduler
            from schedulers.lookahead import LookaheadScheduler
            from schedulers.heuristic import HeuristicScheduler
            from schedulers.backtracking import BacktrackingScheduler
            from schedulers.optimal import OptimalScheduler
            
            # Map strategies to scheduler classes
            strategy_mapping = {
                SchedulerStrategy.GREEDY: GreedyScheduler,
                SchedulerStrategy.STOCHASTIC: StochasticScheduler,
                SchedulerStrategy.LOOKAHEAD: LookaheadScheduler,
                SchedulerStrategy.BACKTRACKING: BacktrackingScheduler,
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
                SchedulerStrategy.BACKTRACKING: 'BacktrackingScheduler',
                SchedulerStrategy.RANDOM: 'RandomScheduler',
                SchedulerStrategy.HEURISTIC: 'HeuristicScheduler',
                SchedulerStrategy.OPTIMAL: 'OptimalScheduler'
            }
            
            if strategy in strategy_mapping:
                class_name = strategy_mapping[strategy]
                if hasattr(module, class_name):
                    cls._strategy_registry[strategy] = getattr(module, class_name)
    
    def _topological_order(self) -> List[str]:
        """Get submissions in topological order based on dependencies.
        
        Returns:
            List of submission IDs in topological order
            
        Raises:
            ValueError: If circular dependencies are detected
        """
        # Simple topological sort implementation
        visited = set()
        temp_visited = set()
        result = []
        
        def dfs(node_id: str) -> None:
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
    
    def _calculate_earliest_start_date(self, submission: Submission, schedule: Schedule) -> date:
        """Calculate the earliest possible start date for a submission.
        
        Args:
            submission: Submission to calculate start date for
            schedule: Current schedule
            
        Returns:
            Earliest possible start date
        """
        # Use a reasonable reference date instead of date.today() to avoid future failures
        # This allows for historical data and resubmissions
        earliest = date.today() - timedelta(days=SCHEDULING_CONSTANTS.conference_response_time_days)  # Allow scheduling up to response time in the past
        
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
    
    def _get_end_date(self, start: date, submission: Submission) -> date:
        """Calculate when a submission finishes (start + duration).
        
        Args:
            start: Start date
            submission: Submission to calculate duration for
            
        Returns:
            End date (start + duration)
        """
        duration_days = submission.get_duration_days(self.config)
        return start + timedelta(days=duration_days)
    
    def _find_next_working_day(self, current_date: date) -> date:
        """Find the next working day (skip blackout dates and weekends).
        
        Args:
            current_date: Current date to start from
            
        Returns:
            Next working day
        """
        next_date = current_date + timedelta(days=1)
        
        while not is_working_day(next_date, self.config.blackout_dates):
            next_date += timedelta(days=1)
        
        return next_date
    
    # ===== CONFERENCE ASSIGNMENT HELPERS =====
    
    def _get_preferred_conferences(self, submission: Submission) -> List[str]:
        """Get list of preferred conferences for a submission.
        
        Args:
            submission: Submission to get preferences for
            
        Returns:
            List of preferred conference names
        """
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
    
    def _find_conference_by_name(self, conf_name: str) -> Optional[Conference]:
        """Find conference by name.
        
        Args:
            conf_name: Name of conference to find
            
        Returns:
            Conference object if found, None otherwise
        """
        for conf in self.conferences.values():
            if conf.name == conf_name:
                return conf
        return None
    
    def _try_assign_conference(self, submission: Submission, conf: Conference) -> bool:
        """Try to assign a submission to a specific conference.
        
        Args:
            submission: Submission to assign
            conf: Conference to assign to
            
        Returns:
            True if assignment was successful, False otherwise
        """
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
    
    def _get_submission_types_to_try(self, submission: Submission) -> List[SubmissionType]:
        """Get list of submission types to try in priority order.
        
        Args:
            submission: Submission to get types for
            
        Returns:
            List of submission types in priority order
        """
        if submission.preferred_kinds is not None:
            return submission.preferred_kinds
        
        if (submission.preferred_workflow and 
            submission.preferred_workflow.value == "all_types"):
            return [SubmissionType.POSTER, SubmissionType.ABSTRACT, SubmissionType.PAPER]
        
        # Default priority order
        return [SubmissionType.POSTER, SubmissionType.ABSTRACT, SubmissionType.PAPER]
    
    def _can_meet_deadline(self, submission: Submission, conf: Conference, submission_type: SubmissionType) -> bool:
        """Check if submission can meet the deadline for a specific submission type.
        
        Args:
            submission: Submission to check
            conf: Conference to check against
            submission_type: Type of submission to check
            
        Returns:
            True if deadline can be met, False otherwise
        """
        duration = submission.get_duration_days(self.config)
        latest_start = conf.deadlines[submission_type] - timedelta(days=duration)
        return latest_start >= date.today()

    def _check_conference_compatibility_for_type(self, conference: Conference, submission_type: SubmissionType) -> bool:
        """Check if a submission is compatible with a conference for a specific submission type.
        
        Args:
            conference: Conference to check
            submission_type: Submission type to check
            
        Returns:
            True if compatible, False otherwise
        """
        return submission_type in conference.deadlines
    

    

    

    

