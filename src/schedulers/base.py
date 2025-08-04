from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Type
from datetime import date, timedelta
from core.types import Config, Submission, SchedulerStrategy

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
        # Check that all submissions are scheduled
        if len(schedule) != len(self.submissions):
            return False
        
        # Check dependencies
        for sid, start_date in schedule.items():
            sub = self.submissions[sid]
            for dep_id in sub.depends_on:
                if dep_id not in schedule:
                    return False
                dep_start = schedule[dep_id]
                dep_sub = self.submissions[dep_id]
                
                # Calculate dependency end date
                if dep_sub.kind.value == "PAPER":
                    dep_duration = self.config.min_paper_lead_time_days
                else:
                    dep_duration = 0
                dep_end = dep_start + timedelta(days=dep_duration)
                
                # Submission should start after dependency ends
                if start_date <= dep_end:
                    return False
        
        return True 