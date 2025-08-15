"""
Background visual elements for Gantt charts.
Handles working days, monthly markers, and other visual enhancements.
"""

from datetime import date, timedelta
import plotly.graph_objects as go
from plotly.graph_objs import Figure


def add_background_elements(fig: Figure) -> None:
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


def _add_working_days_background(fig: Figure, start_date: date, end_date: date, y_min: float, y_max: float) -> None:
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


def _add_monthly_markers(fig: Figure, start_date: date, end_date: date, y_min: float, y_max: float) -> None:
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
