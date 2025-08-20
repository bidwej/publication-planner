"""
Web application specific models.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import date
from pydantic import BaseModel, Field, ConfigDict, field_validator
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


# Proper type definitions that match backend models
class IntervalData(BaseModel):
    """Time interval data for frontend use."""
    start_date: date
    end_date: date
    duration_days: int


class SubmissionData(BaseModel):
    """Submission data for frontend use."""
    id: str
    title: str
    kind: str  # "paper", "abstract", "poster"
    author: Optional[str] = None
    conference_id: Optional[str] = None
    depends_on: Optional[List[str]] = None
    engineering: bool = False


class ConferenceData(BaseModel):
    """Conference data for frontend use."""
    id: str
    name: str
    conf_type: str  # "medical", "engineering"
    recurrence: str  # "annual", "biennial"
    deadlines: Dict[str, date]  # submission_type -> deadline


class ConfigData(BaseModel):
    """Configuration data for frontend use - matches backend Config structure."""
    submissions: List[SubmissionData]
    conferences: List[ConferenceData]
    min_abstract_lead_time_days: int
    min_paper_lead_time_days: int
    max_concurrent_submissions: int
    default_paper_lead_time_months: int = 3
    work_item_duration_days: int = 30
    conference_response_time_days: int = 90
    penalty_costs: Optional[Dict[str, float]] = None
    priority_weights: Optional[Dict[str, float]] = None
    scheduling_options: Optional[Dict[str, Any]] = None
    blackout_dates: Optional[List[date]] = None
    data_files: Optional[Dict[str, str]] = None


class ScheduleData(BaseModel):
    """Schedule data for frontend use - matches backend Schedule structure."""
    intervals: Dict[str, IntervalData] = Field(default_factory=dict)
    
    @property
    def submission_count(self) -> int:
        return len(self.intervals)
    
    @property
    def start_date(self) -> Optional[date]:
        if not self.intervals:
            return None
        return min(interval.start_date for interval in self.intervals.values())
    
    @property
    def end_date(self) -> Optional[date]:
        if not self.intervals:
            return None
        return max(interval.end_date for interval in self.intervals.values())


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
