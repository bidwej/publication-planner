"""
Web application specific models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from src.core.models import ScheduleState, SchedulerStrategy, Config


class WebAppState(BaseModel):
    """State for the web application."""
    model_config = ConfigDict(validate_assignment=True)
    
    current_schedule: Optional[ScheduleState] = None
    available_strategies: Optional[List[SchedulerStrategy]] = None
    config_path: str = "config.json"
    # Add config data for components to access
    config_data: Optional[Dict[str, Any]] = None
    
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


class ComponentState(BaseModel):
    """State for individual components."""
    model_config = ConfigDict(validate_assignment=True)
    
    component_name: str
    config_data: Optional[Dict[str, Any]] = None
    last_refresh: Optional[str] = None
    chart_type: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ComponentState':
        """Create from dictionary."""
        return cls(**data)
