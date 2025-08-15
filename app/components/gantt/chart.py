"""
Main entry point for creating Gantt charts.
Wrapper that styles the overall chart and orchestrates components.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from typing import Dict, Any, Optional
from datetime import date

from app.components.gantt.timeline import get_timeline_range, add_background_elements
from app.components.gantt.activity import add_activity_bars, add_dependency_arrows
from app.components.gantt.layout import configure_gantt_layout
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