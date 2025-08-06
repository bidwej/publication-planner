"""
Performance metrics chart component.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
from core.models import Config

def create_metrics_chart(validation_result: Dict[str, Any], config: Config) -> go.Figure:
    """Create performance metrics chart."""
    if not validation_result:
        return _create_empty_metrics()
    
    scores = validation_result.get('scores', {})
    if not scores:
        return _create_empty_metrics()
    
    # Extract scores
    penalty_score = scores.get('penalty_score', 0)
    quality_score = scores.get('quality_score', 0)
    efficiency_score = scores.get('efficiency_score', 0)
    
    # Create radar chart
    categories = ['Penalty', 'Quality', 'Efficiency']
    values = [penalty_score, quality_score, efficiency_score]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Performance',
        line_color='#2E86AB'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title={'text': 'Performance Metrics', 'x': 0.5, 'xanchor': 'center'},
        height=400
    )
    
    return fig

def create_score_comparison_chart(scores_data: List[Dict[str, Any]]) -> go.Figure:
    """Create comparison chart for multiple strategies."""
    if not scores_data:
        return _create_empty_metrics()
    
    strategies = [item['strategy'] for item in scores_data]
    penalty_scores = [item.get('penalty_score', 0) for item in scores_data]
    quality_scores = [item.get('quality_score', 0) for item in scores_data]
    efficiency_scores = [item.get('efficiency_score', 0) for item in scores_data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Penalty',
        x=strategies,
        y=penalty_scores,
        marker_color='#A23B72'
    ))
    
    fig.add_trace(go.Bar(
        name='Quality',
        x=strategies,
        y=quality_scores,
        marker_color='#F18F01'
    ))
    
    fig.add_trace(go.Bar(
        name='Efficiency',
        x=strategies,
        y=efficiency_scores,
        marker_color='#C73E1D'
    ))
    
    fig.update_layout(
        title={'text': 'Strategy Comparison', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Strategy',
        yaxis_title='Score',
        barmode='group',
        height=400
    )
    
    return fig

def create_timeline_metrics_chart(schedule: Dict[str, Any], config: Config) -> go.Figure:
    """Create timeline-based metrics visualization."""
    if not schedule:
        return _create_empty_metrics()
    
    # Calculate timeline metrics
    timeline_data = _calculate_timeline_metrics(schedule, config)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timeline_data['dates'],
        y=timeline_data['workload'],
        mode='lines+markers',
        name='Workload',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title={'text': 'Timeline Workload', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Date',
        yaxis_title='Active Submissions',
        height=400,
        showlegend=False
    )
    
    return fig

def _calculate_timeline_metrics(schedule: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Calculate timeline-based metrics."""
    from datetime import date, timedelta
    
    if not schedule:
        return {'dates': [], 'workload': []}
    
    # Get date range
    all_dates = list(schedule.values())
    if not all_dates:
        return {'dates': [], 'workload': []}
    
    start_date = min(all_dates)
    end_date = max(all_dates) + timedelta(days=90)
    
    # Calculate daily workload
    dates = []
    workload = []
    current_date = start_date
    
    while current_date <= end_date:
        active_count = sum(1 for start_date in schedule.values() 
                          if start_date <= current_date <= start_date + timedelta(days=30))
        
        dates.append(current_date)
        workload.append(active_count)
        current_date += timedelta(days=7)  # Weekly intervals
    
    return {'dates': dates, 'workload': workload}

def _create_empty_metrics() -> go.Figure:
    """Create empty metrics chart."""
    fig = go.Figure()
    fig.update_layout(
        title={'text': 'No Metrics Available', 'x': 0.5, 'xanchor': 'center'},
        height=400,
        annotations=[{
            'text': 'Generate a schedule to see metrics',
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': 0.5,
            'showarrow': False,
            'font': {'size': 16, 'color': 'gray'}
        }]
    )
    return fig
