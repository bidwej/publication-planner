"""
Gantt layout components for Paper Planner.
"""

from dash import html, dcc, Input, Output, callback, State, callback_context
from typing import Dict, Any
from datetime import datetime
from app.components.gantt.chart import (
    create_gantt_chart,
    _create_error_chart
)
from app.components.export_controls.export_controls import create_export_controls, export_chart
from app.storage import save_state, load_state


def create_gantt_layout() -> html.Div:
    """Create the gantt-only layout with minimal UI."""
    return html.Div([
        _create_gantt_header(),
        _create_gantt_graph(),
        create_export_controls('gantt-chart', 'gantt_chart'),
        html.Div(id="gantt-storage-status", className="storage-status")
    ], className="gantt-container")


def _create_gantt_header() -> html.H1:
    """Create the gantt chart header."""
    return html.H1("📚 Paper Planner - Gantt", className="gantt-header")


def _create_gantt_graph() -> dcc.Graph:
    """Create the gantt chart graph component."""
    return dcc.Graph(
        id='gantt-chart',
        className="gantt-chart",
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'paper_planner_gantt',
                'height': 800,
                'width': 1400,
                'scale': 2
            }
        }
    )





# Dash Callbacks
@callback(
    Output('gantt-chart', 'figure'),
    Input('gantt-chart', 'id'),
    prevent_initial_call=False
)
def update_gantt_chart(chart_id):
    """Update gantt chart."""
    try:
        return create_gantt_chart()
    except Exception as e:
        return _create_error_chart(str(e))


@callback(
    Output('export-gantt-chart-status', 'children'),
    Input('export-gantt-chart-png-btn', 'n_clicks'),
    Input('export-gantt-chart-html-btn', 'n_clicks'),
    State('gantt-chart', 'figure'),
    prevent_initial_call=True
)
def handle_gantt_export(n_clicks_png, n_clicks_html, figure):
    """Handle gantt chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return export_chart(button_id, figure, 'gantt_chart')


@callback(
    Output('gantt-storage-status', 'children'),
    Input('gantt-chart', 'figure'),
    prevent_initial_call=False
)
def save_gantt_state(figure):
    """Save gantt chart state to storage."""
    try:
        state = {
            'chart_data': figure,
            'timestamp': datetime.now().isoformat()
        }
        save_state('gantt', state)
        return "✅ Gantt state saved"
    except Exception as e:
        return f"❌ Error saving state: {e}"






