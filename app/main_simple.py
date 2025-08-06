"""
Minimal Dash application for the Paper Planner - Timeline Only.
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
from app.components.charts.gantt_chart import create_gantt_chart

# Initialize the Dash app
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
        print(f"Error generating schedule: {e}")
        return create_gantt_chart({}, Config.create_default())

if __name__ == '__main__':
    app.run_server(debug=False, host='127.0.0.1', port=8050)
