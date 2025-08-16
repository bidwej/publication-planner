"""
Gantt layout components for Paper Planner.
"""

from dash import html, dcc, Input, Output, callback, State, callback_context
from typing import Dict, Any, Optional
from datetime import datetime
from plotly.graph_objs import Figure
from app.components.gantt.chart import (
    create_gantt_chart,
    _create_error_chart
)
from app.components.exporters.controls import create_export_controls
from app.storage import get_state_manager
from src.core.models import Config


def create_gantt_layout(config: Optional[Config] = None) -> html.Div:
    """Create the gantt-only layout with minimal UI.
    
    Args:
        config: Configuration object containing submissions, conferences, etc.
    
    Returns:
        Gantt layout as html.Div
    """
    # Create initial chart with real data
    initial_figure = create_gantt_chart()
    
    # Store component state using clean state manager
    if config:
        get_state_manager().save_component_state('gantt', config, 'gantt')
    
    return html.Div([
        _create_gantt_header(),
        dcc.Graph(
            id='gantt-chart',
            figure=initial_figure,
            className="gantt-chart",
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'gantt_chart',
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                }
            }
        ),
        _create_gantt_controls(),
        create_export_controls('gantt-chart', 'gantt_chart'),
        html.Div(id="export-gantt-chart-status", className="export-status"),
        html.Div(id="gantt-storage-status", className="storage-status"),
        # Store refresh timestamp for debugging
        html.Div(id="gantt-last-refresh", style={"display": "none"})
    ], className="gantt-layout")


def _create_gantt_header() -> html.Div:
    """Create gantt header."""
    return html.Div([
        html.H1("Paper Planner Gantt Chart", className="gantt-title"),
        html.P("Detailed timeline view of your paper submission schedule", className="gantt-subtitle")
    ], className="gantt-header")


def _create_gantt_controls() -> html.Div:
    """Create gantt controls."""
    return html.Div([
        html.Div([
            html.Button(
                'Refresh Chart',
                id='refresh-gantt-btn',
                className="control-button"
            )
        ], className="control-group")
    ], className="gantt-controls")


# Dash Callbacks
@callback(
    Output('gantt-chart', 'figure'),
    Input('refresh-gantt-btn', 'n_clicks'),
    prevent_initial_call=True
)
def update_gantt_chart(n_clicks: Optional[int]) -> Figure:
    """Update gantt chart.
    
    Args:
        n_clicks: Number of times refresh button was clicked
        
    Returns:
        Updated chart figure as Plotly Figure
    """
    try:
        # Update component state
        get_state_manager().update_component_refresh_time('gantt')
        
        # For now, always use sample data since we're not loading custom configs in callbacks
        # In a full implementation, you'd want to load the custom config here
        config = None
        
        # Create chart with sample data
        figure = create_gantt_chart()
        
        return figure
        
    except Exception as e:
        print(f"Error updating gantt chart: {e}")
        return _create_error_chart(f"Error updating chart: {str(e)}")


@callback(
    Output('gantt-storage-status', 'children'),
    Input('gantt-chart', 'figure'),
    prevent_initial_call=True
)
def update_gantt_storage_status(figure: Figure) -> str:
    """Update gantt storage status display."""
    try:
        stored_state = get_state_manager().load_component_state('gantt')
        if stored_state and 'config_data' in stored_state:
            config_summary = stored_state['config_data']
            return f"✅ Config loaded: {config_summary.get('submission_count', 0)} submissions, {config_summary.get('conference_count', 0)} conferences"
        else:
            return "⚠️ No config in storage - using sample data"
    except Exception as e:
        return f"❌ Storage error: {str(e)}"


# Export callback
@callback(
    Output('export-gantt-chart-status', 'children'),
    Input('export-gantt-chart-png-btn', 'n_clicks'),
    Input('export-gantt-chart-html-btn', 'n_clicks'),
    State('gantt-chart', 'figure'),
    prevent_initial_call=True
)
def handle_gantt_export(n_clicks_png: Optional[int], n_clicks_html: Optional[int], figure: Figure) -> str:
    """Handle gantt chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if 'png' in button_id:
            result = export_chart_png(figure, "gantt_chart.png")
            if result:
                return f"✅ PNG exported to: {result}"
            else:
                return "❌ PNG export failed"
        elif 'html' in button_id:
            result = export_chart_html(figure, "gantt_chart.html")
            if result:
                return f"✅ HTML exported to: {result}"
            else:
                return "❌ HTML export failed"
    except Exception as e:
        return f"❌ Export error: {e}"
    
    return ""
    






