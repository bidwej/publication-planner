"""
Sidebar layout component for the Paper Planner web application.
"""

from dash import html, dcc
from core.models import SchedulerStrategy

def create_sidebar():
    """Create the application sidebar with controls."""
    return html.Aside([
        html.Div([
            # Strategy Selection
            html.Div([
                html.H3("Scheduling Strategy", className="sidebar-section-title"),
                html.Div([
                    dcc.Dropdown(
                        id='strategy-selector',
                        options=[
                            {'label': 'Greedy', 'value': SchedulerStrategy.GREEDY.value},
                            {'label': 'Backtracking', 'value': SchedulerStrategy.BACKTRACKING.value},
                            {'label': 'Heuristic', 'value': SchedulerStrategy.HEURISTIC.value},
                            {'label': 'Lookahead', 'value': SchedulerStrategy.LOOKAHEAD.value},
                            {'label': 'Random', 'value': SchedulerStrategy.RANDOM.value},
                            {'label': 'Stochastic', 'value': SchedulerStrategy.STOCHASTIC.value},
                            {'label': 'Optimal', 'value': SchedulerStrategy.OPTIMAL.value}
                        ],
                        value=SchedulerStrategy.GREEDY.value,
                        placeholder="Select strategy...",
                        className="strategy-dropdown"
                    )
                ], className="control-group"),
                
                # Generate Schedule Button
                html.Button([
                    html.I(className="fas fa-play"),
                    " Generate Schedule"
                ], id="generate-schedule-btn", className="btn btn-primary btn-full"),
                
                # Quick Actions
                html.Div([
                    html.H4("Quick Actions", className="sidebar-subtitle"),
                    html.Button([
                        html.I(className="fas fa-sync"),
                        " Refresh"
                    ], id="refresh-btn", className="btn btn-secondary btn-small"),
                    html.Button([
                        html.I(className="fas fa-download"),
                        " Export"
                    ], id="export-btn", className="btn btn-secondary btn-small"),
                    html.Button([
                        html.I(className="fas fa-print"),
                        " Print"
                    ], id="print-btn", className="btn btn-secondary btn-small")
                ], className="quick-actions")
            ], className="sidebar-section"),
            
            # Configuration
            html.Div([
                html.H3("Configuration", className="sidebar-section-title"),
                html.Div([
                    html.Label("Max Concurrent Submissions:"),
                    dcc.Slider(
                        id='max-concurrent-slider',
                        min=1,
                        max=5,
                        step=1,
                        value=2,
                        marks={i: str(i) for i in range(1, 6)},
                        className="config-slider"
                    )
                ], className="control-group"),
                
                html.Div([
                    html.Label("Paper Lead Time (months):"),
                    dcc.Slider(
                        id='paper-lead-time-slider',
                        min=1,
                        max=6,
                        step=1,
                        value=3,
                        marks={i: str(i) for i in range(1, 7)},
                        className="config-slider"
                    )
                ], className="control-group"),
                
                html.Div([
                    html.Label("Abstract Lead Time (days):"),
                    dcc.Slider(
                        id='abstract-lead-time-slider',
                        min=0,
                        max=60,
                        step=5,
                        value=30,
                        marks={0: '0', 15: '15', 30: '30', 45: '45', 60: '60'},
                        className="config-slider"
                    )
                ], className="control-group")
            ], className="sidebar-section"),
            
            # Options
            html.Div([
                html.H3("Options", className="sidebar-section-title"),
                html.Div([
                    dcc.Checklist(
                        id='options-checklist',
                        options=[
                            {'label': 'Enable Blackout Periods', 'value': 'blackout'},
                            {'label': 'Working Days Only', 'value': 'working_days'},
                            {'label': 'Early Abstract Scheduling', 'value': 'early_abstract'},
                            {'label': 'Priority Weighting', 'value': 'priority'},
                            {'label': 'Dependency Tracking', 'value': 'dependency'},
                            {'label': 'Concurrency Control', 'value': 'concurrency'}
                        ],
                        value=['priority', 'dependency', 'concurrency'],
                        className="options-checklist"
                    )
                ], className="control-group")
            ], className="sidebar-section"),
            
            # Status
            html.Div([
                html.H3("Status", className="sidebar-section-title"),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-circle status-icon ready"),
                        html.Span("Ready", className="status-text")
                    ], className="status-item"),
                    html.Div([
                        html.I(className="fas fa-circle status-icon idle"),
                        html.Span("Idle", className="status-text")
                    ], className="status-item"),
                    html.Div([
                        html.I(className="fas fa-circle status-icon success"),
                        html.Span("Success", className="status-text")
                    ], className="status-item")
                ], className="status-list")
            ], className="sidebar-section")
        ], className="sidebar-content")
    ], className="app-sidebar")
