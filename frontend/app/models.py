"""
Web application specific models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from enum import Enum

# Import backend models directly - TOML pythonpath should handle this
from core.models import Config, Schedule, Submission, Conference


class SchedulerStrategy(str, Enum):
    """Available scheduling strategies."""
    GREEDY = "greedy"
    OPTIMAL = "optimal"
    BACKTRACKING = "backtracking"
    STOCHASTIC = "stochastic"
    LOOKAHEAD = "lookahead"
    HEURISTIC = "heuristic"
    RANDOM = "random"


class WebAppState(BaseModel):
    """State for the web application."""
    model_config = ConfigDict(validate_assignment=True)
    
    current_schedule: Optional[Schedule] = None  # Proper Schedule object
    available_strategies: Optional[List[SchedulerStrategy]] = None
    config_path: str = "config.json"
    # Add config data for components to access
    config_data: Optional[Config] = None  # Proper Config object
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.available_strategies is None:
            self.available_strategies = list(SchedulerStrategy)


class ComponentState(BaseModel):
    """State for individual components."""
    model_config = ConfigDict(validate_assignment=True)
    
    component_name: str
    config_data: Optional[Config] = None  # Proper Config object
    last_refresh: Optional[str] = None
    chart_type: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None  # Custom settings as dict
