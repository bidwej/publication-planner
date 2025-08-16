"""
Dashboard layout components for Paper Planner.
"""

from dash import html, dcc, callback, callback_context, ALL, MATCH
from dash.dependencies import Input, Output, State
from typing import Dict, Optional
from datetime import datetime
from plotly.graph_objs import Figure
from app.components.dashboard.chart import (
    create_dashboard_chart,
    _create_error_chart
)
from app.components.exporters.controls import create_export_controls, export_chart_png, export_chart_html
from app.storage import get_state_manager
from core.models import Config


def create_dashboard_layout(config: Optional[Config] = None) -> html.Div:
    """Create the dashboard layout with dynamic chart.
    
    Args:
        config: Configuration object containing submissions, conferences, etc.
    
    Returns:
        Dashboard layout as html.Div
    """
    # Create initial chart with real data
    initial_figure = create_dashboard_chart('timeline', config)
    
    # Store component state using clean state manager
    if config:
        get_state_manager().save_component_state('dashboard', config, 'timeline')
    
    return html.Div([
        _create_header(),
        _create_info_panels(),
        dcc.Graph(
            id='dashboard-chart',
            figure=initial_figure,
            className="dashboard-chart",
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'dashboard_chart',
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                }
            }
        ),
        _create_controls(),
        create_export_controls('dashboard-chart', 'dashboard_chart'),
        html.Div(id="export-dashboard-chart-status", className="export-status"),
        html.Div(id="dashboard-storage-status", className="storage-status"),
        # Store refresh timestamp for debugging
        html.Div(id="dashboard-last-refresh", style={"display": "none"})
    ], className="dashboard-layout")


def _create_header() -> html.Div:
    """Create dashboard header."""
    return html.Div([
        html.H1("Paper Planner Dashboard", className="dashboard-title"),
        html.P("Interactive visualization of your paper submission schedule", className="dashboard-subtitle")
    ], className="dashboard-header")


def _create_info_panels() -> html.Div:
    """Create information panels."""
    return html.Div([
        html.Div([
            html.H3("📊 Overview", className="panel-title"),
            html.P("Track your paper submissions, deadlines, and progress", className="panel-description")
        ], className="info-panel"),
        html.Div([
            html.H3("🔄 Updates", className="panel-title"),
            html.P("Real-time data from your configuration", className="panel-description")
        ], className="info-panel")
    ], className="info-panels")


def _create_controls() -> html.Div:
    """Create dashboard controls."""
    return html.Div([
        html.Div([
            html.Label("Chart Type:", className="control-label"),
            dcc.Dropdown(
                id='chart-type-dropdown',
                options=[
                    {'label': 'Timeline View', 'value': 'timeline'},
                    {'label': 'Gantt Chart', 'value': 'gantt'},
                    {'label': 'Resource Usage', 'value': 'resources'},
                    {'label': 'Dependencies', 'value': 'dependencies'}
                ],
                value='timeline',
                className="control-dropdown"
            )
        ], className="control-group"),
        html.Div([
            html.Button(
                'Refresh Chart',
                id='refresh-chart-btn',
                className="control-button"
            )
        ], className="control-group")
    ], className="dashboard-controls")


# Dash Callbacks
# IMPORTANT: prevent_initial_call=True prevents infinite loops
# The initial chart is created in create_dashboard_layout() with real data
# Callbacks only run on user interaction (refresh button, chart type change)
@callback(
    Output('dashboard-chart', 'figure'),
    Input('refresh-chart-btn', 'n_clicks'),
    Input('chart-type-dropdown', 'value'),
    prevent_initial_call=True
)
def update_dashboard_chart(n_clicks: Optional[int], chart_type: str) -> Figure:
    """Update dashboard chart based on user inputs.
    
    Args:
        n_clicks: Number of times refresh button was clicked
        chart_type: Selected chart type
        
    Returns:
        Updated chart figure as Plotly Figure
    """
    try:
        # Update component state
        get_state_manager().update_component_refresh_time('dashboard')
        
        # Load stored config from state manager
        stored_state = get_state_manager().load_component_state('dashboard')
        config = None
        
        if stored_state and 'config_data' in stored_state:
            # Reconstruct config from stored state
            config_data = stored_state['config_data']
            config = Config(
                submissions=[],  # We'll need to store actual submission data
                conferences=[],
                min_abstract_lead_time_days=config_data.get('min_abstract_lead_time_days', 30),
                min_paper_lead_time_days=config_data.get('min_paper_lead_time_days', 60),
                max_concurrent_submissions=config_data.get('max_concurrent_submissions', 2)
            )
        
        # Create chart with stored config or fallback to sample data
        figure = create_dashboard_chart(chart_type, config)
        
        return figure
        
    except Exception as e:
        print(f"Error updating dashboard chart: {e}")
        return _create_error_chart(f"Error updating chart: {str(e)}")


@callback(
    Output('dashboard-storage-status', 'children'),
    Input('dashboard-chart', 'figure'),
    prevent_initial_call=True
)
def update_storage_status(figure: Figure) -> str:
    """Update storage status display."""
    try:
        stored_state = get_state_manager().load_component_state('dashboard')
        if stored_state and 'config_data' in stored_state:
            config_summary = stored_state['config_data']
            return f"✅ Config loaded: {config_summary.get('submission_count', 0)} submissions, {config_summary.get('conference_count', 0)} conferences"
        else:
            return "⚠️ No config in storage - using sample data"
    except Exception as e:
        return f"❌ Storage error: {str(e)}"


# Export callback
@callback(
    Output('export-dashboard-chart-status', 'children'),
    Input('export-dashboard-chart-png-btn', 'n_clicks'),
    Input('export-dashboard-chart-html-btn', 'n_clicks'),
    State('dashboard-chart', 'figure'),
    prevent_initial_call=True
)
def handle_dashboard_export(n_clicks_png: Optional[int], n_clicks_html: Optional[int], figure: Figure) -> str:
    """Handle dashboard chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if 'png' in button_id:
            result = export_chart_png(figure, "dashboard_chart.png")
            if result:
                return f"✅ PNG exported to: {result}"
            else:
                return "❌ PNG export failed"
        elif 'html' in button_id:
            result = export_chart_html(figure, "dashboard_chart.html")
            if result:
                return f"✅ HTML exported to: {result}"
            else:
                return "❌ HTML export failed"
    except Exception as e:
        return f"❌ Export error: {e}"
    
    return ""