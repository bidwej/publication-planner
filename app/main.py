"""
Main Dash application for the Paper Planner web interface.

This module provides the main entry point for the web application,
including the Dash app initialization, layout, and callbacks.
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
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

# Import app components
from layouts.header import create_header
from layouts.sidebar import create_sidebar
from layouts.main_content import create_main_content
from components.charts.gantt_chart import create_gantt_chart
from components.charts.metrics_chart import create_metrics_chart
from components.controls.strategy_selector import create_strategy_selector
from components.tables.schedule_table import create_schedule_table
from components.modals.save_load_modal import create_save_load_modal

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
        # Header
        create_header(),
        
        # Main container
        html.Div([
            # Sidebar
            create_sidebar(),
            
            # Main content area
            create_main_content()
        ], className="app-container"),
        
        # Save/Load Modal
        create_save_load_modal(),
        
        # Store components for data persistence
        dcc.Store(id='schedule-store', storage_type='memory'),
        dcc.Store(id='config-store', storage_type='memory'),
        dcc.Store(id='app-state-store', storage_type='memory'),
        
        # Interval for auto-refresh
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # 30 seconds
            n_intervals=0
        )
    ], className="app-wrapper")

# Set the layout
app.layout = create_app_layout()

# Callbacks
@app.callback(
    [Output('gantt-chart', 'figure'),
     Output('metrics-chart', 'figure'),
     Output('schedule-table', 'data'),
     Output('violations-table', 'data'),
     Output('summary-metrics', 'children')],
    [Input('generate-schedule-btn', 'n_clicks'),
     Input('load-schedule-btn', 'n_clicks'),
     Input('strategy-selector', 'value')],
    [State('schedule-store', 'data'),
     State('config-store', 'data')]
)
def update_schedule(n_generate, n_load, strategy, schedule_data, config_data):
    """Update the schedule display based on user actions."""
    ctx = callback_context
    if not ctx.triggered:
        return create_default_figures()
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'generate-schedule-btn':
        return generate_new_schedule(strategy)
    elif trigger_id == 'load-schedule-btn':
        return load_saved_schedule()
    else:
        return create_default_figures()

@app.callback(
    Output('save-load-modal', 'is_open'),
    [Input('save-schedule-btn', 'n_clicks'),
     Input('load-schedule-btn', 'n_clicks'),
     Input('close-modal-btn', 'n_clicks')],
    [State('save-load-modal', 'is_open')]
)
def toggle_modal(n_save, n_load, n_close, is_open):
    """Toggle the save/load modal."""
    if n_save or n_load or n_close:
        return not is_open
    return is_open

@app.callback(
    Output('saved-schedules-list', 'options'),
    [Input('refresh-schedules-btn', 'n_clicks')]
)
def update_saved_schedules_list(n_clicks):
    """Update the list of saved schedules."""
    schedules = app_state.list_saved_schedules()
    return [{'label': f"{s['filename']} ({s['strategy']})", 'value': s['filename']} 
            for s in schedules]

def generate_new_schedule(strategy: str) -> tuple:
    """Generate a new schedule using the specified strategy."""
    try:
        # Load configuration
        config = load_config("config.json")
        
        # Create scheduler
        scheduler = BaseScheduler.create_scheduler(SchedulerStrategy(strategy), config)
        
        # Generate schedule
        schedule = scheduler.schedule()
        
        # Validate and analyze
        validation_result = validate_schedule_comprehensive(schedule, config)
        
        # Create visualizations
        gantt_fig = create_gantt_chart(schedule, config)
        metrics_fig = create_metrics_chart(validation_result)
        schedule_table = create_schedule_table(schedule, config)
        violations_table = create_violations_table(validation_result)
        summary_metrics = create_summary_metrics(validation_result)
        
        return gantt_fig, metrics_fig, schedule_table, violations_table, summary_metrics
        
    except Exception as e:
        print(f"Error generating schedule: {e}")
        return create_default_figures()

def load_saved_schedule() -> tuple:
    """Load a saved schedule."""
    # Implementation for loading saved schedules
    return create_default_figures()

def create_default_figures() -> tuple:
    """Create default empty figures."""
    empty_gantt = go.Figure()
    empty_gantt.add_annotation(
        text="Generate a schedule to see the Gantt chart",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False
    )
    
    empty_metrics = go.Figure()
    empty_metrics.add_annotation(
        text="Generate a schedule to see metrics",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False
    )
    
    return empty_gantt, empty_metrics, [], [], "No schedule loaded"

def create_summary_metrics(validation_result: Dict[str, Any]) -> html.Div:
    """Create summary metrics display."""
    if not validation_result:
        return html.Div("No metrics available")
    
    summary = validation_result.get("summary", {})
    
    return html.Div([
        html.H4("Schedule Summary"),
        html.Div([
            html.Div([
                html.H5("Overall Score"),
                html.P(f"{summary.get('overall_score', 0):.1f}/100")
            ], className="metric-card"),
            html.Div([
                html.H5("Completion Rate"),
                html.P(f"{summary.get('completion_rate', 0):.1f}%")
            ], className="metric-card"),
            html.Div([
                html.H5("Duration"),
                html.P(f"{summary.get('duration_days', 0)} days")
            ], className="metric-card"),
            html.Div([
                html.H5("Peak Load"),
                html.P(f"{summary.get('peak_load', 0)} submissions")
            ], className="metric-card")
        ], className="metrics-grid")
    ])

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)
