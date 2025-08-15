"""
Web application specific models.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from src.core.models import ScheduleState, SchedulerStrategy


class WebAppState(BaseModel):
    """State for the web application."""
    model_config = ConfigDict(validate_assignment=True)
    
    current_schedule: Optional[ScheduleState] = None
    available_strategies: Optional[List[SchedulerStrategy]] = None
    config_path: str = "config.json"
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.available_strategies is None:
            self.available_strategies = list(SchedulerStrategy)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WebAppState':
        """Create from dictionary."""
        return cls(**data)
