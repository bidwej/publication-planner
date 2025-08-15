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


def add_activity_bars(fig: Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add activity bars to the gantt chart."""
    if not schedule:
        return
    
    # Get concurrency map for proper row positioning
    concurrency_map = get_concurrency_map(schedule, config)
    
    # Add bars for each submission
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if submission:
            # Calculate duration and end date
            duration_days = max(submission.get_duration_days(config), 7)
            end_date = start_date + timedelta(days=duration_days)
            
            # Add the bar
            _add_activity_bar(fig, submission, start_date, end_date, concurrency_map[submission_id])
            
            # Add label
            _add_bar_label(fig, submission, start_date, end_date, concurrency_map[submission_id])


def add_dependency_arrows(fig: Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add dependency arrows between activities."""
    if not schedule:
        return
    
    # Get concurrency map for proper row positioning
    concurrency_map = get_concurrency_map(schedule, config)
    
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
                        
                        _add_dependency_arrow(fig, dep_end_date, concurrency_map[dep_id], 
                                            start_date, concurrency_map[submission_id])


def _add_activity_bar(fig: Figure, submission: Submission, start_date: date, 
                     end_date: date, row: int) -> None:
    """Add an activity bar for a submission."""
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
    
    # Add type icon with proper positioning
    _add_type_icon(fig, submission, start_date, end_date, row)
    
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


def _add_type_icon(fig: Figure, submission: Submission, start_date: date, end_date: date, row: int) -> None:
    """Add type label with positioning: abstracts in top left, papers in top right."""
    # Determine descriptive text based on submission type and author
    if submission.kind.value == "paper":
        if submission.author == "pccp":
            type_text = "Paper: Engineering"
        elif submission.author == "ed":
            type_text = "Paper: Medical"
        else:
            type_text = "Paper"
    elif submission.kind.value == "abstract":
        if submission.author == "pccp":
            type_text = "Abstract: Engineering"
        elif submission.author == "ed":
            type_text = "Abstract: Medical"
        else:
            type_text = "Abstract"
    elif submission.kind.value == "poster":
        type_text = "Poster"
    else:
        type_text = "Document"
    
    # Position abstracts in top left, papers in top right
    if submission.kind.value == "abstract":
        # Abstract: TOP LEFT
        x_pos = start_date
        x_anchor = 'left'
    else:
        # Paper/Poster: TOP RIGHT  
        x_pos = end_date
        x_anchor = 'right'
    
    # Add type label annotation
    fig.add_annotation(
        text=type_text,
        x=x_pos,
        y=row + 0.2,  # Inside the bar, below the top border
        xref="x", yref="y",
        xanchor=x_anchor, yanchor='bottom',
        font={'size': 8, 'color': '#1a1a1a', 'weight': 'bold'},  # Much darker text for visibility
        showarrow=False
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
        # MODs (pccp) are engineering papers (blue), ED papers (ed) are medical papers (purple)
        if hasattr(submission, 'author') and submission.author == "pccp":
            return "#3498db"  # Blue for MODs (engineering)
        else:
            return "#9b59b6"  # Purple for ED papers (medical)
    elif submission.kind.value == "abstract":
        return "#e67e22"  # Orange for abstracts
    elif submission.kind.value == "poster":
        return "#f39c12"  # Yellow for posters
    else:
        # Fallback for any other types
        return "#95a5a6"  # Gray fallback


def _get_border_color(submission: Submission) -> str:
    """Get border color for submission."""
    if submission.kind.value == "paper":
        # MODs (pccp) have darker blue borders, ED papers have darker purple
        if hasattr(submission, 'author') and submission.author == "pccp":
            return "#2980b9"  # Darker blue for MODs
        else:
            return "#8e44ad"  # Darker purple for ED papers
    elif submission.kind.value == "abstract":
        return "#d35400"  # Darker orange for abstracts
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
