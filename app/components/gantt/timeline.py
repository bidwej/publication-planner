"""Timeline-related functions for Gantt charts."""

from datetime import date, timedelta
from typing import Dict, Any, List, Optional

from src.core.models import Config
from src.validation.resources import validate_resources_constraints


def get_timeline_range(schedule: Dict[str, date], config: Config, forced_timeline: Optional[Dict] = None) -> Dict[str, Any]:
    """Get the complete timeline range information."""
    return _calculate_timeline_range(schedule, config, forced_timeline)


def get_title_text(timeline_range: Dict[str, Any]) -> str:
    """Generate title text for the chart."""
    min_date = timeline_range['min_date']
    max_date = timeline_range['max_date']
    
    if min_date.year == max_date.year:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
    else:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"


def get_working_days_filter(timeline_range: Dict[str, Any]) -> List[date]:
    """Get working days filter for the timeline."""
    # For now, return all days in the range
    # This could be enhanced to filter out weekends/holidays
    start_date = timeline_range['timeline_start']
    end_date = timeline_range['max_date']
    
    working_days = []
    current_date = start_date
    while current_date <= end_date:
        working_days.append(current_date)
        current_date += timedelta(days=1)
    
    return working_days


def _calculate_timeline_range(schedule: Dict[str, date], config: Config, forced_timeline: Optional[Dict] = None) -> Dict[str, Any]:
    """Calculate timeline range using existing business logic."""
    if not schedule:
        # Default timeline if no schedule
        default_start = date.today()
        default_end = default_start + timedelta(days=365)
        return {
            'min_date': default_start,
            'max_date': default_end,
            'timeline_start': default_start,
            'span_days': 365,
            'max_concurrency': 0
        }
    
    # Calculate natural timeline from schedule
    min_date = min(schedule.values())
    max_date = max(schedule.values())
    
    # Add buffer for better visualization
    buffer_days = 30
    timeline_start = min_date - timedelta(days=buffer_days)
    timeline_end = max_date + timedelta(days=buffer_days)
    
    # Calculate span
    span_days = (timeline_end - timeline_start).days
    
    # Get max concurrency from existing business logic
    resource_validation = validate_resources_constraints(schedule, config)
    max_concurrency = resource_validation.max_observed
    
    # Apply forced timeline if provided
    if forced_timeline and forced_timeline.get('force_timeline_range'):
        timeline_start = forced_timeline.get('timeline_start', timeline_start)
        timeline_end = forced_timeline.get('timeline_end', timeline_end)
        span_days = (timeline_end - timeline_start).days
    
    return {
        'min_date': timeline_start,
        'max_date': timeline_end,
        'timeline_start': timeline_start,
        'span_days': span_days,
        'max_concurrency': max_concurrency
    }
