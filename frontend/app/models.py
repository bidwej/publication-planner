"""
Web application specific models.
"""

from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

# Import backend modules with fallback to avoid hanging
try:
    from core.models import SchedulerStrategy, Config, Schedule
    BACKEND_AVAILABLE = True
except ImportError:
    # Fallback types when backend is not available
    if TYPE_CHECKING:
        from core.models import SchedulerStrategy, Config, Schedule
    else:
        SchedulerStrategy = object  # type: ignore
        Config = object  # type: ignore
        Schedule = object  # type: ignore
    BACKEND_AVAILABLE = False


class WebAppState(BaseModel):
    """State for the web application."""
    model_config = ConfigDict(validate_assignment=True)
    
    current_schedule: Optional[Schedule] = None  # Use proper Schedule model
    available_strategies: Optional[List[SchedulerStrategy]] = None
    config_path: str = "config.json"
    # Add config data for components to access
    config_data: Optional[Config] = None  # Use proper Config model
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.available_strategies is None:
            self.available_strategies = list(SchedulerStrategy)


class ComponentState(BaseModel):
    """State for individual components."""
    model_config = ConfigDict(validate_assignment=True)
    
    component_name: str
    config_data: Optional[Config] = None  # Use proper Config model
    last_refresh: Optional[str] = None
    chart_type: Optional[str] = None
    custom_settings: Optional[dict] = None  # Use generic dict for settings
