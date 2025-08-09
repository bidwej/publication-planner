"""
Sidebar layout component for the Paper Planner web application.
"""

from dash import html, dcc
from src.core.models import SchedulerStrategy
from typing import Any

def create_sidebar() -> Any:
    """Create the application sidebar with controls."""
    return html.Aside([
        # Strategy Selection
        html.Div([
            html.H3("Scheduling Strategy", className="sidebar-section-title"),
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
                placeholder="Select strategy",
                className="strategy-dropdown"
            ),
            
            html.Button([
                html.I(className="fas fa-play"),
                " Generate Schedule"
            ], id="generate-schedule-btn", className="btn btn-primary btn-full")
        ], className="sidebar-section"),
        
        # Configuration
        html.Div([
            html.H3("Configuration", className="sidebar-section-title"),
            
            html.Div([
                html.Label("Max Concurrent Submissions:"),
                dcc.Slider(
                    id='max-concurrent-slider',
                    min=1, max=5, step=1, value=2,
                    marks={i: str(i) for i in range(1, 6)},
                    className="config-slider"
                )
            ], className="control-group"),
            
            html.Div([
                html.Label("Paper Lead Time (months):"),
                dcc.Slider(
                    id='paper-lead-time-slider',
                    min=1, max=6, step=1, value=3,
                    marks={i: str(i) for i in range(1, 7)},
                    className="config-slider"
                )
            ], className="control-group"),
            
            html.Div([
                html.Label("Abstract Lead Time (days):"),
                dcc.Slider(
                    id='abstract-lead-time-slider',
                    min=0, max=60, step=5, value=30,
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
                    id='enable-blackout-dates',
                    options=[{'label': 'Enable Blackout Dates', 'value': 'enabled'}],
                    value=['enabled'],
                    className="option-checklist"
                )
            ], className="control-group"),
            
            html.Div([
                dcc.Checklist(
                    id='enable-dependencies',
                    options=[{'label': 'Respect Dependencies', 'value': 'enabled'}],
                    value=['enabled'],
                    className="option-checklist"
                )
            ], className="control-group"),
            
            html.Div([
                dcc.Checklist(
                    id='enable-engineering-priority',
                    options=[{'label': 'Prioritize Engineering', 'value': 'enabled'}],
                    value=[],
                    className="option-checklist"
                )
            ], className="control-group")
        ], className="sidebar-section"),
        
        # Actions
        html.Div([
            html.H3("Actions", className="sidebar-section-title"),
            
            html.Button([
                html.I(className="fas fa-save"),
                " Save Schedule"
            ], id="save-schedule-btn", className="btn btn-secondary btn-full"),
            
            html.Button([
                html.I(className="fas fa-folder-open"),
                " Load Schedule"
            ], id="load-schedule-btn", className="btn btn-secondary btn-full"),
            
            html.Button([
                html.I(className="fas fa-download"),
                " Export CSV"
            ], id="export-schedule-btn", className="btn btn-secondary btn-full"),
            
            html.Button([
                html.I(className="fas fa-print"),
                " Print Report"
            ], id="print-report-btn", className="btn btn-secondary btn-full")
        ], className="sidebar-section")
    ], className="sidebar")
