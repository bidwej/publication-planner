"""
Web application specific models.
"""

from dataclasses import dataclass
from typing import Optional, List
from src.core.models import ScheduleState, SchedulerStrategy


@dataclass
class WebAppState:
    """State for the web application."""
    current_schedule: Optional[ScheduleState] = None
    available_strategies: Optional[List[SchedulerStrategy]] = None
    config_path: str = "config.json"
    
    def __post_init__(self):
        if self.available_strategies is None:
            self.available_strategies = list(SchedulerStrategy)
