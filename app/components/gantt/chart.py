"""Main entry point for creating Gantt charts."""

import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Dict, Any, Optional

from app.components.gantt.timeline import get_timeline_range
from app.components.gantt.activities import add_activity_bars, add_dependency_arrows
from app.components.gantt.backgrounds import add_background_elements
from src.core.models import Config
from src.validation.resources import validate_resources_constraints


def create_gantt_chart(schedule: Dict[str, date], config: Config, forced_timeline: Optional[Dict] = None) -> go.Figure:
    """Create a beautiful gantt chart from schedule data."""
    # Validate inputs first
    _validate_inputs(schedule, config)
    
    if not schedule:
        return _create_empty_chart()
    
    try:
        # Get timeline range using existing business logic
        timeline_range = get_timeline_range(schedule, config, forced_timeline)
        
        # Use existing concurrency validation from src instead of duplicating
        resource_validation = validate_resources_constraints(schedule, config)
        max_concurrency = resource_validation.max_observed
        
        # Create chart figure
        fig = _create_chart_figure(timeline_range, max_concurrency)
        
        # Add chart elements
        _add_chart_elements(fig, schedule, config, timeline_range, max_concurrency)
        
        return fig
        
    except Exception as e:
        return _create_error_chart(f"Error creating chart: {str(e)}")


def _validate_inputs(schedule: Dict[str, date], config: Config) -> None:
    """Validate input parameters."""
    if not isinstance(schedule, dict):
        raise TypeError("Schedule must be a dictionary")
    if not isinstance(config, Config):
        raise TypeError("Config must be a Config object")


def _create_empty_chart() -> go.Figure:
    """Create an empty chart when no schedule data is available."""
    fig = go.Figure()
    fig.update_layout(
        title={
            'text': 'No Schedule Data Available',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#7f8c8d'},
            'y': 0.5
        },
        height=400,
        margin=dict(l=80, r=80, t=100, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig


def _create_error_chart(error_message: str) -> go.Figure:
    """Create an error chart when chart creation fails."""
    fig = go.Figure()
    fig.update_layout(
        title={
            'text': 'Chart Creation Failed',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#e74c3c'},
            'y': 0.6
        },
        height=400,
        margin=dict(l=80, r=80, t=100, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Add error annotation
    fig.add_annotation(
        text=error_message,
        xref="paper", yref="paper",
        x=0.5, y=0.4,
        xanchor='center', yanchor='middle',
        font={'size': 14, 'color': '#e74c3c'},
        showarrow=False
    )
    
    return fig


def _create_chart_figure(timeline_range: Dict[str, Any], max_concurrency: int) -> go.Figure:
    """Create the base chart figure with proper dimensions."""
    # Calculate optimal height based on concurrency
    base_height = 400
    concurrency_height = max(50, max_concurrency * 30)
    total_height = base_height + concurrency_height
    
    fig = go.Figure()
    fig.update_layout(
        height=total_height,
        margin=dict(l=80, r=80, t=100, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig


def _add_chart_elements(fig: go.Figure, schedule: Dict[str, date], config: Config,
                       timeline_range: Dict[str, Any], max_concurrency: int) -> None:
    """Add all chart elements in the correct order."""
    # Add backgrounds first (bottom layer)
    add_background_elements(fig, config, timeline_range['timeline_start'], 
                          timeline_range['max_date'], max_concurrency)
    
    # Add activities (middle layer) - pass empty concurrency_map since we're not calculating it here
    # The activities module will handle positioning based on the schedule data
    add_activity_bars(fig, schedule, config, {}, timeline_range['timeline_start'])
    add_dependency_arrows(fig, schedule, config, {}, timeline_range['timeline_start'])
    
    # Configure layout last (top layer)
    _configure_layout(fig, timeline_range, max_concurrency)


def _configure_layout(fig: go.Figure, timeline_range: Dict[str, Any], max_concurrency: int) -> None:
    """Configure the chart layout with elegant styling."""
    from app.components.gantt.timeline import get_title_text
    
    title_text = get_title_text(timeline_range)
    
    # Calculate Y-axis range
    bar_height = 0.8
    y_margin = bar_height / 2 + 0.2
    y_range = [-y_margin, max_concurrency + y_margin]
    
    # Create elegant layout
    fig.update_layout(
        title={
            'text': title_text,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'},
            'y': 0.95
        },
        xaxis={
            'title': {'text': 'Timeline', 'font': {'size': 14, 'color': '#34495e'}},
            'type': 'date',
            'range': [timeline_range['min_date'], timeline_range['max_date']],
            'showgrid': True,
            'gridcolor': '#ecf0f1',
            'gridwidth': 1,
            'zeroline': False,
            'showline': True,
            'linecolor': '#bdc3c7',
            'linewidth': 1,
            'tickfont': {'size': 12, 'color': '#7f8c8d'},
            'tickangle': 0
        },
        yaxis={
            'title': {'text': 'Submissions', 'font': {'size': 14, 'color': '#34495e'}},
            'range': y_range,
            'showgrid': True,
            'gridcolor': '#ecf0f1',
            'gridwidth': 1,
            'zeroline': False,
            'showline': True,
            'linecolor': '#bdc3c7',
            'linewidth': 1,
            'tickfont': {'size': 12, 'color': '#7f8c8d'},
            'tickmode': 'linear',
            'dtick': 1
        },
        showlegend=False,
        hovermode='closest',
        hoverlabel={
            'bgcolor': 'white',
            'font': {'size': 12, 'color': '#2c3e50'},
            'bordercolor': '#bdc3c7'
        }
    )
