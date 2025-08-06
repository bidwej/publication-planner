"""
Header layout component for the Paper Planner web application.
"""

from dash import html

def create_header():
    """Create the application header."""
    return html.Header([
        # Logo and title
        html.Div([
            html.I(className="fas fa-calendar-alt header-icon"),
            html.H1("Paper Planner", className="header-title"),
            html.Span("Academic Schedule Optimizer", className="header-subtitle")
        ], className="header-brand"),
        
        # Navigation menu
        html.Nav([
            html.A("Dashboard", href="#", className="nav-link active"),
            html.A("Analytics", href="#", className="nav-link"),
            html.A("Settings", href="#", className="nav-link"),
            html.A("Help", href="#", className="nav-link")
        ], className="header-nav"),
        
        # User actions
        html.Div([
            html.Button([
                html.I(className="fas fa-save"),
                " Save"
            ], id="save-schedule-btn", className="btn btn-primary"),
            html.Button([
                html.I(className="fas fa-download"),
                " Load"
            ], id="load-schedule-btn", className="btn btn-secondary"),
            html.Button([
                html.I(className="fas fa-cog")
            ], className="btn btn-icon", title="Settings")
        ], className="header-actions")
    ], className="app-header")
