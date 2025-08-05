"""Base scheduler class and strategy registry."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Type
from ..models import Config, Submission, SchedulerStrategy
from datetime import date, timedelta

class BaseScheduler(ABC):
    """Abstract base class for all schedulers."""
    
    # Strategy registry - maps strategy names to scheduler classes
    _strategies: Dict[SchedulerStrategy, Type['BaseScheduler']] = {}
    
    def __init__(self, config: Config):
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}
        self.conferences = {c.id: c for c in config.conferences}
    
    @classmethod
    def register_strategy(cls, strategy: SchedulerStrategy):
        """Decorator to register a scheduler class with a strategy."""
        def decorator(scheduler_class: Type['BaseScheduler']):
            cls._strategies[strategy] = scheduler_class
            return scheduler_class
        return decorator
    
    @classmethod
    def create_scheduler(cls, strategy: SchedulerStrategy, config: Config) -> 'BaseScheduler':
        """Create a scheduler instance for the given strategy."""
        if strategy not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        scheduler_class = cls._strategies[strategy]
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
        pass
    
    def validate_schedule(self, schedule: Dict[str, date]) -> bool:
        """Validate that a schedule meets all constraints."""
        # This method is deprecated. Use constraints module instead.
        # Import here to avoid circular imports
        from ..constraints import validate_deadline_compliance, validate_dependency_satisfaction, validate_resource_constraints
        
        deadline_validation = validate_deadline_compliance(schedule, self.config)
        dependency_validation = validate_dependency_satisfaction(schedule, self.config)
        resource_validation = validate_resource_constraints(schedule, self.config)
        
        return (deadline_validation.is_valid and 
                dependency_validation.is_valid and 
                resource_validation.is_valid) 