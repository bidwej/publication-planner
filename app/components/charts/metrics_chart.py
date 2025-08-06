"""
Metrics chart component for performance visualization.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
from datetime import date

def create_metrics_chart(validation_result: Dict[str, Any]) -> go.Figure:
    """
    Create a metrics chart showing performance indicators.
    
    Parameters
    ----------
    validation_result : Dict[str, Any]
        Comprehensive validation and scoring results
        
    Returns
    -------
    go.Figure
        Metrics visualization chart
    """
    if not validation_result:
        return create_empty_metrics()
    
    # Extract metrics
    summary = validation_result.get("summary", {})
    constraints = validation_result.get("constraints", {})
    
    # Create radar chart for key metrics
    fig = go.Figure()
    
    # Define metrics
    metrics = [
        "Deadline Compliance",
        "Dependency Satisfaction", 
        "Resource Utilization",
        "Overall Quality",
        "Timeline Efficiency"
    ]
    
    # Calculate values (0-100 scale)
    values = [
        summary.get("deadline_compliance", 0),
        summary.get("dependency_satisfaction", 0),
        summary.get("resource_valid", 100) if summary.get("resource_valid", False) else 0,
        summary.get("overall_score", 0),
        summary.get("timeline_efficiency", 0)
    ]
    
    # Create radar chart
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=metrics,
        fill='toself',
        name='Current Schedule',
        line_color='#1f77b4',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    # Add target values (ideal performance)
    target_values = [100, 100, 80, 85, 90]  # Ideal targets
    fig.add_trace(go.Scatterpolar(
        r=target_values,
        theta=metrics,
        fill='toself',
        name='Target Performance',
        line_color='#2ca02c',
        fillcolor='rgba(44, 160, 44, 0.1)'
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title={
            'text': 'Performance Metrics',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        height=400
    )
    
    return fig

def create_metrics_dashboard(validation_result: Dict[str, Any]) -> go.Figure:
    """Create a comprehensive metrics dashboard."""
    if not validation_result:
        return create_empty_metrics()
    
    # Create subplots
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Performance Radar', 'Resource Utilization', 'Timeline Analysis', 'Quality Breakdown'),
        specs=[[{"type": "scatterpolar"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "pie"}]]
    )
    
    # 1. Performance Radar
    summary = validation_result.get("summary", {})
    metrics = ["Deadline Compliance", "Dependency Satisfaction", "Resource Utilization", "Overall Quality"]
    values = [
        summary.get("deadline_compliance", 0),
        summary.get("dependency_satisfaction", 0),
        80 if summary.get("resource_valid", False) else 0,
        summary.get("overall_score", 0)
    ]
    
    fig.add_trace(
        go.Scatterpolar(r=values, theta=metrics, fill='toself', name='Performance'),
        row=1, col=1
    )
    
    # 2. Resource Utilization
    resources = validation_result.get("resources", {})
    if resources:
        fig.add_trace(
            go.Bar(
                x=['Peak Load', 'Average Load', 'Utilization Rate'],
                y=[
                    resources.get("max_observed", 0),
                    resources.get("avg_utilization", 0),
                    resources.get("utilization_rate", 0)
                ],
                name='Resource Metrics'
            ),
            row=1, col=2
        )
    
    # 3. Timeline Analysis
    timeline = validation_result.get("timeline", {})
    if timeline:
        fig.add_trace(
            go.Scatter(
                x=['Duration', 'Efficiency', 'Completion Rate'],
                y=[
                    timeline.get("duration_days", 0),
                    timeline.get("timeline_efficiency", 0),
                    timeline.get("completion_rate", 0)
                ],
                mode='markers+lines',
                name='Timeline Metrics'
            ),
            row=2, col=1
        )
    
    # 4. Quality Breakdown
    quality_metrics = {
        'Deadline Compliance': summary.get("deadline_compliance", 0),
        'Dependency Satisfaction': summary.get("dependency_satisfaction", 0),
        'Resource Efficiency': 80 if summary.get("resource_valid", False) else 0,
        'Overall Quality': summary.get("overall_score", 0)
    }
    
    fig.add_trace(
        go.Pie(
            labels=list(quality_metrics.keys()),
            values=list(quality_metrics.values()),
            name='Quality Breakdown'
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title_text="Comprehensive Metrics Dashboard",
        height=600,
        showlegend=True
    )
    
    return fig

def create_violations_chart(validation_result: Dict[str, Any]) -> go.Figure:
    """Create a chart showing constraint violations."""
    if not validation_result:
        return create_empty_metrics()
    
    constraints = validation_result.get("constraints", {})
    
    # Count violations by type
    violation_counts = {
        'Deadline': len(constraints.get("deadlines", {}).get("violations", [])),
        'Dependency': len(constraints.get("dependencies", {}).get("violations", [])),
        'Resource': len(constraints.get("resources", {}).get("violations", [])),
        'Conference': len(constraints.get("conference_compatibility", {}).get("violations", [])),
        'Other': len(constraints.get("scheduling_options", {}).get("violations", []))
    }
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=list(violation_counts.keys()),
            y=list(violation_counts.values()),
            marker_color=['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4', '#9467bd']
        )
    ])
    
    fig.update_layout(
        title="Constraint Violations by Type",
        xaxis_title="Violation Type",
        yaxis_title="Number of Violations",
        height=400
    )
    
    return fig

def create_efficiency_chart(validation_result: Dict[str, Any]) -> go.Figure:
    """Create an efficiency analysis chart."""
    if not validation_result:
        return create_empty_metrics()
    
    efficiency = validation_result.get("efficiency_score", 0)
    quality = validation_result.get("quality_score", 0)
    penalty = validation_result.get("total_penalty", 0)
    
    # Create gauge charts
    fig = go.Figure()
    
    # Efficiency gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=efficiency,
        domain={'x': [0, 0.3], 'y': [0, 1]},
        title={'text': "Efficiency Score"},
        delta={'reference': 80},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    # Quality gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=quality,
        domain={'x': [0.35, 0.65], 'y': [0, 1]},
        title={'text': "Quality Score"},
        delta={'reference': 85},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 60], 'color': "lightgray"},
                {'range': [60, 85], 'color': "yellow"},
                {'range': [85, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    # Penalty gauge (inverted)
    penalty_score = max(0, 100 - penalty / 100)  # Convert penalty to score
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=penalty_score,
        domain={'x': [0.7, 1], 'y': [0, 1]},
        title={'text': "Penalty Score"},
        delta={'reference': 90},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, 70], 'color': "red"},
                {'range': [70, 90], 'color': "yellow"},
                {'range': [90, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    
    fig.update_layout(
        title="Performance Gauges",
        height=400
    )
    
    return fig

def create_empty_metrics() -> go.Figure:
    """Create an empty metrics chart."""
    fig = go.Figure()
    
    fig.add_annotation(
        text="Generate a schedule to see metrics",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray"),
        bgcolor="white",
        bordercolor="lightgray",
        borderwidth=1
    )
    
    fig.update_layout(
        title="Performance Metrics",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400
    )
    
    return fig
