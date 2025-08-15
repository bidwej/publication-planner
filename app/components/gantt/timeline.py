"""
Timeline calculations and styling for Gantt charts.
Handles timeline range, date calculations, timeline-specific styling, and background elements.
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional, List
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from src.core.models import Config
from src.validation.resources import validate_resources_constraints
from src.core.models import Submission


def get_chart_dimensions(schedule: Optional[Dict[str, date]], config: Config) -> Dict[str, Any]:
    """Calculate chart dimensions and display settings."""
    if not schedule:
        # Default chart dimensions if no schedule
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





def get_concurrency_map(schedule: Optional[Dict[str, date]], config: Config) -> Dict[str, int]:
    """Get concurrency map treating dependent tasks as single units for better readability."""
    if not schedule:
        return {}
    
    # Get submission objects to calculate durations
    submissions = {sub.id: sub for sub in config.submissions}
    
    # Group submissions by their dependency chains (treat dependent tasks as one unit)
    dependency_groups = _group_by_dependencies(schedule, submissions)
    
    # Calculate time intervals for each dependency group (not individual submissions)
    group_intervals = []
    for group_id, group_submissions in dependency_groups.items():
        # Find the earliest start and latest end for the entire group
        group_start = min(schedule[sub_id] for sub_id in group_submissions)
        group_end = max(
            schedule[sub_id] + timedelta(days=submissions[sub_id].get_duration_days(config)) 
            for sub_id in group_submissions
        )
        group_intervals.append((group_id, group_start, group_end, group_submissions))
    
    # Sort by start date
    group_intervals.sort(key=lambda x: x[1])
    
    # Assign rows based on actual overlaps between dependency groups
    concurrency_map = {}
    used_rows = []  # Track which rows are occupied and until when
    
    for group_id, start_date, end_date, group_submissions in group_intervals:
        # Find the first available row
        row = 0
        while row < len(used_rows):
            if used_rows[row] <= start_date:
                # This row is free
                break
            row += 1
        
        # If no free row found, create a new one
        if row >= len(used_rows):
            used_rows.append(end_date)
        else:
            # Update the row's end time
            used_rows[row] = end_date
        
        # Assign all submissions in this group to the same row
        for submission_id in group_submissions:
            concurrency_map[submission_id] = row
    
    return concurrency_map


def add_background_elements(fig: go.Figure) -> None:
    """Add background elements to the chart."""
    # Get chart dimensions from the figure (layout is now configured)
    x_range = getattr(fig.layout, 'xaxis', None)
    if not x_range or not hasattr(x_range, 'range') or not x_range.range:
        print("Warning: No x-axis range found in figure layout")
        return
    
    start_date_val = x_range.range[0]
    end_date_val = x_range.range[1]
    
    # Handle both string dates and date objects
    if isinstance(start_date_val, str):
        try:
            start_date = date.fromisoformat(start_date_val)
        except ValueError:
            print(f"Warning: Invalid date format in x-axis range: {start_date_val}")
            return
    elif isinstance(start_date_val, date):
        start_date = start_date_val
    else:
        print(f"Warning: Unexpected date type in x-axis range: {type(start_date_val)}")
        return
    
    if isinstance(end_date_val, str):
        try:
            end_date = date.fromisoformat(end_date_val)
        except ValueError:
            print(f"Warning: Invalid date format in x-axis range: {end_date_val}")
            return
    elif isinstance(end_date_val, date):
        end_date = end_date_val
    else:
        print(f"Warning: Unexpected date type in x-axis range: {type(end_date_val)}")
        return
    
    # Get y-axis range for full chart coverage
    y_range = getattr(fig.layout, 'yaxis', None)
    if not y_range or not hasattr(y_range, 'range') or not y_range.range:
        print("Warning: No y-axis range found in figure layout")
        return
    
    y_min = y_range.range[0]
    y_max = y_range.range[1]
    
    # Add working days background
    _add_working_days_background(fig, start_date, end_date, y_min, y_max)
    
    # Add monthly markers
    _add_monthly_markers(fig, start_date, end_date, y_min, y_max)


def _group_by_dependencies(schedule: Dict[str, date], submissions: Dict[str, Submission]) -> Dict[str, List[str]]:
    """Group submissions by their dependency relationships."""
    groups = {}
    processed = set()
    
    for submission_id in schedule.keys():
        if submission_id in processed:
            continue
            
        # Start a new group
        group_id = f"group_{len(groups)}"
        group_submissions = []
        
        # Find all submissions in this dependency chain
        _collect_dependency_chain(submission_id, schedule, submissions, group_submissions, processed)
        
        groups[group_id] = group_submissions
    
    return groups


def _collect_dependency_chain(submission_id: str, schedule: Dict[str, date], 
                            submissions: Dict[str, Submission], group: List[str], processed: set):
    """Recursively collect all submissions in a dependency chain."""
    if submission_id in processed or submission_id not in schedule:
        return
    
    processed.add(submission_id)
    group.append(submission_id)
    
    submission = submissions.get(submission_id)
    if submission and submission.depends_on:
        # Add dependencies first (they come before this submission)
        for dep_id in submission.depends_on:
            if dep_id in schedule:
                _collect_dependency_chain(dep_id, schedule, submissions, group, processed)
    
    # Find submissions that depend on this one
    for other_id, other_submission in submissions.items():
        if (other_id in schedule and other_submission.depends_on and 
            submission_id in other_submission.depends_on):
            _collect_dependency_chain(other_id, schedule, submissions, group, processed)


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
