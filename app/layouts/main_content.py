"""
Main content layout component for the Paper Planner web application.
"""

from dash import html, dcc, dash_table

def create_main_content():
    """Create the main content area with charts and tables."""
    return html.Main([
        # Dashboard Overview
        html.Div([
            html.H2("Schedule Dashboard", className="dashboard-title"),
            html.P("Generate and analyze academic paper schedules with interactive visualizations.", 
                   className="dashboard-description")
        ], className="dashboard-header"),
        
        # Summary Metrics
        html.Div([
            html.Div([
                html.H3("Summary Metrics", className="section-title"),
                html.Div(id="summary-metrics", className="metrics-container")
            ], className="metrics-section")
        ], className="dashboard-section"),
        
        # Charts Row
        html.Div([
            # Gantt Chart
            html.Div([
                html.H3("Schedule Timeline", className="section-title"),
                html.Div([
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
                ], className="chart-wrapper")
            ], className="chart-section"),
            
            # Metrics Chart
            html.Div([
                html.H3("Performance Metrics", className="section-title"),
                html.Div([
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
                ], className="chart-wrapper")
            ], className="chart-section")
        ], className="charts-row"),
        
        # Tables Row
        html.Div([
            # Schedule Table
            html.Div([
                html.H3("Schedule Details", className="section-title"),
                html.Div([
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
                            ], id="export-schedule-btn", className="btn btn-secondary btn-small")
                        ], className="table-actions")
                    ], className="table-header"),
                    html.Div([
                        dash_table.DataTable(
                            id='schedule-table',
                            columns=[
                                {'name': 'ID', 'id': 'id'},
                                {'name': 'Title', 'id': 'title'},
                                {'name': 'Type', 'id': 'type'},
                                {'name': 'Start Date', 'id': 'start_date'},
                                {'name': 'End Date', 'id': 'end_date'},
                                {'name': 'Conference', 'id': 'conference'},
                                {'name': 'Status', 'id': 'status'}
                            ],
                            data=[],
                            sort_action='native',
                            filter_action='native',
                            page_action='native',
                            page_current=0,
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px',
                                'fontSize': '14px'
                            },
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': 'bold',
                                'border': '1px solid #dee2e6'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': '#f8f9fa'
                                }
                            ]
                        )
                    ], className="table-container")
                ], className="table-section")
            ], className="table-column"),
            
            # Violations Table
            html.Div([
                html.H3("Constraint Violations", className="section-title"),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Label("Filter by severity:"),
                            dcc.Dropdown(
                                id='violations-filter',
                                options=[
                                    {'label': 'All Violations', 'value': 'all'},
                                    {'label': 'High Severity', 'value': 'high'},
                                    {'label': 'Medium Severity', 'value': 'medium'},
                                    {'label': 'Low Severity', 'value': 'low'}
                                ],
                                value='all',
                                className="table-filter"
                            )
                        ], className="table-controls"),
                        html.Div([
                            html.Button([
                                html.I(className="fas fa-exclamation-triangle"),
                                " View All"
                            ], id="view-violations-btn", className="btn btn-warning btn-small")
                        ], className="table-actions")
                    ], className="table-header"),
                    html.Div([
                        dash_table.DataTable(
                            id='violations-table',
                            columns=[
                                {'name': 'Submission', 'id': 'submission'},
                                {'name': 'Type', 'id': 'type'},
                                {'name': 'Description', 'id': 'description'},
                                {'name': 'Severity', 'id': 'severity'},
                                {'name': 'Impact', 'id': 'impact'}
                            ],
                            data=[],
                            sort_action='native',
                            filter_action='native',
                            page_action='native',
                            page_current=0,
                            page_size=5,
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px',
                                'fontSize': '14px'
                            },
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': 'bold',
                                'border': '1px solid #dee2e6'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{severity} = high'},
                                    'backgroundColor': '#f8d7da',
                                    'color': '#721c24'
                                },
                                {
                                    'if': {'filter_query': '{severity} = medium'},
                                    'backgroundColor': '#fff3cd',
                                    'color': '#856404'
                                },
                                {
                                    'if': {'filter_query': '{severity} = low'},
                                    'backgroundColor': '#d1ecf1',
                                    'color': '#0c5460'
                                }
                            ]
                        )
                    ], className="table-container")
                ], className="table-section")
            ], className="table-column")
        ], className="tables-row"),
        
        # Analytics Section
        html.Div([
            html.H3("Advanced Analytics", className="section-title"),
            html.Div([
                html.Div([
                    html.H4("Resource Utilization", className="analytics-subtitle"),
                    html.Div(id="resource-analytics", className="analytics-content")
                ], className="analytics-card"),
                html.Div([
                    html.H4("Timeline Analysis", className="analytics-subtitle"),
                    html.Div(id="timeline-analytics", className="analytics-content")
                ], className="analytics-card"),
                html.Div([
                    html.H4("Quality Metrics", className="analytics-subtitle"),
                    html.Div(id="quality-analytics", className="analytics-content")
                ], className="analytics-card")
            ], className="analytics-grid")
        ], className="analytics-section")
    ], className="app-main")
