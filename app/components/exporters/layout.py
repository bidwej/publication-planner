"""
Export layout and callbacks for Paper Planner charts.
Handles export button interactions and status updates.
"""

from dash import Input, Output, callback, State, callback_context
from typing import Optional
from plotly.graph_objs import Figure
from .controls import export_chart_png, export_chart_html


# Dashboard export callback
@callback(
    Output('export-dashboard-chart-status', 'children'),
    Input('export-dashboard-chart-png-btn', 'n_clicks'),
    Input('export-dashboard-chart-html-btn', 'n_clicks'),
    State('dashboard-chart', 'figure'),
    prevent_initial_call=True
)
def dashboard_export_callback(n_clicks_png: Optional[int], n_clicks_html: Optional[int], figure: Figure) -> str:
    """Handle dashboard chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if 'png' in button_id:
            result = export_chart_png(figure, "dashboard_chart.png")
            if result:
                return f"✅ PNG exported to: {result}"
            else:
                return "❌ PNG export failed"
        elif 'html' in button_id:
            result = export_chart_html(figure, "dashboard_chart.html")
            if result:
                return f"✅ HTML exported to: {result}"
            else:
                return "❌ HTML export failed"
    except Exception as e:
        return f"❌ Export error: {e}"
    
    return ""


# Gantt export callback
@callback(
    Output('export-gantt-chart-status', 'children'),
    Input('export-gantt-chart-png-btn', 'n_clicks'),
    Input('export-gantt-chart-html-btn', 'n_clicks'),
    State('gantt-chart', 'figure'),
    prevent_initial_call=True
)
def gantt_export_callback(n_clicks_png: Optional[int], n_clicks_html: Optional[int], figure: Figure) -> str:
    """Handle gantt chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if 'png' in button_id:
            result = export_chart_png(figure, "gantt_chart.png")
            if result:
                return f"✅ PNG exported to: {result}"
            else:
                return "❌ PNG export failed"
        elif 'html' in button_id:
            result = export_chart_html(figure, "gantt_chart.html")
            if result:
                return f"✅ HTML exported to: {result}"
            else:
                return "❌ HTML export failed"
    except Exception as e:
        return f"❌ Export error: {e}"
    
    return ""


# Metrics export callback
@callback(
    Output('export-metrics-chart-status', 'children'),
    Input('export-metrics-chart-png-btn', 'n_clicks'),
    Input('export-metrics-chart-html-btn', 'n_clicks'),
    State('metrics-chart', 'figure'),
    prevent_initial_call=True
)
def metrics_export_callback(n_clicks_png: Optional[int], n_clicks_html: Optional[int], figure: Figure) -> str:
    """Handle metrics chart export."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if 'png' in button_id:
            result = export_chart_png(figure, "metrics_chart.png")
            if result:
                return f"✅ PNG exported to: {result}"
            else:
                return "❌ PNG export failed"
        elif 'html' in button_id:
            result = export_chart_html(figure, "metrics_chart.html")
            if result:
                return f"✅ HTML exported to: {result}"
            else:
                return "❌ HTML export failed"
    except Exception as e:
        return f"❌ Export error: {e}"
    
    return ""
