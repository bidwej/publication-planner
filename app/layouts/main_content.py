"""
Main content layout component for the Paper Planner web application.
"""

from dash import html, dcc
from typing import Any

def create_main_content() -> Any:
    """Create the main content area with charts and tables."""
    return html.Main([
        # Dashboard Header
        html.Div([
            html.H2("Schedule Dashboard", className="dashboard-title"),
            html.P("Generate and analyze academic paper schedules with interactive visualizations.", 
                   className="dashboard-description")
        ], className="dashboard-header"),
        
        # Summary Metrics
        html.Div([
            html.H3("Summary Metrics", className="section-title"),
            html.Div(id="summary-metrics", className="metrics-container")
        ], className="metrics-section"),
        
        # Charts Row
        html.Div([
            # Gantt Chart
            html.Div([
                html.H3("Schedule Timeline", className="section-title"),
                dcc.Graph(
                    id='gantt-chart',
                    className="chart-container",
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': 'schedule_gantt',
                            'height': 600,
                            'width': 1200,
                            'scale': 2
                        }
                    }
                )
            ], className="chart-section"),
            
            # Metrics Chart
            html.Div([
                html.H3("Performance Metrics", className="section-title"),
                dcc.Graph(
                    id='metrics-chart',
                    className="chart-container",
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': 'performance_metrics',
                            'height': 400,
                            'width': 600,
                            'scale': 2
                        }
                    }
                )
            ], className="chart-section")
        ], className="charts-row"),
        
        # Tables Row
        html.Div([
            # Schedule Table
            html.Div([
                html.H3("Schedule Details", className="section-title"),
                html.Div([
                    html.Div([
                        html.Label("Filter by:"),
                        dcc.Dropdown(
                            id='schedule-filter',
                            options=[
                                {'label': 'All Submissions', 'value': 'all'},
                                {'label': 'Papers Only', 'value': 'papers'},
                                {'label': 'Abstracts Only', 'value': 'abstracts'},
                                {'label': 'Mods Only', 'value': 'mods'}
                            ],
                            value='all',
                            className="table-filter"
                        )
                    ], className="table-controls"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-download"),
                            " Export CSV"
                        ], id="table-export-btn", className="btn btn-secondary btn-small")
                    ], className="table-actions")
                ], className="table-header"),
                
                dcc.Loading(
                    id="loading-schedule-table",
                    type="default",
                    children=[
                        dcc.Store(id='schedule-table-data'),
                        html.Div(id='schedule-table-container')
                    ]
                )
            ], className="table-section"),
            
            # Violations Table
            html.Div([
                html.H3("Constraint Violations", className="section-title"),
                dcc.Loading(
                    id="loading-violations-table",
                    type="default",
                    children=[
                        dcc.Store(id='violations-table-data'),
                        html.Div(id='violations-table-container')
                    ]
                )
            ], className="table-section")
        ], className="tables-row"),
        
        # Analytics Section
        html.Div([
            html.H3("Schedule Analytics", className="section-title"),
            html.Div([
                html.Div([
                    html.H4("Timeline Analysis", className="subsection-title"),
                    html.Div(id="timeline-analytics", className="analytics-content")
                ], className="analytics-card"),
                
                html.Div([
                    html.H4("Resource Utilization", className="subsection-title"),
                    html.Div(id="resource-analytics", className="analytics-content")
                ], className="analytics-card"),
                
                html.Div([
                    html.H4("Quality Metrics", className="subsection-title"),
                    html.Div(id="quality-analytics", className="analytics-content")
                ], className="analytics-card")
            ], className="analytics-grid")
        ], className="analytics-section")
    ], className="main-content")
