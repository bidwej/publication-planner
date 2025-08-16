"""
Centralized export controls for Paper Planner charts.
Provides reusable export UI components and simple helper functions.
"""

from dash import html
from app.exporters import export_chart_png, export_chart_html


def create_export_controls(component_id: str, filename_prefix: str) -> html.Div:
    """Create export control buttons for any component.
    
    Args:
        component_id: The ID of the chart component (e.g., 'dashboard-chart')
        filename_prefix: Prefix for exported files (e.g., 'dashboard_chart')
    
    Returns:
        html.Div containing export buttons and status
    """
    return html.Div([
        html.Button("Export PNG", id=f"export-{component_id}-png-btn", className="chart-export-btn"),
        html.Button("Export HTML", id=f"export-{component_id}-html-btn", className="chart-export-btn"),
        html.Div(id=f"export-{component_id}-status", className="export-status")
    ], style={'textAlign': 'center', 'marginTop': '20px'})


def export_chart(button_id: str, figure, filename_prefix: str) -> str:
    """Simple export helper function.
    
    Args:
        button_id: The ID of the button that was clicked
        figure: The Plotly figure to export
        filename_prefix: Prefix for exported files
    
    Returns:
        Status message string
    """
    try:
        if 'png' in button_id:
            result = export_chart_png(figure, f"{filename_prefix}.png")
            if result:
                return f"✅ PNG exported to: {result}"
            else:
                return "❌ PNG export failed"
        elif 'html' in button_id:
            result = export_chart_html(figure, f"{filename_prefix}.html")
            if result:
                return f"✅ HTML exported to: {result}"
            else:
                return "❌ HTML export failed"
    except Exception as e:
        return f"❌ Export error: {e}"
    
    return ""
