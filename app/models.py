"""
Web application specific models.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import date
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


@dataclass
class ChartSubmission:
    """Data model for a submission in a chart."""
    id: str
    title: str
    start_date: date
    end_date: date
    duration_days: int
    row: int
    engineering: bool
    kind: str
    conference_id: Optional[str] = None


@dataclass
class TimelineRange:
    """Data model for chart timeline range."""
    start: date
    end: date
    span_days: int


@dataclass
class GanttChartData:
    """Data model for gantt chart display."""
    min_date: date
    max_date: date
    timeline_start: date
    bar_height: float
    y_margin: float
    concurrency_map: Dict[str, int]
    max_concurrency: int
    submissions: List[ChartSubmission]
    timeline_range: TimelineRange
