"""
Timeline calculations and styling for Gantt charts.
Handles timeline range, date calculations, timeline-specific styling, and background elements.
"""

from datetime import date, timedelta
from typing import Dict, Any
import plotly.graph_objects as go

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


def get_title_text(timeline_range: Dict[str, Any]) -> str:
    """Generate title text for the chart."""
    min_date = timeline_range['min_date']
    max_date = timeline_range['max_date']
    
    if min_date.year == max_date.year:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
    else:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"


def get_concurrency_map(schedule: Dict[str, date]) -> Dict[str, int]:
    """Get concurrency map for proper row positioning."""
    if not schedule:
        return {}
    
    # Sort by start date for consistent row assignment
    sorted_items = sorted(schedule.items(), key=lambda x: x[1])
    concurrency_map = {}
    
    for row, (submission_id, _) in enumerate(sorted_items):
        concurrency_map[submission_id] = row
    
    return concurrency_map


def add_background_elements(fig: go.Figure) -> None:
    """Add background elements to the chart."""
    # Get chart dimensions from the figure (layout is now configured)
    x_range = fig.layout.xaxis.range  # type: ignore
    if not x_range:
        print("Warning: No x-axis range found in figure layout")
        return
    
    start_date = x_range[0]
    end_date = x_range[1]
    
    # Get y-axis range for full chart coverage
    y_range = fig.layout.yaxis.range  # type: ignore
    if not y_range:
        print("Warning: No y-axis range found in figure layout")
        return
    
    y_min = y_range[0]
    y_max = y_range[1]
    
    # Add working days background
    _add_working_days_background(fig, start_date, end_date, y_min, y_max)
    
    # Add monthly markers
    _add_monthly_markers(fig, start_date, end_date, y_min, y_max)


def _add_working_days_background(fig: go.Figure, start_date: date, end_date: date, y_min: float, y_max: float) -> None:
    """Add alternating working days background."""
    current_date = start_date
    week_count = 0
    
    while current_date <= end_date:
        # Alternate weeks for visual clarity
        if week_count % 2 == 0:
            # Add light background for even weeks
            week_end = min(current_date + timedelta(days=6), end_date)
            
            fig.add_shape(
                type="rect",
                x0=current_date,
                x1=week_end,
                y0=y_min - 0.5,  # Cover full chart height
                y1=y_max + 0.5,
                fillcolor='rgba(236, 240, 241, 0.3)',
                line=dict(width=0),
                layer='below'
            )
        
        current_date += timedelta(days=7)
        week_count += 1


def _add_monthly_markers(fig: go.Figure, start_date: date, end_date: date, y_min: float, y_max: float) -> None:
    """Add monthly marker lines and labels for timeline orientation."""
    # Add monthly markers
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
        if current_date >= start_date:
            fig.add_shape(
                type="line",
                x0=current_date,
                x1=current_date,
                y0=y_min - 0.5,  # Cover full chart height
                y1=y_max + 0.5,
                line=dict(color='rgba(189, 195, 199, 0.5)', width=1, dash='dot'),
                layer='below'
            )
            
            # Add month label
            fig.add_annotation(
                text=current_date.strftime('%b %Y'),
                x=current_date,
                y=y_max + 1,  # Position above the chart
                xanchor='center',
                yanchor='bottom',
                font={'size': 10, 'color': '#7f8c8d'},
                showarrow=False,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='rgba(0, 0, 0, 0.1)',
                borderwidth=1
            )
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
