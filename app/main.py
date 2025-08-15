"""
Main entry point for Paper Planner web applications.
Creates a gantt chart timeline view.
"""

import argparse
import sys
import dash
from dash import html, dcc, Input, Output, callback_context, exceptions
from datetime import datetime

from src.core.config import load_config
from src.core.models import Config, SchedulerStrategy, ScheduleState
from src.schedulers.base import BaseScheduler

from app.components.gantt.chart import create_gantt_chart
from app.models import WebAppState


def create_timeline_app():
    """Create a simple timeline app that's just a gantt chart."""
    app = dash.Dash(
        __name__,
        title="Paper Planner - Timeline",
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ]
    )
    
    app_state = WebAppState()
    app.layout = _create_timeline_layout()
    
    @app.callback(
        Output('timeline-chart', 'figure'),
        Input('generate-btn', 'n_clicks')
    )
    def update_timeline(n_clicks):
        """Update timeline chart when generate button is clicked."""
        if not n_clicks or n_clicks <= 0:
            raise exceptions.PreventUpdate
        
        try:
            config = load_config('config.json')
            scheduler = BaseScheduler.create_scheduler(SchedulerStrategy.GREEDY, config)
            schedule = scheduler.schedule()
            
            # Create proper ScheduleState
            schedule_state = ScheduleState(
                schedule=schedule,
                config=config,
                strategy=SchedulerStrategy.GREEDY,
                metadata={'source': 'web_app'},
                timestamp=datetime.now().isoformat()
            )
            
            # Store in app state
            app_state.current_schedule = schedule_state
            
            return create_gantt_chart(schedule_state)
            
        except Exception as e:
            print(f"Error generating schedule: {e}")
            # Create empty ScheduleState for error case
            empty_state = ScheduleState(
                schedule={},
                config=Config.create_default(),
                strategy=SchedulerStrategy.GREEDY,
                metadata={'error': str(e)},
                timestamp=datetime.now().isoformat()
            )
            return create_gantt_chart(empty_state)
    
    return app


def main():
    """Main entry point that creates the timeline app."""
    parser = argparse.ArgumentParser(description='Paper Planner Web Application')
    parser.add_argument('--port', type=int, default=8050, help='Port to run the server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Create the timeline app (gantt chart)
    app = create_timeline_app()
    print("[START] Starting Paper Planner Timeline")
    print("[CHART] Timeline will be available at: http://127.0.0.1:8050")
    print("[REFRESH] Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run the app
    try:
        app.run(
            debug=args.debug,
            host=args.host,
            port=args.port,
            threaded=True,
            use_reloader=False
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"[ERROR] Port {args.port} is already in use. Please stop the existing server or use a different port.")
            sys.exit(1)
        else:
            print(f"[ERROR] Server error: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error starting server: {e}")
        sys.exit(1)


def _create_timeline_layout():
    """Create a minimal timeline layout with just the chart."""
    return html.Div([
        # Simple generate button
        html.Div([
            html.Button([
                html.I(className="fas fa-play"),
                " Generate Timeline"
            ], id="generate-btn", className="btn btn-primary", style={'margin': '10px'})
        ], style={'textAlign': 'center'}),
        
        # Timeline Chart
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


if __name__ == "__main__":
    main()
