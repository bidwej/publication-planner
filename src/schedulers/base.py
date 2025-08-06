"""Base scheduler class and strategy registry."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Type, Union
from core.models import Config, Submission, SchedulerStrategy
from datetime import date, timedelta

class BaseScheduler(ABC):
    """Abstract base class for all schedulers."""
    
    # Strategy registry - maps strategy names to scheduler classes
    _strategies: Dict[SchedulerStrategy, Type['BaseScheduler']] = {}
    
    def __init__(self, config: Config):
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}
        self.conferences = {c.id: c for c in config.conferences}
    
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
    
    @classmethod
    def register_strategy(cls, strategy: SchedulerStrategy):
        """Decorator to register a scheduler class with a strategy."""
        def decorator(scheduler_class: Type['BaseScheduler']):
            cls._strategies[strategy] = scheduler_class
            return scheduler_class
        return decorator
    
    @classmethod
    def create_scheduler(cls, strategy: Union[SchedulerStrategy, str], config: Config) -> 'BaseScheduler':
        """Create a scheduler instance for the given strategy."""
        # Convert string to enum if needed
        if isinstance(strategy, str):
            try:
                strategy = SchedulerStrategy(strategy)
            except ValueError:
                raise ValueError(f"Unknown strategy: {strategy}")
        
        if strategy not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        scheduler_class = cls._strategies[strategy]
        return scheduler_class(config) 