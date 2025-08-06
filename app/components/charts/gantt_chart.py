"""
Interactive Gantt chart component for schedule visualization.
"""

import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Dict, List, Optional
from core.models import Config, Submission, SubmissionType

def create_gantt_chart(schedule: Dict[str, date], config: Config) -> go.Figure:
    """Create an interactive Gantt chart for the schedule."""
    if not schedule:
        return _create_empty_gantt()
    
    gantt_data = _prepare_gantt_data(schedule, config)
    
    fig = go.Figure()
    
    # Add bars for each submission
    for data in gantt_data:
        fig.add_trace(go.Bar(
            x=[data['duration']],
            y=[data['title']],  # Use title instead of ID
            orientation='h',
            name=data['title'],
            text=data['hover_text'],
            hoverinfo='text',
            marker=dict(color=data['color'], line=dict(color='black', width=1)),
            base=data['start_days'],
            customdata=data['custom_data']
        ))
    
    # Update layout with cleaner configuration
    fig.update_layout(
        title={'text': 'Schedule Timeline', 'x': 0.5, 'xanchor': 'center'},
        xaxis=dict(
            title='Timeline (Weeks)', 
            showgrid=True, 
            gridcolor='lightgray',
            tickmode='array',
            tickvals=list(range(0, max([d['start_days'] + d['duration'] for d in gantt_data]) + 1, 7))
        yaxis=dict(title='Papers & Submissions', showgrid=False),
        barmode='overlay',
        height=600,
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    _add_deadline_markers(fig, schedule, config)
    _add_dependency_arrows(fig, schedule, config)
    
    return fig

def _prepare_gantt_data(schedule: Dict[str, date], config: Config) -> List[Dict]:
    """Prepare data for Gantt chart visualization."""
    submissions_dict = config.submissions_dict
    
    all_dates = list(schedule.values())
    if not all_dates:
        return []
    
    min_date = min(all_dates)
    max_date = max(all_dates) + timedelta(days=90)
    
    gantt_data = []
    
    for submission_id, start_date in schedule.items():
        submission = submissions_dict.get(submission_id)
        if not submission:
            continue
        
        duration_days = submission.get_duration_days(config)
        start_days = (start_date - min_date).days
        
        # Create hover text
        conference_name = "No conference"
        if submission.conference_id:
            conference = config.conferences_dict.get(submission.conference_id)
            if conference:
                conference_name = conference.name
        
        hover_text = f"<b>{submission.title}</b><br>"
        hover_text += f"Type: {submission.kind.value}<br>"
        hover_text += f"Conference: {conference_name}<br>"
        hover_text += f"Start: {start_date.strftime('%Y-%m-%d')}<br>"
        hover_text += f"Duration: {duration_days} days"
        
        gantt_data.append({
            'id': submission_id,
            'title': submission.title,
            'duration': duration_days,
            'start_days': start_days,
            'color': _get_submission_color(submission, config),
            'hover_text': hover_text,
            'custom_data': [submission_id]
        })
    
    return gantt_data

def _get_submission_color(submission: Submission, config: Config) -> str:
    """Get color for submission based on type and engineering flag."""
    if submission.kind == SubmissionType.PAPER:
        return '#2E86AB' if submission.engineering else '#A23B72'
    else:  # Abstract
        return '#F18F01' if submission.engineering else '#C73E1D'

def _add_deadline_markers(fig: go.Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add deadline markers to the chart."""
    if not config.conferences_dict:
        return
    
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if not submission or not submission.conference_id:
            continue
        
        conference = config.conferences_dict.get(submission.conference_id)
        if not conference or not conference.deadline:
            continue
        
        deadline_days = (conference.deadline - min(schedule.values())).days
        
        fig.add_vline(
            x=deadline_days,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Deadline: {conference.deadline.strftime('%Y-%m-%d')}",
            annotation_position="top right"
        )

def _add_dependency_arrows(fig: go.Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add dependency arrows between submissions."""
    submissions_dict = config.submissions_dict
    
    for submission_id, start_date in schedule.items():
        submission = submissions_dict.get(submission_id)
        if not submission or not submission.depends_on:
            continue
        
        for dep_id in submission.depends_on:
            if dep_id in schedule:
                dep_start = schedule[dep_id]
                dep_submission = submissions_dict.get(dep_id)
                if dep_submission:
                    dep_duration = dep_submission.get_duration_days(config)
                    dep_end_days = (dep_start + timedelta(days=dep_duration) - min(schedule.values())).days
                    current_start_days = (start_date - min(schedule.values())).days
                    
                    fig.add_annotation(
                        x=dep_end_days,
                        y=dep_submission.title,  # Use title instead of ID
                        xref="x",
                        yref="y",
                        axref="x",
                        ayref="y",
                        ax=current_start_days,
                        ay=submission.title,  # Use title instead of ID
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="gray"
                    )

def _create_empty_gantt() -> go.Figure:
    """Create an empty Gantt chart."""
    fig = go.Figure()
    fig.update_layout(
        title={'text': 'No Schedule Available', 'x': 0.5, 'xanchor': 'center'},
        xaxis=dict(title='Timeline (Days)'),
        yaxis=dict(title='Submissions'),
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        annotations=[{
            'text': 'Generate a schedule to see the timeline',
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': 0.5,
            'showarrow': False,
            'font': {'size': 16, 'color': 'gray'}
        }]
    )
    return fig
