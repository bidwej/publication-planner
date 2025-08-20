"""
Gantt chart component for timeline visualization.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from datetime import date, timedelta
from typing import Dict, Any, Optional, Union
import sys
import os
from pathlib import Path

# Import backend modules directly - TOML pythonpath should handle this
from core.models import Config, Submission, Schedule
from core.config import load_config

# Frontend imports
from app.components.gantt.sample import create_sample_gantt_chart, create_demo_schedule_from_config
from app.components.gantt.activity import add_activity_bars
from app.components.gantt.timeline import add_background_elements


# Type aliases for frontend use
ConfigData = Dict[str, Any]  # Simplified config representation
SubmissionData = Dict[str, Any]  # Simplified submission representation
ScheduleData = Dict[str, Any]  # Simplified schedule representation


def create_gantt_chart(config: Optional[Union[Config, Dict[str, Any]]] = None, use_sample_data: bool = False) -> Figure:
    """Create a gantt chart with real data or sample data.
    
    Args:
        config: Configuration object or dictionary with submissions data (optional)
        use_sample_data: Force use of sample data instead of trying config (default: False)
        
    Returns:
        Plotly Figure object
    """
    # If sample data is forced or no config provided, use sample data
    if use_sample_data or not config:
        return create_sample_gantt_chart()
    
    # Try to use real data from config
    if config:
        if hasattr(config, 'submissions') and config.submissions:
            # Backend Config object
            demo_schedule = create_demo_schedule_from_config(config)
            return _create_chart_from_config({
                'schedule': demo_schedule,
                'config': config
            })
        elif isinstance(config, dict) and config.get('submissions'):
            # Dictionary config
            demo_schedule = create_demo_schedule_from_config(config)
            return _create_chart_from_config({
                'schedule': demo_schedule,
                'config': config
            })
    
    return _create_empty_chart()


def _create_chart_from_config(config_data: Dict[str, Any]) -> Figure:
    """Create a gantt chart with real data from stored state or database."""
    fig = go.Figure()
    
    schedule = config_data.get('schedule', {})
    config = config_data.get('config', {})
    
    if schedule and config:
        _setup_chart_layout(fig, 'Paper Planner Timeline - Database Data')
        
        # Use the real activity bars and background elements
        add_activity_bars(fig, schedule, config)
        add_background_elements(fig)
        
        # Set y-axis range based on number of activities
        if schedule:
            num_activities = len(schedule)
            fig.update_layout(yaxis=dict(range=[-0.5, num_activities - 0.5]))
    else:
        return _create_empty_chart()
    
    return fig


def _setup_chart_layout(fig: Figure, title: str) -> None:
    """Setup common chart layout configuration."""
    fig.update_layout(
        title=title,
        xaxis_title='Timeline',
        yaxis_title='Activities',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=60, t=80, b=60),
        xaxis=dict(
            type='date',
            showgrid=True,
            gridcolor='lightgray',
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            showticklabels=True
        )
    )


def _create_empty_chart() -> Figure:
    """Create empty chart when no data is available."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available<br>Please load a schedule",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color="#666")
    )
    fig.update_layout(
        title="Paper Planner Gantt Chart",
        xaxis_title="Date",
        yaxis_title="Tasks",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig


def _create_error_chart(error_msg: str) -> Figure:
    """Create an error chart when something goes wrong."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"Error: {error_msg}<br>Check console for details",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color="#e74c3c")
    )
    fig.update_layout(
        title="Paper Planner Gantt - Error",
        xaxis_title="Date",
        yaxis_title="Tasks",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig
