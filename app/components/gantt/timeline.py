"""
Timeline calculations for Gantt charts.
Handles timeline range, concurrency mapping, and positioning.
"""

from datetime import date, timedelta
from typing import Dict, Any

from src.core.models import Config
from src.validation.resources import validate_resources_constraints


def get_timeline_range(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Calculate timeline range with buffer for visualization."""
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
    
    # Get max concurrency from business logic
    resource_validation = validate_resources_constraints(schedule, config)
    max_concurrency = resource_validation.max_observed
    
    return {
        'min_date': timeline_start,
        'max_date': timeline_end,
        'timeline_start': timeline_start,
        'span_days': span_days,
        'max_concurrency': max_concurrency
    }


def get_concurrency_map(schedule: Dict[str, date], config: Config) -> Dict[str, int]:
    """Get concurrency map from business logic for proper row positioning."""
    # This should come from the scheduler's business logic
    # For now, we'll calculate a simple row assignment
    sorted_items = sorted(schedule.items(), key=lambda x: x[1])
    concurrency_map = {}
    
    for row, (submission_id, _) in enumerate(sorted_items):
        concurrency_map[submission_id] = row
    
    return concurrency_map


def get_title_text(timeline_range: Dict[str, Any]) -> str:
    """Generate title text for the chart."""
    min_date = timeline_range['min_date']
    max_date = timeline_range['max_date']
    
    if min_date.year == max_date.year:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
    else:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
