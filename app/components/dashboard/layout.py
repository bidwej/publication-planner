"""
Dashboard layout components for Paper Planner.
"""

from dash import html, dcc, Input, Output, callback, State, callback_context
from typing import Dict, Any
from datetime import datetime
from app.components.dashboard.chart import (
    create_dashboard_chart,
    _create_error_chart
)
from app.components.export_controls.export_controls import create_export_controls, export_chart
from app.storage import save_state, load_state


def create_dashboard_layout() -> html.Div:
    """Create the dashboard layout with dynamic chart."""
    return html.Div([
        _create_header(),
        _create_info_panels(),
        _create_dashboard_graph(),
        create_export_controls('dashboard-chart', 'dashboard_chart'),
        _create_data_controls(),
        html.Div(id="dashboard-storage-status", className="storage-status")
    ], className="dashboard-container")


def _create_header() -> html.Div:
    """Create the dashboard header."""
    return html.Div([
        html.H1("📚 Paper Planner - Dashboard", className="dashboard-title"),
        html.P("Real Paper Planner data with concurrency, dependencies, and scheduling logic",
               className="dashboard-subtitle")
    ], className="dashboard-header")


def _create_info_panels() -> html.Div:
    """Create the info panels section."""
    return html.Div([
        _create_what_it_shows_panel(),
        _create_data_sources_panel()
    ], className="info-panels-container")


def _create_what_it_shows_panel() -> html.Div:
    """Create the 'What This Shows' info panel."""
    return html.Div([
        html.H3("🔧 What This Shows:", className="panel-title blue"),
        html.Ul([
            html.Li("Real mods (engineering work items) from your data"),
            html.Li("Real papers with actual dependencies"),
            html.Li("Conference deadlines and abstract→paper workflows"),
            html.Li("Concurrency constraints (max 2 concurrent per author)"),
            html.Li("Resource allocation between Engineering and ED teams")
        ])
    ], className="info-panel blue-panel")


def _create_data_sources_panel() -> html.Div:
    """Create the data sources info panel."""
    return html.Div([
        html.H3("📊 Demo Data Sources:", className="panel-title green"),
        html.Ul([
            html.Li("Mods: app/assets/demo/data/mod_papers.json"),
            html.Li("Papers: app/assets/demo/data/ed_papers.json"),
            html.Li("Conferences: app/assets/demo/data/conferences.json"),
            html.Li("Config: app/assets/demo/data/config.json")
        ])
    ], className="info-panel green-panel")


def _create_dashboard_graph() -> dcc.Graph:
    """Create the dashboard chart component."""
    return dcc.Graph(
        id='dashboard-chart',
        className="dashboard-chart",
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'paper_planner_dashboard',
                'height': 800,
                'width': 1400,
                'scale': 2
            }
        }
    )





def _create_data_controls() -> html.Div:
    """Create data control inputs."""
    return html.Div([
        html.Div([
            html.Label("Data Source:", className="control-label"),
            dcc.Dropdown(
                id='data-source-dropdown',
                options=[
                    {'label': 'Demo Data', 'value': 'demo'},
                    {'label': 'Custom Config', 'value': 'custom'}
                ],
                value='demo',
                className="control-dropdown"
            )
        ], className="control-group"),
        
        html.Div([
            html.Label("Chart Type:", className="control-label"),
            dcc.Dropdown(
                id='chart-type-dropdown',
                options=[
                    {'label': 'Schedule Timeline', 'value': 'timeline'},
                    {'label': 'Schedule Gantt', 'value': 'gantt'},
                    {'label': 'Team Utilization', 'value': 'resources'},
                    {'label': 'Project Dependencies', 'value': 'dependencies'}
                ],
                value='timeline',
                className="control-dropdown"
            )
        ], className="control-group"),
        
        html.Button("Refresh Chart", id="refresh-chart-btn", className="refresh-btn")
    ], className="data-controls")


# Dash Callbacks
@callback(
    Output('dashboard-chart', 'figure'),
    Input('refresh-chart-btn', 'n_clicks'),
    Input('data-source-dropdown', 'value'),
    Input('chart-type-dropdown', 'value'),
    prevent_initial_call=False
)
def update_dashboard_chart(n_clicks, data_source, chart_type):
    """Update dashboard chart based on user inputs."""
    try:
        return create_dashboard_chart(chart_type, data_source)
    except Exception as e:
        return _create_error_chart(f"Error: {e}")


@callback(
    Output('export-dashboard-chart-status', 'children'),
    Input('export-dashboard-chart-png-btn', 'n_clicks'),
    Input('export-dashboard-chart-html-btn', 'n_clicks'),
    State('dashboard-chart', 'figure'),
    prevent_initial_call=True
)
def handle_dashboard_export(n_clicks_png, n_clicks_html, figure):
    """Handle dashboard chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return export_chart(button_id, figure, 'dashboard_chart')


@callback(
    Output('data-source-dropdown', 'value'),
    Output('chart-type-dropdown', 'value'),
    Input('dashboard-chart', 'id'),
    prevent_initial_call=False
)
def load_dashboard_state(chart_id):
    """Load saved dashboard state from storage."""
    try:
        state = load_state('dashboard')
        return state.get('data_source', 'demo'), state.get('chart_type', 'timeline')
    except Exception as e:
        print(f"❌ Error loading dashboard state: {e}")
        return 'demo', 'timeline'


@callback(
    Output('dashboard-storage-status', 'children'),
    Input('data-source-dropdown', 'value'),
    Input('chart-type-dropdown', 'value'),
    prevent_initial_call=True
)
def save_dashboard_state(data_source, chart_type):
    """Save dashboard state to storage."""
    try:
        state = {
            'data_source': data_source,
            'chart_type': chart_type,
            'timestamp': datetime.now().isoformat()
        }
        save_state('dashboard', state)
        return f"✅ State saved: {data_source} / {chart_type}"
    except Exception as e:
        return f"❌ Error saving state: {e}"






