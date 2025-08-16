"""
Dashboard layout components for Paper Planner.
"""

from dash import html, dcc
from app.components.dashboard.chart import generate_timeline_chart


def create_dashboard_layout():
    """Create the dashboard layout with timeline chart."""
    return html.Div([
        # Header
        html.Div([
            html.H1("📚 Paper Planner - Dashboard", 
                    style={'textAlign': 'center', 'color': '#333', 'marginBottom': '20px'}),
            html.P("Real Paper Planner data with concurrency, dependencies, and scheduling logic",
                   style={'textAlign': 'center', 'color': '#666', 'marginBottom': '30px'})
        ]),
        
        # Info panels
        html.Div([
            html.Div([
                html.H3("🔧 What This Shows:", style={'color': '#2196f3'}),
                html.Ul([
                    html.Li("Real mods (engineering work items) from your data"),
                    html.Li("Real papers with actual dependencies"),
                    html.Li("Conference deadlines and abstract→paper workflows"),
                    html.Li("Concurrency constraints (max 2 concurrent per author)"),
                    html.Li("Resource allocation between Engineering and ED teams")
                ])
            ], style={'flex': 1, 'margin': '10px', 'padding': '15px', 'backgroundColor': '#e3f2fd', 
                      'borderRadius': '8px', 'borderLeft': '4px solid #2196f3'}),
            
            html.Div([
                html.H3("📊 Demo Data Sources:", style={'color': '#4caf50'}),
                html.Ul([
                    html.Li("Mods: app/assets/demo/data/mod_papers.json"),
                    html.Li("Papers: app/assets/demo/data/ed_papers.json"),
                    html.Li("Conferences: app/assets/demo/data/conferences.json"),
                    html.Li("Config: app/assets/demo/data/config.json")
                ])
            ], style={'flex': 1, 'margin': '10px', 'padding': '15px', 'backgroundColor': '#e8f5e8', 
                      'borderRadius': '8px', 'borderLeft': '4px solid #4caf50'})
        ], style={'display': 'flex', 'marginBottom': '30px'}),
        
        # Timeline Chart - Generate directly
        dcc.Graph(
            id='timeline-chart',
            figure=generate_timeline_chart(),
            style={'height': '70vh', 'width': '100%'},
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'paper_planner_timeline',
                    'height': 800,
                    'width': 1400,
                    'scale': 2
                }
            }
        )
    ], style={'height': '100vh', 'width': '100%', 'margin': 0, 'padding': '20px'})


def create_timeline_layout():
    """Create the timeline-only layout with minimal UI."""
    return html.Div([
        html.H1("📚 Paper Planner - Timeline", 
                style={'textAlign': 'center', 'color': '#333', 'marginBottom': '20px'}),
        dcc.Graph(
            id='timeline-chart',
            figure=generate_timeline_chart(),
            style={'height': '80vh', 'width': '100%'},
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'paper_planner_timeline',
                    'height': 800,
                    'width': 1400,
                    'scale': 2
                }
            }
        )
    ], style={'height': '100vh', 'width': '100%', 'margin': 0, 'padding': '20px'})
