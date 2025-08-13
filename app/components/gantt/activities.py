"""
Activity-related functions for Gantt charts.
Handles bars, labels, and dependency arrows.
"""

import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Dict

from src.core.models import Config, Submission


def add_activity_bars(fig: go.Figure, schedule: Dict[str, date], config: Config,
                     concurrency_map: Dict[str, int], timeline_start: date) -> None:
    """Add activity bars to the gantt chart using proper row positioning."""
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if not submission:
            continue
        
        # Get row position from concurrency map
        row = concurrency_map.get(submission_id, 0)
        
        # Calculate duration and end date
        duration_days = max(submission.get_duration_days(config), 7)
        end_date = start_date + timedelta(days=duration_days)
        
        # Add the bar
        _add_elegant_bar(fig, submission, start_date, end_date, row)
        
        # Add label
        _add_bar_label(fig, submission, start_date, end_date, row)


def add_dependency_arrows(fig: go.Figure, schedule: Dict[str, date], config: Config,
                         concurrency_map: Dict[str, int], timeline_start: date) -> None:
    """Add dependency arrows between activities using proper row positioning."""
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if not submission or not submission.depends_on:
            continue
        
        for dep_id in submission.depends_on:
            dep_start = schedule.get(dep_id)
            if not dep_start:
                continue
            
            # Calculate positions for arrow
            dep_submission = config.submissions_dict.get(dep_id)
            if not dep_submission:
                continue
            
            dep_duration = max(dep_submission.get_duration_days(config), 7)
            dep_end = dep_start + timedelta(days=dep_duration)
            
            # Get row positions from concurrency map
            from_row = concurrency_map.get(dep_id, 0)
            to_row = concurrency_map.get(submission_id, 0)
            
            _add_dependency_arrow(fig, dep_end, from_row, start_date, to_row)


def _add_elegant_bar(fig: go.Figure, submission: Submission, start_date: date, 
                     end_date: date, row: int) -> None:
    """Add an elegant bar for a submission."""
    # Get colors based on submission type
    color = _get_submission_color(submission)
    border_color = _get_border_color(submission)
    
    # Add the bar as a shape
    fig.add_shape(
        type="rect",
        x0=start_date,
        x1=end_date,
        y0=row - 0.4,
        y1=row + 0.4,
        fillcolor=color,
        line=dict(color=border_color, width=2),
        opacity=0.8
    )


def _add_bar_label(fig: go.Figure, submission: Submission, start_date: date, 
                   end_date: date, row: int) -> None:
    """Add a label for the bar."""
    # Calculate label position (center of bar)
    mid_date = start_date + (end_date - start_date) / 2
    
    # Get display title
    display_title = _get_display_title(submission)
    
    # Add label annotation
    fig.add_annotation(
        text=display_title,
        x=mid_date,
        y=row,
        xref="x", yref="y",
        xanchor='center', yanchor='middle',
        font={'size': 10, 'color': '#2c3e50'},
        showarrow=False,
        bgcolor='rgba(255, 255, 255, 0.8)',
        bordercolor='rgba(0, 0, 0, 0.1)',
        borderwidth=1
    )


def _add_dependency_arrow(fig: go.Figure, from_date: date, from_row: int, 
                         to_date: date, to_row: int) -> None:
    """Add a dependency arrow between two submissions."""
    # Calculate arrow position
    arrow_x = [from_date, to_date]
    arrow_y = [from_row, to_row]
    
    # Add arrow as a line with arrowhead
    fig.add_trace(go.Scatter(
        x=arrow_x,
        y=arrow_y,
        mode='lines+markers',
        line=dict(color='#e74c3c', width=2, dash='dot'),
        marker=dict(symbol='arrow-up', size=8, color='#e74c3c'),
        showlegend=False,
        hoverinfo='skip'
    ))


def _get_submission_color(submission: Submission) -> str:
    """Get elegant color for submission based on type."""
    if submission.kind.value == "PAPER":
        return "#3498db" if submission.engineering else "#9b59b6"
    elif submission.kind.value == "ABSTRACT":
        return "#e67e22"
    elif submission.kind.value == "POSTER":
        return "#f39c12"
    else:  # MOD
        return "#27ae60"


def _get_border_color(submission: Submission) -> str:
    """Get border color for submission."""
    if submission.kind.value == "PAPER":
        return "#2980b9" if submission.engineering else "#8e44ad"
    elif submission.kind.value == "ABSTRACT":
        return "#d35400"
    elif submission.kind.value == "POSTER":
        return "#e67e22"
    else:  # MOD
        return "#229954"


def _get_display_title(submission: Submission) -> str:
    """Get display title for submission."""
    title = submission.title
    
    # Extract MOD number if present
    import re
    mod_match = re.search(r'MOD\s*(\d+)', title, re.IGNORECASE)
    if mod_match:
        return f"MOD {mod_match.group(1)}"
    
    # Extract ED number if present
    ed_match = re.search(r'ED\s*(\d+)', title, re.IGNORECASE)
    if ed_match:
        return f"ED {ed_match.group(1)}"
    
    # Truncate long titles
    max_length = 25
    if len(title) <= max_length:
        return title
    
    truncated = title[:max_length-3]
    return (truncated + "...") if truncated else title[:max_length-3] + "..."
