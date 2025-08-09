"""Schedule analysis functions for analytics."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config
from src.core.dates import calculate_schedule_duration


def analyze_schedule_with_scoring(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Analyze complete schedule with scoring and penalty calculations."""
    # Add additional schedule analysis (without recursive call)
    return {
        "schedule_analysis": {
            "total_submissions": len(schedule),
            "schedule_span": _calculate_schedule_span(schedule) if schedule else 0,
            "average_daily_load": _calculate_average_daily_load(schedule, config) if schedule else 0
        }
    }


def _calculate_schedule_span(schedule: Dict[str, date]) -> int:
    """Calculate the span of the schedule in days."""
    # Use the centralized schedule duration calculation
    return calculate_schedule_duration(schedule)


def _calculate_average_daily_load(schedule: Dict[str, date], config: Config) -> float:
    """Calculate average daily load."""
    if not schedule:
        return 0.0
    
    from src.validation.resources import _calculate_daily_load
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return 0.0
    
    total_load = sum(daily_load.values())
    return total_load / len(daily_load)
