from dash import html, dcc
from core.models import SchedulerStrategy

def create_strategy_selector():
    """Create a strategy selector dropdown component."""
    return html.Div([
        html.Label("Scheduling Strategy:", className="control-label"),
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
    ], className="control-group")
