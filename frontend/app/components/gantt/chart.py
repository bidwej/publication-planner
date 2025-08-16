"""
Main entry point for creating Gantt charts.
Wrapper that styles the overall chart and orchestrates components.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from typing import Dict, Any, Optional, List
from datetime import date, timedelta
from core.models import Config



def create_gantt_chart() -> Figure:
    """Create the main gantt chart - public function.
    
    Returns:
        Plotly Figure object
    """
    # Try to get data from state manager, fall back to sample data
    try:
        from app.storage import get_state_manager
        stored_state = get_state_manager().load_component_state('gantt')
        if stored_state and 'config_data' in stored_state:
            # We have stored config data, use it
            return _create_real_gantt_chart(stored_state['config_data'])
        else:
            return _create_placeholder_gantt_chart()
    except Exception:
        return _create_placeholder_gantt_chart()


def _create_real_gantt_chart(config_data: Dict[str, Any]) -> Figure:
    """Create a gantt chart with real data from stored state."""
    fig = go.Figure()
    
    # Use stored config data
    submission_count = config_data.get('submission_count', 0)
    conference_count = config_data.get('conference_count', 0)
    
    # Create a simple representation based on stored data
    fig.add_trace(go.Bar(
        name=f'Submissions ({submission_count})',
        x=[submission_count],
        y=['Submissions'],
        orientation='h',
        marker_color='lightblue',
        opacity=0.8
    ))
    
    fig.add_trace(go.Bar(
        name=f'Conferences ({conference_count})',
        x=[conference_count],
        y=['Conferences'],
        orientation='h',
        marker_color='lightgreen',
        opacity=0.8
    ))
    
    fig.update_layout(
        title=f'Paper Planner Gantt Chart - Real Data ({submission_count} submissions, {conference_count} conferences)',
        xaxis_title='Count',
        yaxis_title='Categories',
        height=400,
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig


def _create_placeholder_gantt_chart() -> Figure:
    """Create a placeholder gantt chart."""
    fig = go.Figure()
    
    # Sample gantt data
    tasks: List[str] = ['Task A', 'Task B', 'Task C', 'Task D']
    start_dates: List[str] = ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15']
    end_dates: List[str] = ['2024-01-14', '2024-01-31', '2024-02-14', '2024-02-28']
    
    for i, task in enumerate(tasks):
        fig.add_trace(go.Bar(
            name=task,
            x=[(end_dates[i], start_dates[i])],
            y=[task],
            orientation='h',
            marker_color='lightblue',
            opacity=0.8
        ))
    
    fig.update_layout(
        title='Paper Planner Gantt Chart',
        xaxis_title='Timeline',
        yaxis_title='Tasks',
        height=400,
        barmode='overlay',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig


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