"""
Main entry point for creating Gantt charts.
Wrapper that styles the overall chart and orchestrates components.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from typing import Dict, Any, Optional
from datetime import date
from pathlib import Path

from app.components.gantt.timeline import get_timeline_range
from app.components.gantt.activity import add_activity_bars, add_dependency_arrows
from app.components.gantt.layout import configure_gantt_layout, add_background_elements
from src.core.models import ScheduleState


def create_gantt_chart(schedule_state: Optional[ScheduleState]) -> Figure:
    """Create a gantt chart from schedule state."""
    if not schedule_state or not hasattr(schedule_state, 'schedule') or not schedule_state.schedule:
        return _create_empty_chart()
    
    try:
        # Get chart dimensions
        chart_dimensions = get_timeline_range(schedule_state.schedule, schedule_state.config)
        
        # Create figure
        fig = go.Figure()
        
        # Configure chart layout and styling
        configure_gantt_layout(fig, chart_dimensions)
        
        # Add background elements (can now read chart dimensions from figure)
        add_background_elements(fig)
        
        # Add activities (middle layer) - concurrency map is generated internally
        add_activity_bars(fig, schedule_state.schedule, schedule_state.config)
        add_dependency_arrows(fig, schedule_state.schedule, schedule_state.config)
        
        return fig
        
    except Exception as e:
        return _create_error_chart(str(e))


def generate_gantt_png(schedule: Dict[str, date], config: Any, filename: str, 
                       output_dir: Optional[str] = None) -> Optional[str]:
    """
    Generate a PNG file from a Gantt chart.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        The schedule to visualize
    config : Any
        Configuration object
    filename : str
        Output filename
    output_dir : Optional[str]
        Output directory (defaults to current directory)
        
    Returns
    -------
    Optional[str]
        Path to generated PNG file, or None if failed
    """
    try:
        # Create ScheduleState for compatibility
        from src.core.models import ScheduleState, SchedulerStrategy
        from datetime import datetime
        
        schedule_state = ScheduleState(
            schedule=schedule,
            config=config,
            strategy=SchedulerStrategy.GREEDY,
            timestamp=datetime.now().isoformat()
        )
        
        # Create the chart
        fig = create_gantt_chart(schedule_state)
        
        # Determine output path
        if output_dir:
            output_path = Path(output_dir) / filename
        else:
            output_path = Path(filename)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as PNG using headless server (as per user preferences)
        fig.write_image(str(output_path), engine="kaleido")
        
        return str(output_path)
        
    except Exception as e:
        print(f"Error generating PNG: {e}")
        return None


def generate_gantt_html(schedule: Dict[str, date], config: Any, filename: str,
                       output_dir: Optional[str] = None) -> Optional[str]:
    """
    Generate an HTML file from a Gantt chart.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        The schedule to visualize
    config : Any
        Configuration object
    filename : str
        Output filename
    output_dir : Optional[str]
        Output directory (defaults to current directory)
        
    Returns
    -------
    Optional[str]
        Path to generated HTML file, or None if failed
    """
    try:
        # Create ScheduleState for compatibility
        from src.core.models import ScheduleState, SchedulerStrategy
        from datetime import datetime
        
        schedule_state = ScheduleState(
            schedule=schedule,
            config=config,
            strategy=SchedulerStrategy.GREEDY,
            timestamp=datetime.now().isoformat()
        )
        
        # Create the chart
        fig = create_gantt_chart(schedule_state)
        
        # Determine output path
        if output_dir:
            output_path = Path(output_dir) / filename
        else:
            output_path = Path(filename)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as HTML
        fig.write_html(str(output_path))
        
        return str(output_path)
        
    except Exception as e:
        print(f"Error generating HTML: {e}")
        return None


def _create_empty_chart() -> Figure:
    """Create empty chart when no data is available."""
    fig = go.Figure()
    fig.update_layout(
        title={'text': 'No Schedule Data Available', 'x': 0.5, 'xanchor': 'center'},
        height=400, plot_bgcolor='white', paper_bgcolor='white'
    )
    return fig


def _create_error_chart(error_message: str) -> Figure:
    """Create error chart when chart creation fails."""
    fig = go.Figure()
    fig.update_layout(
        title={'text': 'Chart Creation Failed', 'x': 0.5, 'xanchor': 'center'},
        height=400, plot_bgcolor='white', paper_bgcolor='white'
    )
    fig.add_annotation(
        text=error_message, xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        font={'size': 14, 'color': '#e74c3c'}, showarrow=False
    )
    return fig 