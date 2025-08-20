"""
Web application specific models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class SchedulerStrategy(str, Enum):
    """Available scheduling strategies."""
    GREEDY = "greedy"
    OPTIMAL = "optimal"
    BACKTRACKING = "backtracking"
    STOCHASTIC = "stochastic"
    LOOKAHEAD = "lookahead"
    HEURISTIC = "heuristic"
    RANDOM = "random"


# Type aliases for frontend use - no backend dependencies
ConfigData = Dict[str, Any]  # Simplified config representation
ScheduleData = Dict[str, Any]  # Simplified schedule representation


class WebAppState(BaseModel):
    """State for the web application."""
    model_config = ConfigDict(validate_assignment=True)
    
    current_schedule: Optional[ScheduleData] = None  # Use simplified schedule data
    available_strategies: Optional[List[SchedulerStrategy]] = None
    config_path: str = "config.json"
    # Add config data for components to access
    config_data: Optional[ConfigData] = None  # Use simplified config data
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.available_strategies is None:
            self.available_strategies = list(SchedulerStrategy)


class ComponentState(BaseModel):
    """State for individual components."""
    model_config = ConfigDict(validate_assignment=True)
    
    component_name: str
    config_data: Optional[ConfigData] = None  # Use simplified config data
    last_refresh: Optional[str] = None
    chart_type: Optional[str] = None
    custom_settings: Optional[dict] = None  # Use generic dict for settings
