"""Activity-related functions for Gantt charts."""

import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Dict, Any, List, Tuple

from src.core.models import Config, Submission


def add_activity_bars(fig: go.Figure, schedule: Dict[str, date], config: Config,
                     concurrency_map: Dict[str, int], timeline_start: date) -> None:
    """Add beautiful submission bars to the gantt chart."""
    try:
        # Sort schedule by start date for consistent positioning
        sorted_schedule = _get_sorted_schedule(schedule)
        
        # Calculate row positions based on schedule order (no concurrency conflicts)
        row_positions = {}
        current_row = 0
        
        for submission_id, start_date in sorted_schedule:
            row_positions[submission_id] = current_row
            current_row += 1
        
        # Add bars for each submission
        for submission_id, start_date in sorted_schedule:
            submission = config.submissions_dict.get(submission_id)
            if not submission:
                continue
            
            duration_days = max(submission.get_duration_days(config), 7)
            end_date = start_date + timedelta(days=duration_days)
            row = row_positions[submission_id]
            
            # Add the bar
            _add_elegant_bar(fig, submission, start_date, end_date, row)
            
            # Add label
            _add_bar_label(fig, submission, start_date, end_date, row)
            
    except Exception as e:
        fig.add_annotation(
            text=f"Error rendering bars: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font={'size': 14, 'color': '#e74c3c'},
            showarrow=False
        )


def add_dependency_arrows(fig: go.Figure, schedule: Dict[str, date], config: Config,
                         concurrency_map: Dict[str, int], timeline_start: date) -> None:
    """Add elegant dependency arrows between submissions."""
    try:
        # Find dependencies and add arrows
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
                
                # Find row positions (simplified - just use submission order)
                submission_order = list(schedule.keys())
                from_row = submission_order.index(dep_id)
                to_row = submission_order.index(submission_id)
                
                _add_dependency_arrow(fig, dep_end, from_row, start_date, to_row)
                
    except Exception as e:
        fig.add_annotation(
            text=f"Error rendering dependencies: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.4,
            xanchor='center', yanchor='middle',
            font={'size': 14, 'color': '#e74c3c'},
            showarrow=False
        )


def _get_sorted_schedule(schedule: Dict[str, date]) -> List[Tuple[str, date]]:
    """Get schedule sorted by start date."""
    return sorted(schedule.items(), key=lambda x: x[1])


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
    mod_number = _extract_mod_number(title)
    if mod_number:
        return f"MOD {mod_number}"
    
    # Extract ED number if present
    ed_number = _extract_ed_number(title)
    if ed_number:
        return f"ED {ed_number}"
    
    # Truncate long titles
    max_length = 25
    if len(title) <= max_length:
        return title
    
    truncated = title[:max_length-3]
    return (truncated + "...") if truncated else title[:max_length-3] + "..."


def _extract_mod_number(title: str) -> str:
    """Extract MOD number from title."""
    import re
    match = re.search(r'MOD\s*(\d+)', title, re.IGNORECASE)
    return match.group(1) if match else ""


def _extract_ed_number(title: str) -> str:
    """Extract ED number from title."""
    import re
    match = re.search(r'ED\s*(\d+)', title, re.IGNORECASE)
    return match.group(1) if match else ""
