"""
Main Dash application for the Paper Planner web interface.
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context, exceptions
import plotly.graph_objects as go
from datetime import date, datetime
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import core functionality
import sys
sys.path.append('src')
from core.config import load_config
from core.models import Config, SchedulerStrategy, ScheduleState, WebAppState
from core.constraints import validate_schedule_comprehensive
from scoring.penalty import calculate_penalty_score
from scoring.quality import calculate_quality_score
from scoring.efficiency import calculate_efficiency_score
from schedulers.base import BaseScheduler
# Import all schedulers to ensure they're registered
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from schedulers.backtracking import BacktrackingGreedyScheduler
from schedulers.random import RandomScheduler
from schedulers.heuristic import HeuristicScheduler
from schedulers.optimal import OptimalScheduler

# Import app components
from app.layouts.header import create_header
from app.layouts.sidebar import create_sidebar
from app.layouts.main_content import create_main_content
from app.components.charts.gantt_chart import create_gantt_chart
from app.components.charts.metrics_chart import create_metrics_chart
from app.components.tables.schedule_table import create_schedule_table, create_violations_table

# Initialize the Dash app
app = dash.Dash(
    __name__,
    title="Paper Planner - Academic Schedule Optimizer",
    suppress_callback_exceptions=True,
    external_stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ]
)

# Initialize application state
app_state = WebAppState()

def create_app_layout():
    """Create the main application layout."""
    return html.Div([
        create_header(),
        
        html.Div([
            create_sidebar(),
            create_main_content()
        ], className="app-container"),
        
        # Store components for data persistence
        dcc.Store(id='schedule-store', storage_type='memory')
    ], className="app-wrapper")

# Set the layout
app.layout = create_app_layout()

# Callbacks
@app.callback(
    [Output('gantt-chart', 'figure'),
     Output('metrics-chart', 'figure'),
     Output('schedule-table-container', 'children'),
     Output('violations-table-container', 'children'),
     Output('summary-metrics', 'children')],
    [Input('generate-schedule-btn', 'n_clicks'),
     Input('load-schedule-btn', 'n_clicks')],
    [State('strategy-selector', 'value')]
)
def update_schedule(n_generate, n_load, strategy):
    """Update schedule display based on user actions."""
    ctx = callback_context
    
    # Only run callback if a button was actually clicked
    if not ctx.triggered:
        raise exceptions.PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Check if buttons were actually clicked (not just initialized)
    if trigger_id == 'generate-schedule-btn' and n_generate and n_generate > 0:
        return _generate_new_schedule(strategy)
    elif trigger_id == 'load-schedule-btn' and n_load and n_load > 0:
        return _load_saved_schedule()
    else:
        raise exceptions.PreventUpdate

def _generate_new_schedule(strategy: str) -> tuple:
    """Generate a new schedule using the selected strategy."""
    try:
        config = load_config('config.json')
        scheduler = BaseScheduler.create_scheduler(SchedulerStrategy(strategy), config)
        schedule = scheduler.schedule()
        
        # Validate schedule
        validation_result = validate_schedule_comprehensive(schedule, config)
        
        # Create figures
        gantt_fig = create_gantt_chart(schedule, config)
        metrics_fig = create_metrics_chart(validation_result, config)
        
        # Create tables
        schedule_table = create_schedule_table(schedule, config)
        violations_table = create_violations_table(validation_result)
        
        # Create summary metrics
        summary_metrics = _create_summary_metrics(validation_result)
        
        return gantt_fig, metrics_fig, schedule_table, violations_table, summary_metrics
        
    except Exception as e:
        print(f"Error generating schedule: {e}")
        return _create_default_figures()

def _load_saved_schedule() -> tuple:
    """Load a saved schedule."""
    # Placeholder for load functionality
    return _create_default_figures()

def _create_default_figures() -> tuple:
    """Create default empty figures."""
    empty_gantt = create_gantt_chart({}, Config.create_default())
    empty_metrics = create_metrics_chart({}, Config.create_default())
    empty_tables = []
    empty_summary = html.Div("No schedule available")
    
    return empty_gantt, empty_metrics, empty_tables, empty_tables, empty_summary

def _create_summary_metrics(validation_result: Dict[str, Any]) -> html.Div:
    """Create summary metrics display."""
    if not validation_result:
        return html.Div("No metrics available")
    
    scores = validation_result.get('scores', {})
    summary = validation_result.get('summary', {})
    
    return html.Div([
        html.Div([
            html.H4("Overall Score"),
            html.Span(f"{summary.get('overall_score', 0):.1f}", className="metric-value")
        ], className="metric-card"),
        html.Div([
            html.H4("Penalty Score"),
            html.Span(f"{scores.get('penalty_score', 0):.1f}", className="metric-value")
        ], className="metric-card"),
        html.Div([
            html.H4("Quality Score"),
            html.Span(f"{scores.get('quality_score', 0):.1f}", className="metric-value")
        ], className="metric-card"),
        html.Div([
            html.H4("Efficiency Score"),
            html.Span(f"{scores.get('efficiency_score', 0):.1f}", className="metric-value")
        ], className="metric-card")
    ], className="metrics-grid")

if __name__ == '__main__':
    app.run_server(debug=False, host='127.0.0.1', port=8050)
