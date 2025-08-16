"""
Main entry point for creating Gantt charts.
Wrapper that styles the overall chart and orchestrates components.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from typing import Dict, Any, Optional, List
from datetime import date, timedelta



def create_gantt_chart() -> Figure:
    """Create the main gantt chart - public function."""
    return _create_placeholder_gantt_chart()


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