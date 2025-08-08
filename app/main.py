"""
Main Dash application for the Paper Planner web interface.
Supports both dashboard and timeline modes.
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context, exceptions
from typing import Any, Dict
import argparse
import sys

# Import core functionality
from src.core.config import load_config
from src.core.models import Config, SchedulerStrategy
from app.models import WebAppState
from src.planner import validate_schedule_comprehensive

from src.schedulers.base import BaseScheduler
# Import scheduler implementations to register them
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.stochastic import StochasticGreedyScheduler
from src.schedulers.lookahead import LookaheadGreedyScheduler
from src.schedulers.backtracking import BacktrackingGreedyScheduler
from src.schedulers.random import RandomScheduler
from src.schedulers.heuristic import HeuristicScheduler
from src.schedulers.optimal import OptimalScheduler


# Import app components
from app.layouts.header import create_header
from app.layouts.sidebar import create_sidebar
from app.layouts.main_content import create_main_content
from app.components.charts.gantt_chart import create_gantt_chart
from app.components.charts.metrics_chart import create_metrics_chart
from app.components.tables.schedule_table import create_schedule_table, create_violations_table

# Global state for the application
_current_schedule_data = None

def create_dashboard_app():
    """Create the full dashboard application."""
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
            
            # Validate the schedule
            validation_result = validate_schedule_comprehensive(schedule, config)
            
            # Create charts and tables
            gantt_fig = create_gantt_chart(schedule, config)
            metrics_fig = create_metrics_chart(schedule, config)
            schedule_table = create_schedule_table(schedule, config)
            violations_table = create_violations_table(validation_result)
            summary_metrics = _create_summary_metrics(validation_result)
            
            return gantt_fig, metrics_fig, schedule_table, violations_table, summary_metrics
            
        except Exception as e:
            print("Error generating schedule: %s", e)
            return _create_default_figures()
    
    def _load_saved_schedule() -> tuple:
        """Load a previously saved schedule."""
        # Implementation for loading saved schedules
        return _create_default_figures()
    
    def _create_default_figures() -> tuple:
        """Create default empty figures."""
        empty_gantt = create_gantt_chart({}, Config.create_default())
        empty_metrics = create_metrics_chart({}, Config.create_default())
        empty_table = html.Div("No schedule loaded")
        empty_violations = html.Div("No violations to display")
        empty_summary = html.Div("No metrics available")
        
        return empty_gantt, empty_metrics, empty_table, empty_violations, empty_summary
    
    def _create_summary_metrics(validation_result: Dict[str, Any]) -> html.Div:
        """Create summary metrics display."""
        return html.Div([
            html.H4("Schedule Summary"),
            html.P(f"Total Tasks: {len(validation_result.get('schedule', {}))}"),
            html.P(f"Violations: {len(validation_result.get('violations', []))}"),
            html.P(f"Score: {validation_result.get('score', 'N/A')}")
        ])
    
    return app


def get_current_schedule_data():
    """Get the current schedule data."""
    global _current_schedule_data
    return _current_schedule_data


def generate_schedule(config_data=None):
    """Generate a new schedule."""
    global _current_schedule_data
    try:
        config = load_config('config.json')
        scheduler = BaseScheduler.create_scheduler(SchedulerStrategy('greedy'), config)
        schedule = scheduler.schedule()
        _current_schedule_data = schedule
        return schedule
    except Exception as e:
        print("Error generating schedule: %s", e)
        return {}


def create_timeline_app():
    """Create the minimal timeline application."""
    app = dash.Dash(
        __name__,
        title="Paper Planner - Timeline",
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ]
    )
    
    def create_minimal_layout():
        """Create a truly minimal layout with just the timeline."""
        return html.Div([
            # Single generate button at top
            html.Div([
                html.Button([
                    html.I(className="fas fa-play"),
                    " Generate Timeline"
                ], id="generate-btn", className="btn btn-primary", style={'margin': '10px'})
            ], style={'textAlign': 'center'}),
            
            # Timeline Chart - full screen
            dcc.Graph(
                id='timeline-chart',
                style={'height': '90vh', 'width': '100%'},
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'schedule_timeline',
                        'height': 600,
                        'width': 1200,
                        'scale': 2
                    }
                }
            )
        ], style={'height': '100vh', 'width': '100%', 'margin': 0, 'padding': 0})
    
    # Set the layout
    app.layout = create_minimal_layout()
    
    # Simple callback
    @app.callback(
        Output('timeline-chart', 'figure'),
        Input('generate-btn', 'n_clicks')
    )
    def update_timeline(n_clicks):
        """Update timeline chart when generate button is clicked."""
        if not n_clicks or n_clicks == 0:
            # Return empty chart on initial load
            return create_gantt_chart({}, Config.create_default())
        
        try:
            config = load_config('config.json')
            scheduler = BaseScheduler.create_scheduler(SchedulerStrategy('greedy'), config)
            schedule = scheduler.schedule()
            
            # Create timeline chart
            timeline_fig = create_gantt_chart(schedule, config)
            return timeline_fig
            
        except Exception as e:
            print("Error generating schedule: %s", e)
            return create_gantt_chart({}, Config.create_default())
    
    return app

def main():
    """Main entry point that determines which app to run."""
    parser = argparse.ArgumentParser(description='Paper Planner Web Application')
    parser.add_argument('--mode', choices=['dashboard', 'timeline'], default='dashboard',
                       help='Application mode: dashboard (default) or timeline')
    parser.add_argument('--port', type=int, default=8050, help='Port to run the server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Create the appropriate app based on mode
    if args.mode == 'timeline':
        app = create_timeline_app()
        print("[START] Starting Paper Planner Timeline")
        print("[CHART] Timeline will be available at: http://127.0.0.1:8050")
    else:
        app = create_dashboard_app()
        print("[START] Starting Paper Planner Web Application")
        print("[CHART] Dashboard will be available at: http://127.0.0.1:8050")
    
    print("[REFRESH] Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run the app with improved timeout handling
    try:
        app.run(
            debug=args.debug,
            host=args.host,
            port=args.port,
            threaded=True,  # Enable threading for better performance
            use_reloader=False  # Disable reloader to avoid issues
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print("[ERROR] Port %d is already in use. Please stop the existing server or use a different port.", args.port)
            sys.exit(1)
        else:
            print("[ERROR] Server error: %s", e)
            sys.exit(1)
    except Exception as e:
        print("[ERROR] Unexpected error starting server: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
