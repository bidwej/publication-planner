"""
Backgrounds component for gantt charts.

Creates beautiful, professional background elements including working days,
holidays, blackout periods, and time interval bands.
"""

from datetime import date, timedelta
from typing import Dict, List, Tuple, Any
import plotly.graph_objects as go
from src.core.models import Config


def add_background_elements(fig: go.Figure, config: Config, timeline_start: date, 
                          max_date: date, max_concurrency: int) -> None:
    """
    Add all background elements to the chart with elegant styling.
    
    Args:
        fig: Plotly figure to add backgrounds to
        config: Configuration object
        timeline_start: Start date for timeline
        max_date: End date for timeline
        max_concurrency: Maximum concurrency level
    """
    try:
        # Add backgrounds in order (bottom to top)
        _add_time_interval_bands(fig, timeline_start, max_date, max_concurrency)
        _add_non_working_days(fig, timeline_start, max_date, max_concurrency)
        _add_blackout_periods(fig, config, timeline_start, max_date, max_concurrency)
        
    except Exception as e:
        # Add error annotation
        fig.add_annotation(
            text=f"Error rendering backgrounds: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.3,
            showarrow=False,
            font=dict(size=14, color="#e74c3c"),
            bgcolor="#fdf2f2",
            bordercolor="#e74c3c"
        )


def _add_time_interval_bands(fig: go.Figure, timeline_start: date, max_date: date, max_concurrency: int) -> None:
    """Add elegant time interval bands for better readability."""
    # Calculate dimensions
    bar_height = 0.8
    y_margin = bar_height / 2 + 0.2
    
    # Add alternating bands every 2 weeks
    current_date = timeline_start
    week_count = 0
    
    while current_date <= max_date:
        start_offset = (current_date - timeline_start).days
        end_offset = min(start_offset + 14, (max_date - timeline_start).days + 1)
        
        # Elegant alternating colors
        if week_count % 2 == 0:
            fillcolor = "rgba(236, 240, 241, 0.4)"  # Light gray
        else:
            fillcolor = "rgba(245, 245, 245, 0.6)"  # Lighter gray
        
        fig.add_shape(
            type="rect",
            x0=start_offset,
            x1=end_offset,
            y0=-y_margin,
            y1=max_concurrency + y_margin,
            fillcolor=fillcolor,
            line=dict(width=0),
            layer="below"
        )
        
        current_date += timedelta(days=14)
        week_count += 1


def _add_non_working_days(fig: go.Figure, timeline_start: date, max_date: date, max_concurrency: int) -> None:
    """Add elegant non-working days (weekends) styling."""
    # Calculate dimensions
    bar_height = 0.8
    y_margin = bar_height / 2 + 0.2
    
    current_date = timeline_start
    while current_date <= max_date:
        # Check if it's a weekend (Saturday = 5, Sunday = 6)
        if current_date.weekday() >= 5:
            start_offset = (current_date - timeline_start).days
            end_offset = start_offset + 1
            
            # Elegant weekend styling
            fig.add_shape(
                type="rect",
                x0=start_offset,
                x1=end_offset,
                y0=-y_margin,
                y1=max_concurrency + y_margin,
                fillcolor="rgba(189, 195, 199, 0.3)",  # Subtle blue-gray
                line=dict(width=0),
                layer="below"
            )
        
        current_date += timedelta(days=1)


def _add_blackout_periods(fig: go.Figure, config: Config, timeline_start: date, 
                         max_date: date, max_concurrency: int) -> None:
    """Add elegant blackout periods from config."""
    blackout_dates = getattr(config, 'blackout_dates', []) or []
    if not blackout_dates:
        return
    
    # Group consecutive blackout dates into periods
    periods = _get_consecutive_periods(blackout_dates)
    
    # Calculate dimensions
    bar_height = 0.8
    y_margin = bar_height / 2 + 0.2
    
    for start_date, end_date in periods:
        start_offset = (start_date - timeline_start).days
        end_offset = (end_date - timeline_start).days + 1
        
        # Elegant blackout styling with subtle red
        fig.add_shape(
            type="rect",
            x0=start_offset,
            x1=end_offset,
            y0=-y_margin,
            y1=max_concurrency + y_margin,
            fillcolor="rgba(231, 76, 60, 0.15)",  # Subtle red
            line=dict(
                color="rgba(231, 76, 60, 0.3)",
                width=1,
                dash="dot"
            ),
            layer="below"
        )
        
        # Add subtle text label for blackout periods
        if (end_offset - start_offset) > 3:  # Only for periods longer than 3 days
            center_x = start_offset + (end_offset - start_offset) / 2
            fig.add_annotation(
                x=center_x,
                y=max_concurrency + y_margin + 0.5,
                text="Blackout",
                showarrow=False,
                xanchor="center",
                yanchor="bottom",
                font=dict(size=10, color="#c0392b"),
                bgcolor="rgba(231, 76, 60, 0.1)",
                bordercolor="rgba(231, 76, 60, 0.3)",
                borderwidth=1
            )


def _get_consecutive_periods(dates: List[date]) -> List[Tuple[date, date]]:
    """Group consecutive dates into periods efficiently."""
    if not dates:
        return []
    
    # Sort dates
    sorted_dates = sorted(dates)
    periods = []
    current_start = None
    current_end = None
    
    for date_obj in sorted_dates:
        if current_start is None:
            current_start = date_obj
            current_end = date_obj
        elif (date_obj - current_end).days == 1:
            # Consecutive date, extend current period
            current_end = date_obj
        else:
            # Gap found, save current period and start new one
            if current_start and current_end:
                periods.append((current_start, current_end))
            current_start = date_obj
            current_end = date_obj
    
    # Add final period
    if current_start and current_end:
        periods.append((current_start, current_end))
    
    return periods
