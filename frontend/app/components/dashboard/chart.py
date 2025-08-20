"""
Dashboard chart generation for Paper Planner.
Contains ONLY Plotly figure generation functions.
"""

from datetime import datetime
from typing import Optional, List, Union, Any
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from app.components.gantt.chart import create_gantt_chart

# Import backend modules directly - TOML pythonpath should handle this
from core.models import Config, Submission


def create_dashboard_chart(chart_type: str = 'timeline', config: Optional[Config] = None) -> Figure:
    """Create the main dashboard chart - public function.
    
    Args:
        chart_type: Type of chart to create ('timeline', 'gantt', 'resources', 'dependencies')
        config: Configuration object containing submissions, conferences, etc.
        
    Returns:
        Plotly Figure object
    """
    chart_functions = {
        'timeline': _create_schedule_timeline_chart,
        'gantt': _create_schedule_gantt_chart,
        'resources': _create_team_utilization_chart,
        'dependencies': _create_project_dependencies_chart
    }
    chart_func = chart_functions.get(chart_type, _create_schedule_timeline_chart)
    return chart_func(config)


def _create_schedule_timeline_chart(config: Optional[Config] = None) -> Figure:
    """Create schedule timeline overview chart.
    
    Args:
        config: Configuration object with submissions data
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    if config and config.submissions:
        # Use real data from config
        submission_names = []
        for submission in config.submissions:
            title = submission.title
            if len(title) > 30:
                submission_names.append(title[:30] + "...")
            else:
                submission_names.append(title)
        
        submission_counts = [1] * len(config.submissions)  # Each submission counts as 1
        
        fig.add_trace(go.Scatter(
            x=submission_names,
            y=submission_counts,
            mode='lines+markers',
            name='Real Submissions',
            marker=dict(size=12, color='blue')
        ))
        
        title = f'Paper Planner Schedule Timeline - Real Data ({len(config.submissions)} submissions)'
    else:
        # Fallback to realistic demo data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        # Realistic submission counts showing the actual scheduling patterns
        # Jan: mod_1 starts, Feb: mod_2 starts, Mar: abstracts start, Apr-May: papers start
        submission_counts = [1, 2, 4, 5, 6, 7]
        
        fig.add_trace(go.Scatter(
            x=months,
            y=submission_counts,
            mode='lines+markers',
            name='Demo Schedule',
            marker=dict(size=12, color='blue'),
            line=dict(width=3)
        ))
        
        # Add annotations for key milestones
        fig.add_annotation(x=0, y=1, text="mod_1 starts", showarrow=True, arrowhead=2)
        fig.add_annotation(x=1, y=2, text="mod_2 starts", showarrow=True, arrowhead=2)
        fig.add_annotation(x=2, y=4, text="Abstracts start", showarrow=True, arrowhead=2)
        fig.add_annotation(x=3, y=5, text="Papers start", showarrow=True, arrowhead=2)
        
        title = 'Paper Planner Schedule Timeline - Realistic Demo'
    
    fig.update_layout(
        title=title,
        xaxis_title='Submissions',
        yaxis_title='Count',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig


def _create_schedule_gantt_chart(config: Optional[Config] = None) -> Figure:
    """Create schedule gantt chart for dashboard overview.
    
    Args:
        config: Configuration object with submissions data
        
    Returns:
        Plotly Figure object
    """
    # Use the Gantt chart functionality from gantt component
    # If no config provided, it will automatically use sample data
    fig = create_gantt_chart(config=config, use_sample_data=(config is None))
    
    # Update title to reflect it's a dashboard overview
    if config and config.submissions:
        title = f'Paper Planner Schedule Gantt - Real Data ({len(config.submissions)} submissions)'
    else:
        title = 'Paper Planner Schedule Gantt - Sample Data'
    
    fig.update_layout(title=title)
    
    return fig


def _create_team_utilization_chart(config: Optional[Config] = None) -> Figure:
    """Create team resource utilization chart.
    
    Args:
        config: Configuration object with submissions data
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    if config and config.submissions:
        # Use real data from config - group by author/team
        team_counts = {}
        for submission in config.submissions:
            team = getattr(submission, 'author', 'Unknown')
            team_counts[team] = team_counts.get(team, 0) + 1
        
        teams = list(team_counts.keys())
        counts = list(team_counts.values())
        
        fig.add_trace(go.Bar(
            x=teams,
            y=counts,
            name='Real Team Workload',
            marker_color='lightgreen'
        ))
        
        title = f'Team Resource Utilization - Real Data ({len(config.submissions)} submissions)'
    else:
        # Fallback to sample data
        fig.add_trace(go.Bar(
            x=['Engineering', 'Medical', 'Research', 'Admin'],
            y=[75, 60, 85, 45],
            name='Sample Data',
            marker_color='lightgreen'
        ))
        title = 'Team Resource Utilization - Sample Data'
    
    fig.update_layout(
        title=title,
        xaxis_title='Team',
        yaxis_title='Submission Count',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig


def _create_project_dependencies_chart(config: Optional[Config] = None) -> Figure:
    """Create project dependency analysis chart.
    
    Args:
        config: Configuration object with submissions data
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    if config and config.submissions:
        # Use real data from config - analyze dependencies
        dependency_counts = []
        submission_names = []
        
        for submission in config.submissions:
            deps = submission.depends_on or []
            dependency_counts.append(len(deps))
            
            title = submission.title
            if len(title) > 25:
                submission_names.append(title[:25] + "...")
            else:
                submission_names.append(title)
        
        fig.add_trace(go.Scatter(
            x=submission_names,
            y=dependency_counts,
            mode='lines+markers',
            name='Real Dependencies',
            marker=dict(size=10, color='orange')
        ))
        
        title = f'Project Dependencies Analysis - Real Data ({len(config.submissions)} submissions)'
    else:
        # Fallback to sample data
        fig.add_trace(go.Scatter(
            x=[1, 2, 3, 4, 5],
            y=[2, 4, 1, 3, 2],
            mode='lines+markers',
            name='Sample Data',
            marker=dict(size=10, color='orange')
        ))
        title = 'Project Dependencies Analysis - Sample Data'
    
    fig.update_layout(
        title=title,
        xaxis_title='Submissions',
        yaxis_title='Dependency Count',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig


def _create_error_chart(error_msg: str) -> Figure:
    """Create an error chart when something goes wrong.
    
    Args:
        error_msg: Error message to display
        
    Returns:
        Plotly Figure object
    """
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



