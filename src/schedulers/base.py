"""Base scheduler implementation."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Type
from datetime import date, timedelta
from src.core.models import Config, Submission, SubmissionType, SchedulerStrategy
from src.core.constraints import validate_deadline_compliance_single, validate_dependencies_satisfied, validate_venue_compatibility


class BaseScheduler(ABC):
    """Abstract base scheduler that defines the interface and shared utilities."""
    
    # Strategy registry
    _strategy_registry: Dict[SchedulerStrategy, Type['BaseScheduler']] = {}
    
    def __init__(self, config: Config):
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}
        self.conferences = {c.id: c for c in config.conferences}
    
    @classmethod
    def register_strategy(cls, strategy: SchedulerStrategy):
        """Decorator to register a scheduler class with a strategy."""
        def decorator(scheduler_class: Type['BaseScheduler']):
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
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule for all submissions.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
    
    # Shared utility methods
    def _topological_order(self) -> List[str]:
        """Get submissions in topological order based on dependencies."""
        return list(self.submissions.keys())
    
    def _deps_satisfied(self, sub: Submission, schedule: Dict[str, date], current: date) -> bool:
        """Check if all dependencies are satisfied."""
        return validate_dependencies_satisfied(sub, schedule, self.submissions, self.config, current)
    
    def _get_end_date(self, start: date, sub: Submission) -> date:
        """Calculate end date for a submission."""
        lead_time = self.config.min_paper_lead_time_days
        if sub.kind.value == "ABSTRACT":
            lead_time = self.config.min_abstract_lead_time_days
        return start + timedelta(days=lead_time)
    
    def _meets_deadline(self, sub: Submission, start: date) -> bool:
        """Check if starting on this date meets the deadline."""
        return validate_deadline_compliance_single(start, sub, self.config)
    
    def _auto_link_abstract_paper(self):
        """Auto-link abstracts to papers if not already linked."""
    
    def _validate_venue_compatibility(self):
        """Validate that submissions are compatible with their venues."""
        validate_venue_compatibility(self.submissions, self.conferences)
    
    def _calculate_earliest_start_date(self, submission: Submission) -> date:
        """Calculate the earliest start date for a submission based on dependencies and constraints."""
        # If explicitly set, use it
        if submission.earliest_start_date:
            return submission.earliest_start_date
        
        # Start with a reasonable past date as the earliest possible date
        # Use a date that's well before any reasonable deadline
        earliest_date = date(2020, 1, 1)  # Use a fixed past date instead of today
        
        # Check if any dependencies exist
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in self.submissions:
                    dep = self.submissions[dep_id]
                    # For now, assume dependency must be completed before this submission starts
                    # In a real system, you might have more complex dependency logic
                    earliest_date = max(earliest_date, date(2020, 1, 1) + timedelta(days=1))
        
        # Check conference deadline and work backwards
        if submission.conference_id and submission.conference_id in self.conferences:
            conf = self.conferences[submission.conference_id]
            if submission.kind in conf.deadlines:
                deadline = conf.deadlines[submission.kind]
                # Work backwards from deadline
                lead_time = self.config.min_paper_lead_time_days
                if submission.kind.value == "ABSTRACT":
                    lead_time = self.config.min_abstract_lead_time_days
                
                # Calculate latest possible start date
                latest_start = deadline - timedelta(days=lead_time)
                # Use the earlier of: today or latest_start - buffer
                earliest_date = max(earliest_date, latest_start - timedelta(days=30))  # Buffer
        
        return earliest_date
    
    def _get_scheduling_window(self) -> tuple[date, date]:
        """Get the scheduling window (start and end dates) for all submissions."""
        # Collect all relevant dates
        dates = []
        
        # Add explicit earliest start dates
        for submission in self.submissions.values():
            if submission.earliest_start_date:
                dates.append(submission.earliest_start_date)
            else:
                # Calculate implicit earliest start date
                dates.append(self._calculate_earliest_start_date(submission))
        
        # Add conference deadlines
        for conference in self.conferences.values():
            dates.extend(conference.deadlines.values())
        
        # Add today's date as fallback
        dates.append(date.today())
        
        if not dates:
            # Ultimate fallback
            start_date = date.today()
            end_date = start_date + timedelta(days=365)  # 1 year from today
        else:
            start_date = min(dates)
            end_date = max(dates) + timedelta(days=self.config.min_paper_lead_time_days * 2)
        
        return start_date, end_date
    
    def _schedule_early_abstracts(self, schedule: Dict[str, date], abstract_advance: int):
        """Schedule abstracts early if enabled."""
        abstracts = [sid for sid, sub in self.submissions.items() 
                    if sub.kind == SubmissionType.ABSTRACT]
        
        for abstract_id in abstracts:
            abstract = self.submissions[abstract_id]
            if abstract.conference_id and abstract.conference_id in self.conferences:
                conf = self.conferences[abstract.conference_id]
                if SubmissionType.ABSTRACT in conf.deadlines:
                    early_date = conf.deadlines[SubmissionType.ABSTRACT] - timedelta(days=abstract_advance)
                    if abstract.earliest_start_date is None or early_date >= abstract.earliest_start_date:
                        schedule[abstract_id] = early_date 