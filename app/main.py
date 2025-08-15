"""
Main entry point for Paper Planner web applications.
Creates a real timeline view using actual project data and components.
"""

import argparse
import sys
import os
import dash
from dash import html, dcc, Input, Output, callback_context, exceptions
from datetime import datetime, date, timedelta
import plotly.graph_objects as go

# Import real Paper Planner components

def create_real_paper_planner_app():
    """Create the real Paper Planner timeline app using actual data and components."""
    app = dash.Dash(
        __name__,
        title="Paper Planner - Real Timeline",
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ]
    )
    
    app.layout = _create_real_timeline_layout()
    
    @app.callback(
        Output('timeline-chart', 'figure'),
        Input('generate-real-btn', 'n_clicks'),
        Input('scheduler-selector', 'value')
    )
    def update_real_timeline(n_clicks, scheduler_type):
        """Update timeline chart with real Paper Planner data."""
        if not n_clicks or n_clicks <= 0:
            raise exceptions.PreventUpdate
        
        try:
            print(f"Generating real Paper Planner chart with {scheduler_type} scheduler...")
            
            # Import real Paper Planner components
            from src.core.config import load_config
            from src.schedulers.greedy import GreedyScheduler
            from src.schedulers.heuristic import HeuristicScheduler
            from src.schedulers.optimal import OptimalScheduler
            from app.components.gantt.chart import create_gantt_chart
            
            # Load demo configuration
            config = load_config('app/assets/demo/data/config.json')
            print("✅ Configuration loaded")
            
            # Create scheduler based on selection
            if scheduler_type == 'greedy':
                scheduler = GreedyScheduler(config)
            elif scheduler_type == 'heuristic':
                scheduler = HeuristicScheduler(config)
            elif scheduler_type == 'optimal':
                scheduler = OptimalScheduler(config)
            else:
                scheduler = GreedyScheduler(config)
            
            # Generate real schedule
            schedule = scheduler.schedule()
            
            if schedule:
                print(f"✅ Schedule generated with {len(schedule)} items")
                
                # Create ScheduleState for the chart
                from src.core.models import ScheduleState, SchedulerStrategy
                schedule_state = ScheduleState(
                    schedule=schedule,
                    config=config,
                    strategy=SchedulerStrategy(scheduler_type.upper()),
                    timestamp=datetime.now().isoformat()
                )
                
                # Generate real gantt chart
                fig = create_gantt_chart(schedule_state)
                return fig
            else:
                print("⚠️ No schedule generated")
                return _create_error_chart("No schedule could be generated")
                
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return _create_error_chart(f"Import error: {e}")
        except Exception as e:
            print(f"❌ Error generating chart: {e}")
            return _create_error_chart(f"Error: {e}")
    
    @app.callback(
        Output('status-display', 'children'),
        Input('generate-real-btn', 'n_clicks')
    )
    def update_status(n_clicks):
        """Update status display."""
        if not n_clicks or n_clicks <= 0:
            return "Ready to generate Paper Planner timeline"
        return f"Generating timeline... (click #{n_clicks})"
    
    return app


def _create_real_timeline_layout():
    """Create the real Paper Planner timeline layout."""
    return html.Div([
        # Header
        html.Div([
            html.H1("📚 Paper Planner - Real Timeline", 
                    style={'textAlign': 'center', 'color': '#333', 'marginBottom': '20px'}),
            html.P("Real Paper Planner data with concurrency, dependencies, and scheduling logic",
                   style={'textAlign': 'center', 'color': '#666', 'marginBottom': '30px'})
        ]),
        
        # Controls
        html.Div([
            html.Div([
                html.Label("Scheduler Type:", style={'marginRight': '10px', 'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='scheduler-selector',
                    options=[
                        {'label': 'Greedy Scheduler', 'value': 'greedy'},
                        {'label': 'Heuristic Scheduler', 'value': 'heuristic'},
                        {'label': 'Optimal Scheduler', 'value': 'optimal'}
                    ],
                    value='greedy',
                    style={'width': '200px', 'display': 'inline-block'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
            
            html.Button([
                html.I(className="fas fa-play"),
                " Generate Real Paper Planner Timeline"
            ], id="generate-real-btn", className="btn btn-primary", 
               style={'margin': '10px', 'padding': '15px 25px', 'fontSize': '16px'}),
            
            html.Div(id='status-display', 
                     style={'margin': '10px', 'padding': '10px', 'backgroundColor': '#f0f0f0', 
                            'borderRadius': '5px', 'textAlign': 'center'})
        ], style={'textAlign': 'center', 'marginBottom': '30px'}),
        
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
        
        # Timeline Chart
        dcc.Graph(
            id='timeline-chart',
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


def _create_error_chart(error_msg: str) -> go.Figure:
    """Create an error chart when something goes wrong."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"Error: {error_msg}<br>Check console for details",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="red")
    )
    fig.update_layout(
        title="Paper Planner Timeline - Error",
        xaxis_title="Date",
        yaxis_title="Items",
        height=400
    )
    return fig


def main():
    """Main entry point that creates the real Paper Planner timeline app."""
    parser = argparse.ArgumentParser(description='Paper Planner Web Application')
    parser.add_argument('--port', type=int, default=8050, help='Port to run the server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Create the real Paper Planner timeline app
    app = create_real_paper_planner_app()
    print("[START] Starting Paper Planner - Real Timeline")
    print(f"[CHART] Timeline will be available at: http://{args.host}:{args.port}")
    print("[DATA] Using real Paper Planner data and components")
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


if __name__ == "__main__":
    main()
