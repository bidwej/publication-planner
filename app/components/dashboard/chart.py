"""
Dashboard chart generation for Paper Planner.
Contains ONLY Plotly figure generation functions.
"""

from datetime import datetime
from typing import Optional, List
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from app.components.gantt.chart import _create_placeholder_gantt_chart


def create_dashboard_chart(chart_type: str = 'timeline', data_source: str = 'demo') -> Figure:
    """Create the main dashboard chart - public function."""
    chart_functions = {
        'timeline': _create_schedule_timeline_chart,
        'gantt': _create_schedule_gantt_chart,
        'resources': _create_team_utilization_chart,
        'dependencies': _create_project_dependencies_chart
    }
    chart_func = chart_functions.get(chart_type, _create_schedule_timeline_chart)
    return chart_func(data_source)


def _create_schedule_timeline_chart(data_source: str = 'demo') -> Figure:
    """Create schedule timeline overview chart."""
    fig = go.Figure()
    
    # Sample data for demonstration
    fig.add_trace(go.Scatter(
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        y=[10, 15, 13, 17, 20],
        mode='lines+markers',
        name='Schedule Items',
        marker=dict(size=12, color='blue')
    ))
    
    fig.update_layout(
        title=f'Paper Planner Schedule Timeline - {data_source.title()} Data',
        xaxis_title='Month',
        yaxis_title='Items',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig


def _create_schedule_gantt_chart(data_source: str = 'demo') -> Figure:
    """Create schedule gantt chart for dashboard overview."""
    # Use the Gantt chart functionality from gantt component
    fig = _create_placeholder_gantt_chart()
    
    # Update title to reflect it's a dashboard overview
    fig.update_layout(
        title=f'Paper Planner Schedule Gantt - {data_source.title()} Data'
    )
    
    return fig


def _create_team_utilization_chart(data_source: str = 'demo') -> Figure:
    """Create team resource utilization chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=['Engineering', 'Medical', 'Research', 'Admin'],
        y=[75, 60, 85, 45],
        name='Team Utilization',
        marker_color='lightgreen'
    ))
    
    fig.update_layout(
        title=f'Team Resource Utilization - {data_source.title()} Data',
        xaxis_title='Team',
        yaxis_title='Utilization (%)',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig


def _create_project_dependencies_chart(data_source: str = 'demo') -> Figure:
    """Create project dependency analysis chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[1, 2, 3, 4, 5],
        y=[2, 4, 1, 3, 2],
        mode='lines+markers',
        name='Dependencies',
        marker=dict(size=10, color='orange')
    ))
    
    fig.update_layout(
        title=f'Project Dependencies Analysis - {data_source.title()} Data',
        xaxis_title='Project Phase',
        yaxis_title='Dependency Count',
        height=600,
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
        title="Paper Planner Dashboard - Error",
        xaxis_title="Date",
        yaxis_title="Items",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig



