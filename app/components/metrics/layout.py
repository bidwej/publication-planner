"""
Metrics layout components for Paper Planner.
"""

from dash import html, dcc, Input, Output, callback, State, callback_context
from typing import Dict, Any
from datetime import datetime
from app.components.metrics.chart import (
    create_metrics_chart,
    _create_error_chart
)
from app.components.export_controls.export_controls import create_export_controls, export_chart
from app.storage import save_state, load_state


def create_metrics_layout() -> html.Div:
    """Create the metrics layout with charts."""
    return html.Div([
        _create_metrics_header(),
        _create_metrics_graph(),
        create_export_controls('metrics-chart', 'metrics_chart'),
        html.Div(id="metrics-storage-status", className="storage-status")
    ], className="metrics-container")


def _create_metrics_header() -> html.Div:
    """Create the metrics header."""
    return html.Div([
        html.H1("📊 Paper Planner - Metrics", className="metrics-header"),
        html.P("Performance metrics and analytics for your paper planning",
               className="metrics-subtitle")
    ])


def _create_metrics_graph() -> dcc.Graph:
    """Create the metrics graph component."""
    return dcc.Graph(
        id='metrics-chart',
        className="metrics-chart",
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'paper_planner_metrics',
                'height': 800,
                'width': 1400,
                'scale': 2
            }
        }
    )





# Dash Callbacks
@callback(
    Output('metrics-chart', 'figure'),
    Input('metrics-chart', 'id'),
    prevent_initial_call=False
)
def update_metrics_chart(chart_id):
    """Update metrics chart."""
    try:
        return create_metrics_chart()
    except Exception as e:
        return _create_error_chart(str(e))


@callback(
    Output('export-metrics-chart-status', 'children'),
    Input('export-metrics-chart-png-btn', 'n_clicks'),
    Input('export-metrics-chart-html-btn', 'n_clicks'),
    State('metrics-chart', 'figure'),
    prevent_initial_call=True
)
def handle_metrics_export(n_clicks_png, n_clicks_html, figure):
    """Handle metrics chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return export_chart(button_id, figure, 'metrics_chart')


@callback(
    Output('metrics-storage-status', 'children'),
    Input('metrics-chart', 'figure'),
    prevent_initial_call=False
)
def save_metrics_state(figure):
    """Save metrics chart state to storage."""
    try:
        state = {
            'chart_data': figure,
            'timestamp': datetime.now().isoformat()
        }
        save_state('metrics', state)
        return "✅ Metrics state saved"
    except Exception as e:
        return f"❌ Error saving state: {e}"





def _create_error_chart(error_msg: str):
    """Create an error chart when something goes wrong."""
    import plotly.graph_objects as go
    
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
        title="Paper Planner Metrics - Error",
        xaxis_title="Metrics",
        yaxis_title="Score",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig
