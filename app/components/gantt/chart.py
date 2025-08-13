"""
Main entry point for creating Gantt charts.
"""

import plotly.graph_objects as go
from typing import Dict, Any

from app.components.gantt.timeline import get_timeline_range, get_concurrency_map, get_title_text
from app.components.gantt.activities import add_activity_bars, add_dependency_arrows
from app.components.gantt.backgrounds import add_background_elements
from src.core.models import ScheduleState


def create_gantt_chart(schedule_state: ScheduleState) -> go.Figure:
    """Create a gantt chart from schedule state."""
    if not schedule_state or not schedule_state.schedule:
        return _create_empty_chart()
    
    try:
        # Get timeline range and concurrency map
        timeline_range = get_timeline_range(schedule_state.schedule, schedule_state.config)
        concurrency_map = get_concurrency_map(schedule_state.schedule, schedule_state.config)
        
        # Create figure
        fig = go.Figure()
        
        # Configure layout FIRST (so backgrounds can read from it)
        _configure_layout(fig, timeline_range)
        
        # Add background elements (can now read chart dimensions from figure)
        add_background_elements(fig, timeline_range['max_concurrency'])
        
        # Add activities (middle layer)
        add_activity_bars(fig, schedule_state.schedule, schedule_state.config, concurrency_map, timeline_range['timeline_start'])
        add_dependency_arrows(fig, schedule_state.schedule, schedule_state.config, concurrency_map, timeline_range['timeline_start'])
        
        return fig
        
    except Exception as e:
        return _create_error_chart(str(e))


def _configure_layout(fig: go.Figure, timeline_range: Dict[str, Any]) -> None:
    """Configure the chart layout."""
    title_text = get_title_text(timeline_range)
    max_concurrency = timeline_range['max_concurrency']
    
    fig.update_layout(
        title={
            'text': title_text,
            'x': 0.5, 'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        height=400 + max_concurrency * 30,
        margin=dict(l=80, r=80, t=100, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis={
            'type': 'date',
            'range': [timeline_range['min_date'], timeline_range['max_date']],
            'title': 'Timeline',
            'showgrid': True, 'gridcolor': '#ecf0f1'
        },
        yaxis={
            'title': 'Activities',
            'range': [-0.5, max_concurrency + 0.5],
            'tickmode': 'linear', 'dtick': 1,
            'showgrid': True, 'gridcolor': '#ecf0f1'
        },
        showlegend=False
    )


def _create_empty_chart() -> go.Figure:
    """Create empty chart."""
    fig = go.Figure()
    fig.update_layout(
        title={'text': 'No Schedule Data Available', 'x': 0.5, 'xanchor': 'center'},
        height=400, plot_bgcolor='white', paper_bgcolor='white'
    )
    return fig


def _create_error_chart(error_message: str) -> go.Figure:
    """Create error chart."""
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
