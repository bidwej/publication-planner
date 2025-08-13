"""
Background elements for Gantt charts.
Handles working days, time bands, and visual backgrounds.
"""

import plotly.graph_objects as go
from datetime import date, timedelta


def add_background_elements(fig: go.Figure, chart_height: int) -> None:
    """Add background elements to the chart."""
    # Get chart dimensions from the figure (layout is now configured)
    x_range = fig.layout.xaxis.range  # type: ignore
    if not x_range:
        print("Warning: No x-axis range found in figure layout")
        return
    
    start_date = x_range[0]
    end_date = x_range[1]
    
    # Add working days background
    _add_working_days_background(fig, start_date, end_date, chart_height)
    
    # Add time bands
    _add_time_bands(fig, start_date, end_date, chart_height)


def _add_working_days_background(fig: go.Figure, start_date: date, end_date: date, chart_height: int) -> None:
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
                y0=-0.5,
                y1=chart_height + 0.5,  # Use chart_height directly
                fillcolor='rgba(236, 240, 241, 0.3)',
                line=dict(width=0),
                layer='below'
            )
        
        current_date += timedelta(days=7)
        week_count += 1


def _add_time_bands(fig: go.Figure, start_date: date, end_date: date, chart_height: int) -> None:
    """Add time band indicators for major milestones."""
    # Add monthly markers
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
        if current_date >= start_date:
            fig.add_shape(
                type="line",
                x0=current_date,
                x1=current_date,
                y0=-0.5,
                y1=chart_height + 0.5,  # Use chart_height directly
                line=dict(color='rgba(189, 195, 199, 0.5)', width=1, dash='dot'),
                layer='below'
            )
            
            # Add month label
            fig.add_annotation(
                text=current_date.strftime('%b %Y'),
                x=current_date,
                y=chart_height + 1,  # Use chart_height directly
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
