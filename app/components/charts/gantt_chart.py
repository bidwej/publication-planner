"""
Interactive Gantt chart component for schedule visualization.
"""

import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
from typing import Dict, List, Optional
from core.models import Config, Submission, SubmissionType

def create_gantt_chart(schedule: Dict[str, date], config: Config) -> go.Figure:
    """
    Create an interactive Gantt chart for the schedule.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Schedule mapping submission_id to start_date
    config : Config
        Configuration containing submission data
        
    Returns
    -------
    go.Figure
        Interactive Gantt chart
    """
    if not schedule:
        return create_empty_gantt()
    
    # Prepare data for Gantt chart
    gantt_data = prepare_gantt_data(schedule, config)
    
    # Create the Gantt chart
    fig = go.Figure()
    
    # Add bars for each submission
    for submission_data in gantt_data:
        fig.add_trace(go.Bar(
            x=[submission_data['duration']],
            y=[submission_data['id']],
            orientation='h',
            name=submission_data['title'],
            text=submission_data['hover_text'],
            hoverinfo='text',
            marker=dict(
                color=submission_data['color'],
                line=dict(color='black', width=1)
            ),
            base=submission_data['start_days'],
            customdata=submission_data['custom_data']
        ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Schedule Timeline',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis=dict(
            title='Timeline (Days)',
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        ),
        yaxis=dict(
            title='Submissions',
            showgrid=False,
            zeroline=False
        ),
        barmode='overlay',
        height=600,
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add deadline markers
    add_deadline_markers(fig, schedule, config)
    
    # Add dependency arrows
    add_dependency_arrows(fig, schedule, config)
    
    return fig

def prepare_gantt_data(schedule: Dict[str, date], config: Config) -> List[Dict]:
    """Prepare data for Gantt chart visualization."""
    submissions_dict = config.submissions_dict
    conferences_dict = config.conferences_dict
    
    # Find timeline bounds
    all_dates = list(schedule.values())
    if not all_dates:
        return []
    
    min_date = min(all_dates)
    max_date = max(all_dates) + timedelta(days=90)  # Add buffer
    
    gantt_data = []
    
    for submission_id, start_date in schedule.items():
        submission = submissions_dict.get(submission_id)
        if not submission:
            continue
        
        # Calculate duration and end date
        duration_days = submission.get_duration_days(config)
        end_date = start_date + timedelta(days=duration_days)
        
        # Calculate position relative to timeline start
        start_days = (start_date - min_date).days
        
        # Determine color based on submission type and priority
        color = get_submission_color(submission, config)
        
        # Create hover text
        conference_name = conferences_dict.get(submission.conference_id, {}).name if submission.conference_id else "No conference"
        hover_text = f"""
        <b>{submission.title}</b><br>
        Type: {submission.kind.value.title()}<br>
        Conference: {conference_name}<br>
        Start: {start_date.strftime('%Y-%m-%d')}<br>
        End: {end_date.strftime('%Y-%m-%d')}<br>
        Duration: {duration_days} days
        """
        
        # Custom data for interactions
        custom_data = {
            'submission_id': submission_id,
            'submission_type': submission.kind.value,
            'conference_id': submission.conference_id,
            'engineering': submission.engineering,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_days': duration_days
        }
        
        gantt_data.append({
            'id': submission_id,
            'title': submission.title,
            'start_days': start_days,
            'duration': duration_days,
            'color': color,
            'hover_text': hover_text,
            'custom_data': custom_data,
            'submission': submission
        })
    
    return sorted(gantt_data, key=lambda x: x['start_days'])

def get_submission_color(submission: Submission, config: Config) -> str:
    """Get color for submission based on type and priority."""
    if submission.kind == SubmissionType.PAPER:
        if submission.engineering:
            return '#1f77b4'  # Blue for engineering papers
        else:
            return '#2ca02c'  # Green for medical papers
    elif submission.kind == SubmissionType.ABSTRACT:
        return '#ff7f0e'  # Orange for abstracts
    else:
        return '#d62728'  # Red for other types

def add_deadline_markers(fig: go.Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add deadline markers to the Gantt chart."""
    submissions_dict = config.submissions_dict
    conferences_dict = config.conferences_dict
    
    # Find timeline bounds
    all_dates = list(schedule.values())
    if not all_dates:
        return
    
    min_date = min(all_dates)
    
    deadline_data = []
    
    for submission_id, start_date in schedule.items():
        submission = submissions_dict.get(submission_id)
        if not submission or not submission.conference_id:
            continue
        
        conference = conferences_dict.get(submission.conference_id)
        if not conference or submission.kind not in conference.deadlines:
            continue
        
        deadline = conference.deadlines[submission.kind]
        deadline_days = (deadline - min_date).days
        
        deadline_data.append({
            'x': deadline_days,
            'y': submission_id,
            'deadline': deadline,
            'conference': conference.name,
            'submission_type': submission.kind.value
        })
    
    if deadline_data:
        fig.add_trace(go.Scatter(
            x=[d['x'] for d in deadline_data],
            y=[d['y'] for d in deadline_data],
            mode='markers',
            marker=dict(
                symbol='diamond',
                size=12,
                color='red',
                line=dict(color='darkred', width=2)
            ),
            name='Deadlines',
            text=[f"Deadline: {d['deadline'].strftime('%Y-%m-%d')}<br>{d['conference']}" 
                  for d in deadline_data],
            hoverinfo='text',
            showlegend=True
        ))

def add_dependency_arrows(fig: go.Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add dependency arrows to the Gantt chart."""
    submissions_dict = config.submissions_dict
    
    # Find timeline bounds
    all_dates = list(schedule.values())
    if not all_dates:
        return
    
    min_date = min(all_dates)
    
    arrows_data = []
    
    for submission_id, start_date in schedule.items():
        submission = submissions_dict.get(submission_id)
        if not submission or not submission.depends_on:
            continue
        
        for dep_id in submission.depends_on:
            if dep_id not in schedule:
                continue
            
            dep_submission = submissions_dict.get(dep_id)
            if not dep_submission:
                continue
            
            # Calculate positions
            dep_start_days = (schedule[dep_id] - min_date).days
            dep_duration = dep_submission.get_duration_days(config)
            dep_end_days = dep_start_days + dep_duration
            
            current_start_days = (start_date - min_date).days
            
            # Create arrow from dependency end to current start
            arrows_data.append({
                'x': [dep_end_days, current_start_days],
                'y': [dep_id, submission_id],
                'arrow_color': '#666666'
            })
    
    # Add arrows (using scatter with arrows)
    for arrow in arrows_data:
        fig.add_trace(go.Scatter(
            x=arrow['x'],
            y=arrow['y'],
            mode='lines+markers',
            line=dict(color=arrow['arrow_color'], width=2, dash='dot'),
            marker=dict(size=6, color=arrow['arrow_color']),
            showlegend=False,
            hoverinfo='skip'
        ))

def create_empty_gantt() -> go.Figure:
    """Create an empty Gantt chart with placeholder message."""
    fig = go.Figure()
    
    fig.add_annotation(
        text="Generate a schedule to see the Gantt chart",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray"),
        bgcolor="white",
        bordercolor="lightgray",
        borderwidth=1
    )
    
    fig.update_layout(
        title="Schedule Timeline",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400
    )
    
    return fig

def create_gantt_with_annotations(schedule: Dict[str, date], config: Config) -> go.Figure:
    """Create Gantt chart with additional annotations."""
    fig = create_gantt_chart(schedule, config)
    
    # Add timeline annotations
    add_timeline_annotations(fig, schedule, config)
    
    return fig

def add_timeline_annotations(fig: go.Figure, schedule: Dict[str, date], config: Config) -> None:
    """Add timeline annotations to the Gantt chart."""
    if not schedule:
        return
    
    all_dates = list(schedule.values())
    min_date = min(all_dates)
    max_date = max(all_dates) + timedelta(days=90)
    
    # Add month markers
    current_date = min_date.replace(day=1)
    while current_date <= max_date:
        days_from_start = (current_date - min_date).days
        fig.add_annotation(
            x=days_from_start,
            y=1.02,
            yref='paper',
            text=current_date.strftime('%b %Y'),
            showarrow=False,
            font=dict(size=10),
            xanchor='left'
        )
        current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
