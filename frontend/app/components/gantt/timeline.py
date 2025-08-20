"""
Timeline calculations and activity positioning for Gantt charts.
Handles activity row assignments, dependency grouping, and background visualization.
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional, List, TYPE_CHECKING
import plotly.graph_objects as go
from plotly.graph_objs import Figure

# Import backend modules with fallback to avoid hanging
try:
    from core.models import Config, Submission, Schedule
    from validation.resources import validate_resources_constraints
    BACKEND_AVAILABLE = True
except ImportError:
    # Fallback types when backend is not available
    if TYPE_CHECKING:
        from core.models import Config, Submission, Schedule
        from validation.resources import validate_resources_constraints
    else:
        Config = object  # type: ignore
        Submission = object  # type: ignore
        Schedule = object  # type: ignore
        validate_resources_constraints = lambda *args, **kwargs: None  # type: ignore
    BACKEND_AVAILABLE = False


def assign_activity_rows(schedule: Optional[Schedule], config: Config) -> Dict[str, int]:
    """Assign each activity to a specific row for visual layout."""
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
        group_start = min(schedule.intervals[sub_id].start_date for sub_id in group_submissions)
        group_end = max(
            schedule.intervals[sub_id].end_date
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


def add_background_elements(fig: Figure) -> None:
    """Add background elements to the chart."""
    try:
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
        _add_weekend_shading(fig, start_date, end_date)
        
        # Add monthly markers
        _add_month_boundaries(fig, start_date, end_date)
        
    except Exception as e:
        print(f"Background elements failed: {e}")


def _add_weekend_shading(fig: Figure, start_date: date, end_date: date) -> None:
    """Add shading for weekends."""
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() >= 5: # Saturday or Sunday
            fig.add_shape(
                type="rect",
                x0=current_date,
                x1=min(current_date + timedelta(days=1), end_date),
                y0=0, # Start from the bottom of the chart
                y1=1, # Cover the full height
                fillcolor='rgba(236, 240, 241, 0.3)',
                line=dict(width=0),
                layer='below'
            )
        current_date += timedelta(days=1)


def _add_month_boundaries(fig: Figure, start_date: date, end_date: date) -> None:
    """Add vertical lines for month boundaries."""
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
        if current_date >= start_date:
            fig.add_shape(
                type="line",
                x0=current_date,
                x1=current_date,
                y0=0, # Start from the bottom of the chart
                y1=1, # Cover the full height
                line=dict(color='rgba(189, 195, 199, 0.5)', width=1, dash='dot'),
                layer='below'
            )
            
            # Add month label
            fig.add_annotation(
                text=current_date.strftime('%b %Y'),
                x=current_date,
                y=1.1,  # Position above the chart
                xanchor='center',
                yanchor='bottom',
                font={'size': 10, 'color': '#7f8c8d'},
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='rgba(0, 0, 0, 0.1)',
                borderwidth=1
            )
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)


def _group_by_dependencies(schedule: Schedule, submissions: Dict[str, Submission]) -> Dict[str, List[str]]:
    """Group submissions by their dependency relationships."""
    groups = {}
    processed = set()
    
    for submission_id in schedule.intervals.keys():
        if submission_id in processed:
            continue
            
        # Start a new group
        group_id = f"group_{len(groups)}"
        group_submissions = []
        
        # Find all submissions in this dependency chain
        _collect_dependency_chain(submission_id, schedule, submissions, group_submissions, processed)
        
        groups[group_id] = group_submissions
    
    return groups


def _collect_dependency_chain(submission_id: str, schedule: Schedule, 
                            submissions: Dict[str, Submission], group: List[str], processed: set):
    """Recursively collect all submissions in a dependency chain."""
    if submission_id in processed or submission_id not in schedule.intervals:
        return
    
    processed.add(submission_id)
    group.append(submission_id)
    
    submission = submissions.get(submission_id)
    if submission and submission.depends_on:
        # Add dependencies first (they come before this submission)
        for dep_id in submission.depends_on:
            if dep_id in schedule.intervals:
                _collect_dependency_chain(dep_id, schedule, submissions, group, processed)
    
    # Find submissions that depend on this one
    for other_id, other_submission in submissions.items():
        if (other_id in schedule.intervals and other_submission.depends_on and 
            submission_id in other_submission.depends_on):
            _collect_dependency_chain(other_id, schedule, submissions, group, processed)



