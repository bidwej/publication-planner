"""
Metrics layout components for Paper Planner.
"""

from dash import html, dcc, Input, Output, callback, State, callback_context
from typing import Dict, Any, Optional
from datetime import datetime
from plotly.graph_objs import Figure
from app.components.metrics.chart import (
    create_metrics_chart,
    _create_error_chart
)
from app.components.exporter.controls import create_export_controls
from app.storage import get_state_manager
from core.models import Config

def create_metrics_layout(config: Optional[Config] = None) -> html.Div:
    """Create the metrics-only layout with minimal UI.
    
    Args:
        config: Configuration object containing submissions, conferences, etc.
    
    Returns:
        Metrics layout as html.Div
    """
    # Create initial chart with real data
    initial_figure = create_metrics_chart()
    
    # Store component state using clean state manager
    if config:
        get_state_manager().save_component_state('metrics', config, 'metrics')
    
    return html.Div([
        _create_metrics_header(),
        dcc.Graph(
            id='metrics-chart',
            figure=initial_figure,
            className="metrics-chart",
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'metrics_chart',
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                }
            }
        ),
        _create_metrics_controls(),
        create_export_controls('metrics-chart', 'metrics_chart'),
        html.Div(id="metrics-storage-status", className="storage-status"),
        # Store refresh timestamp for debugging
        html.Div(id="metrics-last-refresh", style={"display": "none"})
    ], className="metrics-layout")

def _create_metrics_header() -> html.Div:
    """Create metrics header."""
    return html.Div([
        html.H1("Paper Planner Metrics", className="metrics-title"),
        html.P("Performance and efficiency metrics for your paper submissions", className="metrics-subtitle")
    ], className="metrics-header")

def _create_metrics_controls() -> html.Div:
    """Create metrics controls."""
    return html.Div([
        html.Div([
            html.Button(
                'Refresh Chart',
                id='refresh-metrics-btn',
                className="control-button"
            )
        ], className="control-group")
    ], className="metrics-controls")

@callback(
    Output('metrics-chart', 'figure'),
    Input('refresh-metrics-btn', 'n_clicks'),
    prevent_initial_call=True
)
def update_metrics_chart(n_clicks: Optional[int]) -> Figure:
    """Update metrics chart.
    
    Args:
        n_clicks: Number of times refresh button was clicked
        
    Returns:
        Updated chart figure as Plotly Figure
    """
    try:
        # Update component state
        get_state_manager().update_component_refresh_time('metrics')
        
        # For now, always use sample data since we're not loading custom configs in callbacks
        # In a full implementation, you'd want to load the custom config here
        config = None
        
        # Create chart with sample data
        figure = create_metrics_chart()
        
        return figure
        
    except Exception as e:
        print(f"Error updating metrics chart: {e}")
        return _create_error_chart(f"Error updating chart: {str(e)}")

@callback(
    Output('metrics-storage-status', 'children'),
    Input('metrics-chart', 'figure'),
    prevent_initial_call=True
)
def update_metrics_storage_status(figure: Figure) -> str:
    """Update metrics storage status display."""
    try:
        stored_state = get_state_manager().load_component_state('metrics')
        if stored_state and 'config_data' in stored_state:
            config_summary = stored_state['config_data']
            return f"✅ Config loaded: {config_summary.get('submission_count', 0)} submissions, {config_summary.get('conference_count', 0)} conferences"
        else:
            return "⚠️ No config in storage - using sample data"
    except Exception as e:
        return f"❌ Storage error: {str(e)}"


# Export callback
@callback(
    Output('export-metrics-chart-status', 'children'),
    Input('export-metrics-chart-png-btn', 'n_clicks'),
    Input('export-metrics-chart-html-btn', 'n_clicks'),
    State('metrics-chart', 'figure'),
    prevent_initial_call=True
)
def handle_metrics_export(n_clicks_png: Optional[int], n_clicks_html: Optional[int], figure: Figure) -> str:
    """Handle metrics chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if 'png' in button_id:
            from app.components.exporter.controls import export_chart_png
            result = export_chart_png(figure, "metrics_chart.png")
            if result:
                return f"✅ PNG exported to: {result}"
            else:
                return "❌ PNG export failed"
        elif 'html' in button_id:
            from app.components.exporter.controls import export_chart_html
            result = export_chart_html(figure, "metrics_chart.html")
            if result:
                return f"✅ HTML exported to: {result}"
            else:
                return "❌ HTML export failed"
    except Exception as e:
        return f"❌ Export error: {e}"
    
    return ""






