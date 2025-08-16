"""
Metrics layout components for Paper Planner.
"""

from dash import html, dcc
from app.components.metrics.chart import generate_metrics_chart


def create_metrics_layout():
    """Create the metrics layout with metrics chart."""
    return html.Div([
        # Header
        html.Div([
            html.H1("📊 Paper Planner - Metrics Dashboard", 
                    style={'textAlign': 'center', 'color': '#333', 'marginBottom': '20px'}),
            html.P("Performance metrics and analytics for your paper planning",
                   style={'textAlign': 'center', 'color': '#666', 'marginBottom': '30px'})
        ]),
        
        # Info panels
        html.Div([
            html.Div([
                html.H3("📈 What This Shows:", style={'color': '#2196f3'}),
                html.Ul([
                    html.Li("Schedule efficiency metrics"),
                    html.Li("Resource utilization"),
                    html.Li("Timeline optimization"),
                    html.Li("Performance analytics")
                ])
            ], style={'flex': 1, 'margin': '10px', 'padding': '15px', 'backgroundColor': '#e3f2fd', 
                      'borderRadius': '8px', 'borderLeft': '4px solid #2196f3'}),
            
            html.Div([
                html.H3("🔍 Data Sources:", style={'color': '#4caf50'}),
                html.Ul([
                    html.Li("Real Paper Planner data"),
                    html.Li("Scheduling algorithms"),
                    html.Li("Performance metrics")
                ])
            ], style={'flex': 1, 'margin': '10px', 'padding': '15px', 'backgroundColor': '#e8f5e8', 
                      'borderRadius': '8px', 'borderLeft': '4px solid #4caf50'})
        ], style={'display': 'flex', 'marginBottom': '30px'}),
        
        # Metrics Chart - Generate directly
        dcc.Graph(
            id='metrics-chart',
            figure=generate_metrics_chart(),
            style={'height': '70vh', 'width': '100%'},
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
    ], style={'height': '100vh', 'width': '100%', 'margin': 0, 'padding': '20px'})
