"""
Layout configuration for Gantt charts.
Handles chart dimensions, styling, and axis configuration.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from typing import Dict, Any




def get_title_text(chart_dimensions: Dict[str, Any]) -> str:
    """Generate title text for the chart."""
    min_date = chart_dimensions['min_date']
    max_date = chart_dimensions['max_date']
    
    if min_date.year == max_date.year:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
    else:
        return f"Paper Submission Timeline: {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"


def configure_gantt_layout(fig: Figure, chart_dimensions: Dict[str, Any]) -> None:
    """Configure the chart layout with proper styling and dimensions."""
    title_text = get_title_text(chart_dimensions)
    max_concurrency = chart_dimensions['max_concurrency']
    
    fig.update_layout(
        title={
            'text': title_text,
            'x': 0.5, 'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        height=400 + max_concurrency * 30,
        margin=dict(l=80, r=80, t=100, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis={
            'type': 'date',
            'range': [chart_dimensions['min_date'], chart_dimensions['max_date']],
            'title': 'Timeline',
            'showgrid': True, 'gridcolor': '#ecf0f1'
        },
        yaxis={
            'title': 'Activities',
            'range': [-0.5, max_concurrency + 0.5],
            'tickmode': 'linear', 'dtick': 1,
            'showgrid': True, 'gridcolor': '#ecf0f1'
        },
        showlegend=False
    )



