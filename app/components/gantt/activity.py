"""
Individual activity bar for Gantt charts.
Handles a single activity bar with its styling and positioning.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from datetime import date, timedelta
from typing import Dict, Optional

from src.core.models import Config, Submission
from app.components.gantt.timeline import assign_activity_rows


def add_activity_bars(fig: Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add activity bars to the gantt chart."""
    if not schedule:
        return
    
    # Get activity row assignments for proper positioning
    activity_rows = assign_activity_rows(schedule, config)
    
    # Add bars for each submission
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if submission:
            # Calculate duration and end date
            duration_days = max(submission.get_duration_days(config), 7)
            end_date = start_date + timedelta(days=duration_days)
            
            # Add the bar
            _add_activity_bar(fig, submission, start_date, end_date, activity_rows[submission_id])
            
            # Add label
            _add_bar_label(fig, submission, start_date, end_date, activity_rows[submission_id])


def add_dependency_arrows(fig: Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add dependency arrows between activities."""
    if not schedule:
        return
    
    # Get activity row assignments for proper positioning
    activity_rows = assign_activity_rows(schedule, config)
    
    # Add arrows for each submission
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if submission and submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in schedule:
                    # Calculate end date of dependency
                    dep_submission = config.submissions_dict.get(dep_id)
                    if dep_submission:
                        dep_duration = max(dep_submission.get_duration_days(config), 7)
                        dep_end_date = schedule[dep_id] + timedelta(days=dep_duration)
                        
                        # Draw arrow from end of dependency to start of dependent submission
                        _add_dependency_arrow(fig, dep_end_date, activity_rows[dep_id], 
                                            start_date, activity_rows[submission_id])


def _add_activity_bar(fig: Figure, submission: Submission, start_date: date, end_date: date, row: int) -> None:
    """Add a single activity bar to the chart."""
    # Get colors for this submission
    fill_color = _get_submission_color(submission)
    border_color = _get_border_color(submission)
    
    # Add the bar shape
    fig.add_shape(
        type="rect",
        x0=start_date, y0=row - 0.4,
        x1=end_date, y1=row + 0.4,
        fillcolor=fill_color,
        line=dict(color=border_color, width=2),
        opacity=0.8,
        layer="below"
    )
    
    # Add type label with proper positioning
    _add_type_label(fig, submission, start_date, end_date, row)
    
    # Add author label in main lower left corner (simple text)
    _add_author_label(fig, submission, start_date, row)


def _add_bar_label(fig: Figure, submission: Submission, start_date: date, 
                   end_date: date, row: int) -> None:
    """Add a label for the bar."""
    # Calculate label position (center of bar)
    mid_date = start_date + (end_date - start_date) / 2
    
    # Get display title (limited to 20 characters)
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


def _add_author_label(fig: Figure, submission: Submission, start_date: date, row: int) -> None:
    """Add author label (PCCP or ED) in bottom left corner inside the bar."""
    # Get author for label - just the author code, not "Author: "
    author_text = submission.author.upper() if submission.author else "Unknown"
    
    # Add author label annotation in bottom left corner inside the bar
    fig.add_annotation(
        text=author_text,
        x=start_date,
        y=row - 0.2,  # Inside the bar, above the bottom border
        xref="x", yref="y",
        xanchor='left', yanchor='top',
        font={'size': 8, 'color': '#2c3e50', 'weight': 'bold'},
        showarrow=False
    )


def _add_type_label(fig: Figure, submission: Submission, start_date: date, end_date: date, row: int) -> None:
    """Add type label (Abstract, Paper, Poster) in top left corner."""
    # Determine descriptive text based on submission type ONLY (no author info)
    if submission.kind.value == "paper":
        type_text = "Paper"
    elif submission.kind.value == "abstract":
        type_text = "Abstract"
    elif submission.kind.value == "poster":
        type_text = "Poster"
    else:
        type_text = "Document"
    
    # Check if bar is too narrow for full text and truncate if needed
    type_text = _truncate_text_for_bar_width(type_text, start_date, end_date)
    
    # Add type label annotation in top left corner
    fig.add_annotation(
        text=type_text,
        x=start_date,
        y=row + 0.2,  # Positioned to be clearly visible inside the bar
        xref="x", yref="y",
        xanchor='left', yanchor='bottom',
        font={'size': 8, 'color': '#2c3e50', 'weight': 'bold'},
        showarrow=False
    )


def _add_dependency_arrow(fig: Figure, from_date: date, from_row: int, 
                         to_date: date, to_row: int) -> None:
    """Add a dependency arrow between two submissions."""
    # Calculate arrow position - connect from end of source bar to start of target bar
    # Use row positions but offset slightly for better visual connection
    arrow_x = [from_date, to_date]
    arrow_y = [from_row + 0.3, to_row - 0.3]  # Offset to connect bars properly
    
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
    """Get color for submission based on type and author."""
    # Determine base color based on engineering vs medical
    is_engineering = submission.is_engineering
    
    if submission.kind.value == "paper":
        # Engineering papers are blue, Medical papers are purple
        return "#3498db" if is_engineering else "#9b59b6"
    elif submission.kind.value == "abstract":
        # Lighter shades for abstracts
        return "#85c1e9" if is_engineering else "#bb8fce"
    elif submission.kind.value == "poster":
        # Very light shades for posters
        return "#d6eaf8" if is_engineering else "#e8d5f0"
    else:
        # Fallback for any other types
        return "#95a5a6"


def _get_border_color(submission: Submission) -> str:
    """Get border color for submission."""
    # Determine base color based on engineering vs medical
    is_engineering = submission.is_engineering
    
    if submission.kind.value == "paper":
        # Engineering papers have darker blue borders, Medical papers have darker purple
        return "#2980b9" if is_engineering else "#e8d5f0"
    elif submission.kind.value == "abstract":
        # Medium border colors for abstracts
        return "#5dade2" if is_engineering else "#a569bd"
    elif submission.kind.value == "poster":
        # Light border colors for posters
        return "#85c1e9" if is_engineering else "#bb8fce"
    else:
        # Fallback for any other types
        return "#7f8c8d"


def _get_display_title(submission: Submission, max_length: int = 20) -> str:
    """Get display title for submission, truncated if too long."""
    title = submission.title
    if len(title) <= max_length:
        return title
    
    # Truncate and add ellipsis
    truncated = title[:max_length-3]
    return (truncated + "...") if truncated else title[:max_length-3] + "..."


def _truncate_text_for_bar_width(text: str, start_date: date, end_date: date, min_width_days: int = 14) -> str:
    """Truncate text if bar is too narrow to display it properly."""
    bar_width_days = (end_date - start_date).days
    if bar_width_days < min_width_days and len(text) > 8:
        return text[:5] + "..."
    return text
