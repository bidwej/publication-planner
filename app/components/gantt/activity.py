"""
Individual activity bar for Gantt charts.
Handles a single activity bar with its styling and positioning.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from datetime import date, timedelta
from typing import Dict, Optional

from src.core.models import Config, Submission
from app.components.gantt.timeline import get_concurrency_map


def add_activity_bars(fig: Figure, schedule: Optional[Dict[str, date]], config: Config) -> None:
    """Add activity bars to the gantt chart using proper row positioning."""
    if not schedule:
        return
    
    concurrency_map = get_concurrency_map(schedule)
    
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


def add_dependency_arrows(fig: Figure, schedule: Optional[Dict[str, date]], config: Config) -> None:
    """Add dependency arrows between activities using proper row positioning."""
    if not schedule:
        return
    
    concurrency_map = get_concurrency_map(schedule)
    
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


def _add_elegant_bar(fig: Figure, submission: Submission, start_date: date, 
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
    
    # Add type icon in upper left corner (darker background)
    _add_type_icon(fig, submission, start_date, row)
    
    # Add author label in main lower left corner (simple text)
    _add_author_label(fig, submission, start_date, row)


def _add_author_label(fig: Figure, submission: Submission, start_date: date, row: int) -> None:
    """Add author label (Author: PCCP or Author: ED) in main lower left corner of bar."""
    # Get author for label
    author_text = f"Author: {submission.author.upper()}" if submission.author else "Author: Unknown"
    
    # Add author label annotation in main lower left corner of bar
    fig.add_annotation(
        text=author_text,
        x=start_date,
        y=row - 0.3,  # Lower part of bar
        xref="x", yref="y",
        xanchor='left', yanchor='top',
        font={'size': 8, 'color': '#2c3e50', 'weight': 'bold'},
        showarrow=False,
        bgcolor='rgba(255, 255, 255, 0.9)',  # Light background
        bordercolor='rgba(0, 0, 0, 0.2)',
        borderwidth=1,
        borderpad=4
    )


def _add_type_icon(fig: Figure, submission: Submission, start_date: date, row: int) -> None:
    """Add type icon (Paper/Abstract) in upper left corner with darker background."""
    # Determine icon based on submission type
    if submission.kind.value == "paper":
        icon = "📄"  # Paper icon
    elif submission.kind.value == "abstract":
        icon = "📝"  # Abstract icon
    elif submission.kind.value == "poster":
        icon = "🖼️"  # Poster icon
    else:
        icon = "📋"  # Generic document icon
    
    # Add icon annotation in upper left corner of bar
    fig.add_annotation(
        text=icon,
        x=start_date,
        y=row + 0.3,  # Upper part of bar
        xref="x", yref="y",
        xanchor='left', yanchor='bottom',
        font={'size': 12},
        showarrow=False,
        bgcolor='rgba(0, 0, 0, 0.7)',  # Darker background
        bordercolor='rgba(0, 0, 0, 0.9)',
        borderwidth=1,
        borderpad=4
    )


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


def _add_dependency_arrow(fig: Figure, from_date: date, from_row: int, 
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
    """Get elegant color for submission based on type and author."""
    if submission.kind.value == "paper":
        # MODs (pccp) are engineering papers (blue), ED papers (ed) are medical papers (orange)
        if hasattr(submission, 'author') and submission.author == "pccp":
            return "#3498db"  # Blue for MODs (engineering)
        else:
            return "#e67e22"  # Orange for ED papers (medical)
    elif submission.kind.value == "abstract":
        return "#27ae60"  # Green for abstracts
    elif submission.kind.value == "poster":
        return "#f39c12"  # Yellow for posters
    else:
        # Fallback for any other types
        return "#95a5a6"  # Gray fallback


def _get_border_color(submission: Submission) -> str:
    """Get border color for submission."""
    if submission.kind.value == "paper":
        # MODs (pccp) have darker blue borders, ED papers have darker orange
        if hasattr(submission, 'author') and submission.author == "pccp":
            return "#2980b9"  # Darker blue for MODs
        else:
            return "#d35400"  # Darker orange for ED papers
    elif submission.kind.value == "abstract":
        return "#229954"  # Darker green for abstracts
    elif submission.kind.value == "poster":
        return "#e67e22"  # Darker yellow for posters
    else:
        # Fallback for any other types
        return "#7f8c8d"  # Darker gray fallback


def _get_display_title(submission: Submission, max_length: int = 20) -> str:
    """Get display title for submission, truncated if too long."""
    title = submission.title
    if len(title) <= max_length:
        return title
    
    # Truncate and add ellipsis
    truncated = title[:max_length-3]
    return (truncated + "...") if truncated else title[:max_length-3] + "..."
